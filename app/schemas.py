from pydantic import BaseModel, HttpUrl, EmailStr, field_validator
from typing import Optional, Literal

class TrackerCreate(BaseModel):
    url: HttpUrl
    selector: Optional[str] = None
    alert_method: Literal["email","sms"]
    contact: str
    name: Optional[str] = None
    profile_id: Optional[int] = None

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v, values):
        method = values.get("alert_method")
        if method == "email":
            EmailStr(v)
        elif method == "sms":
            digits = [ch for ch in v if ch.isdigit()]
            if len(digits) < 10:
                raise ValueError("Phone number seems invalid for SMS")
        return v

class TrackerOut(BaseModel):
    id: int
    url: str
    name: Optional[str] = None
    alert_method: str
    contact: str
    selector: Optional[str] = None
    currency: str
    is_active: bool
    last_price: Optional[float] = None
    profile_id: Optional[int] = None

    class Config:
        from_attributes = True

class ProfileCreate(BaseModel):
    name: str
    email_from: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
