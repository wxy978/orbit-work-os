from datetime import date
from pathlib import Path
import shutil
from contextlib import asynccontextmanager
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from . import ai
from .auth import create_token, current_user, decrypt_secret, encrypt_secret, hash_password, verify_password
from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import ChatMessage, Conversation, DailyReport, Document, DocumentChunk, Meeting, TeamInvitation, User, UserApiCredential
from .schemas import ApiKeyUpdateRequest, AskRequest, AuthResponse, ConversationCreate, DocumentOut, LoginRequest, MeetingOut, MessageOut, ProfileUpdateRequest, RegisterRequest, ReportGenerateRequest, ReportOut, ReportUpdateRequest, TeamInviteRequest, UserOut

@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Orbit Work OS API", version="1.0.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "ai_mode": "openai" if settings.openai_api_key else "demo"}


@app.post("/api/v1/auth/desktop-session", response_model=AuthResponse)
def desktop_session(db: Session = Depends(get_db)):
    """Create or resume the single local desktop workspace."""
    email = "local@orbit.work"
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, password_hash=hash_password(__import__("secrets").token_urlsafe(32)), display_name="本地用户")
        db.add(user); db.commit(); db.refresh(user)
    return AuthResponse(access_token=create_token(user.id), user=UserOut.model_validate(user))


@app.post("/api/v1/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "该邮箱已注册")
    user = User(email=email, password_hash=hash_password(payload.password), display_name=payload.display_name)
    db.add(user); db.commit(); db.refresh(user)
    return AuthResponse(access_token=create_token(user.id), user=UserOut.model_validate(user))


@app.post("/api/v1/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "邮箱或密码错误")
    return AuthResponse(access_token=create_token(user.id), user=UserOut.model_validate(user))


@app.get("/api/v1/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


def save_upload(upload: UploadFile, folder: str) -> tuple[Path, int]:
    suffix = Path(upload.filename or "upload").suffix.lower()
    target_dir = settings.upload_dir / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{__import__('uuid').uuid4()}{suffix}"
    with target.open("wb") as output:
        shutil.copyfileobj(upload.file, output)
    size = target.stat().st_size
    if size > 100 * 1024 * 1024:
        target.unlink(missing_ok=True)
        raise HTTPException(413, "文件不能超过 100MB")
    return target, size


def user_api_key(db: Session, user_id: str) -> str | dict | None:
    credential = db.get(UserApiCredential, user_id)
    if not credential:
        return None
    value = decrypt_secret(credential.encrypted_api_key)
    try:
        return __import__("json").loads(value)
    except (ValueError, TypeError):
        return value


def process_meeting(meeting_id: str):
    db = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if not meeting: return
        meeting.status = "transcribing"; db.commit()
        key = user_api_key(db, meeting.user_id)
        meeting.transcript = ai.transcribe(Path(meeting.file_path), key)
        meeting.status = "summarizing"; db.commit()
        meeting.summary = ai.summarize(meeting.transcript, key)
        meeting.status = "completed"; db.commit()
    except Exception as exc:
        meeting = db.get(Meeting, meeting_id)
        if meeting:
            meeting.status = "failed"; meeting.error_message = str(exc)[:1000]; db.commit()
    finally: db.close()


@app.post("/api/v1/meetings", response_model=MeetingOut)
def upload_meeting(background: BackgroundTasks, title: str = Form(...), file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not (file.content_type or "").startswith("audio/"):
        raise HTTPException(415, "请上传音频文件")
    path, _ = save_upload(file, "meetings")
    meeting = Meeting(user_id=user.id, title=title, filename=file.filename or "meeting-audio", file_path=str(path), mime_type=file.content_type or "audio/mpeg")
    db.add(meeting); db.commit(); db.refresh(meeting)
    background.add_task(process_meeting, meeting.id)
    return meeting


@app.get("/api/v1/meetings", response_model=list[MeetingOut])
def meetings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Meeting).where(Meeting.user_id == user.id).order_by(desc(Meeting.created_at))).all()


@app.get("/api/v1/meetings/{meeting_id}", response_model=MeetingOut)
def meeting_detail(meeting_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user.id))
    if not item: raise HTTPException(404, "会议不存在")
    return item


@app.delete("/api/v1/meetings/{meeting_id}")
def delete_meeting(meeting_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user.id))
    if not item: raise HTTPException(404, "会议不存在")
    Path(item.file_path).unlink(missing_ok=True); db.delete(item); db.commit()
    return {"ok": True}


