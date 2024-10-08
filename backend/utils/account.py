from fastapi import Depends, HTTPException, status

from ..core import models, auth


def get_user(username: str):
    user_dict = models.mock_users.get(username)
    if user_dict:
        return models.UserInDB(**user_dict)
    return None


def get_current_user(token: str = Depends(auth.oauth2_scheme)):
    token_data = auth.decode_access_token(token)
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
