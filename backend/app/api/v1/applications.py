from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
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
def create_application(body: ApplicationCreate, db: Session = Depends(get_db)):
    return ApplicationService.create(db, body)


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(db: Session = Depends(get_db)):
    return ApplicationService.list_all(db)


@router.get("/applications/{app_id}", response_model=ApplicationResponse)
def get_application(app_id: int, db: Session = Depends(get_db)):
    app = ApplicationService.get(db, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/applications/{app_id}", response_model=ApplicationResponse)
def update_application(app_id: int, body: ApplicationUpdate, db: Session = Depends(get_db)):
    app = ApplicationService.update(db, app_id, body)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/applications/{app_id}/status", response_model=ApplicationResponse)
def update_status(app_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    app = ApplicationService.update_status(db, app_id, body)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.delete("/applications/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(get_db)):
    ok = ApplicationService.delete(db, app_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Application not found")


@router.get("/applications/{app_id}/cooldown", response_model=CooldownInfo)
def check_cooldown(app_id: int, db: Session = Depends(get_db)):
    info = ApplicationService.check_cooldown(db, app_id)
    if not info:
        raise HTTPException(status_code=404, detail="Application not found")
    return info
