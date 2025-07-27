"""
인증 서비스
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.user import User, UserPermission, Role, RolePermission
from app.schemas.auth import UserCreate, UserUpdate, TokenData
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    authenticate_user, create_user_permissions
)

logger = logging.getLogger(__name__)


class AuthService:
    """인증 서비스"""
    
    def create_user(self, db: Session, user_create: UserCreate) -> User:
        """사용자 생성"""
        try:
            # 중복 사용자명 확인
            existing_user = db.query(User).filter(User.username == user_create.username).first()
            if existing_user:
                raise ValueError("Username already registered")
            
            # 중복 이메일 확인
            existing_email = db.query(User).filter(User.email == user_create.email).first()
            if existing_email:
                raise ValueError("Email already registered")
            
            # 비밀번호 해싱
            hashed_password = get_password_hash(user_create.password)
            
            # 사용자 생성
            db_user = User(
                username=user_create.username,
                email=user_create.email,
                hashed_password=hashed_password,
                full_name=user_create.full_name,
                role=user_create.role
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # 사용자 권한 생성
            create_user_permissions(db, db_user.id, user_create.role)
            
            logger.info(f"사용자 생성 완료: {user_create.username}")
            return db_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"사용자 생성 실패: {e}")
            raise
    
    def authenticate_user_and_create_token(self, db: Session, username: str, password: str) -> Optional[str]:
        """사용자 인증 및 토큰 생성"""
        try:
            user = authenticate_user(db, username, password)
            if not user:
                return None
            
            if not user.is_active:
                raise ValueError("Inactive user")
            
            # 토큰 데이터 생성
            token_data = {
                "sub": user.username,
                "user_id": user.id,
                "role": user.role
            }
            
            # 액세스 토큰 생성
            access_token = create_access_token(token_data)
            
            logger.info(f"사용자 인증 성공: {username}")
            return access_token
            
        except Exception as e:
            logger.error(f"사용자 인증 실패: {e}")
            return None
    
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        """사용자 조회"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        return db.query(User).filter(User.username == username).first()
    
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """사용자 목록 조회"""
        return db.query(User).offset(skip).limit(limit).all()
    
    def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """사용자 정보 업데이트"""
        try:
            user = self.get_user(db, user_id)
            if not user:
                return None
            
            update_data = user_update.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            logger.info(f"사용자 정보 업데이트 완료: {user.username}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"사용자 정보 업데이트 실패: {e}")
            return None
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """사용자 삭제"""
        try:
            user = self.get_user(db, user_id)
            if not user:
                return False
            
            # 사용자 권한 삭제
            db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
            
            # 사용자 삭제
            db.delete(user)
            db.commit()
            
            logger.info(f"사용자 삭제 완료: {user.username}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"사용자 삭제 실패: {e}")
            return False
    
    def change_password(self, db: Session, user_id: int, current_password: str, new_password: str) -> bool:
        """비밀번호 변경"""
        try:
            user = self.get_user(db, user_id)
            if not user:
                return False
            
            # 현재 비밀번호 확인
            if not verify_password(current_password, user.hashed_password):
                return False
            
            # 새 비밀번호 해싱
            user.hashed_password = get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"비밀번호 변경 완료: {user.username}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"비밀번호 변경 실패: {e}")
            return False
    
    def get_user_permissions(self, db: Session, user_id: int) -> List[UserPermission]:
        """사용자 권한 조회"""
        return db.query(UserPermission).filter(UserPermission.user_id == user_id).all()
    
    def add_user_permission(self, db: Session, user_id: int, resource: str, action: str) -> bool:
        """사용자 권한 추가"""
        try:
            # 기존 권한 확인
            existing = db.query(UserPermission).filter(
                UserPermission.user_id == user_id,
                UserPermission.resource == resource,
                UserPermission.action == action
            ).first()
            
            if existing:
                return True  # 이미 존재하는 권한
            
            # 새 권한 생성
            permission = UserPermission(
                user_id=user_id,
                resource=resource,
                action=action
            )
            
            db.add(permission)
            db.commit()
            
            logger.info(f"사용자 권한 추가 완료: user_id={user_id}, resource={resource}, action={action}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"사용자 권한 추가 실패: {e}")
            return False
    
    def remove_user_permission(self, db: Session, user_id: int, resource: str, action: str) -> bool:
        """사용자 권한 제거"""
        try:
            permission = db.query(UserPermission).filter(
                UserPermission.user_id == user_id,
                UserPermission.resource == resource,
                UserPermission.action == action
            ).first()
            
            if not permission:
                return True  # 이미 존재하지 않는 권한
            
            db.delete(permission)
            db.commit()
            
            logger.info(f"사용자 권한 제거 완료: user_id={user_id}, resource={resource}, action={action}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"사용자 권한 제거 실패: {e}")
            return False
    
    def create_role(self, db: Session, name: str, description: str = None) -> Optional[Role]:
        """역할 생성"""
        try:
            # 중복 역할명 확인
            existing_role = db.query(Role).filter(Role.name == name).first()
            if existing_role:
                raise ValueError("Role name already exists")
            
            role = Role(name=name, description=description)
            db.add(role)
            db.commit()
            db.refresh(role)
            
            logger.info(f"역할 생성 완료: {name}")
            return role
            
        except Exception as e:
            db.rollback()
            logger.error(f"역할 생성 실패: {e}")
            return None
    
    def get_roles(self, db: Session) -> List[Role]:
        """역할 목록 조회"""
        return db.query(Role).all()
    
    def add_role_permission(self, db: Session, role_id: int, resource: str, action: str) -> bool:
        """역할 권한 추가"""
        try:
            # 기존 권한 확인
            existing = db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.resource == resource,
                RolePermission.action == action
            ).first()
            
            if existing:
                return True  # 이미 존재하는 권한
            
            # 새 권한 생성
            permission = RolePermission(
                role_id=role_id,
                resource=resource,
                action=action
            )
            
            db.add(permission)
            db.commit()
            
            logger.info(f"역할 권한 추가 완료: role_id={role_id}, resource={resource}, action={action}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"역할 권한 추가 실패: {e}")
            return False


# 전역 인증 서비스 인스턴스
auth_service = AuthService() 