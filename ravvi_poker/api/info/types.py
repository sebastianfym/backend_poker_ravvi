from pydantic import BaseModel


class TimeZoneInput(BaseModel):
    timezone_user: str | None