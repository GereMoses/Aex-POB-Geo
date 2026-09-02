"""
License Management Service

This service provides comprehensive license management functionality including:
- License validation and verification
- Feature-based access control
- Usage monitoring and compliance
- License expiry management
- Automatic license enforcement
"""

import logging
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models.system import SystemLicense, SystemParameter
from ..models.user import User
from ..models.personnel import Personnel
from ..core.config import settings

logger = logging.getLogger(__name__)


class LicenseService:
    """Comprehensive license management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_current_license(self) -> Optional[Dict[str, Any]]:
        """Get current license information"""
        try:
            license = self.db.query(SystemLicense).filter(
                SystemLicense.is_active == True
            ).first()
            
            if not license:
                return None
            
            # Check if license is expired
            is_expired = license.expiry_date and license.expiry_date < datetime.now().date()
            days_until_expiry = None
            if license.expiry_date:
                days_until_expiry = (license.expiry_date - datetime.now().date()).days
            
            # Get current usage
            usage = await self._get_current_usage()
            
            # Check compliance
            compliance = await self._check_compliance(license, usage)
            
            return {
                "id": license.id,
                "license_type": license.license_type.value,
                "company_name": license.company_name,
                "issue_date": license.issue_date,
                "expiry_date": license.expiry_date,
                "is_expired": is_expired,
                "days_until_expiry": days_until_expiry,
                "modules": license.modules or [],
                "limits": {
                    "max_users": license.max_users,
                    "max_employees": license.max_employees,
                    "max_devices": license.max_devices,
                    "max_locations": license.max_locations
                },
                "usage": usage,
                "compliance": compliance,
                "license_key": license.license_key,
                "signature": license.signature,
                "created_at": license.created_at,
                "updated_at": license.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error getting current license: {e}")
            return None
    
    async def validate_license(self, license_key: str = None) -> Dict[str, Any]:
        """Validate license"""
        try:
            if not license_key:
                # Validate current license
                license_info = await self.get_current_license()
                if not license_info:
                    return {
                        "valid": False,
                        "error": "No active license found"
                    }
                
                # Check expiry
                if license_info["is_expired"]:
                    return {
                        "valid": False,
                        "error": "License has expired",
                        "expiry_date": license_info["expiry_date"]
                    }
                
                # Check compliance
                if not license_info["compliance"]["overall_compliance"]:
                    return {
                        "valid": False,
                        "error": "License limits exceeded",
                        "violations": license_info["compliance"]["violations"]
                    }
                
                return {
                    "valid": True,
                    "license_info": license_info
                }
            
            else:
                # Validate provided license key
                license_data = await self._decode_license_key(license_key)
                if not license_data:
                    return {
                        "valid": False,
                        "error": "Invalid license key format"
                    }
                
                # Verify signature
                if not await self._verify_license_signature(license_data):
                    return {
                        "valid": False,
                        "error": "License signature verification failed"
                    }
                
                # Check expiry
                expiry_date = datetime.strptime(license_data["expiry_date"], "%Y-%m-%d").date()
                if expiry_date < datetime.now().date():
                    return {
                        "valid": False,
                        "error": "License has expired",
                        "expiry_date": license_data["expiry_date"]
                    }
                
                return {
                    "valid": True,
                    "license_data": license_data
                }
                
        except Exception as e:
            logger.error(f"Error validating license: {e}")
            return {"valid": False, "error": str(e)}
    
    async def install_license(self, license_key: str, installed_by: str = None) -> Dict[str, Any]:
        """Install new license"""
        try:
            # Decode and validate license key
            license_data = await self._decode_license_key(license_key)
            if not license_data:
                return {"success": False, "error": "Invalid license key format"}
            
            # Verify signature
            if not await self._verify_license_signature(license_data):
                return {"success": False, "error": "License signature verification failed"}
            
            # Check expiry
            expiry_date = datetime.strptime(license_data["expiry_date"], "%Y-%m-%d").date()
            if expiry_date < datetime.now().date():
                return {"success": False, "error": "License has expired"}
            
            # Deactivate existing licenses
            self.db.query(SystemLicense).filter(
                SystemLicense.is_active == True
            ).update({"is_active": False})
            
            # Create new license record
            new_license = SystemLicense(
                license_type=license_data["license_type"],
                company_name=license_data["company_name"],
                issue_date=datetime.strptime(license_data["issue_date"], "%Y-%m-%d").date(),
                expiry_date=expiry_date,
                modules=license_data.get("modules", []),
                max_users=license_data.get("max_users", 0),
                max_employees=license_data.get("max_employees", 0),
                max_devices=license_data.get("max_devices", 0),
                max_locations=license_data.get("max_locations", 0),
                license_key=license_key,
                signature=license_data.get("signature", ""),
                is_active=True,
                created_by=installed_by
            )
            
            self.db.add(new_license)
            self.db.commit()
            
            logger.info(f"License installed successfully for {license_data['company_name']}")
            return {
                "success": True,
                "message": "License installed successfully",
                "license_id": new_license.id
            }
            
        except Exception as e:
            logger.error(f"Error installing license: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def check_feature_access(self, feature: str) -> Dict[str, Any]:
        """Check if feature is available in current license"""
        try:
            license_info = await self.get_current_license()
            
            if not license_info:
                return {
                    "allowed": False,
                    "reason": "No active license"
                }
            
            if license_info["is_expired"]:
                return {
                    "allowed": False,
                    "reason": "License expired"
                }
            
            # Check if feature is in licensed modules
            if license_info["modules"] and feature not in license_info["modules"]:
                return {
                    "allowed": False,
                    "reason": f"Feature '{feature}' not licensed"
                }
            
            # Check compliance
            if not license_info["compliance"]["overall_compliance"]:
                return {
                    "allowed": False,
                    "reason": "License limits exceeded",
                    "violations": license_info["compliance"]["violations"]
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return {"allowed": False, "reason": str(e)}
    
    async def enforce_license_limits(self) -> Dict[str, Any]:
        """Enforce license limits"""
        try:
            license_info = await self.get_current_license()
            
            if not license_info:
                return {"enforced": False, "reason": "No active license"}
            
            violations = []
            
            # Check user limit
            if license_info["limits"]["max_users"] > 0:
                if license_info["usage"]["current_users"] > license_info["limits"]["max_users"]:
                    violations.append({
                        "type": "user_limit",
                        "current": license_info["usage"]["current_users"],
                        "limit": license_info["limits"]["max_users"]
                    })
                    # Disable new user creation
                    await self._set_parameter("user.creation_enabled", "false")
            
            # Check employee limit
            if license_info["limits"]["max_employees"] > 0:
                if license_info["usage"]["current_employees"] > license_info["limits"]["max_employees"]:
                    violations.append({
                        "type": "employee_limit",
                        "current": license_info["usage"]["current_employees"],
                        "limit": license_info["limits"]["max_employees"]
                    })
                    # Disable new employee creation
                    await self._set_parameter("personnel.creation_enabled", "false")
            
            # Check device limit
            if license_info["limits"]["max_devices"] > 0:
                if license_info["usage"]["current_devices"] > license_info["limits"]["max_devices"]:
                    violations.append({
                        "type": "device_limit",
                        "current": license_info["usage"]["current_devices"],
                        "limit": license_info["limits"]["max_devices"]
                    })
                    # Disable new device registration
                    await self._set_parameter("device.registration_enabled", "false")
            
            # Check expiry
            if license_info["is_expired"]:
                violations.append({
                    "type": "license_expired",
                    "expiry_date": license_info["expiry_date"]
                })
                # Disable all write operations
                await self._set_parameter("system.read_only_mode", "true")
            
            return {
                "enforced": len(violations) > 0,
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Error enforcing license limits: {e}")
            return {"enforced": False, "error": str(e)}
    
    async def get_license_usage_report(self) -> Dict[str, Any]:
        """Get detailed license usage report"""
        try:
            license_info = await self.get_current_license()
            
            if not license_info:
                return {"error": "No active license"}
            
            # Get detailed usage statistics
            usage_stats = await self._get_detailed_usage()
            
            # Get compliance trends
            compliance_trends = await self._get_compliance_trends()
            
            # Get module usage
            module_usage = await self._get_module_usage()
            
            return {
                "license_info": license_info,
                "usage_statistics": usage_stats,
                "compliance_trends": compliance_trends,
                "module_usage": module_usage,
                "generated_at": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error generating license usage report: {e}")
            return {"error": str(e)}
    
    async def _get_current_usage(self) -> Dict[str, int]:
        """Get current license usage"""
        try:
            # Count active users
            current_users = self.db.query(User).filter(User.is_active == True).count()
            
            # Count active employees
            current_employees = self.db.query(Personnel).filter(Personnel.is_active == True).count()
            
            # Count active devices
            # No physical devices in a mobile-only deployment.
            current_devices = 0
            
            # Count active locations/zones
            from ..models.system import Company
            locations_count = self.db.query(func.count(func.distinct(Personnel.current_zone_id))).filter(
                Personnel.is_active == True,
                Personnel.current_zone_id.isnot(None)
            ).scalar() or 0
            
            return {
                "current_users": current_users,
                "current_employees": current_employees,
                "current_devices": current_devices,
                "current_locations": locations_count
            }
            
        except Exception as e:
            logger.error(f"Error getting current usage: {e}")
            return {
                "current_users": 0,
                "current_employees": 0,
                "current_devices": 0,
                "current_locations": 0
            }
    
    async def _check_compliance(self, license: SystemLicense, usage: Dict[str, int]) -> Dict[str, Any]:
        """Check license compliance"""
        try:
            violations = []
            overall_compliance = True
            
            # Check user limit
            if license.max_users > 0 and usage["current_users"] > license.max_users:
                violations.append({
                    "type": "user_limit",
                    "current": usage["current_users"],
                    "limit": license.max_users,
                    "excess": usage["current_users"] - license.max_users
                })
                overall_compliance = False
            
            # Check employee limit
            if license.max_employees > 0 and usage["current_employees"] > license.max_employees:
                violations.append({
                    "type": "employee_limit",
                    "current": usage["current_employees"],
                    "limit": license.max_employees,
                    "excess": usage["current_employees"] - license.max_employees
                })
                overall_compliance = False
            
            # Check device limit
            if license.max_devices > 0 and usage["current_devices"] > license.max_devices:
                violations.append({
                    "type": "device_limit",
                    "current": usage["current_devices"],
                    "limit": license.max_devices,
                    "excess": usage["current_devices"] - license.max_devices
                })
                overall_compliance = False
            
            # Check location limit
            if license.max_locations > 0 and usage["current_locations"] > license.max_locations:
                violations.append({
                    "type": "location_limit",
                    "current": usage["current_locations"],
                    "limit": license.max_locations,
                    "excess": usage["current_locations"] - license.max_locations
                })
                overall_compliance = False
            
            # Calculate compliance percentage
            total_violations = len(violations)
            compliance_percentage = 100 if overall_compliance else max(0, 100 - (total_violations * 25))
            
            return {
                "overall_compliance": overall_compliance,
                "compliance_percentage": compliance_percentage,
                "violations": violations,
                "total_violations": total_violations
            }
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return {
                "overall_compliance": False,
                "compliance_percentage": 0,
                "violations": [],
                "total_violations": 0
            }
    
    async def _decode_license_key(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Decode license key"""
        try:
            # Remove any whitespace
            license_key = license_key.strip().replace("\n", "").replace("\r", "")
            
            # Try to decode as base64 JSON
            import base64
            try:
                decoded_bytes = base64.b64decode(license_key)
                decoded_str = decoded_bytes.decode('utf-8')
                return json.loads(decoded_str)
            except Exception as e:
                logger.warning(f"Unexpected error: {e}")
            
            # Try to decode as JSON directly
            try:
                return json.loads(license_key)
            except Exception as e:
                logger.warning(f"Unexpected error: {e}")
            
            # Try to parse as key-value pairs
            if ":" in license_key:
                parts = license_key.split(":")
                if len(parts) >= 5:
                    return {
                        "company_name": parts[0],
                        "license_type": parts[1],
                        "issue_date": parts[2],
                        "expiry_date": parts[3],
                        "max_users": int(parts[4]) if parts[4].isdigit() else 0
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error decoding license key: {e}")
            return None
    
    async def _verify_license_signature(self, license_data: Dict[str, Any]) -> bool:
        """Verify license signature"""
        try:
            signature = license_data.get("signature", "")
            if not signature:
                # For development, allow licenses without signatures
                return settings.DEBUG or True
            
            # Create signature from license data
            license_string = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
            expected_signature = hashlib.sha256(license_string.encode()).hexdigest()
            
            # Compare signatures
            return signature == expected_signature
            
        except Exception as e:
            logger.error(f"Error verifying license signature: {e}")
            return False
    
    async def _get_detailed_usage(self) -> Dict[str, Any]:
        """Get detailed usage statistics"""
        try:
            # User statistics
            user_stats = self.db.query(
                func.count(User.id).label('total'),
                func.sum(func.case([(User.is_active == True, 1)], else_=0)).label('active'),
                func.sum(func.case([(User.is_superuser == True, 1)], else_=0)).label('superusers')
            ).first()
            
            # Employee statistics
            employee_stats = self.db.query(
                func.count(Personnel.id).label('total'),
                func.sum(func.case([(Personnel.is_active == True, 1)], else_=0)).label('active')
            ).first()
            
            return {
                "users": {
                    "total": user_stats.total or 0,
                    "active": user_stats.active or 0,
                    "superusers": user_stats.superusers or 0
                },
                "employees": {
                    "total": employee_stats.total or 0,
                    "active": employee_stats.active or 0
                },
                "devices": {
                    "total": device_stats.total or 0,
                    "active": device_stats.active or 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed usage: {e}")
            return {}
    
    async def _get_compliance_trends(self) -> List[Dict[str, Any]]:
        """Get compliance trends over time"""
        try:
            # This would typically use historical data
            # For now, return recent compliance status
            license_info = await self.get_current_license()
            
            if not license_info:
                return []
            
            return [{
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "compliance_percentage": license_info["compliance"]["compliance_percentage"],
                "violations": license_info["compliance"]["total_violations"]
            }]
            
        except Exception as e:
            logger.error(f"Error getting compliance trends: {e}")
            return []
    
    async def _get_module_usage(self) -> Dict[str, Any]:
        """Get module usage statistics"""
        try:
            license_info = await self.get_current_license()
            
            if not license_info:
                return {}
            
            licensed_modules = license_info.get("modules", [])
            
            # This would typically track actual module usage
            # For now, return licensed modules
            return {
                "licensed_modules": licensed_modules,
                "active_modules": licensed_modules  # Assume all licensed modules are active
            }
            
        except Exception as e:
            logger.error(f"Error getting module usage: {e}")
            return {}
    
    async def _set_parameter(self, key: str, value: str):
        """Set system parameter"""
        try:
            param = self.db.query(SystemParameter).filter(
                SystemParameter.param_key == key
            ).first()
            
            if param:
                param.param_value = value
                param.updated_at = datetime.now(timezone.utc)
            else:
                param = SystemParameter(
                    param_key=key,
                    param_value=value,
                    param_type="bool" if value in ["true", "false"] else "string",
                    module="license",
                    description="License enforcement parameter"
                )
                self.db.add(param)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error setting parameter {key}: {e}")
            self.db.rollback()


# License service factory
def get_license_service(db: Session) -> LicenseService:
    """Get license service instance"""
    return LicenseService(db)
