from pydantic import BaseModel


class ConnectRequest(BaseModel):
    provider: str
    redirect_uri: str


class ConnectResponse(BaseModel):
    authorize_url: str
    state: str


class CallbackRequest(BaseModel):
    code: str
    state: str


class StoreKeyRequest(BaseModel):
    provider: str
    api_key: str


class ConnectionStatusResponse(BaseModel):
    provider: str
    connected: bool
    expires_at: str | None = None
