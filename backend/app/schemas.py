from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=2, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    filename: str
    status: str
    transcript: str | None
    summary: dict | None
    error_message: str | None
    created_at: datetime


class ReportGenerateRequest(BaseModel):
    report_date: date
    additional_notes: str = ""


class ReportUpdateRequest(BaseModel):
    content: dict
    status: str | None = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    report_date: date
    status: str
    content: dict
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    filename: str
    mime_type: str
    file_size: int
    status: str
    error_message: str | None
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str = "新对话"


class AskRequest(BaseModel):
    content: str = Field(min_length=2, max_length=5000)
    document_ids: list[str] = []


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    role: str
    content: str
    citations: list | None
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)


class ApiKeyUpdateRequest(BaseModel):
    api_key: str = Field(min_length=20, max_length=300)
    base_url: str = Field(default="https://api.openai.com/v1", min_length=8, max_length=500)
    model: str = Field(default="gpt-5.5", min_length=2, max_length=100)


class TeamInviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"
