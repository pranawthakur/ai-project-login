from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from jose.backends import ECKey
import json

from app.config import settings

bearer_scheme = HTTPBearer()

SUPABASE_PUBLIC_KEY = {
    "x": "Uu49gRgWf8xQCytbX0aWywSPaASUbzH-aJzZ9e_aIY8",
    "y": "wshVnNUXRCWSKXJQd525JpvgIvAF02D5oRKYB2YYcuk",
    "alg": "ES256",
    "crv": "P-256",
    "ext": True,
    "kid": "f16c9d0a-f71e-4c1f-8f9b-2091c07c1f26",
    "kty": "EC",
    "key_ops": ["verify"]
}

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SUPABASE_PUBLIC_KEY,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )

    return payload
