import jwt
from typing import Annotated, Any
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks

ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = 100

# Token permanente estará dentro de um banco de dados
PERMANENT_AUTH_TOKEN = "tokenlegalebonito"

# JWT virá de um arquivo .env
JWT_SECRET = "algumsecretlegal"

bearer_scheme = HTTPBearer(auto_error=False)



def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=JWT_EXPIRES_MINUTES)
    # aqui vai mudar quando for fazer um token para cada usuário
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


def require_auth(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais ausentes",
        )
    return decode_access_token(credentials.credentials)
