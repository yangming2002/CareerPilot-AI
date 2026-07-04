from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    CooldownInfo,
    StatusUpdate,
)
from app.services.application_service import ApplicationService

router = APIRouter()


@router.post("/applications", response_model=ApplicationResponse, status_code=201)
def create_application(
    body: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ApplicationService.create(db, body, current_user.id)


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ApplicationService.list_all(db, current_user.id)


@router.get("/applications/{app_id}", response_model=ApplicationResponse)
def get_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = ApplicationService.get(db, app_id, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="投递记录不存在或无权访问")
    return app


@router.patch("/applications/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: int,
    body: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = ApplicationService.update(db, app_id, body, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="投递记录不存在或无权访问")
    return app


@router.patch("/applications/{app_id}/status", response_model=ApplicationResponse)
def update_status(
    app_id: int,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = ApplicationService.update_status(db, app_id, body, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="投递记录不存在或无权访问")
    return app


@router.delete("/applications/{app_id}", status_code=204)
def delete_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = ApplicationService.delete(db, app_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="投递记录不存在或无权访问")


@router.get("/applications/{app_id}/cooldown", response_model=CooldownInfo)
def check_cooldown(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    info = ApplicationService.check_cooldown(db, app_id, current_user.id)
    if not info:
        raise HTTPException(status_code=404, detail="投递记录不存在或无权访问")
    return info
