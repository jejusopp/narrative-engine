from __future__ import annotations

from fastapi import APIRouter, Response, status
from app.db.supabase import get_supabase

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check(response: Response):
    health_status = {
        "status": "ok",
        "details": {
            "database": "connected"
        }
    }
    
    try:
        # DB 연결 확인을 위해 간단한 쿼리 실행
        # supabase-py 클라이언트는 리포지토리에서 사용하는 것과 동일하게 .table(...).select(...) 형식을 사용
        # 보통 어떤 테이블이든 존재할 것이므로 'novels' 테이블을 확인하거나, 
        # 더 범용적인 방법이 있다면 그것을 사용하지만 여기서는 novels를 활용
        get_supabase().table("novels").select("count", count="exact").limit(1).execute()
    except Exception as e:
        health_status["status"] = "error"
        health_status["details"]["database"] = f"disconnected: {str(e)}"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return health_status
