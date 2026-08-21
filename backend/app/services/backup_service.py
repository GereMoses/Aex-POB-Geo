"""
Database Backup Service

This service provides comprehensive database backup functionality including:
- Manual and scheduled backups
- Backup encryption and compression
- Cloud storage integration
- Backup restoration and verification
- Backup retention policies
"""

import os
import subprocess
import gzip
import shutil
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import json
import hashlib
import boto3
from botocore.exceptions import ClientError

from ..models.system import DatabaseBackup, SystemParameter
from ..core.config import settings

logger = logging.getLogger(__name__)


class BackupService:
    """Comprehensive database backup service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.backup_dir = settings.BACKUP_DIR or "backups"
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
    
    async def create_manual_backup(self, backup_name: str = None, 
                                 created_by: str = None, 
                                 include_files: bool = True,
                                 encrypt: bool = True) -> Dict[str, Any]:
        """Create manual database backup"""
        try:
            if not backup_name:
                backup_name = f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting manual backup: {backup_name}")
            
            # Create backup record
            backup_record = DatabaseBackup(
                backup_name=backup_name,
                backup_type="manual",
                status="in_progress",
                created_by=created_by,
                started_at=datetime.now(timezone.utc)
            )
            self.db.add(backup_record)
            self.db.commit()
            
            try:
                # Perform backup
                backup_result = await self._perform_backup(
                    backup_record.id, backup_name, include_files, encrypt
                )
                
                # Update backup record
                backup_record.status = "completed"
                backup_record.completed_at = datetime.now(timezone.utc)
                backup_record.file_path = backup_result["file_path"]
                backup_record.file_size = backup_result["file_size"]
                backup_record.checksum = backup_result["checksum"]
                backup_record.compression_ratio = backup_result["compression_ratio"]
                
                self.db.commit()
                
                logger.info(f"Manual backup completed: {backup_name}")
                return {
                    "success": True,
                    "backup_id": backup_record.id,
                    "backup_name": backup_name,
                    "file_path": backup_result["file_path"],
                    "file_size": backup_result["file_size"],
                    "duration": (backup_record.completed_at - backup_record.started_at).total_seconds()
                }
                
            except Exception as e:
                # Update backup record with error
                backup_record.status = "failed"
                backup_record.error_message = str(e)
                backup_record.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                
                logger.error(f"Manual backup failed: {backup_name} - {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "backup_id": backup_record.id
                }
                
        except Exception as e:
            logger.error(f"Error creating manual backup: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def create_scheduled_backup(self, schedule_type: str = "daily") -> Dict[str, Any]:
        """Create scheduled database backup"""
        try:
            backup_name = f"{schedule_type}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Check if backup already exists for today
            today = datetime.now().date()
            existing_backup = self.db.query(DatabaseBackup).filter(
                DatabaseBackup.backup_type == schedule_type,
                DatabaseBackup.created_at >= datetime.combine(today, datetime.min.time()),
                DatabaseBackup.status == "completed"
            ).first()
            
            if existing_backup:
                logger.info(f"Scheduled backup already exists for today: {schedule_type}")
                return {
                    "success": True,
                    "message": "Backup already exists for today",
                    "backup_id": existing_backup.id
                }
            
            logger.info(f"Starting scheduled backup: {backup_name}")
            
            # Create backup record
            backup_record = DatabaseBackup(
                backup_name=backup_name,
                backup_type=schedule_type,
                status="in_progress",
                created_by="system",
                started_at=datetime.now(timezone.utc)
            )
            self.db.add(backup_record)
            self.db.commit()
            
            try:
                # Get backup settings
                include_files = await self._get_backup_setting("include_files", True)
                encrypt = await self._get_backup_setting("encrypt_backups", True)
                upload_to_cloud = await self._get_backup_setting("upload_to_cloud", False)
                
                # Perform backup
                backup_result = await self._perform_backup(
                    backup_record.id, backup_name, include_files, encrypt
                )
                
                # Upload to cloud if enabled
                cloud_url = None
                if upload_to_cloud:
                    cloud_url = await self._upload_to_cloud(
                        backup_result["file_path"], backup_name
                    )
                
                # Update backup record
                backup_record.status = "completed"
                backup_record.completed_at = datetime.now(timezone.utc)
                backup_record.file_path = backup_result["file_path"]
                backup_record.file_size = backup_result["file_size"]
                backup_record.checksum = backup_result["checksum"]
                backup_record.compression_ratio = backup_result["compression_ratio"]
                backup_record.cloud_url = cloud_url
                
                self.db.commit()
                
                logger.info(f"Scheduled backup completed: {backup_name}")
                return {
                    "success": True,
                    "backup_id": backup_record.id,
                    "backup_name": backup_name,
                    "file_path": backup_result["file_path"],
                    "cloud_url": cloud_url,
                    "duration": (backup_record.completed_at - backup_record.started_at).total_seconds()
                }
                
            except Exception as e:
                # Update backup record with error
                backup_record.status = "failed"
                backup_record.error_message = str(e)
                backup_record.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                
                logger.error(f"Scheduled backup failed: {backup_name} - {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "backup_id": backup_record.id
                }
                
        except Exception as e:
            logger.error(f"Error creating scheduled backup: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def _perform_backup(self, backup_id: int, backup_name: str, 
                            include_files: bool, encrypt: bool) -> Dict[str, Any]:
        """Perform the actual database backup"""
        try:
            # Parse database URL
            db_url = settings.DATABASE_URL
            if not db_url:
                raise ValueError("Database URL not configured")
            
            # Extract connection details
            if db_url.startswith("postgresql://"):
                # postgresql://user:password@host:port/database
                url_parts = db_url.replace("postgresql://", "").split("@")
                if len(url_parts) != 2:
                    raise ValueError("Invalid database URL format")
                
                user_pass = url_parts[0].split(":")
                host_port_db = url_parts[1].split("/")
                
                if len(user_pass) != 2 or len(host_port_db) < 2:
                    raise ValueError("Invalid database URL format")
                
                db_user = user_pass[0]
                db_password = user_pass[1]
                host_port = host_port_db[0].split(":")
                db_host = host_port[0]
                db_port = host_port[1] if len(host_port) > 1 else "5432"
                db_name = host_port_db[1]
                
                # Create backup file path
                backup_file = os.path.join(self.backup_dir, f"{backup_name}.sql")
                
                # Use pg_dump for PostgreSQL
                pg_dump_cmd = [
                    "pg_dump",
                    "-h", db_host,
                    "-p", db_port,
                    "-U", db_user,
                    "-d", db_name,
                    "--no-password",
                    "--verbose",
                    "--clean",
                    "--if-exists",
                    "--create",
                    "--format=custom",
                    "--file", backup_file
                ]
                
                # Set password environment variable
                env = os.environ.copy()
                env["PGPASSWORD"] = db_password
                
                logger.info(f"Running pg_dump command: {' '.join(pg_dump_cmd)}")
                
                # Execute backup
                result = subprocess.run(
                    pg_dump_cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
                
                if result.returncode != 0:
                    raise Exception(f"pg_dump failed: {result.stderr}")
                
                # Get file size
                original_size = os.path.getsize(backup_file)
                
                # Compress backup
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                os.remove(backup_file)
                
                # Get compressed file size
                compressed_size = os.path.getsize(compressed_file)
                compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                
                # Calculate checksum
                checksum = self._calculate_checksum(compressed_file)
                
                # Encrypt if requested
                final_file = compressed_file
                if encrypt:
                    encrypted_file = f"{compressed_file}.enc"
                    await self._encrypt_file(compressed_file, encrypted_file)
                    os.remove(compressed_file)
                    final_file = encrypted_file
                
                return {
                    "file_path": final_file,
                    "file_size": compressed_size,
                    "original_size": original_size,
                    "compression_ratio": compression_ratio,
                    "checksum": checksum
                }
                
            else:
                raise ValueError("Only PostgreSQL is supported")
                
        except Exception as e:
            logger.error(f"Error performing backup: {e}")
            raise
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return ""
    
    async def _encrypt_file(self, input_file: str, output_file: str):
        """Encrypt file using AES-256"""
        try:
            from cryptography.fernet import Fernet
            
            # Get or generate encryption key
            encryption_key = await self._get_encryption_key()
            fernet = Fernet(encryption_key)
            
            # Encrypt file
            with open(input_file, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = fernet.encrypt(file_data)
            
            with open(output_file, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
            raise
    
    async def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key"""
        try:
            # Try to get from system parameters
            key_param = self.db.query(SystemParameter).filter(
                SystemParameter.param_key == "backup.encryption_key"
            ).first()
            
            if key_param and key_param.param_value:
                return key_param.param_value.encode()
            
            # Generate new key
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            
            # Store key
            if not key_param:
                key_param = SystemParameter(
                    param_key="backup.encryption_key",
                    param_value=key.decode(),
                    param_type="string",
                    module="backup",
                    description="Backup encryption key",
                    is_encrypted=True
                )
                self.db.add(key_param)
            else:
                key_param.param_value = key.decode()
            
            self.db.commit()
            return key
            
        except Exception as e:
            logger.error(f"Error getting encryption key: {e}")
            raise
    
    async def _upload_to_cloud(self, file_path: str, backup_name: str) -> Optional[str]:
        """Upload backup to cloud storage"""
        try:
            # Get cloud settings
            cloud_provider = await self._get_backup_setting("cloud_provider", "aws")
            
            if cloud_provider == "aws":
                return await self._upload_to_aws_s3(file_path, backup_name)
            else:
                logger.warning(f"Cloud provider {cloud_provider} not supported")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading to cloud: {e}")
            return None
    
    async def _upload_to_aws_s3(self, file_path: str, backup_name: str) -> Optional[str]:
        """Upload backup to AWS S3"""
        try:
            # Get AWS settings
            access_key = await self._get_backup_setting("aws_access_key")
            secret_key = await self._get_backup_setting("aws_secret_key")
            bucket_name = await self._get_backup_setting("aws_bucket_name")
            region = await self._get_backup_setting("aws_region", "us-east-1")
            
            if not all([access_key, secret_key, bucket_name]):
                raise ValueError("AWS S3 settings not configured")
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Upload file
            s3_key = f"backups/{backup_name}.gz"
            if file_path.endswith('.enc'):
                s3_key += '.enc'
            
            s3_client.upload_file(file_path, bucket_name, s3_key)
            
            # Generate presigned URL
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=3600 * 24 * 7  # 7 days
            )
            
            logger.info(f"Backup uploaded to S3: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"AWS S3 upload error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise
    
    async def restore_backup(self, backup_id: int, confirm: bool = False) -> Dict[str, Any]:
        """Restore database from backup"""
        try:
            if not confirm:
                return {
                    "success": False,
                    "error": "Restore requires explicit confirmation"
                }
            
            # Get backup record
            backup = self.db.query(DatabaseBackup).filter(
                DatabaseBackup.id == backup_id
            ).first()
            
            if not backup:
                return {"success": False, "error": "Backup not found"}
            
            if backup.status != "completed":
                return {"success": False, "error": "Backup is not completed"}
            
            logger.info(f"Starting restore from backup: {backup.backup_name}")
            
            # Download from cloud if needed
            file_path = backup.file_path
            if backup.cloud_url and not os.path.exists(file_path):
                file_path = await self._download_from_cloud(backup)
            
            if not os.path.exists(file_path):
                return {"success": False, "error": "Backup file not found"}
            
            # Decrypt if needed
            restore_file = file_path
            if file_path.endswith('.enc'):
                restore_file = file_path.replace('.enc', '')
                await self._decrypt_file(file_path, restore_file)
            
            # Decompress if needed
            if restore_file.endswith('.gz'):
                sql_file = restore_file.replace('.gz', '')
                with gzip.open(restore_file, 'rb') as f_in:
                    with open(sql_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = sql_file
            
            # Perform restore
            await self._perform_restore(restore_file)
            
            # Create restore record
            restore_record = DatabaseBackup(
                backup_name=f"restore_from_{backup.backup_name}",
                backup_type="restore",
                status="completed",
                created_by="system",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                source_backup_id=backup.id
            )
            self.db.add(restore_record)
            self.db.commit()
            
            logger.info(f"Restore completed from backup: {backup.backup_name}")
            return {
                "success": True,
                "message": "Database restored successfully",
                "restore_id": restore_record.id,
                "source_backup": backup.backup_name
            }
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_restore(self, sql_file: str):
        """Perform database restore from SQL file"""
        try:
            # Parse database URL
            db_url = settings.DATABASE_URL
            if not db_url.startswith("postgresql://"):
                raise ValueError("Only PostgreSQL is supported")
            
            # Extract connection details (similar to backup)
            url_parts = db_url.replace("postgresql://", "").split("@")
            user_pass = url_parts[0].split(":")
            host_port_db = url_parts[1].split("/")
            host_port = host_port_db[0].split(":")
            
            db_user = user_pass[0]
            db_password = user_pass[1]
            db_host = host_port[0]
            db_port = host_port[1] if len(host_port) > 1 else "5432"
            db_name = host_port_db[1]
            
            # Use psql for restore
            psql_cmd = [
                "psql",
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", db_name,
                "--file", sql_file
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password
            
            logger.info(f"Running psql restore command: {' '.join(psql_cmd)}")
            
            # Execute restore
            result = subprocess.run(
                psql_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"psql restore failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error performing restore: {e}")
            raise
    
    async def get_backup_list(self, backup_type: str = None, 
                           status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of backups"""
        try:
            query = self.db.query(DatabaseBackup)
            
            if backup_type:
                query = query.filter(DatabaseBackup.backup_type == backup_type)
            
            if status:
                query = query.filter(DatabaseBackup.status == status)
            
            backups = query.order_by(DatabaseBackup.created_at.desc()).limit(limit).all()
            
            result = []
            for backup in backups:
                result.append({
                    "id": backup.id,
                    "backup_name": backup.backup_name,
                    "backup_type": backup.backup_type,
                    "status": backup.status,
                    "file_size": backup.file_size,
                    "compression_ratio": backup.compression_ratio,
                    "created_by": backup.created_by,
                    "created_at": backup.created_at,
                    "started_at": backup.started_at,
                    "completed_at": backup.completed_at,
                    "cloud_url": backup.cloud_url,
                    "error_message": backup.error_message
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
            return []
    
    async def delete_backup(self, backup_id: int) -> Dict[str, Any]:
        """Delete backup"""
        try:
            backup = self.db.query(DatabaseBackup).filter(
                DatabaseBackup.id == backup_id
            ).first()
            
            if not backup:
                return {"success": False, "error": "Backup not found"}
            
            # Delete file
            if backup.file_path and os.path.exists(backup.file_path):
                os.remove(backup.file_path)
            
            # Delete from cloud if exists
            if backup.cloud_url:
                await self._delete_from_cloud(backup)
            
            # Delete database record
            self.db.delete(backup)
            self.db.commit()
            
            logger.info(f"Backup deleted: {backup.backup_name}")
            return {"success": True, "message": "Backup deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics"""
        try:
            # Total backups
            total_backups = self.db.query(DatabaseBackup).count()
            
            # Backups by type
            backups_by_type = self.db.query(
                DatabaseBackup.backup_type,
                func.count(DatabaseBackup.id).label('count')
            ).group_by(DatabaseBackup.backup_type).all()
            
            # Backups by status
            backups_by_status = self.db.query(
                DatabaseBackup.status,
                func.count(DatabaseBackup.id).label('count')
            ).group_by(DatabaseBackup.status).all()
            
            # Recent backups
            recent_backups = self.db.query(DatabaseBackup).filter(
                DatabaseBackup.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
            ).count()
            
            # Total storage used
            total_storage = self.db.query(
                func.sum(DatabaseBackup.file_size)
            ).filter(DatabaseBackup.status == "completed").scalar() or 0
            
            return {
                "total_backups": total_backups,
                "recent_backups": recent_backups,
                "total_storage_mb": round(total_storage / (1024 * 1024), 2),
                "backups_by_type": {bt: count for bt, count in backups_by_type},
                "backups_by_status": {bs: count for bs, count in backups_by_status}
            }
            
        except Exception as e:
            logger.error(f"Error getting backup statistics: {e}")
            return {}
    
    async def _get_backup_setting(self, key: str, default: Any = None) -> Any:
        """Get backup setting from system parameters"""
        try:
            param = self.db.query(SystemParameter).filter(
                SystemParameter.param_key == f"backup.{key}"
            ).first()
            
            if param:
                if param.param_type == "bool":
                    return param.param_value.lower() in ('true', '1', 'yes')
                elif param.param_type == "int":
                    return int(param.param_value)
                else:
                    return param.param_value
            
            return default
            
        except Exception as e:
            logger.error(f"Error getting backup setting {key}: {e}")
            return default


# Backup service factory
def get_backup_service(db: Session) -> BackupService:
    """Get backup service instance"""
    return BackupService(db)
