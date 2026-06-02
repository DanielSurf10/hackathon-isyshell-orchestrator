import secrets
from fastapi import APIRouter, HTTPException, status
from ..core.sercurity import create_access_token, PERMANENT_AUTH_TOKEN, JWT_EXPIRES_MINUTES
from ..models.schemas import AuthTokenResponse, AuthTokenRequest

auth_router = APIRouter()


@auth_router.post("/auth/token", response_model=AuthTokenResponse)
def issue_token(body: AuthTokenRequest) -> AuthTokenResponse:
    if not secrets.compare_digest(body.token, PERMANENT_AUTH_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    # aqui vai mudar quando for fazer um token para cada usuário
    access_token = create_access_token(subject="orchestrator-user")
    return AuthTokenResponse(
        access_token=access_token,
        expires_in=JWT_EXPIRES_MINUTES * 60
    )
