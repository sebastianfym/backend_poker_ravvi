from pydantic import BaseModel

from ravvi_poker.api.users.types import UserPrivateProfile



class UserAccessProfile(BaseModel):
    device_token: str | None = None
    login_token: str | None = None
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserPrivateProfile | None


class UserChangePassword(BaseModel):
    current_password: str | None = None
    new_password: str | None = None