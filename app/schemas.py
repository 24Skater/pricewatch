from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl, EmailStr, Field, model_validator, TypeAdapter


# Field length constants (matching database schema)
class FieldLimits:
    """Maximum field lengths for input validation."""
    URL_MAX = 2000
    NAME_MAX = 500
    SELECTOR_MAX = 1000
    CONTACT_MAX = 255
    EMAIL_MAX = 255
    SMTP_HOST_MAX = 255
    PROFILE_NAME_MAX = 255
    PHONE_MAX = 20


class TrackerCreate(BaseModel):
    """Schema for creating a new price tracker."""
    url: HttpUrl = Field(..., description="Product URL to track")
    selector: Optional[str] = Field(
        None, 
        max_length=FieldLimits.SELECTOR_MAX,
        description="CSS selector for price element"
    )
    alert_method: Literal["email", "sms"] = Field(..., description="Notification method")
    contact: str = Field(
        ..., 
        max_length=FieldLimits.CONTACT_MAX,
        description="Email address or phone number"
    )
    name: Optional[str] = Field(
        None, 
        max_length=FieldLimits.NAME_MAX,
        description="Friendly name for the tracker"
    )
    profile_id: Optional[int] = Field(None, description="Notification profile ID")

    @model_validator(mode="after")
    def validate_contact_matches_method(self):
        if self.alert_method == "email":
            TypeAdapter(EmailStr).validate_python(self.contact)
        elif self.alert_method == "sms":
            digits = [ch for ch in self.contact if ch.isdigit()]
            if len(digits) < 10:
                raise ValueError("Phone number seems invalid for SMS (need at least 10 digits).")
        return self
    
    @model_validator(mode="after")
    def validate_url_length(self):
        """Validate URL length (HttpUrl doesn't have max_length)."""
        url_str = str(self.url)
        if len(url_str) > FieldLimits.URL_MAX:
            raise ValueError(f"URL must be at most {FieldLimits.URL_MAX} characters")
        return self


class TrackerOut(BaseModel):
    """Schema for tracker output/response."""
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
    """Schema for creating a notification profile."""
    name: str = Field(
        ..., 
        min_length=1,
        max_length=FieldLimits.PROFILE_NAME_MAX,
        description="Profile name"
    )
    email_from: Optional[str] = Field(
        None, 
        max_length=FieldLimits.EMAIL_MAX,
        description="From email address"
    )
    smtp_host: Optional[str] = Field(
        None, 
        max_length=FieldLimits.SMTP_HOST_MAX,
        description="SMTP server hostname"
    )
    smtp_port: Optional[int] = Field(
        None, 
        ge=1, 
        le=65535,
        description="SMTP server port"
    )
    smtp_user: Optional[str] = Field(
        None, 
        max_length=FieldLimits.EMAIL_MAX,
        description="SMTP username"
    )
    smtp_pass: Optional[str] = Field(
        None, 
        max_length=FieldLimits.CONTACT_MAX,
        description="SMTP password"
    )
    twilio_account_sid: Optional[str] = Field(
        None, 
        max_length=FieldLimits.EMAIL_MAX,
        description="Twilio Account SID"
    )
    twilio_auth_token: Optional[str] = Field(
        None, 
        max_length=FieldLimits.EMAIL_MAX,
        description="Twilio Auth Token"
    )
    twilio_from_number: Optional[str] = Field(
        None, 
        max_length=FieldLimits.PHONE_MAX,
        description="Twilio phone number"
    )