@app.post("/api/v1/reports/daily/generate", response_model=ReportOut)
def report_generate(payload: ReportGenerateRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    day_meetings = db.scalars(select(Meeting).where(Meeting.user_id == user.id)).all()
    context = "\n".join((m.transcript or "") for m in day_meetings if m.created_at.date() == payload.report_date)
    content = ai.generate_report(context, payload.additional_notes, user_api_key(db, user.id))
    report = db.scalar(select(DailyReport).where(DailyReport.user_id == user.id, DailyReport.report_date == payload.report_date))
    if report: report.content = content
    else: report = DailyReport(user_id=user.id, report_date=payload.report_date, content=content); db.add(report)
    db.commit(); db.refresh(report); return report


@app.get("/api/v1/reports/daily", response_model=list[ReportOut])
def reports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(DailyReport).where(DailyReport.user_id == user.id).order_by(desc(DailyReport.report_date))).all()


@app.patch("/api/v1/reports/daily/{report_id}", response_model=ReportOut)
def report_update(report_id: str, payload: ReportUpdateRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    report = db.scalar(select(DailyReport).where(DailyReport.id == report_id, DailyReport.user_id == user.id))
    if not report: raise HTTPException(404, "日报不存在")
    report.content = payload.content
    if payload.status: report.status = payload.status
    db.commit(); db.refresh(report); return report


def process_document(document_id: str):
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc: return
        doc.status = "indexing"; db.commit()
        chunks = ai.split_text(ai.extract_text(Path(doc.file_path), doc.mime_type))
        if not chunks: raise ValueError("未能从文档中提取文字")
        embeddings = ai.embed(chunks, user_api_key(db, doc.user_id))
        for i, (content, vector) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(document_id=doc.id, chunk_index=i, content=content, embedding=vector))
        doc.status = "ready"; db.commit()
    except Exception as exc:
        doc = db.get(Document, document_id)
        if doc: doc.status = "failed"; doc.error_message = str(exc)[:1000]; db.commit()
    finally: db.close()


@app.post("/api/v1/documents", response_model=DocumentOut)
def upload_document(background: BackgroundTasks, title: str = Form(...), file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    allowed = {".pdf", ".docx", ".txt", ".md"}
    if Path(file.filename or "").suffix.lower() not in allowed: raise HTTPException(415, "仅支持 PDF、DOCX、TXT、Markdown")
    path, size = save_upload(file, "documents")
    doc = Document(user_id=user.id, title=title, filename=file.filename or "document", file_path=str(path), mime_type=file.content_type or "application/octet-stream", file_size=size)
    db.add(doc); db.commit(); db.refresh(doc); background.add_task(process_document, doc.id); return doc


@app.get("/api/v1/documents", response_model=list[DocumentOut])
def documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Document).where(Document.user_id == user.id).order_by(desc(Document.created_at))).all()


@app.delete("/api/v1/documents/{document_id}")
def delete_document(document_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user.id))
    if not doc: raise HTTPException(404, "文档不存在")
    Path(doc.file_path).unlink(missing_ok=True); db.delete(doc); db.commit(); return {"ok": True}


@app.post("/api/v1/conversations")
def conversation_create(payload: ConversationCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Conversation(user_id=user.id, title=payload.title); db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "title": item.title}


@app.get("/api/v1/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def conversation_messages(conversation_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not conv: raise HTTPException(404, "对话不存在")
    return db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conv.id).order_by(ChatMessage.created_at)).all()


