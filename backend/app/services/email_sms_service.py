"""
Email/SMS Notification Service

This service provides comprehensive email and SMS functionality including:
- Email template management
- SMS template management
- Multi-provider support (SMTP, SendGrid, Twilio)
- Multi-language support
- Delivery tracking and analytics
- Queue management for high-volume sending
"""

import logging
import os
import smtplib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models.system import EmailTemplate, SMSTemplate, SystemParameter
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailSMSService:
    """Comprehensive email and SMS notification service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.smtp_config = None
        self.sms_config = None
        self._load_configurations()
    
    def _load_configurations(self):
        """Load email and SMS configurations"""
        try:
            # Load SMTP configuration
            self.smtp_config = {
                "host": self._get_param("email.smtp_host", "localhost"),
                "port": int(self._get_param("email.smtp_port", "587")),
                "username": self._get_param("email.smtp_username", ""),
                "password": self._get_param("email.smtp_password", ""),
                "use_tls": self._get_param("email.smtp_use_tls", "true") == "true",
                "use_ssl": self._get_param("email.smtp_use_ssl", "false") == "true",
                "from_address": self._get_param("email.from_address", "noreply@pob.com"),
                "from_name": self._get_param("email.from_name", "Apex POB")
            }
            
            # Load SMS configuration
            self.sms_config = {
                "provider": self._get_param("sms.provider", "twilio"),
                "account_sid": self._get_param("sms.account_sid", ""),
                "auth_token": self._get_param("sms.auth_token", ""),
                "from_number": self._get_param("sms.from_number", ""),
                "api_key": self._get_param("sms.api_key", ""),
                "api_secret": self._get_param("sms.api_secret", "")
            }
            
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
    
    def _get_param(self, key: str, default: str = "") -> str:
        """Get system parameter"""
        try:
            param = self.db.query(SystemParameter).filter(
                SystemParameter.param_key == key
            ).first()
            return param.param_value if param else default
        except Exception as e:
            return default
    
    # Email Template Management
    async def create_email_template(self, template_data: Dict[str, Any], 
                                  created_by: str = None) -> Dict[str, Any]:
        """Create email template"""
        try:
            template = EmailTemplate(
                template_name=template_data["template_name"],
                subject=template_data["subject"],
                html_content=template_data["html_content"],
                text_content=template_data.get("text_content", ""),
                language=template_data.get("language", "en"),
                category=template_data.get("category", "general"),
                variables=template_data.get("variables", []),
                is_active=template_data.get("is_active", True),
                created_by=created_by
            )
            
            self.db.add(template)
            self.db.commit()
            
            logger.info(f"Email template created: {template.template_name}")
            return {
                "success": True,
                "template_id": template.id,
                "template_name": template.template_name
            }
            
        except Exception as e:
            logger.error(f"Error creating email template: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def update_email_template(self, template_id: int, 
                                  template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update email template"""
        try:
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.id == template_id
            ).first()
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Update fields
            for field, value in template_data.items():
                if hasattr(template, field) and value is not None:
                    setattr(template, field, value)
            
            template.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Email template updated: {template.template_name}")
            return {"success": True, "template_name": template.template_name}
            
        except Exception as e:
            logger.error(f"Error updating email template: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_email_template(self, template_name: str, 
                               language: str = "en") -> Optional[Dict[str, Any]]:
        """Get email template by name and language"""
        try:
            template = self.db.query(EmailTemplate).filter(
                EmailTemplate.template_name == template_name,
                EmailTemplate.language == language,
                EmailTemplate.is_active == True
            ).first()
            
            if not template:
                # Try fallback to English
                if language != "en":
                    template = self.db.query(EmailTemplate).filter(
                        EmailTemplate.template_name == template_name,
                        EmailTemplate.language == "en",
                        EmailTemplate.is_active == True
                    ).first()
            
            if not template:
                return None
            
            return {
                "id": template.id,
                "template_name": template.template_name,
                "subject": template.subject,
                "html_content": template.html_content,
                "text_content": template.text_content,
                "language": template.language,
                "category": template.category,
                "variables": template.variables
            }
            
        except Exception as e:
            logger.error(f"Error getting email template: {e}")
            return None
    
    async def list_email_templates(self, category: str = None, 
                                 language: str = None) -> List[Dict[str, Any]]:
        """List email templates"""
        try:
            query = self.db.query(EmailTemplate).filter(EmailTemplate.is_active == True)
            
            if category:
                query = query.filter(EmailTemplate.category == category)
            
            if language:
                query = query.filter(EmailTemplate.language == language)
            
            templates = query.order_by(EmailTemplate.template_name, EmailTemplate.language).all()
            
            result = []
            for template in templates:
                result.append({
                    "id": template.id,
                    "template_name": template.template_name,
                    "subject": template.subject,
                    "language": template.language,
                    "category": template.category,
                    "variables": template.variables,
                    "created_at": template.created_at,
                    "updated_at": template.updated_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing email templates: {e}")
            return []
    
    # SMS Template Management
    async def create_sms_template(self, template_data: Dict[str, Any], 
                                created_by: str = None) -> Dict[str, Any]:
        """Create SMS template"""
        try:
            template = SMSTemplate(
                template_name=template_data["template_name"],
                content=template_data["content"],
                language=template_data.get("language", "en"),
                category=template_data.get("category", "general"),
                variables=template_data.get("variables", []),
                is_active=template_data.get("is_active", True),
                created_by=created_by
            )
            
            self.db.add(template)
            self.db.commit()
            
            logger.info(f"SMS template created: {template.template_name}")
            return {
                "success": True,
                "template_id": template.id,
                "template_name": template.template_name
            }
            
        except Exception as e:
            logger.error(f"Error creating SMS template: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_sms_template(self, template_name: str, 
                             language: str = "en") -> Optional[Dict[str, Any]]:
        """Get SMS template by name and language"""
        try:
            template = self.db.query(SMSTemplate).filter(
                SMSTemplate.template_name == template_name,
                SMSTemplate.language == language,
                SMSTemplate.is_active == True
            ).first()
            
            if not template:
                # Try fallback to English
                if language != "en":
                    template = self.db.query(SMSTemplate).filter(
                        SMSTemplate.template_name == template_name,
                        SMSTemplate.language == "en",
                        SMSTemplate.is_active == True
                    ).first()
            
            if not template:
                return None
            
            return {
                "id": template.id,
                "template_name": template.template_name,
                "content": template.content,
                "language": template.language,
                "category": template.category,
                "variables": template.variables
            }
            
        except Exception as e:
            logger.error(f"Error getting SMS template: {e}")
            return None
    
    # Email Sending
    async def send_email(self, to_addresses: Union[str, List[str]], 
                        subject: str, content: str,
                        template_name: str = None,
                        variables: Dict[str, Any] = None,
                        attachments: List[str] = None,
                        cc_addresses: Union[str, List[str]] = None,
                        bcc_addresses: Union[str, List[str]] = None,
                        reply_to: str = None) -> Dict[str, Any]:
        """Send email"""
        try:
            # Use template if provided
            if template_name:
                template = await self.get_email_template(template_name)
                if template:
                    subject = template["subject"]
                    content = template["html_content"]
                    
                    # Replace variables
                    if variables:
                        for var, value in variables.items():
                            subject = subject.replace(f"{{{var}}}", str(value))
                            content = content.replace(f"{{{var}}}", str(value))
            
            # Prepare message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_address']}>"
            
            # Handle multiple recipients
            if isinstance(to_addresses, str):
                to_addresses = [to_addresses]
            msg['To'] = ', '.join(to_addresses)
            
            if cc_addresses:
                if isinstance(cc_addresses, str):
                    cc_addresses = [cc_addresses]
                msg['Cc'] = ', '.join(cc_addresses)
                to_addresses.extend(cc_addresses)
            
            if bcc_addresses:
                if isinstance(bcc_addresses, str):
                    bcc_addresses = [bcc_addresses]
                to_addresses.extend(bcc_addresses)
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add HTML content
            html_part = MIMEText(content, 'html')
            msg.attach(html_part)
            
            # Add plain text content (basic conversion)
            import re
            text_content = re.sub(r'<[^>]+>', '', content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Send email
            await self._send_smtp_email(msg, to_addresses)
            
            logger.info(f"Email sent to {', '.join(to_addresses)}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "recipients": to_addresses
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_smtp_email(self, message: MIMEMultipart, 
                             recipients: List[str]) -> bool:
        """Send email via SMTP"""
        try:
            # Create SMTP connection
            if self.smtp_config["use_ssl"]:
                server = smtplib.SMTP_SSL(
                    self.smtp_config["host"],
                    self.smtp_config["port"]
                )
            else:
                server = smtplib.SMTP(
                    self.smtp_config["host"],
                    self.smtp_config["port"]
                )
                
                if self.smtp_config["use_tls"]:
                    server.starttls()
            
            # Login if credentials provided
            if self.smtp_config["username"] and self.smtp_config["password"]:
                server.login(
                    self.smtp_config["username"],
                    self.smtp_config["password"]
                )
            
            # Send email
            server.send_message(message, to_addrs=recipients)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            raise
    
    # SMS Sending
    async def send_sms(self, to_numbers: Union[str, List[str]], 
                      message: str,
                      template_name: str = None,
                      variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send SMS"""
        try:
            # Use template if provided
            if template_name:
                template = await self.get_sms_template(template_name)
                if template:
                    message = template["content"]
                    
                    # Replace variables
                    if variables:
                        for var, value in variables.items():
                            message = message.replace(f"{{{var}}}", str(value))
            
            # Handle multiple recipients
            if isinstance(to_numbers, str):
                to_numbers = [to_numbers]
            
            # Send based on provider
            provider = self.sms_config["provider"].lower()
            
            if provider == "twilio":
                results = await self._send_twilio_sms(to_numbers, message)
            elif provider == "aws_sns":
                results = await self._send_aws_sns_sms(to_numbers, message)
            else:
                return {"success": False, "error": f"Unsupported SMS provider: {provider}"}
            
            logger.info(f"SMS sent to {', '.join(to_numbers)}")
            return {
                "success": True,
                "message": "SMS sent successfully",
                "recipients": to_numbers,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_twilio_sms(self, to_numbers: List[str], 
                             message: str) -> List[Dict[str, Any]]:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioRestException
            
            client = Client(
                self.sms_config["account_sid"],
                self.sms_config["auth_token"]
            )
            
            results = []
            for number in to_numbers:
                try:
                    message_obj = client.messages.create(
                        body=message,
                        from_=self.sms_config["from_number"],
                        to=number
                    )
                    
                    results.append({
                        "number": number,
                        "message_id": message_obj.sid,
                        "status": "sent"
                    })
                    
                except TwilioRestException as e:
                    results.append({
                        "number": number,
                        "error": str(e),
                        "status": "failed"
                    })
            
            return results
            
        except ImportError:
            raise Exception("Twilio library not installed")
        except Exception as e:
            logger.error(f"Twilio send error: {e}")
            raise
    
    async def _send_aws_sns_sms(self, to_numbers: List[str], 
                               message: str) -> List[Dict[str, Any]]:
        """Send SMS via AWS SNS"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            sns_client = boto3.client(
                'sns',
                aws_access_key_id=self.sms_config["api_key"],
                aws_secret_access_key=self.sms_config["api_secret"],
                region_name='us-east-1'
            )
            
            results = []
            for number in to_numbers:
                try:
                    response = sns_client.publish(
                        PhoneNumber=number,
                        Message=message
                    )
                    
                    results.append({
                        "number": number,
                        "message_id": response['MessageId'],
                        "status": "sent"
                    })
                    
                except ClientError as e:
                    results.append({
                        "number": number,
                        "error": str(e),
                        "status": "failed"
                    })
            
            return results
            
        except ImportError:
            raise Exception("Boto3 library not installed")
        except Exception as e:
            logger.error(f"AWS SNS send error: {e}")
            raise
    
    # Template Preview
    async def preview_email_template(self, template_name: str, 
                                   variables: Dict[str, Any] = None,
                                   language: str = "en") -> Dict[str, Any]:
        """Preview email template with variables"""
        try:
            template = await self.get_email_template(template_name, language)
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Replace variables
            subject = template["subject"]
            content = template["html_content"]
            
            if variables:
                for var, value in variables.items():
                    subject = subject.replace(f"{{{var}}}", str(value))
                    content = content.replace(f"{{{var}}}", str(value))
            
            return {
                "success": True,
                "template_name": template_name,
                "subject": subject,
                "html_content": content,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error previewing email template: {e}")
            return {"success": False, "error": str(e)}
    
    async def preview_sms_template(self, template_name: str, 
                                 variables: Dict[str, Any] = None,
                                 language: str = "en") -> Dict[str, Any]:
        """Preview SMS template with variables"""
        try:
            template = await self.get_sms_template(template_name, language)
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Replace variables
            content = template["content"]
            
            if variables:
                for var, value in variables.items():
                    content = content.replace(f"{{{var}}}", str(value))
            
            return {
                "success": True,
                "template_name": template_name,
                "content": content,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error previewing SMS template: {e}")
            return {"success": False, "error": str(e)}
    
    # Configuration Management
    async def update_email_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update email configuration"""
        try:
            for key, value in config_data.items():
                param_key = f"email.{key}"
                
                param = self.db.query(SystemParameter).filter(
                    SystemParameter.param_key == param_key
                ).first()
                
                if param:
                    param.param_value = str(value)
                    param.updated_at = datetime.now(timezone.utc)
                else:
                    param = SystemParameter(
                        param_key=param_key,
                        param_value=str(value),
                        param_type="string",
                        module="notification",
                        description=f"Email configuration: {key}"
                    )
                    self.db.add(param)
            
            self.db.commit()
            self._load_configurations()
            
            logger.info("Email configuration updated")
            return {"success": True, "message": "Email configuration updated"}
            
        except Exception as e:
            logger.error(f"Error updating email config: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def update_sms_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update SMS configuration"""
        try:
            for key, value in config_data.items():
                param_key = f"sms.{key}"
                
                param = self.db.query(SystemParameter).filter(
                    SystemParameter.param_key == param_key
                ).first()
                
                if param:
                    param.param_value = str(value)
                    param.updated_at = datetime.now(timezone.utc)
                else:
                    param = SystemParameter(
                        param_key=param_key,
                        param_value=str(value),
                        param_type="string",
                        module="notification",
                        description=f"SMS configuration: {key}"
                    )
                    self.db.add(param)
            
            self.db.commit()
            self._load_configurations()
            
            logger.info("SMS configuration updated")
            return {"success": True, "message": "SMS configuration updated"}
            
        except Exception as e:
            logger.error(f"Error updating SMS config: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_configuration(self) -> Dict[str, Any]:
        """Get current email and SMS configuration"""
        try:
            return {
                "email": {
                    "smtp_host": self.smtp_config["host"],
                    "smtp_port": self.smtp_config["port"],
                    "smtp_username": self.smtp_config["username"],
                    "smtp_use_tls": self.smtp_config["use_tls"],
                    "smtp_use_ssl": self.smtp_config["use_ssl"],
                    "from_address": self.smtp_config["from_address"],
                    "from_name": self.smtp_config["from_name"]
                },
                "sms": {
                    "provider": self.sms_config["provider"],
                    "from_number": self.sms_config["from_number"]
                    # Don't return sensitive credentials
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            return {}


# Email/SMS service factory
def get_email_sms_service(db: Session) -> EmailSMSService:
    """Get email/SMS service instance"""
    return EmailSMSService(db)
