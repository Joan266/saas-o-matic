from fastapi import APIRouter

from app.models.schemas import StatsOut
from app.services import stats as stats_svc

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def get_stats() -> StatsOut:
    return stats_svc.get_stats()