@app.post("/api/v1/conversations/{conversation_id}/messages", response_model=MessageOut)
def ask(conversation_id: str, payload: AskRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not conv: raise HTTPException(404, "对话不存在")
    db.add(ChatMessage(conversation_id=conv.id, role="user", content=payload.content))
    key = user_api_key(db, user.id)
    query_vector = ai.embed([payload.content], key)[0]
    statement = select(DocumentChunk).join(Document).where(Document.user_id == user.id, Document.status == "ready")
    if payload.document_ids: statement = statement.where(Document.id.in_(payload.document_ids))
    chunks = db.scalars(statement).all()
    def score(chunk: DocumentChunk) -> float:
        return ai.cosine(query_vector, chunk.embedding or []) if (key or settings.openai_api_key) else ai.lexical_score(payload.content, chunk.content)
    ranked = sorted(chunks, key=score, reverse=True)
    minimum_score = 0.15 if (key or settings.openai_api_key) else 0.12
    contexts = [{"content": c.content, "document_id": c.document_id, "chunk_id": c.id, "score": score(c)} for c in ranked[:6] if score(c) >= minimum_score]
    citations = [{"document_id": c["document_id"], "chunk_id": c["chunk_id"], "quote": c["content"][:180], "score": round(c["score"], 4)} for c in contexts]
    message = ChatMessage(conversation_id=conv.id, role="assistant", content=ai.answer(payload.content, contexts, key), citations=citations)
    db.add(message); db.commit(); db.refresh(message); return message


@app.patch("/api/v1/settings/profile", response_model=UserOut)
def update_profile(payload: ProfileUpdateRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.display_name = payload.display_name.strip()
    db.commit(); db.refresh(user); return user


@app.get("/api/v1/settings/api-key")
def api_key_status(user: User = Depends(current_user), db: Session = Depends(get_db)):
    credential = db.get(UserApiCredential, user.id)
    config = user_api_key(db, user.id) if credential else {}
    config = config if isinstance(config, dict) else {}
    return {"configured": bool(credential), "key_hint": credential.key_hint if credential else None, "provider": "OpenAI Compatible", "base_url": config.get("base_url", "https://api.openai.com/v1"), "model": config.get("model", config.get("text_model", "gpt-5.5"))}


@app.put("/api/v1/settings/api-key")
def update_api_key(payload: ApiKeyUpdateRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    value = payload.api_key.strip()
    credential = db.get(UserApiCredential, user.id)
    config = payload.model_dump(); config["api_key"] = value; config["base_url"] = config["base_url"].rstrip("/")
    encrypted = encrypt_secret(__import__("json").dumps(config))
    hint = f"{value[:7]}…{value[-4:]}"
    if credential:
        credential.encrypted_api_key = encrypted; credential.key_hint = hint
    else:
        db.add(UserApiCredential(user_id=user.id, encrypted_api_key=encrypted, key_hint=hint))
    db.commit()
    return api_key_status(user, db)


@app.post("/api/v1/settings/api-key/test")
def test_api_key(payload: ApiKeyUpdateRequest, user: User = Depends(current_user)):
    try:
        result = ai.client(payload.model_dump()).models.list()
        return {"ok": True, "message": "连接成功", "model_count": len(result.data)}
    except Exception as exc:
        raise HTTPException(400, f"连接失败：{str(exc)[:300]}") from exc


@app.delete("/api/v1/settings/api-key")
def delete_api_key(user: User = Depends(current_user), db: Session = Depends(get_db)):
    credential = db.get(UserApiCredential, user.id)
    if credential: db.delete(credential); db.commit()
    return {"configured": False, "key_hint": None, "provider": "OpenAI Compatible", "base_url": "https://api.openai.com/v1", "model": "gpt-5.5"}


@app.get("/api/v1/team")
def team(user: User = Depends(current_user), db: Session = Depends(get_db)):
    invitations = db.scalars(select(TeamInvitation).where(TeamInvitation.owner_id == user.id).order_by(desc(TeamInvitation.created_at))).all()
    return {"members": [{"id": user.id, "email": user.email, "display_name": user.display_name, "role": "owner", "status": "active"}], "invitations": [{"id": i.id, "email": i.email, "role": i.role, "status": i.status, "created_at": i.created_at} for i in invitations]}


@app.post("/api/v1/team/invitations")
def invite_member(payload: TeamInviteRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if payload.role not in {"admin", "member"}: raise HTTPException(422, "角色不合法")
    email = payload.email.lower()
    existing = db.scalar(select(TeamInvitation).where(TeamInvitation.owner_id == user.id, TeamInvitation.email == email, TeamInvitation.status == "pending"))
    if existing: raise HTTPException(409, "该邮箱已有待接受邀请")
    invitation = TeamInvitation(owner_id=user.id, email=email, role=payload.role)
    db.add(invitation); db.commit(); db.refresh(invitation)
    return {"id": invitation.id, "email": invitation.email, "role": invitation.role, "status": invitation.status, "created_at": invitation.created_at}


@app.delete("/api/v1/team/invitations/{invitation_id}")
def cancel_invitation(invitation_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    invitation = db.scalar(select(TeamInvitation).where(TeamInvitation.id == invitation_id, TeamInvitation.owner_id == user.id))
    if not invitation: raise HTTPException(404, "邀请不存在")
    db.delete(invitation); db.commit(); return {"ok": True}


@app.get("/api/v1/analytics")
def analytics(user: User = Depends(current_user), db: Session = Depends(get_db)):
    meeting_count = db.scalar(select(func.count()).select_from(Meeting).where(Meeting.user_id == user.id)) or 0
    completed_meetings = db.scalar(select(func.count()).select_from(Meeting).where(Meeting.user_id == user.id, Meeting.status == "completed")) or 0
    document_count = db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user.id)) or 0
    ready_documents = db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user.id, Document.status == "ready")) or 0
    report_count = db.scalar(select(func.count()).select_from(DailyReport).where(DailyReport.user_id == user.id)) or 0
    question_count = db.scalar(select(func.count()).select_from(ChatMessage).join(Conversation).where(Conversation.user_id == user.id, ChatMessage.role == "user")) or 0
    recent_meetings = db.scalars(select(Meeting).where(Meeting.user_id == user.id).order_by(desc(Meeting.created_at)).limit(7)).all()
    return {"totals": {"meetings": meeting_count, "reports": report_count, "documents": document_count, "questions": question_count}, "rates": {"meeting_completion": round(completed_meetings / meeting_count * 100) if meeting_count else 0, "document_ready": round(ready_documents / document_count * 100) if document_count else 0}, "recent_meetings": [{"title": m.title, "status": m.status, "created_at": m.created_at} for m in recent_meetings]}
