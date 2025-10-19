from fastapi import APIRouter
from fastapi.responses import FileResponse
from sqlmodel import select, func
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.db import get_session, Incident, CallAttempt

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
async def admin_page():
    """관리자 페이지 HTML 반환"""
    return FileResponse("app/static/admin.html")


@router.get("/stats")
async def get_stats():
    """전체 통계 정보 반환"""
    with get_session() as session:
        # 총 인시던트 수
        total_incidents = session.exec(
            select(func.count(Incident.id))
        ).one()
        
        # 상태별 인시던트 수
        acknowledged = session.exec(
            select(func.count(Incident.id)).where(Incident.status == "ack")
        ).one()
        
        # 총 통화 시도 수
        total_calls = session.exec(
            select(func.count(CallAttempt.id))
        ).one()
        
        # 성공한 통화 수 (answered 또는 ack)
        successful_calls = session.exec(
            select(func.count(CallAttempt.id)).where(
                CallAttempt.result.in_(["answered", "ack"])
            )
        ).one()
        
        # 평균 응답 시간
        avg_duration = session.exec(
            select(func.avg(CallAttempt.duration_sec)).where(
                CallAttempt.duration_sec.isnot(None)
            )
        ).one()
        
        # 오늘 인시던트 수
        today = datetime.utcnow().date()
        today_incidents = session.exec(
            select(func.count(Incident.id)).where(
                func.date(Incident.created_at) == today
            )
        ).one()
        
        # DTMF 입력 통계 (1번: 호전환, 2번: 문자)
        dtmf_1_count = session.exec(
            select(func.count(CallAttempt.id)).where(CallAttempt.dtmf == "1")
        ).one()
        
        dtmf_2_count = session.exec(
            select(func.count(CallAttempt.id)).where(CallAttempt.dtmf == "2")
        ).one()
        
        return {
            "total_incidents": total_incidents,
            "acknowledged_incidents": acknowledged,
            "pending_incidents": total_incidents - acknowledged,
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "success_rate": round(successful_calls / total_calls * 100, 1) if total_calls > 0 else 0,
            "avg_duration_sec": round(avg_duration, 1) if avg_duration else 0,
            "today_incidents": today_incidents,
            "dtmf_transfer_count": dtmf_1_count,
            "dtmf_sms_count": dtmf_2_count,
        }


@router.get("/recent-incidents")
async def get_recent_incidents(limit: int = 50):
    """최근 인시던트 목록"""
    with get_session() as session:
        incidents = session.exec(
            select(Incident).order_by(Incident.created_at.desc()).limit(limit)
        ).all()
        
        result = []
        for inc in incidents:
            # 해당 인시던트의 통화 시도들
            calls = session.exec(
                select(CallAttempt).where(CallAttempt.incident_id == inc.id)
            ).all()
            
            result.append({
                "id": inc.id,
                "summary": inc.summary,
                "status": inc.status,
                "attempts": inc.attempts,
                "created_at": inc.created_at.isoformat(),
                "acknowledged_at": inc.acknowledged_at.isoformat() if inc.acknowledged_at else None,
                "calls": [
                    {
                        "callee": call.callee,
                        "provider": call.provider,
                        "result": call.result,
                        "dtmf": call.dtmf,
                        "duration_sec": call.duration_sec,
                        "created_at": call.created_at.isoformat(),
                    }
                    for call in calls
                ]
            })
        
        return result


@router.get("/hourly-traffic")
async def get_hourly_traffic():
    """시간대별 트래픽 (최근 24시간)"""
    with get_session() as session:
        # 최근 24시간 데이터
        since = datetime.utcnow() - timedelta(hours=24)
        
        incidents = session.exec(
            select(Incident).where(Incident.created_at >= since)
        ).all()
        
        # 시간대별 그룹화
        hourly_data = {}
        for inc in incidents:
            hour = inc.created_at.replace(minute=0, second=0, microsecond=0)
            hour_str = hour.isoformat()
            if hour_str not in hourly_data:
                hourly_data[hour_str] = 0
            hourly_data[hour_str] += 1
        
        # 정렬해서 반환
        return [
            {"hour": hour, "count": count}
            for hour, count in sorted(hourly_data.items())
        ]


@router.get("/provider-stats")
async def get_provider_stats():
    """프로바이더별 통계"""
    with get_session() as session:
        providers = session.exec(
            select(CallAttempt.provider, func.count(CallAttempt.id))
            .group_by(CallAttempt.provider)
        ).all()
        
        result = {}
        for provider, count in providers:
            # 성공률 계산
            successful = session.exec(
                select(func.count(CallAttempt.id))
                .where(CallAttempt.provider == provider)
                .where(CallAttempt.result.in_(["answered", "ack"]))
            ).one()
            
            result[provider] = {
                "total": count,
                "successful": successful,
                "success_rate": round(successful / count * 100, 1) if count > 0 else 0
            }
        
        return result

