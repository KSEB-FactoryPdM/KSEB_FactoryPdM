"""
보안 및 인증 유틸리티
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserPermission
from app.schemas.auth import TokenData

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 토큰 스키마
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """토큰 검증"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        if username is None:
            return None
        
        token_data = TokenData(username=username, user_id=user_id, role=role)
        return token_data
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 사용자 조회"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """현재 활성 사용자 조회"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def check_permission(
    resource: str,
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """권한 확인"""
    # 관리자는 모든 권한 허용
    if current_user.role == "admin":
        return True
    
    # 사용자별 권한 확인
    permission = db.query(UserPermission).filter(
        UserPermission.user_id == current_user.id,
        UserPermission.resource == resource,
        UserPermission.action == action
    ).first()
    
    if permission:
        return True
    
    # 역할별 기본 권한 확인
    if current_user.role == "operator":
        # 운영자는 읽기/쓰기 권한
        if action in ["read", "write"]:
            return True
    elif current_user.role == "viewer":
        # 뷰어는 읽기 권한만
        if action == "read":
            return True
    
    return False


def require_permission(resource: str, action: str):
    """권한 요구 데코레이터"""
    def permission_decorator(func):
        def wrapper(*args, **kwargs):
            # 실제 구현에서는 권한 확인 로직 추가
            return func(*args, **kwargs)
        return wrapper
    return permission_decorator


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """사용자명으로 사용자 조회"""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """사용자 인증"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_permissions(db: Session, user_id: int, role: str):
    """사용자 권한 생성"""
    permissions = []
    
    if role == "admin":
        # 관리자: 모든 권한
        resources = ["devices", "sensors", "anomalies", "rul", "models", "users"]
        actions = ["read", "write", "delete", "admin"]
    elif role == "operator":
        # 운영자: 장비, 센서, 이상탐지, RUL 관리
        resources = ["devices", "sensors", "anomalies", "rul"]
        actions = ["read", "write"]
    else:  # viewer
        # 뷰어: 읽기 권한만
        resources = ["devices", "sensors", "anomalies", "rul"]
        actions = ["read"]
    
    for resource in resources:
        for action in actions:
            permission = UserPermission(
                user_id=user_id,
                resource=resource,
                action=action
            )
            permissions.append(permission)
    
    db.add_all(permissions)
    db.commit()


def check_resource_permission(
    resource: str,
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """리소스별 권한 확인"""
    return check_permission(resource, action, current_user, db)


# 권한 확인 함수들
def require_device_permission(action: str = "read"):
    """장비 권한 확인"""
    return lambda current_user=Depends(get_current_user), db=Depends(get_db): check_permission("devices", action, current_user, db)


def require_sensor_permission(action: str = "read"):
    """센서 권한 확인"""
    return lambda current_user=Depends(get_current_user), db=Depends(get_db): check_permission("sensors", action, current_user, db)


def require_anomaly_permission(action: str = "read"):
    """이상탐지 권한 확인"""
    return lambda current_user=Depends(get_current_user), db=Depends(get_db): check_permission("anomalies", action, current_user, db)


def require_rul_permission(action: str = "read"):
    """RUL 권한 확인"""
    return lambda current_user=Depends(get_current_user), db=Depends(get_db): check_permission("rul", action, current_user, db)


def require_model_permission(action: str = "read"):
    """모델 권한 확인"""
    return lambda current_user=Depends(get_current_user), db=Depends(get_db): check_permission("models", action, current_user, db)


def require_admin_permission():
    """관리자 권한 확인"""
    def admin_check(current_user: User = Depends(get_current_user)):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin permission required"
            )
        return current_user
    return admin_check 