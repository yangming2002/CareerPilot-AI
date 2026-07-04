import datetime

from sqlalchemy.orm import Session

from app.models.models import Application, ApplicationStatusHistory
from app.schemas.application import ApplicationCreate, ApplicationUpdate, CooldownInfo, StatusUpdate


class ApplicationService:
    COOLDOWN_STATUSES = {"已挂", "已放弃", "冷静期"}

    @staticmethod
    def create(db: Session, data: ApplicationCreate) -> Application:
        app = Application(
            company=data.company,
            position=data.position,
            channel=data.channel,
            application_date=data.application_date,
            resume_version=data.resume_version,
            status=data.status,
            notes=data.notes,
        )
        db.add(app)
        db.flush()

        db.add(ApplicationStatusHistory(
            application_id=app.id,
            old_status=None,
            new_status=data.status,
            changed_at=datetime.datetime.now(),
        ))
        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def list_all(db: Session) -> list[Application]:
        return db.query(Application).order_by(Application.created_at.desc()).all()

    @staticmethod
    def get(db: Session, app_id: int) -> Application | None:
        return db.query(Application).filter(Application.id == app_id).first()

    @staticmethod
    def update(db: Session, app_id: int, data: ApplicationUpdate) -> Application | None:
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(app, field, value)
        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def update_status(db: Session, app_id: int, data: StatusUpdate) -> Application | None:
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            return None
        old_status = app.status
        app.status = data.status
        db.add(ApplicationStatusHistory(
            application_id=app.id,
            old_status=old_status,
            new_status=data.status,
            changed_at=datetime.datetime.now(),
        ))
        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def delete(db: Session, app_id: int) -> bool:
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            return False
        db.delete(app)
        db.commit()
        return True

    @staticmethod
    def check_cooldown(db: Session, app_id: int) -> CooldownInfo | None:
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            return None

        same_company = (
            db.query(Application)
            .filter(Application.company == app.company, Application.id != app.id)
            .order_by(Application.created_at.desc())
            .first()
        )

        if not same_company:
            return CooldownInfo(
                company=app.company,
                has_active_application=False,
                last_application_date=None,
                last_status=None,
                in_cooldown=False,
                cooldown_message=f"未发现对 {app.company} 的其他投递记录",
            )

        in_cooldown = same_company.status in ApplicationService.COOLDOWN_STATUSES
        return CooldownInfo(
            company=app.company,
            has_active_application=True,
            last_application_date=same_company.application_date,
            last_status=same_company.status,
            in_cooldown=in_cooldown,
            cooldown_message=(
                f"{app.company} 上次投递尚在冷静期（状态：{same_company.status}），建议确认是否可再次投递"
                if in_cooldown
                else f"{app.company} 有历史投递记录，状态：{same_company.status}"
            ),
        )
