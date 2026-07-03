import os
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select, SQLModel, Field
from db.database import get_session
from routers.auth import get_current_user, require_superadmin, require_admin_or_above, User

router = APIRouter()

UPLOAD_DIR = "uploads/reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class UpdateReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str
    location: str
    section: str = Field(default="")
    line: str = Field(default="")
    time_start: str
    time_end: str = Field(default="")
    issue: str
    category: str
    pic: str
    images: str = Field(default="")
    submitted_by: str
    status: str = Field(default="pending")
    admin_comment: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    root_cause_category: Optional[str] = None
    countermeasure: Optional[str] = None
    followup_images: str = Field(default="")
    followup_by: Optional[str] = None
    followup_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReportResponse(SQLModel):
    id: int
    date: str
    location: str
    section: str
    line: str
    time_start: str
    time_end: str
    issue: str
    category: str
    pic: str
    images: List[str]
    submitted_by: str
    status: str
    admin_comment: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    root_cause: Optional[str]
    root_cause_category: Optional[str]
    countermeasure: Optional[str]
    followup_images: List[str]
    followup_by: Optional[str]
    followup_at: Optional[datetime]
    created_at: datetime


class ReviewPayload(SQLModel):
    action: str
    comment: Optional[str] = None


def _to_response(r: UpdateReport) -> ReportResponse:
    images = [i for i in r.images.split(",") if i] if r.images else []
    followup_images = [i for i in r.followup_images.split(",") if i] if r.followup_images else []
    return ReportResponse(
        id=r.id, date=r.date, location=r.location,
        section=r.section or "", line=r.line or "",
        time_start=r.time_start, time_end=r.time_end or "",
        issue=r.issue, category=r.category, pic=r.pic,
        images=images, submitted_by=r.submitted_by,
        status=r.status, admin_comment=r.admin_comment,
        reviewed_by=r.reviewed_by, reviewed_at=r.reviewed_at,
        root_cause=r.root_cause, countermeasure=r.countermeasure,
        root_cause_category=r.root_cause_category,
        followup_images=followup_images, followup_by=r.followup_by,
        followup_at=r.followup_at, created_at=r.created_at,
    )


@router.get("/", response_model=List[ReportResponse])
def list_reports(
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    reports = session.exec(select(UpdateReport)).all()
    if status:
        reports = [r for r in reports if r.status == status]
    return sorted([_to_response(r) for r in reports], key=lambda x: x.created_at, reverse=True)


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(
    date: str = Form(...),
    location: str = Form(...),
    section: str = Form(default=""),
    line: str = Form(default=""),
    time_start: str = Form(...),
    time_end: str = Form(default=""),
    issue: str = Form(...),
    category: str = Form(...),
    pic: str = Form(...),
    images: List[UploadFile] = File(default=[]),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    image_urls = []
    for i, img in enumerate(images[:4]):
        ext = os.path.splitext(img.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]: continue
        fname = f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}{ext}"
        with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
            shutil.copyfileobj(img.file, f)
        image_urls.append(f"/uploads/reports/{fname}")

    report = UpdateReport(
        date=date, location=location, section=section, line=line,
        time_start=time_start, time_end=time_end,
        issue=issue, category=category, pic=pic,
        images=",".join(image_urls),
        submitted_by=current_user.username,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return _to_response(report)


@router.post("/{report_id}/review", response_model=ReportResponse)
def review_report(
    report_id: int,
    payload: ReviewPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_or_above),  # admin + superadmin
):
    report = session.get(UpdateReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if payload.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    report.status = "approved" if payload.action == "approve" else "rejected"
    report.admin_comment = payload.comment
    report.reviewed_by = current_user.username
    report.reviewed_at = datetime.utcnow()
    session.add(report)
    session.commit()
    session.refresh(report)
    return _to_response(report)


@router.post("/{report_id}/followup", response_model=ReportResponse)
async def followup_report(
    report_id: int,
    root_cause: str = Form(...),
    root_cause_category: str = Form(default=""),
    countermeasure: str = Form(...),
    time_end: str = Form(default=""),
    images: List[UploadFile] = File(default=[]),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin_or_above),
):
    report = session.get(UpdateReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "approved":
        raise HTTPException(status_code=400, detail="Only approved reports can be updated")
    # Only the submitter can do follow-up (superadmin can also)
    if current_user.role not in ["superadmin", "admin"] and report.submitted_by != current_user.username:
        raise HTTPException(status_code=403, detail="Only admin or the submitter can update this report")

    image_urls = []
    for i, img in enumerate(images[:4]):
        ext = os.path.splitext(img.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]: continue
        fname = f"followup_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}{ext}"
        with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
            shutil.copyfileobj(img.file, f)
        image_urls.append(f"/uploads/reports/{fname}")

    report.root_cause = root_cause
    report.root_cause_category = root_cause_category
    report.countermeasure = countermeasure
    if time_end:
        report.time_end = time_end
    report.followup_images = ",".join(image_urls)
    report.followup_by = current_user.username
    report.followup_at = datetime.utcnow()
    report.status = "completed"
    session.add(report)
    session.commit()
    session.refresh(report)
    return _to_response(report)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_superadmin),  # superadmin only
):
    report = session.get(UpdateReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    for img_url in (report.images + "," + report.followup_images).split(","):
        if img_url:
            path = img_url.lstrip("/")
            if os.path.exists(path):
                os.remove(path)
    session.delete(report)
    session.commit()