from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import os

# Secret key
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    print("⚠️ WARNING: SECRET_KEY environment variable not set. Using default.")
    SECRET_KEY = "a-very-unsafe-default-key-for-local-testing"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # e.g., 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- FIX for ValueError: password cannot be longer than 72 bytes ---
# This helper function is crucial. It encodes the password to bytes and truncates it
# to 72 bytes, which is the maximum length the bcrypt algorithm can handle.
def _truncate_password(password: str) -> bytes:
    """Encodes password to UTF-8 and truncates it to 72 bytes."""
    return password.encode('utf-8')[:72]

def hash_password(password: str) -> str:
    # We use the helper function to ensure the password is safe before hashing.
    safe_password = _truncate_password(password)
    return pwd_context.hash(safe_password)

def verify_password(plain: str, hashed: str) -> bool:
    # We use the helper function here as well to prevent crashes during verification.
    safe_password = _truncate_password(plain)
    return pwd_context.verify(safe_password, hashed)
# --- End of FIX ---

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_user_from_token(token_str: str, db: Session):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token_str)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(models.User).get(int(user_id))
    if not user:
        raise credentials_exception
    return user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return get_user_from_token(token, db)

