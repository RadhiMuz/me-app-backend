from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select, SQLModel, Field
from jose import JWTError, jwt
from db.database import get_session
import hashlib, secrets

router = APIRouter()

SECRET_KEY = "factory-apps-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ROLES = ["superadmin", "admin", "user"]


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":", 1)
        return hashlib.sha256((salt + plain).encode()).hexdigest() == hashed
    except Exception:
        return False


def create_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    full_name: str = Field(default="")
    hashed_password: str
    role: str = Field(default="user")  # superadmin | admin | user
    email: str = Field(default="")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    username: str
    full_name: str = ""
    email: str = ""
    password: str
    role: str = "user"


class UserResponse(SQLModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(SQLModel):
    access_token: str
    token_type: str
    username: str
    full_name: str
    email: str
    role: str


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user


def require_admin_or_above(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def seed_admin(session: Session):
    existing = session.exec(select(User)).first()
    if not existing:
        superadmin = User(
            username="superadmin",
            full_name="Super Administrator",
            hashed_password=hash_password("admin123"),
            role="superadmin",
        )
        session.add(superadmin)
        session.commit()
        print("Default superadmin created — username: superadmin, password: admin123")


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form.username)).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")
    return TokenResponse(
        access_token=create_token(user.username),
        token_type="bearer",
        username=user.username,
        full_name=user.full_name,
        email=user.email or "",
        role=user.role,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=List[UserResponse])
def list_users(current_user: User = Depends(require_admin_or_above), session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, current_user: User = Depends(require_superadmin), session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == payload.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    if payload.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {ROLES}")
    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.patch("/users/{user_id}/toggle", response_model=UserResponse)
def toggle_user(user_id: int, current_user: User = Depends(require_superadmin), session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    user.is_active = not user.is_active
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, current_user: User = Depends(require_superadmin), session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    session.delete(user)
    session.commit()


@router.post("/change-password")
def change_password(payload: dict, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not verify_password(payload.get("current_password", ""), current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(payload.get("new_password", ""))
    session.add(current_user)
    session.commit()
    return {"message": "Password changed successfully"}


@router.post("/update-profile")
def update_profile(payload: dict, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if "email" in payload:
        current_user.email = payload["email"]
    if "full_name" in payload:
        current_user.full_name = payload["full_name"]
    session.add(current_user)
    session.commit()
    return {"message": "Profile updated successfully"}