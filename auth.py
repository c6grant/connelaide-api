from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
from functools import lru_cache
from auth0_config import AUTH0_DOMAIN, AUTH0_API_AUDIENCE, AUTH0_ISSUER, AUTH0_ALGORITHMS

security = HTTPBearer()


@lru_cache()
def get_jwks():
    """Cache the JWKS (JSON Web Key Set) from Auth0"""
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    return jwks


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify the Auth0 JWT token
    Returns the decoded token payload if valid
    Raises HTTPException if invalid
    """
    token = credentials.credentials
    
    try:
        # Get the token header to find the key id (kid)
        unverified_header = jwt.get_unverified_header(token)
        
        # Get the JWKS and find the right key
        jwks = get_jwks()
        rsa_key = {}
        
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
        
        # Verify the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_API_AUDIENCE,
            issuer=AUTH0_ISSUER
        )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unable to validate token: {str(e)}"
        )


def get_current_user(token_payload: dict = Depends(verify_token)) -> dict:
    """
    Extract user information from the verified token
    """
    return {
        "sub": token_payload.get("sub"),
        "permissions": token_payload.get("permissions", []),
        "email": token_payload.get("email"),
    }
