"""
System Service

This service provides comprehensive system management functionality including:
- System parameters management
- Operation logging and audit trail
- User permission checking
- System configuration management
- Cache management for performance
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..models.system import (
    SystemParameter, Company, SystemPermission, 
    SystemRole, SystemRolePermission, SystemUserRole, UserExtension,
    DatabaseBackup, SystemLicense, EmailTemplate, ApiKey, Webhook,
    SSOConfig, Language, Translation, Branding, DataAccessLog,
    ConsentRecord
)
from ..models.user import User
from ..models.biotime_models import BaseOperationLog as OperationLog
from ..core.rbac import clear_user_permission_cache

logger = logging.getLogger(__name__)


class SystemService:
    """Comprehensive system management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # System Parameters Management
    async def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get system parameter value with caching"""
        try:
            from .redis_client import redis_client
            cache_key = f"sys_param:{key}"
            
            # Try cache first
            cached_value = redis_client.get(cache_key)
            if cached_value is not None:
                # Parse based on parameter type
                param = self.db.query(SystemParameter).filter(
                    SystemParameter.param_key == key
                ).first()
                if param:
                    return self._parse_parameter_value(cached_value, param.param_type)
                return cached_value
            
            # Get from database
            param = self.db.query(SystemParameter).filter(
                SystemParameter.param_key == key
            ).first()
            
            if not param:
                return default
            
            # Cache the value for 30 minutes
            redis_client.setex(cache_key, 1800, str(param.param_value))
            
            return self._parse_parameter_value(param.param_value, param.param_type)
            
        except Exception as e:
            logger.error(f"Error getting parameter {key}: {e}")
            return default
    
    async def set_parameter(self, key: str, value: Any, updated_by: str = None) -> bool:
        """Set system parameter value"""
        try:
            # Get existing parameter
            param = self.db.query(SystemParameter).filter(
                SystemParameter.param_key == key
            ).first()
            
            if not param:
                return False
            
            # Update parameter
            old_value = param.param_value
            param.param_value = str(value)
            param.updated_by = updated_by
            param.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Clear cache
            from .redis_client import redis_client
            cache_key = f"sys_param:{key}"
            redis_client.delete(cache_key)
            
            # Log the change
            await self._log_parameter_change(key, old_value, value, updated_by)
            
            logger.info(f"Parameter {key} updated from {old_value} to {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting parameter {key}: {e}")
            self.db.rollback()
            return False
    
    async def get_parameters_by_module(self, module: str) -> List[Dict[str, Any]]:
        """Get all parameters for a specific module"""
        try:
            parameters = self.db.query(SystemParameter).filter(
                SystemParameter.module == module
            ).all()
            
            result = []
            for param in parameters:
                result.append({
                    "id": param.id,
                    "key": param.param_key,
                    "value": param.param_value,
                    "type": param.param_type,
                    "description": param.description,
                    "is_public": param.is_public,
                    "is_encrypted": param.is_encrypted,
                    "updated_at": param.updated_at,
                    "updated_by": param.updated_by
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting parameters for module {module}: {e}")
            return []
    
    async def get_all_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get all system parameters grouped by module"""
        try:
            parameters = self.db.query(SystemParameter).all()
            
            result = {}
            for param in parameters:
                if param.module not in result:
                    result[param.module] = {}
                
                result[param.module][param.param_key] = {
                    "value": param.param_value,
                    "type": param.param_type,
                    "description": param.description,
                    "is_public": param.is_public,
                    "is_encrypted": param.is_encrypted
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all parameters: {e}")
            return {}
    
    # Operation Log Management
    async def log_operation(self, user_id: int, username: str, module: str, 
                         action: str, target: str = None, result: int = 0,
                         details: Dict = None, ip_address: str = None,
                         user_agent: str = None, session_id: str = None,
                         data_classification: int = 0) -> bool:
        """Log operation to operation log"""
        try:
            log_entry = OperationLog(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                module=module,
                action=action,
                target=target,
                result=result,
                details=details,
                data_classification=data_classification,
                session_id=session_id,
                user_agent=user_agent
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging operation: {e}")
            self.db.rollback()
            return False
    
    async def get_operation_logs(self, start_time: datetime = None, 
                              end_time: datetime = None, user_id: int = None,
                              module: str = None, action: str = None,
                              limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get operation logs with filtering"""
        try:
            query = self.db.query(OperationLog)
            
            # Apply filters
            if start_time:
                query = query.filter(OperationLog.log_time >= start_time)
            
            if end_time:
                query = query.filter(OperationLog.log_time <= end_time)
            
            if user_id:
                query = query.filter(OperationLog.user_id == user_id)
            
            if module:
                query = query.filter(OperationLog.module == module)
            
            if action:
                query = query.filter(OperationLog.action == action)
            
            # Order by time descending
            query = query.order_by(desc(OperationLog.log_time))
            
            # Apply pagination
            logs = query.offset(offset).limit(limit).all()
            
            result = []
            for log in logs:
                result.append({
                    "id": log.id,
                    "log_time": log.log_time,
                    "user_id": log.user_id,
                    "username": log.username,
                    "ip_address": log.ip_address,
                    "module": log.module,
                    "action": log.action,
                    "target": log.target,
                    "result": log.result,
                    "details": log.details,
                    "data_classification": log.data_classification,
                    "session_id": log.session_id,
                    "user_agent": log.user_agent
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting operation logs: {e}")
            return []
    
    async def get_operation_log_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get operation log statistics"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Total operations
            total_ops = self.db.query(OperationLog).filter(
                OperationLog.log_time >= start_date
            ).count()
            
            # Operations by module
            ops_by_module = self.db.query(
                OperationLog.module,
                func.count(OperationLog.id).label('count')
            ).filter(
                OperationLog.log_time >= start_date
            ).group_by(OperationLog.module).all()
            
            # Operations by result
            ops_by_result = self.db.query(
                OperationLog.result,
                func.count(OperationLog.id).label('count')
            ).filter(
                OperationLog.log_time >= start_date
            ).group_by(OperationLog.result).all()
            
            # Top users
            top_users = self.db.query(
                OperationLog.username,
                func.count(OperationLog.id).label('count')
            ).filter(
                OperationLog.log_time >= start_date
            ).group_by(OperationLog.username).order_by(
                desc(func.count(OperationLog.id))
            ).limit(10).all()
            
            return {
                "total_operations": total_ops,
                "operations_by_module": {module: count for module, count in ops_by_module},
                "operations_by_result": {result: count for result, count in ops_by_result},
                "top_users": [{"username": username, "count": count} for username, count in top_users],
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting operation log stats: {e}")
            return {}
    
    # Company Management
    async def get_company(self) -> Optional[Dict[str, Any]]:
        """Get company information"""
        try:
            company = self.db.query(Company).filter(Company.is_active == True).first()
            
            if not company:
                return None
            
            return {
                "id": company.id,
                "company_name": company.company_name,
                "address": company.address,
                "phone": company.phone,
                "email": company.email,
                "website": company.website,
                "logo": company.logo,
                "work_days": company.work_days,
                "timezone": company.timezone,
                "date_format": company.date_format,
                "currency": company.currency,
                "emergency_contact": company.emergency_contact,
                "evac_map_pdf": company.evac_map_pdf,
                "parent_company_id": company.parent_company_id,
                "company_type": company.company_type.value if company.company_type else None,
                "created_at": company.created_at,
                "updated_at": company.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error getting company: {e}")
            return None
    
    async def update_company(self, company_data: Dict[str, Any], updated_by: str = None) -> bool:
        """Update company information"""
        try:
            company = self.db.query(Company).filter(Company.is_active == True).first()
            
            if not company:
                return False
            
            # Update fields
            for key, value in company_data.items():
                if hasattr(company, key) and value is not None:
                    setattr(company, key, value)
            
            company.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"Company information updated by {updated_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating company: {e}")
            self.db.rollback()
            return False
    
    # User Management
    async def get_user_with_extension(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user with extension information"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Get user extension
            extension = self.db.query(UserExtension).filter(
                UserExtension.user_id == user_id
            ).first()
            
            # Get user roles
            user_roles = self.db.query(SystemRole).join(SystemUserRole).filter(
                SystemUserRole.user_id == user_id,
                SystemUserRole.is_active == True
            ).all()
            
            # Get user permissions
            from .rbac import get_user_permissions_list
            permissions = await get_user_permissions_list(user_id, self.db)
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "extension": {
                    "avatar": extension.avatar if extension else None,
                    "sso_id": extension.sso_id if extension else None,
                    "ldap_dn": extension.ldap_dn if extension else None,
                    "api_access": extension.api_access if extension else False,
                    "language": extension.language if extension else 'en',
                    "two_fa_enabled": extension.two_fa_enabled if extension else False,
                    "must_change_pass": extension.must_change_pass if extension else True,
                    "failed_login_attempts": extension.failed_login_attempts if extension else 0,
                    "locked_until": extension.locked_until if extension else None
                },
                "roles": [{"id": role.id, "name": role.name} for role in user_roles],
                "permissions": permissions
            }
            
        except Exception as e:
            logger.error(f"Error getting user with extension: {e}")
            return None
    
    async def update_user_extension(self, user_id: int, extension_data: Dict[str, Any], 
                                updated_by: str = None) -> bool:
        """Update user extension information"""
        try:
            extension = self.db.query(UserExtension).filter(
                UserExtension.user_id == user_id
            ).first()
            
            if not extension:
                # Create new extension
                extension = UserExtension(user_id=user_id)
                self.db.add(extension)
            
            # Update fields
            for key, value in extension_data.items():
                if hasattr(extension, key) and value is not None:
                    setattr(extension, key, value)
            
            extension.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Clear permission cache if roles changed
            if 'roles' in extension_data:
                clear_user_permission_cache(user_id)
            
            logger.info(f"User extension updated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user extension: {e}")
            self.db.rollback()
            return False
    
    # Role Management
    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all system roles"""
        try:
            roles = self.db.query(SystemRole).all()
            
            result = []
            for role in roles:
                # Get role permissions
                permissions = self.db.query(SystemPermission).join(SystemRolePermission).filter(
                    SystemRolePermission.role_id == role.id
                ).all()
                
                # Get role user count
                user_count = self.db.query(SystemUserRole).filter(
                    SystemUserRole.role_id == role.id,
                    SystemUserRole.is_active == True
                ).count()
                
                result.append({
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "level": role.level,
                    "is_system": role.is_system,
                    "is_active": role.is_active,
                    "user_count": user_count,
                    "permissions": [{"code": perm.code, "name": perm.name} for perm in permissions],
                    "created_at": role.created_at,
                    "updated_at": role.updated_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all roles: {e}")
            return []
    
    async def assign_role_to_user(self, user_id: int, role_id: int, 
                               assigned_by: str = None, expires_at: datetime = None) -> bool:
        """Assign role to user"""
        try:
            # Check if assignment already exists
            existing = self.db.query(SystemUserRole).filter(
                SystemUserRole.user_id == user_id,
                SystemUserRole.role_id == role_id
            ).first()
            
            if existing:
                # Reactivate if expired
                existing.is_active = True
                existing.expires_at = expires_at
                existing.assigned_by = assigned_by
            else:
                # Create new assignment
                assignment = SystemUserRole(
                    user_id=user_id,
                    role_id=role_id,
                    assigned_by=assigned_by,
                    expires_at=expires_at,
                    is_active=True
                )
                self.db.add(assignment)
            
            self.db.commit()
            
            # Clear permission cache
            clear_user_permission_cache(user_id)
            
            logger.info(f"Role {role_id} assigned to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning role to user: {e}")
            self.db.rollback()
            return False
    
    # License Management
    async def get_license_info(self) -> Optional[Dict[str, Any]]:
        """Get current license information"""
        try:
            license = self.db.query(SystemLicense).filter(
                SystemLicense.is_active == True
            ).first()
            
            if not license:
                return None
            
            # Check if license is expired
            is_expired = license.expiry_date and license.expiry_date < datetime.now().date()
            
            # Get current usage
            from ..models.user import User
            current_users = self.db.query(User).filter(User.is_active == True).count()
            from ..models.personnel import Personnel
            current_employees = self.db.query(Personnel).filter(Personnel.is_active == True).count()
            # No physical devices in a mobile-only deployment.
            current_devices = 0
            
            return {
                "id": license.id,
                "license_type": license.license_type.value,
                "company_name": license.company_name,
                "issue_date": license.issue_date,
                "expiry_date": license.expiry_date,
                "is_expired": is_expired,
                "days_until_expiry": (license.expiry_date - datetime.now().date()).days if license.expiry_date else None,
                "modules": license.modules,
                "limits": {
                    "max_devices": license.max_devices,
                    "max_employees": license.max_employees
                },
                "usage": {
                    "current_users": current_users,
                    "current_employees": current_employees,
                    "current_devices": current_devices
                },
                "compliance": {
                    "users_compliant": current_users <= license.max_users if license.max_users else True,
                    "employees_compliant": current_employees <= license.max_employees if license.max_employees else True,
                    "devices_compliant": current_devices <= license.max_devices if license.max_devices else True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting license info: {e}")
            return None
    
    # Utility Methods
    def _parse_parameter_value(self, value: str, param_type: str) -> Any:
        """Parse parameter value based on type"""
        try:
            if param_type == 'bool':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif param_type == 'int':
                return int(value)
            elif param_type == 'float':
                return float(value)
            elif param_type == 'json':
                return json.loads(value)
            else:
                return value
        except Exception:
            return value
    
    async def _log_parameter_change(self, key: str, old_value: Any, 
                                  new_value: Any, changed_by: str = None):
        """Log parameter change for audit trail"""
        try:
            await self.log_operation(
                user_id=None,
                username=changed_by or 'system',
                module='system',
                action='parameter_update',
                target=f'parameter:{key}',
                result=0,
                details={
                    'parameter_key': key,
                    'old_value': old_value,
                    'new_value': new_value
                }
            )
        except Exception as e:
            logger.error(f"Error logging parameter change: {e}")


# System service factory
def get_system_service(db: Session) -> SystemService:
    """Get system service instance"""
    return SystemService(db)
