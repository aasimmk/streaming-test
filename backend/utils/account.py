from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError

from backend._config import SECRET_KEY, ALGORITHM
from backend.core.auth import oauth2_scheme, decode_access_token
from backend.core.models import TokenData, UserOut, mock_users, UserInDB

users_db = {}


def get_user(username: str):
    user_dict = mock_users.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


def get_current_user(token: str = Depends(oauth2_scheme)):
    token_data = decode_access_token(token)
    if not token_data or not token_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(token_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_data(token: str = Depends(oauth2_scheme)) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = mock_users.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user
