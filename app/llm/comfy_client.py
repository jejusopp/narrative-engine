import json
import uuid
import urllib.request
import urllib.parse
import websocket
import logging

logger = logging.getLogger("ComfyClient")

class ComfyClient:
    def __init__(self, host: str, client_id: str = None):
        self.host = host
        self.client_id = client_id or str(uuid.uuid4())
        self.ws = None

    def connect(self):
        """WebSocket 연결"""
        ws_url = f"ws://{self.host}/ws?clientId={self.client_id}"
        self.ws = websocket.create_connection(ws_url)
        logger.info(f"Connected to ComfyUI WebSocket: {ws_url}")

    def queue_prompt(self, prompt_workflow: dict):
        """워크플로우 실행 요청"""
        p = {"prompt": prompt_workflow, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{self.host}/prompt", data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename: str, subfolder: str, folder_type: str):
        """생성된 이미지 바이너리 가져오기"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{self.host}/view?{url_values}") as response:
            return response.read()

    def get_history(self, prompt_id: str):
        """작업 이력 확인"""
        with urllib.request.urlopen(f"http://{self.host}/history/{prompt_id}") as response:
            return json.loads(response.read())

    def generate_image(self, workflow: dict) -> bytes:
        """전체 생성 프로세스 실행 (동기 방식)"""
        if not self.ws:
            self.connect()

        prompt_res = self.queue_prompt(workflow)
        prompt_id = prompt_res['prompt_id']
        logger.info(f"Prompt queued with ID: {prompt_id}")

        while True:
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break # 실행 완료
            else:
                continue

        history = self.get_history(prompt_id)[prompt_id]
        
        # 마지막 노드의 결과물 찾기 (보통 SaveImage 노드)
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                image_info = node_output['images'][0]
                return self.get_image(
                    image_info['filename'],
                    image_info['subfolder'],
                    image_info['type']
                )
        
        raise Exception("Failed to find generated image in history")
