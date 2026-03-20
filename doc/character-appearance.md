# 캐릭터 `appearance` 처리 흐름

`app/services` 계층에서 캐릭터 외모(`appearance`)가 **어디서 생성되고**, **어떻게 정규화·저장되며**, **이미지 프롬프트에서 어떻게 보완되는지**를 정리한 문서입니다.

---

## 1. 개요

| 단계 | 담당 모듈 | 역할 |
|------|-----------|------|
| 추출 | `scene_processor` | 장면 텍스트 기준으로 LLM이 `appearance` 생성 |
| 이름 매칭 | `character_resolver` | 알려진 캐릭터와 이름 정규화·매칭 (**DB `appearance`는 여기서 읽지 않음**) |
| 정규화·저장 | `scene_pipeline` | 리스트/`null` 토큰 처리 후 DB upsert |
| 프롬프트 보완 | `scene_pipeline` → `prompt_generator` | 이번 장면 값이 비면 DB 값 사용, 그래도 없으면 기본 문구 |

**한 줄 요약:** 외모의 1차 소스는 **항상 해당 장면에 대한 LLM 출력**이고, **이전에 쌓인 DB 외모는 이미지 프롬프트 조립 시에만** fallback으로 붙습니다.

---

## 2. 장면 분석에서의 추출 (`scene_processor.py`)

`process()`가 Groq에 보내는 프롬프트에서 캐릭터 객체 형식과 `appearance` 의미를 고정합니다.

- **포함:** 사진에 보이는 것만 — 성별·연령대, 명시적으로 묘사된 시각적 특징(머리, 눈, 체형, 복장 등) 최대 2개까지, 전체 최대 3항목.
- **제외:** 목소리, 감정, 성격 등 비시각 정보.
- **언어:** JSON 값은 한국어.
- **없음:** 추론·묘사가 전혀 불가하면 `null`.

관련 코드: `app/services/scene_processor.py` — `characters` 항목 및 `appearance` 규칙 설명 부분.

---

## 3. 이름 해석 단계 (`character_resolver.py`)

`resolve()` / `resolve_all()`은 `known_characters`와 **이름만** 맞춥니다.

- 매칭 성공 시 반환하는 `appearance`는 **`extracted`(이번 LLM 출력)** 의 `appearance`뿐입니다.
- `known_characters`에 이미 저장된 `appearance`를 읽어서 합치지 **않습니다**.

따라서 **이름은 기존 캐릭터인데, 이번 장면에서 외모를 안 쓴 경우** resolve 직후 `appearance`가 비어 있을 수 있습니다.

관련 코드: `app/services/character_resolver.py` — `resolve()` 반환 dict의 `"appearance": extracted.get("appearance")`.

---

## 4. 정규화 및 DB 저장 (`scene_pipeline.py`)

`analyze_scene()`에서 `resolved_characters`마다 다음을 수행합니다.

1. `appearance`가 **리스트**면 `", "`로 이어 문자열로 변환.
2. **쉼표 분리** 후, 토큰이 `null`(대소문자 무시)이면 제거.
3. 남는 조각이 없으면 `None` 처리 후 `CharacterRepository.upsert_character(..., appearance=...)`.

이후 같은 루프에서 `character_appearances` 등장 기록 등은 별도 처리됩니다.

---

## 5. 이미지 프롬프트용 fallback (`scene_pipeline.py` + `prompt_generator.py`)

이미지 프롬프트 생성 직전:

1. `char_repo.list_characters(novel_id)`로 `이름 → appearance` 맵(`db_appearance`) 구성.
2. 각 캐릭터에 대해  
   `appearance = ch.get("appearance") or db_appearance.get(ch.get("name"))`  
   로 **이번 장면 값이 없을 때만** DB 값 사용.

`prompt_generator.generate()`에서는 여전히 비어 있으면 상수 `_DEFAULT_APPEARANCE`(`"a person"`)를 사용합니다. 리스트 형태가 남아 있으면 여기서도 문자열로 합칩니다.

---

## 6. 관련 파일

| 파일 | 내용 |
|------|------|
| `app/services/scene_processor.py` | LLM 프롬프트 및 JSON 구조 정의 |
| `app/services/character_resolver.py` | 이름 정규화·매칭, `appearance`는 추출값만 전달 |
| `app/services/scene_pipeline.py` | 정규화, upsert, `db_appearance` fallback, `generate_image_prompt` 호출 |
| `app/services/prompt_generator.py` | 캐릭터 블록 조립, 빈 외모 시 기본 문구 |

---

## 7. 설계 시 유의점 (참고)

- **Resolver 단계에서 DB 외모를 안 붙이는 것**은 의도적일 수 있음(장면별 최신 묘사만 쓰려는 경우). 반대로 “항상 마지막으로 알려진 외모를 유지”하려면 resolver 또는 upsert 정책을 따로 조정해야 함.
- DB upsert가 **빈 `appearance`로 기존 값을 덮는지** 여부는 `CharacterRepository.upsert_character` 구현에 따름 — 외모가 사라지는 버그를 보려면 레포지토리도 함께 확인할 것.
