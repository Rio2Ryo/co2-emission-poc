"""認証 API - ログイン/ユーザー管理"""
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import jwt

from app.db.session import SessionLocal
from app.db.base import User

router = APIRouter()
security = HTTPBearer(auto_error=False)

# 設定
JWT_SECRET = os.environ.get("JWT_SECRET", "co2-poc-dev-secret-key-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    salt = "co2-poc-salt-2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """パスワード検証"""
    return hash_password(password) == password_hash


def create_jwt_token(user_id: str, email: str, role: str) -> str:
    """JWT トークン発行"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Optional[dict]:
    """JWT トークン検証"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """現在のユーザーを取得（認証ミドルウェア）"""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_jwt_token(token)
    if not payload:
        return None
    
    return payload


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "user"


@router.post("/login", response_model=LoginResponse, summary="ログイン")
def login(request: LoginRequest):
    """ユーザーログイン"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == request.email,
            User.is_active == 1
        ).first()
        
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")
        
        token = create_jwt_token(user.id, user.email, user.role)
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=user.to_dict(),
        )
    finally:
        db.close()


@router.post("/register", status_code=201, summary="ユーザー登録")
def register(request: RegisterRequest):
    """新規ユーザー登録"""
    db = SessionLocal()
    try:
        # 重複チェック
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="このメールアドレスは既に登録されています")
        
        user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            password_hash=hash_password(request.password),
            role=request.role or "user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {"message": "ユーザーを登録しました", "user": user.to_dict()}
    finally:
        db.close()


@router.get("/me", summary="現在のユーザー情報")
def get_me(current_user: dict = Depends(get_current_user)):
    """現在のユーザー情報を取得"""
    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")
    
    return current_user


@router.get("/users", summary="ユーザー一覧（管理者のみ）")
def list_users(
    current_user: dict = Depends(get_current_user),
):
    """ユーザー一覧を取得（管理者限定）"""
    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == 1).all()
        return {"users": [u.to_dict() for u in users]}
    finally:
        db.close()


def require_auth(current_user: Optional[dict] = Depends(get_current_user)):
    """認証必須チェック"""
    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")
    return current_user
