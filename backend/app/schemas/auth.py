from pydantic import BaseModel


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str | None = None
