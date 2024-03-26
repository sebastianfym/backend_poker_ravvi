from pydantic import BaseModel, EmailStr


class DeviceProps(BaseModel):
    device_token: str | None = None
    device_props: dict | None = None


class DeviceLoginProps(DeviceProps):
    login_token: str | None = None


class UserLoginProps(DeviceProps):
    username: str | None = None
    # id: int | None = None
    # email: str | None = None
    password: str


class UserPublicProfile(BaseModel):
    id: int
    name: str | None = None
    image_id: int | None = None

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row.id,
            name=row.name,
            image_id=row.image_id
        )


class UserPrivateProfile(UserPublicProfile):
    id: int
    name: str
    image_id: int | None = None
    email: EmailStr | None = None
    has_password: bool
    country: str | None = None

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row.id,
            name=row.name,
            image_id=row.image_id,
            email=row.email,
            has_password=bool(row.password_hash),
            country=row.country
        )


class UserMutableProps(BaseModel):
    name: str | None = None
    email: str | None = None
    image_id: int | None = None
    country: str | None = None
