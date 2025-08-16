from pydantic import BaseModel, HttpUrl, field_validator, EmailStr
from typing import Optional, Literal

class TrackerCreate(BaseModel):
    url: HttpUrl
    selector: Optional[str] = None
    alert_method: Literal["email", "sms"]
    contact: str
    name: Optional[str] = None

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

    class Config:
        from_attributes = True
