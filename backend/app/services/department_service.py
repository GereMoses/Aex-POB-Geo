"""
Department Service for Oil & Gas Personnel Management

This service handles department management, personnel assignments,
and organizational structure for oil and gas operations.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime


logger = logging.getLogger(__name__)


class DepartmentService:
    """Service for department management operations"""
    
    def __init__(self):
        pass
    
    async def get_departments(
        self, 
        db: Session,
        site_id: Optional[int] = None,
        status: Optional[str] = None,
        department_type: Optional[str] = None,
        include_personnel_count: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get departments with optional filtering
        
        Args:
            db: Database session
            site_id: Filter by site
            status: Filter by status
            department_type: Filter by department type
            include_personnel_count: Include personnel count in results
            
        Returns:
            List of departments with their details
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department
            
            query = db.query(Department).filter(Department.is_active == True)
            
            # Apply filters
            if site_id:
                query = query.filter(Department.zone_id == site_id)
            if status:
                query = query.filter(Department.status == status)
            if department_type:
                query = query.filter(Department.department_type == department_type)
            
            departments = query.all()
            logger.info(f"Found {len(departments)} departments")
            
            result = []
            for dept in departments:
                dept_data = {
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.code,
                    "description": dept.description,
                    "department_type": dept.department_type,
                    "status": dept.status,
                    "zone_id": dept.zone_id,
                    "manager_id": dept.manager_id,
                    "parent_id": dept.parent_id,
                    "level": dept.level,
                    "created_at": dept.created_at,
                    "updated_at": dept.updated_at
                }
                
                # Add personnel count if requested
                if include_personnel_count:
                    # Import DepartmentPersonnel here to avoid circular imports
                    from ..models.department import DepartmentPersonnel
                    personnel_count = db.query(DepartmentPersonnel).filter(
                        DepartmentPersonnel.department_id == dept.id,
                        DepartmentPersonnel.status == "active"
                    ).count()
                    dept_data["personnel_count"] = personnel_count
                
                result.append(dept_data)
            
            return result
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
            return []

    async def get_department_by_id(
        self,
        department_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get department by ID
        
        Args:
            department_id: Department ID
            db: Database session
            
        Returns:
            Department details
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department
            
            department = db.query(Department).filter(
                Department.id == department_id
            ).first()
            
            if not department:
                return {
                    "success": False,
                    "error": f"Department with ID {department_id} not found"
                }
            
            return {
                "success": True,
                "department": {
                    "id": department.id,
                    "name": department.name,
                    "code": department.code,
                    "description": department.description,
                    "department_type": department.department_type,
                    "status": department.status,
                    "site_id": department.site_id,
                    "site_name": department.site_name,
                    "manager_id": department.manager_id,
                    "parent_id": department.parent_id,
                    "level": department.level,
                    "created_at": department.created_at,
                    "updated_at": department.updated_at
                }
            }
        except Exception as e:
            logger.error(f"Error getting department: {e}")
            return {
                "success": False,
                "error": f"Failed to get department: {str(e)}"
            }

    async def create_department(
        self,
        db: Session,
        name: str,
        code: str,
        description: Optional[str] = None,
        department_type: str = "operations",
        zone_id: Optional[int] = None,
        manager_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new department
        
        Args:
            db: Database session
            name: Department name
            code: Department code
            description: Department description
            department_type: Type of department
            zone_id: Zone ID
            manager_id: Manager ID
            parent_id: Parent department ID
            created_by: User ID who created
            
        Returns:
            Creation result
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department, DepartmentStatus
            
            # Check if code already exists
            existing = db.query(Department).filter(
                Department.code == code
            ).first()
            
            if existing:
                return {
                    "success": False,
                    "error": f"Department with code '{code}' already exists"
                }
            
            # Create new department
            new_department = Department(
                name=name,
                code=code,
                description=description,
                department_type=department_type,
                status=DepartmentStatus.ACTIVE,  # Set default status
                zone_id=zone_id,
                manager_id=manager_id,
                parent_id=parent_id,
                created_by=created_by,
                updated_by=created_by,
                is_active=True  # Ensure is_active is set
            )
            
            db.add(new_department)
            db.commit()
            
            return {
                "success": True,
                "department": {
                    "id": new_department.id,
                    "name": new_department.name,
                    "code": new_department.code,
                    "description": new_department.description,
                    "department_type": new_department.department_type.value if new_department.department_type else None,
                    "status": new_department.status.value if new_department.status else None,
                    "zone_id": new_department.zone_id,
                    "created_at": new_department.created_at
                }
            }
        except Exception as e:
            logger.error(f"Error creating department: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Failed to create department: {str(e)}"
            }

    async def assign_personnel_to_department(
        self,
        db: Session,
        department_id: int,
        personnel_id: int,
        role: str,
        position: Optional[str] = None,
        is_primary: bool = False,
        is_manager: bool = False,
        approved_by: Optional[int] = None,
        assigned_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Assign personnel to department
        
        Args:
            db: Database session
            department_id: Department ID
            personnel_id: Personnel ID
            role: Role in department
            position: Position in department
            is_primary: Whether this is primary assignment
            is_manager: Whether this person is department manager
            approved_by: User ID who approved
            
        Returns:
            Assignment result
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department, DepartmentPersonnel
            from ..models.personnel import Personnel
            
            # Check if department exists
            department = db.query(Department).filter(
                Department.id == department_id
            ).first()
            
            if not department:
                return {
                    "success": False,
                    "error": f"Department with ID {department_id} not found"
                }
            
            # Check if personnel exists
            personnel = db.query(Personnel).filter(
                Personnel.id == personnel_id
            ).first()
            
            if not personnel:
                return {
                    "success": False,
                    "error": f"Personnel with ID {personnel_id} not found"
                }
            
            # Ensure personnel has auto-generated badge ID for consistency
            if not personnel.badge_id or len(personnel.badge_id) < 10:
                # Generate auto badge ID if not present or too short
                auto_badge_id = self.generate_auto_badge_id(
                    full_name=personnel.full_name,
                    company=personnel.company or "UNKNOWN",
                    existing_id=personnel.id
                )
                personnel.badge_id = auto_badge_id
                db.commit()  # Save the updated badge ID
            
            # Remove existing primary assignment if setting new primary
            if is_primary:
                existing_primary = db.query(DepartmentPersonnel).filter(
                    DepartmentPersonnel.personnel_id == personnel_id,
                    DepartmentPersonnel.is_primary == True,
                    DepartmentPersonnel.status == "active"
                ).first()
                
                if existing_primary:
                    existing_primary.is_primary = False
                    existing_primary.unassigned_at = datetime.utcnow()
            
            # Create new assignment
            assignment = DepartmentPersonnel(
                department_id=department_id,
                personnel_id=personnel_id,
                role=role,
                position=position,
                is_primary=is_primary,
                is_manager=is_manager,
                approved_by=approved_by,
                approved_at=datetime.utcnow() if approved_by else None,
                status="active"
            )
            
            db.add(assignment)
            
            # Update personnel department if primary assignment
            if is_primary:
                personnel.department_id = department_id
            
            return {
                "success": True,
                "assignment": {
                    "id": assignment.id,
                    "department_id": department_id,
                    "personnel_id": personnel_id,
                    "role": role,
                    "position": position,
                    "is_primary": is_primary,
                    "is_manager": is_manager,
                    "assigned_at": assignment.assigned_at,
                    "approved_by": approved_by,
                    "status": assignment.status
                }
            }
        except Exception as e:
            logger.error(f"Error assigning personnel to department: {e}")
            return {
                "success": False,
                "error": f"Failed to assign personnel: {str(e)}"
            }

    async def remove_personnel_from_department(
        self,
        db: Session,
        assignment_id: int
    ) -> Dict[str, Any]:
        """
        Remove personnel assignment from department
        
        Args:
            db: Database session
            assignment_id: Assignment ID
            
        Returns:
            Operation result
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import DepartmentPersonnel
            
            assignment = db.query(DepartmentPersonnel).filter(
                DepartmentPersonnel.id == assignment_id
            ).first()
            
            if not assignment:
                return {
                    "success": False,
                    "error": f"Assignment with ID {assignment_id} not found"
                }
            
            # Update assignment status
            assignment.status = "resigned"
            assignment.unassigned_at = datetime.utcnow()
            
            # Update personnel department if this was primary assignment
            if assignment.is_primary:
                # Check if personnel has other active assignments
                other_assignment = db.query(DepartmentPersonnel).filter(
                    DepartmentPersonnel.personnel_id == assignment.personnel_id,
                    DepartmentPersonnel.status == "active",
                    DepartmentPersonnel.id != assignment_id
                ).first()
                
                if other_assignment:
                    # Import here to avoid circular imports
                    from ..models.personnel import Personnel
                    personnel = db.query(Personnel).filter(
                        Personnel.id == assignment.personnel_id
                    ).first()
                    if personnel:
                        personnel.department_id = other_assignment.department_id
                else:
                    # Import here to avoid circular imports
                    from ..models.personnel import Personnel
                    personnel = db.query(Personnel).filter(
                        Personnel.id == assignment.personnel_id
                    ).first()
                    if personnel:
                        personnel.department_id = None
            
            return {
                "success": True,
                "message": "Personnel removed from department successfully"
            }
        except Exception as e:
            logger.error(f"Error removing personnel from department: {e}")
            return {
                "success": False,
                "error": f"Failed to remove personnel: {str(e)}"
            }

    async def get_department_statistics(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get department statistics for dashboard
        
        Args:
            db: Database session
            
        Returns:
            Department statistics
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department
            from ..models.personnel import Personnel
            
            # Total departments
            total_departments = db.query(Department).filter(Department.is_active == True).count()
            
            # Departments by type
            dept_types = db.query(
                Department.department_type,
                func.count(Department.id).label('count')
            ).filter(Department.is_active == True).group_by(Department.department_type).all()
            
            # Departments by status
            dept_status = db.query(
                Department.status,
                func.count(Department.id).label('count')
            ).filter(Department.is_active == True).group_by(Department.status).all()
            
            # Personnel distribution
            dept_personnel = db.query(
                Department.id,
                func.count(Personnel.id).label('personnel_count')
            ).outerjoin(
                Personnel, Department.id == Personnel.department_id
            ).filter(
                Department.is_active == True,
                # status is a location enum (UPPERCASE); is_active is the employed flag.
                Personnel.is_active.is_(True)
            ).group_by(Department.id).all()
            
            # Budget information (placeholder)
            total_budget = 0
            used_budget = 0
            
            # Safety critical departments
            safety_critical_count = 0
            
            return {
                "total_departments": total_departments,
                "by_type": {str(dt[0]): dt[1] for dt in dept_types},
                "by_status": {str(ds[0]): ds[1] for ds in dept_status},
                "personnel_distribution": {str(dp[0]): dp[1] for dp in dept_personnel},
                "total_budget": total_budget,
                "used_budget": used_budget,
                "budget_utilization": (used_budget / total_budget * 100) if total_budget > 0 else 0,
                "safety_critical_departments": safety_critical_count,
                "average_personnel_per_department": (sum(dp[1] for dp in dept_personnel) / len(dept_personnel)) if dept_personnel else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting department statistics: {e}")
            # Return error structure but with default values to prevent frontend crashes
            return {
                "total_departments": 0,
                "by_type": {},
                "by_status": {},
                "personnel_distribution": {},
                "total_budget": 0,
                "used_budget": 0,
                "budget_utilization": 0,
                "safety_critical_departments": 0,
                "average_personnel_per_department": 0,
                "error": f"Failed to get statistics: {str(e)}"
            }

    async def get_personnel_assignments(
        self,
        db: Session,
        department_id: int
    ) -> Dict[str, Any]:
        """
        Get all personnel assignments for a department
        
        Args:
            db: Database session
            department_id: Department ID
            
        Returns:
            Department with personnel assignments
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department, DepartmentPersonnel
            from ..models.personnel import Personnel
            
            # Get department
            department = db.query(Department).filter(
                Department.id == department_id
            ).first()
            
            if not department:
                return {
                    "success": False,
                    "error": f"Department with ID {department_id} not found"
                }
            
            # Get department personnel
            personnel = db.query(Personnel).filter(
                # status is a location enum (UPPERCASE); is_active is the employed flag.
                Personnel.is_active.is_(True)
            ).all()
            
            # Get department assignments
            assignments = db.query(DepartmentPersonnel).filter(
                DepartmentPersonnel.department_id == department_id
            ).all()
            
            result = {
                "id": department.id,
                "name": department.name,
                "code": department.code,
                "description": department.description,
                "department_type": department.department_type,
                "status": department.status,
                "personnel": [],
                "assignments": []
            }
            
            # Add personnel
            for person in personnel:
                result["personnel"].append({
                    "id": person.id,
                    "badge_id": person.badge_id,
                    "full_name": person.full_name,
                    "email": person.email,
                    "phone": person.phone,
                    "company": person.company,
                    "role": person.role,
                    "position": person.position,
                    "status": person.status,
                    "is_onboard": person.is_onboard
                })
            
            # Add assignments
            for assignment in assignments:
                person = db.query(Personnel).filter(
                    Personnel.id == assignment.personnel_id
                ).first()
                result["assignments"].append({
                    "id": assignment.id,
                    "role": assignment.role,
                    "position": assignment.position,
                    "is_primary": assignment.is_primary,
                    "is_manager": assignment.is_manager,
                    "assigned_at": assignment.assigned_at.isoformat(),
                    "unassigned_at": assignment.unassigned_at.isoformat() if assignment.unassigned_at else None,
                    "status": assignment.status,
                    "personnel": {
                        "id": person.id,
                        "badge_id": person.badge_id,
                        "full_name": person.full_name,
                        "email": person.email
                    }
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting department personnel: {e}")
            return {
                "success": False,
                "error": f"Failed to get department personnel: {str(e)}"
            }

    async def get_assignment_statistics(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get assignment statistics for dashboard
        
        Args:
            db: Database session
            
        Returns:
            Assignment statistics
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department, DepartmentPersonnel
            from ..models.personnel import Personnel
            
            # Get counts
            total_personnel = db.query(Personnel).count()
            total_departments = db.query(Department).filter(Department.is_active == True).count()
            
            # Get assignments
            all_assignments = db.query(DepartmentPersonnel).all()
            active_assignments = [a for a in all_assignments if a.status == "active"]
            
            # Get assigned personnel (those with active assignments)
            assigned_personnel_ids = set(a.personnel_id for a in active_assignments)
            assigned_personnel = len(assigned_personnel_ids)
            unassigned_personnel = total_personnel - assigned_personnel
            
            # Department utilization
            dept_utilization = {}
            for assignment in active_assignments:
                dept_id = assignment.department_id
                if dept_id not in dept_utilization:
                    dept_utilization[dept_id] = 0
                dept_utilization[dept_id] += 1
            
            # Get department names for utilization
            for dept_id, count in list(dept_utilization.items()):
                dept = db.query(Department).filter(Department.id == dept_id).first()
                if dept:
                    dept_utilization[dept.name] = count
                    del dept_utilization[dept_id]
            
            return {
                "total_personnel": total_personnel,
                "total_departments": total_departments,
                "assigned_personnel": assigned_personnel,
                "unassigned_personnel": unassigned_personnel,
                "active_assignments": len(active_assignments),
                "pending_transfers": 0,  # TODO: Implement transfer tracking
                "department_utilization": dept_utilization
            }
        except Exception as e:
            logger.error(f"Error getting assignment statistics: {e}")
            return {
                "total_personnel": 0,
                "total_departments": 0,
                "assigned_personnel": 0,
                "unassigned_personnel": 0,
                "active_assignments": 0,
                "pending_transfers": 0,
                "department_utilization": {}
            }

    async def get_assignments(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        status: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get assignments with filtering and pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term
            department_id: Filter by department
            status: Filter by status
            role: Filter by role
            
        Returns:
            Paginated assignments
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import DepartmentPersonnel, Department
            from ..models.personnel import Personnel
            
            # Build query with proper joins to get complete data
            query = db.query(DepartmentPersonnel, Personnel, Department).join(
                Personnel, DepartmentPersonnel.personnel_id == Personnel.id
            ).join(
                Department, DepartmentPersonnel.department_id == Department.id
            )
            
            # Apply filters
            # Default to only show active assignments unless specific status is requested
            if status:
                query = query.filter(DepartmentPersonnel.status == status)
            else:
                query = query.filter(DepartmentPersonnel.status == "active")
            
            if search:
                query = query.filter(
                    or_(
                        Personnel.full_name.ilike(f"%{search}%"),
                        Personnel.badge_id.ilike(f"%{search}%"),
                        Personnel.email.ilike(f"%{search}%"),
                        Department.name.ilike(f"%{search}%")
                    )
                )
            
            if department_id:
                query = query.filter(DepartmentPersonnel.department_id == department_id)
            
            if role:
                query = query.filter(DepartmentPersonnel.role.ilike(f"%{role}%"))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            assignments = query.offset(skip).limit(limit).all()
            
            # Build response with auto-generated codes and complete data
            result = []
            for assignment, person, department in assignments:
                if person and department:
                    # Auto-generate assignment code
                    assignment_code = f"ASS-{assignment.id:06d}-{person.badge_id}-{department.id:03d}"
                    
                    # Auto-generate department code if not exists
                    department_code = getattr(department, 'department_code', None)
                    if not department_code:
                        department_code = f"DEPT-{department.id:03d}"
                    
                    result.append({
                        "id": assignment.id,
                        "assignment_code": assignment_code,  # Auto-generated
                        "department_id": assignment.department_id,
                        "department_name": department.name,
                        "department_code": department_code,  # Auto-generated
                        "site_id": department.zone_id,
                        "personnel_id": assignment.personnel_id,
                        "badge_id": person.badge_id,
                        "full_name": person.full_name,
                        "email": person.email,
                        "phone": person.phone,
                        "company": person.company,
                        "personnel_type": person.personnel_type,
                        "personnel_status": person.status,
                        "personnel_department": person.department,  # From personnel table
                        "role": assignment.role,
                        "position": assignment.position,
                        "is_primary": assignment.is_primary,
                        "is_manager": assignment.is_manager,
                        "assignment_status": assignment.status,
                        "assigned_at": assignment.assigned_at,
                        "assigned_date": assignment.assigned_at.strftime('%Y-%m-%d') if assignment.assigned_at else None,
                        "unassigned_at": assignment.unassigned_at,
                        "unassigned_date": assignment.unassigned_at.strftime('%Y-%m-%d') if assignment.unassigned_at else None,
                        "approved_by": assignment.approved_by,
                        "approved_at": assignment.approved_at,
                        "created_at": assignment.created_at,
                        "updated_at": assignment.updated_at,
                        # Auto-generated display fields
                        "display_name": f"{person.full_name} ({person.badge_id})",
                        "display_department": f"{department.name} ({department_code})",
                        "display_role": f"{assignment.role} - {assignment.position or 'N/A'}",
                        "display_assignment": f"{assignment_code}: {person.full_name} → {department.name}",
                        "assignment_duration": self._calculate_assignment_duration(assignment.assigned_at, assignment.unassigned_at),
                        "is_active": assignment.status == "active" and (not assignment.unassigned_at or assignment.unassigned_at > assignment.assigned_at)
                    })
            
            return {
                "assignments": result,
                "total": total
            }
        except Exception as e:
            logger.error(f"Error getting assignments: {e}")
            return {
                "assignments": [],
                "total": 0
            }
    
    def _calculate_assignment_duration(self, assigned_at, unassigned_at):
        """
        Calculate assignment duration in human-readable format
        
        Args:
            assigned_at: Assignment start date
            unassigned_at: Assignment end date (if any)
            
        Returns:
            Human-readable duration string
        """
        try:
            from datetime import datetime
            
            start_date = assigned_at
            end_date = unassigned_at or datetime.now()
            
            if start_date:
                duration = end_date - start_date
                days = duration.days
                
                if days == 0:
                    return "Today"
                elif days == 1:
                    return "1 day"
                elif days < 30:
                    return f"{days} days"
                elif days < 365:
                    months = days // 30
                    return f"{months} month{'s' if months > 1 else ''}"
                else:
                    years = days // 365
                    return f"{years} year{'s' if years > 1 else ''}"
            return "N/A"
        except Exception:
            return "N/A"
    
    def generate_auto_badge_id(self, full_name: str, company: str, existing_id: Optional[int] = None) -> str:
        """
        Generate auto badge ID based on personnel name and company
        
        Args:
            full_name: Personnel full name
            company: Company name
            existing_id: Existing personnel ID for consistency
            
        Returns:
            Auto-generated badge ID in format: COMP-YYYY-NNNN
        """
        try:
            import re
            from datetime import datetime
            
            # Create company abbreviation
            company_abbr = re.sub(r'[^A-Za-z]', '', company.upper())[:4]
            if not company_abbr:
                company_abbr = "GEN"
            
            # Create name abbreviation
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                name_abbr = name_parts[0][:3].upper() + name_parts[-1][:2].upper()
            else:
                name_abbr = full_name[:5].upper()
            
            # Use existing ID if provided, otherwise use current year
            if existing_id:
                number_part = f"{existing_id:04d}"
            else:
                year = datetime.now().year
                number_part = f"{year:04d}"
            
            # Generate badge ID
            badge_id = f"{company_abbr}-{name_abbr}-{number_part}"
            
            return badge_id
        except Exception:
            # Fallback to simple format
            return f"ID-{full_name[:5].upper()}-{existing_id or '0001'}"
    
    async def update_personnel_badge_ids(self, db: Session) -> Dict[str, Any]:
        """
        Update all personnel with auto-generated badge IDs for consistency
        
        Args:
            db: Database session
            
        Returns:
            Update results
        """
        try:
            from ..models.personnel import Personnel
            
            # Get all personnel
            personnel_list = db.query(Personnel).all()
            
            updated_count = 0
            updates = []
            
            for person in personnel_list:
                # Generate new badge ID
                new_badge_id = self.generate_auto_badge_id(
                    full_name=person.full_name,
                    company=person.company or "UNKNOWN",
                    existing_id=person.id
                )
                
                # Only update if different
                if person.badge_id != new_badge_id:
                    old_badge_id = person.badge_id
                    person.badge_id = new_badge_id
                    updates.append({
                        "personnel_id": person.id,
                        "full_name": person.full_name,
                        "old_badge_id": old_badge_id,
                        "new_badge_id": new_badge_id
                    })
                    updated_count += 1
            
            # Commit changes
            db.commit()
            
            return {
                "success": True,
                "total_personnel": len(personnel_list),
                "updated_count": updated_count,
                "updates": updates
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating badge IDs: {e}")
            return {
                "success": False,
                "error": str(e),
                "updated_count": 0
            }
    
    async def update_department(
        self,
        db: Session,
        department_id: int,
        department_data: dict,
        updated_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update an existing department
        
        Args:
            db: Database session
            department_id: Department ID
            department_data: Department data to update
            updated_by: User ID who is updating
            
        Returns:
            Updated department details
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department
            
            department = db.query(Department).filter(
                Department.id == department_id
            ).first()
            
            if not department:
                return {
                    "success": False,
                    "error": f"Department with ID {department_id} not found"
                }
            
            # Update fields - only update valid fields and handle enum conversion
            valid_fields = {
                'name', 'description', 'department_type', 'status', 
                'parent_id', 'manager_id', 'contact_person', 'contact_email', 
                'contact_phone', 'max_personnel', 'safety_critical', 
                'required_certifications', 'safety_protocols', 'access_levels',
                'zone_id'  # Add zone_id as valid field
            }
            
            for field, value in department_data.items():
                if field in valid_fields and hasattr(department, field):
                    # Handle enum conversion for department_type and status
                    if field == 'department_type' and value:
                        from ..models.department import DepartmentType
                        try:
                            setattr(department, field, DepartmentType(value.upper()))
                        except ValueError:
                            continue  # Skip invalid enum values
                    elif field == 'status' and value:
                        from ..models.department import DepartmentStatus
                        try:
                            setattr(department, field, DepartmentStatus(value.upper()))
                        except ValueError:
                            continue  # Skip invalid enum values
                    else:
                        setattr(department, field, value)
            
            department.updated_at = datetime.utcnow()
            if updated_by:
                department.updated_by = updated_by
            
            return {
                "success": True,
                "data": {
                    "id": department.id,
                    "name": department.name,
                    "code": department.code,
                    "description": department.description,
                    "department_type": department.department_type.value if department.department_type else None,
                    "status": department.status.value if department.status else None,
                    "zone_id": department.zone_id,
                    "manager_id": department.manager_id,
                    "parent_id": department.parent_id,
                    "level": department.level,
                    "updated_at": department.updated_at
                }
            }
        except Exception as e:
            logger.error(f"Error updating department: {e}")
            return {
                "success": False,
                "error": f"Failed to update department: {str(e)}"
            }

    async def delete_department(
        self,
        db: Session,
        department_id: int
    ) -> Dict[str, Any]:
        """
        Delete a department (soft delete)
        
        Args:
            db: Database session
            department_id: Department ID
            
        Returns:
            Operation result
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department
            
            department = db.query(Department).filter(
                Department.id == department_id
            ).first()
            
            if not department:
                return {
                    "success": False,
                    "error": f"Department with ID {department_id} not found"
                }
            
            # Soft delete by setting is_active to False
            department.is_active = False
            department.updated_at = datetime.utcnow()
            
            return {
                "success": True,
                "data": {
                    "id": department_id,
                    "message": "Department deleted successfully"
                }
            }
        except Exception as e:
            logger.error(f"Error deleting department: {e}")
            return {
                "success": False,
                "error": f"Failed to delete department: {str(e)}"
            }

    async def get_department_with_assignments(
        self,
        department_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get department details with all personnel assignments
        
        Args:
            db: Database session
            department_id: Department ID
            
        Returns:
            Department details with personnel assignments
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import Department, DepartmentPersonnel
            from ..models.personnel import Personnel
            
            # Get department details
            department = db.query(Department).filter(
                Department.id == department_id,
                Department.is_active == True
            ).first()
            
            if not department:
                return {
                    "success": False,
                    "error": f"Department with ID {department_id} not found"
                }
            
            # Get all personnel assignments for this department
            assignments = db.query(DepartmentPersonnel).filter(
                DepartmentPersonnel.department_id == department_id,
                DepartmentPersonnel.status == "active"
            ).all()
            
            # Get personnel details for each assignment
            personnel_list = []
            for assignment in assignments:
                personnel = db.query(Personnel).filter(
                    Personnel.id == assignment.personnel_id,
                    Personnel.is_active == True
                ).first()
                
                if personnel:
                    personnel_data = {
                        "id": assignment.id,
                        "personnel_id": personnel.id,
                        "badge_id": personnel.badge_id,
                        "full_name": personnel.full_name,
                        "company": personnel.company,
                        "position": personnel.position,
                        "department": personnel.department,
                        "phone": personnel.phone,
                        "email": personnel.email,
                        "role": assignment.role,
                        "is_primary": assignment.is_primary_zone,
                        "is_manager": assignment.is_manager,
                        "status": assignment.status,
                        "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                        "access_level": assignment.access_level,
                        "safety_briefing_completed": assignment.safety_briefing_completed,
                        "certifications_verified": assignment.certifications_verified
                    }
                    personnel_list.append(personnel_data)
            
            return {
                "success": True,
                "department": {
                    "id": department.id,
                    "name": department.name,
                    "code": department.code,
                    "description": department.description,
                    "department_type": department.department_type.value if department.department_type else None,
                    "status": department.status.value if department.status else None,
                    "zone_id": department.zone_id,
                    "manager_id": department.manager_id,
                    "max_personnel": department.max_personnel,
                    "current_personnel_count": len(personnel_list),
                    "created_at": department.created_at.isoformat(),
                    "updated_at": department.updated_at.isoformat()
                },
                "personnel_assignments": personnel_list
            }
            
        except Exception as e:
            logger.error(f"Error getting department with assignments: {e}")
            return {
                "success": False,
                "error": f"Failed to get department with assignments: {str(e)}"
            }

    async def get_department_personnel(
        self,
        db: Session,
        department_id: int
    ) -> List[dict]:
        """
        Get all personnel assigned to a department
        
        Args:
            db: Database session
            department_id: Department ID
            
        Returns:
            List of department personnel with their details
        """
        try:
            # Import here to avoid circular imports
            from ..models.department import DepartmentPersonnel
            from ..models.personnel import Personnel
            
            assignments = db.query(
                DepartmentPersonnel.id,
                DepartmentPersonnel.department_id,
                DepartmentPersonnel.personnel_id,
                DepartmentPersonnel.role,
                DepartmentPersonnel.position,
                DepartmentPersonnel.is_primary,
                DepartmentPersonnel.is_manager,
                DepartmentPersonnel.assigned_at,
                DepartmentPersonnel.unassigned_at,
                DepartmentPersonnel.approved_by,
                DepartmentPersonnel.approved_at,
                DepartmentPersonnel.status,
                DepartmentPersonnel.updated_at
            ).filter(
                DepartmentPersonnel.department_id == department_id,
                DepartmentPersonnel.status == "active"
            ).all()
            
            result = []
            for assignment in assignments:
                # Get personnel details
                personnel = db.query(Personnel).filter(
                    Personnel.id == assignment.personnel_id
                ).first()
                
                if personnel:
                    result.append({
                        "id": assignment[0],  # id
                        "personnel_id": assignment[2],  # personnel_id
                        "department_id": assignment[1],  # department_id
                        "personnel": {
                            "id": personnel.id,
                            "full_name": personnel.full_name,
                            "badge_id": personnel.badge_id,
                            "email": personnel.email,
                            "phone": personnel.phone,
                            "company": personnel.company,
                            "personnel_type": personnel.personnel_type
                        },
                        "role": assignment[3],  # role
                        "position": assignment[4],  # position
                        "is_primary": assignment[5],  # is_primary
                        "is_manager": assignment[6],  # is_manager
                        "status": assignment[10],  # status
                        "assigned_at": assignment[7].isoformat() if assignment[7] else None  # assigned_at
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting department personnel: {e}")
            return []


# Create global instance
department_service = DepartmentService()
