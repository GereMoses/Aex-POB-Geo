"""
Personnel QR Code Generation Service

This service handles QR code generation for personnel identification,
including badge QR codes, location QR codes, and access control QR codes.
"""

import qrcode
from io import BytesIO
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from PIL import Image, ImageDraw, ImageFont
import json
import uuid

from ..models.personnel import Personnel

import logging

logger = logging.getLogger(__name__)
from ..core.database import get_db


class QRCodeService:
    """Service for generating and managing personnel QR codes"""
    
    def __init__(self):
        # QR code types
        self.qr_types = {
            "BADGE": "Personnel badge identification",
            "ACCESS": "Access control verification",
            "LOCATION": "Location check-in/out",
            "EMERGENCY": "Emergency contact information",
            "TRAINING": "Training verification",
            "CERTIFICATION": "Certification verification"
        }
        
        # QR code sizes
        self.sizes = {
            "SMALL": 150,
            "MEDIUM": 250,
            "LARGE": 400,
            "EXTRA_LARGE": 600
        }
        
        # Default QR code settings
        self.default_settings = {
            "error_correction": "M",  # Medium error correction
            "box_size": 10,
            "border": 4,
            "fill_color": "black",
            "back_color": "white"
        }
    
    async def generate_personnel_qr_code(
        self,
        personnel_id: int,
        qr_type: str = "BADGE",
        size: str = "MEDIUM",
        include_logo: bool = True,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Generate QR code for personnel
        
        Args:
            personnel_id: Personnel ID
            qr_type: Type of QR code to generate
            size: Size of QR code
            include_logo: Whether to include company logo
            db: Database session
            
        Returns:
            Generated QR code information
        """
        if db is None:
            db = next(get_db())
        
        # Validate QR type
        if qr_type not in self.qr_types:
            raise ValueError(f"Invalid QR code type: {qr_type}")
        
        # Get personnel
        personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not personnel:
            raise ValueError(f"Personnel with ID {personnel_id} not found")
        
        # Generate QR code data based on type
        qr_data = await self._generate_qr_data(personnel, qr_type, db)
        
        # Generate QR code image
        qr_image = await self._generate_qr_image(qr_data, size, include_logo)
        
        # Convert to base64 for storage/transmission
        qr_base64 = self._image_to_base64(qr_image)
        
        # Create QR code record
        qr_record = {
            "id": str(uuid.uuid4()),
            "personnel_id": personnel_id,
            "qr_type": qr_type,
            "qr_data": qr_data,
            "qr_base64": qr_base64,
            "size": self.sizes[size],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": self._calculate_expiry_date(qr_type),
            "is_active": True,
            "usage_count": 0
        }
        
        return {
            "success": True,
            "qr_code": qr_record,
            "message": f"QR code generated successfully for {qr_type}"
        }
    
    async def generate_bulk_qr_codes(
        self,
        personnel_ids: List[int],
        qr_type: str = "BADGE",
        size: str = "MEDIUM",
        include_logo: bool = True,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Generate QR codes for multiple personnel
        
        Args:
            personnel_ids: List of personnel IDs
            qr_type: Type of QR code to generate
            size: Size of QR codes
            include_logo: Whether to include company logo
            db: Database session
            
        Returns:
            Bulk QR code generation result
        """
        if db is None:
            db = next(get_db())
        
        results = []
        failed = []
        
        for personnel_id in personnel_ids:
            try:
                result = await self.generate_personnel_qr_code(
                    personnel_id, qr_type, size, include_logo, db
                )
                results.append(result)
            except Exception as e:
                failed.append({
                    "personnel_id": personnel_id,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_requested": len(personnel_ids),
            "successful": len(results),
            "failed": len(failed),
            "qr_codes": results,
            "failed_items": failed
        }
    
    async def _generate_qr_data(
        self,
        personnel: Personnel,
        qr_type: str,
        db: Session
    ) -> Dict[str, Any]:
        """Generate QR code data based on type"""
        
        base_data = {
            "id": personnel.id,
            "badge_id": personnel.badge_id,
            "full_name": personnel.full_name,
            "company": personnel.company,
            "qr_type": qr_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "verification_token": str(uuid.uuid4())
        }
        
        if qr_type == "BADGE":
            # Badge QR code with basic identification
            return {
                **base_data,
                "type": "PERSONNEL_BADGE",
                "role": personnel.role,
                "department": getattr(personnel, 'department', ''),
                "status": personnel.status,
                "photo": getattr(personnel, 'photo_url', '')
            }
        
        elif qr_type == "ACCESS":
            # Access control QR code with permissions
            from ..services.role_permission_service import role_permission_service
            
            permissions = await role_permission_service.get_personnel_permissions(personnel.id, db)
            roles = await role_permission_service.get_personnel_roles(personnel.id, db)
            
            return {
                **base_data,
                "type": "ACCESS_CONTROL",
                "permissions": list(permissions),
                "roles": [role["role_name"] for role in roles],
                "access_level": max([role.get("level", 0) for role in roles] + [0]),
                "valid_locations": getattr(personnel, 'authorized_locations', []),
                "time_restrictions": getattr(personnel, 'access_time_restrictions', {})
            }
        
        elif qr_type == "LOCATION":
            # Location check-in/out QR code
            return {
                **base_data,
                "type": "LOCATION_CHECK",
                "current_location": getattr(personnel, 'current_location', ''),
                "authorized_zones": getattr(personnel, 'authorized_zones', []),
                "check_in_required": True,
                "gps_coordinates": getattr(personnel, 'last_known_coordinates', {})
            }
        
        elif qr_type == "EMERGENCY":
            # Emergency contact QR code
            emergency_info = getattr(personnel, 'emergency_contact', {})
            
            return {
                **base_data,
                "type": "EMERGENCY_INFO",
                "emergency_contacts": emergency_info.get('contacts', [])[:3],  # Top 3 contacts
                "blood_group": getattr(personnel, 'blood_group', ''),
                "medical_conditions": emergency_info.get('medical_conditions', ''),
                "allergies": emergency_info.get('allergies', ''),
                "medications": emergency_info.get('medications', ''),
                "special_instructions": emergency_info.get('special_instructions', '')
            }
        
        elif qr_type == "TRAINING":
            # Training verification QR code
            from ..services.certification_training_service import certification_training_service
            
            try:
                training_records = await certification_training_service.get_personnel_training_records(personnel.id, db)
                recent_training = training_records[:5]  # Last 5 training records
            except Exception as e:
                recent_training = []
            
            return {
                **base_data,
                "type": "TRAINING_VERIFICATION",
                "training_records": recent_training,
                "last_training": recent_training[0] if recent_training else None,
                "training_status": "COMPLIANT" if len(recent_training) > 0 else "PENDING"
            }
        
        elif qr_type == "CERTIFICATION":
            # Certification verification QR code
            from ..services.certification_training_service import certification_training_service
            
            try:
                certifications = await certification_training_service.get_personnel_certifications(personnel.id, db)
                valid_certs = [cert for cert in certifications if cert.get('status') == 'VALID']
            except Exception as e:
                valid_certs = []
            
            return {
                **base_data,
                "type": "CERTIFICATION_VERIFICATION",
                "certifications": valid_certs[:3],  # Top 3 valid certifications
                "total_certifications": len(valid_certs),
                "certification_status": "VALID" if len(valid_certs) > 0 else "EXPIRED"
            }
        
        else:
            return base_data
    
    async def _generate_qr_image(
        self,
        qr_data: Dict[str, Any],
        size: str,
        include_logo: bool
    ) -> Image.Image:
        """Generate QR code image"""
        
        # Convert data to JSON string
        qr_string = json.dumps(qr_data, separators=(',', ':'))
        
        # Get size
        img_size = self.sizes.get(size, self.sizes["MEDIUM"])
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{self.default_settings["error_correction"]}'),
            box_size=self.default_settings["box_size"],
            border=self.default_settings["border"]
        )
        
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        # Create image
        qr_img = qr.make_image(
            fill_color=self.default_settings["fill_color"],
            back_color=self.default_settings["back_color"]
        )
        
        # Resize to target size
        qr_img = qr_img.resize((img_size, img_size), Image.Resampling.LANCZOS)
        
        # Add logo if requested
        if include_logo:
            qr_img = self._add_logo_to_qr(qr_img)
        
        # Add border and text
        qr_img = self._add_border_and_text(qr_img, qr_data)
        
        return qr_img
    
    def _add_logo_to_qr(self, qr_img: Image.Image) -> Image.Image:
        """Add logo to center of QR code"""
        try:
            # Create a simple logo (in production, you'd use actual company logo)
            logo_size = qr_img.size[0] // 8
            logo = Image.new('RGBA', (logo_size, logo_size), (0, 123, 255, 255))
            
            # Draw a simple "POB" text logo
            draw = ImageDraw.Draw(logo)
            font_size = logo_size // 4
            
            # Try to use a font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception as e:
                font = ImageFont.load_default()
            
            text = "POB"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (logo_size - text_width) // 2
            y = (logo_size - text_height) // 2
            
            draw.text((x, y), text, fill="white", font=font)
            
            # Calculate position to center logo
            pos = ((qr_img.size[0] - logo_size) // 2, (qr_img.size[1] - logo_size) // 2)
            
            # Create a white background for the logo
            logo_bg = Image.new('RGBA', (logo_size + 4, logo_size + 4), (255, 255, 255, 255))
            logo_bg_pos = ((qr_img.size[0] - logo_size - 4) // 2, (qr_img.size[1] - logo_size - 4) // 2)
            
            # Paste logo background
            qr_img.paste(logo_bg, logo_bg_pos, logo_bg)
            
            # Paste logo
            qr_img.paste(logo, pos, logo)
            
        except Exception as e:
            print(f"Failed to add logo to QR code: {e}")
            # Continue without logo if it fails
        
        return qr_img
    
    def _add_border_and_text(self, qr_img: Image.Image, qr_data: Dict[str, Any]) -> Image.Image:
        """Add border and text to QR code"""
        
        # Create new image with border
        border_size = 20
        text_height = 30
        new_size = (qr_img.size[0] + 2 * border_size, qr_img.size[1] + 2 * border_size + text_height)
        
        # Create white background
        final_img = Image.new('RGB', new_size, 'white')
        draw = ImageDraw.Draw(final_img)
        
        # Paste QR code in center
        qr_pos = (border_size, border_size)
        final_img.paste(qr_img, qr_pos)
        
        # Add text at bottom
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except Exception as e:
            font = ImageFont.load_default()
        
        # Add personnel name and badge ID
        text_lines = [
            qr_data.get('full_name', 'Unknown'),
            f"ID: {qr_data.get('badge_id', 'N/A')}"
        ]
        
        y_position = qr_img.size[1] + border_size + 5
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (new_size[0] - text_width) // 2
            draw.text((x, y_position), line, fill='black', font=font)
            y_position += 15
        
        return final_img
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        base64_bytes = base64.b64encode(image_bytes)
        return base64_bytes.decode('utf-8')
    
    def _calculate_expiry_date(self, qr_type: str) -> Optional[str]:
        """Calculate expiry date for QR code based on type"""
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        
        expiry_periods = {
            "BADGE": timedelta(days=365),  # 1 year
            "ACCESS": timedelta(days=30),   # 30 days
            "LOCATION": timedelta(days=7),  # 1 week
            "EMERGENCY": None,             # Never expires
            "TRAINING": timedelta(days=90), # 3 months
            "CERTIFICATION": timedelta(days=180) # 6 months
        }
        
        period = expiry_periods.get(qr_type, timedelta(days=30))
        
        if period:
            return (now + period).isoformat()
        return None
    
    async def validate_qr_code(
        self,
        qr_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Validate QR code data and check if it's still valid
        
        Args:
            qr_data: QR code data to validate
            db: Database session
            
        Returns:
            Validation result
        """
        if db is None:
            db = next(get_db())
        
        try:
            # Check required fields
            required_fields = ["id", "badge_id", "full_name", "qr_type", "generated_at", "verification_token"]
            for field in required_fields:
                if field not in qr_data:
                    return {
                        "valid": False,
                        "error": f"Missing required field: {field}",
                        "error_type": "INVALID_FORMAT"
                    }
            
            # Check if personnel exists
            personnel = db.query(Personnel).filter(Personnel.id == qr_data["id"]).first()
            if not personnel:
                return {
                    "valid": False,
                    "error": "Personnel not found",
                    "error_type": "PERSONNEL_NOT_FOUND"
                }
            
            # Check if data matches personnel
            if (personnel.badge_id != qr_data["badge_id"] or 
                personnel.full_name != qr_data["full_name"]):
                return {
                    "valid": False,
                    "error": "QR code data does not match personnel records",
                    "error_type": "DATA_MISMATCH"
                }
            
            # Check expiry date
            if "expires_at" in qr_data and qr_data["expires_at"]:
                expiry_date = datetime.fromisoformat(qr_data["expires_at"].replace('Z', '+00:00'))
                if expiry_date < datetime.now(timezone.utc):
                    return {
                        "valid": False,
                        "error": "QR code has expired",
                        "error_type": "EXPIRED",
                        "expired_at": qr_data["expires_at"]
                    }
            
            # Check QR type specific validations
            type_validation = await self._validate_qr_type(qr_data, personnel, db)
            if not type_validation["valid"]:
                return type_validation
            
            return {
                "valid": True,
                "personnel": {
                    "id": personnel.id,
                    "badge_id": personnel.badge_id,
                    "full_name": personnel.full_name,
                    "company": personnel.company,
                    "role": personnel.role,
                    "status": personnel.status
                },
                "qr_type": qr_data["qr_type"],
                "generated_at": qr_data["generated_at"],
                "validation_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "error_type": "VALIDATION_ERROR"
            }
    
    async def _validate_qr_type(
        self,
        qr_data: Dict[str, Any],
        personnel: Personnel,
        db: Session
    ) -> Dict[str, Any]:
        """Validate QR code type specific requirements"""
        
        qr_type = qr_data.get("qr_type")
        
        if qr_type == "ACCESS":
            # Validate access permissions
            from ..services.role_permission_service import role_permission_service
            
            try:
                current_permissions = await role_permission_service.get_personnel_permissions(personnel.id, db)
                qr_permissions = set(qr_data.get("permissions", []))
                
                if not qr_permissions.issubset(current_permissions):
                    return {
                        "valid": False,
                        "error": "QR code contains permissions that personnel no longer has",
                        "error_type": "PERMISSION_MISMATCH"
                    }
            except Exception as e:
                logger.warning(f"Unexpected error: {e}")  # Skip permission check if service fails
        
        elif qr_type == "TRAINING":
            # Validate training records
            from ..services.certification_training_service import certification_training_service
            
            try:
                current_training = await certification_training_service.get_personnel_training_records(personnel.id, db)
                qr_training = qr_data.get("training_records", [])
                
                # Check if training records are still valid
                if qr_training:
                    latest_qr_training = qr_training[0]
                    current_latest = current_training[0] if current_training else None
                    
                    if current_latest and latest_qr_training:
                        if (latest_qr_training["training_type"] != current_latest["training_type"] or
                            latest_qr_training["completion_date"] != current_latest["completion_date"]):
                            return {
                                "valid": False,
                                "error": "Training records have been updated",
                                "error_type": "TRAINING_MISMATCH"
                            }
            except Exception as e:
                logger.warning(f"Unexpected error: {e}")  # Skip training check if service fails
        
        elif qr_type == "CERTIFICATION":
            # Validate certifications
            from ..services.certification_training_service import certification_training_service
            
            try:
                current_certs = await certification_training_service.get_personnel_certifications(personnel.id, db)
                qr_certs = qr_data.get("certifications", [])
                
                # Check if certifications are still valid
                if qr_certs:
                    valid_qr_certs = [cert for cert in qr_certs if cert.get("status") == "VALID"]
                    valid_current_certs = [cert for cert in current_certs if cert.get("status") == "VALID"]
                    
                    if len(valid_qr_certs) != len(valid_current_certs):
                        return {
                            "valid": False,
                            "error": "Certification status has changed",
                            "error_type": "CERTIFICATION_MISMATCH"
                        }
            except Exception as e:
                logger.warning(f"Unexpected error: {e}")  # Skip certification check if service fails
        
        return {"valid": True}
    
    async def get_qr_code_usage_statistics(
        self,
        personnel_id: Optional[int] = None,
        qr_type: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get QR code usage statistics
        
        Args:
            personnel_id: Filter by personnel ID (optional)
            qr_type: Filter by QR type (optional)
            db: Database session
            
        Returns:
            Usage statistics
        """
        # This would typically query a QR code usage tracking table
        # For now, return placeholder data
        
        return {
            "total_qr_codes_generated": 0,
            "total_scans": 0,
            "unique_scans": 0,
            "usage_by_type": {},
            "usage_by_personnel": {},
            "most_scanned_qr": None,
            "scan_trends": []
        }


# Create singleton instance
qr_service = QRCodeService()
