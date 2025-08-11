"""Service layer for class (classroom) management."""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId

from app.utils.database import db
from app.models.classroom import (
    ClassCreateRequest, ClassUpdateRequest, ClassResponse, ClassListResponse,
    EnrollmentRequest, EnrollmentResponse, BulkEnrollmentRequest, 
    BulkEnrollmentResponse, ClassStudentsResponse, EnrollmentHistoryResponse
)
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class ClassService:
    def __init__(self):
        # Defer actual collection binding until first use (DB may not be connected at import time)
        self.db = db.database
        self.collection = getattr(self.db, "classes", None) if self.db is not None else None
        self.users = getattr(self.db, "users", None) if self.db is not None else None

    def _ensure_collections(self):
        """Lazy initialize collections after DB connection is established."""
        if self.collection is None or self.users is None:
            self.db = db.database
            if self.db is None:
                raise RuntimeError("Database not initialized")
            self.collection = self.db.classes
            self.users = self.db.users

    async def create_class(self, data: ClassCreateRequest, teacher_id: str) -> ClassResponse:
        self._ensure_collections()
        teacher = await self.users.find_one({"_id": ObjectId(teacher_id)})
        if not teacher:
            raise ValueError("Teacher not found")
        if teacher.get("role") not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise PermissionError("Only teachers or admins can create classes")

        doc = {
            "name": data.name,
            "description": data.description,
            "teacher_id": teacher_id,
            "teacher_name": teacher.get("username"),
            "student_ids": [],
            "course_ids": [],
            "max_students": data.max_students,
            "current_enrollment": 0,
            "start_date": data.start_date,
            "end_date": data.end_date,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return ClassResponse(**self._serialize(doc))

    async def list_classes(self, skip: int = 0, limit: int = 20, teacher_id: Optional[str] = None, is_active: Optional[bool] = None) -> List[ClassListResponse]:
        self._ensure_collections()
        query: Dict[str, Any] = {}
        if teacher_id:
            query["teacher_id"] = teacher_id
        if is_active is not None:
            query["is_active"] = is_active

        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        results: List[ClassListResponse] = []
        async for doc in cursor:
            results.append(ClassListResponse(**self._serialize(doc)))
        return results

    async def get_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_collections()
        if not ObjectId.is_valid(class_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(class_id)})
        if not doc:
            return None
        return self._serialize(doc)

    async def update_class(self, class_id: str, data: ClassUpdateRequest, current_user_id: str) -> Optional[ClassResponse]:
        self._ensure_collections()
        existing = await self.collection.find_one({"_id": ObjectId(class_id)})
        if not existing:
            return None
        # Ownership: only teacher owner or admin
        if existing["teacher_id"] != current_user_id:
            user = await self.users.find_one({"_id": ObjectId(current_user_id)})
            if not user or user.get("role") != UserRole.ADMIN:
                raise PermissionError("Not authorized to update this class")

        update_fields = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        if update_fields:
            update_fields["updated_at"] = datetime.utcnow()
            await self.collection.update_one({"_id": ObjectId(class_id)}, {"$set": update_fields})
        updated = await self.collection.find_one({"_id": ObjectId(class_id)})
        return ClassResponse(**self._serialize(updated))

    async def delete_class(self, class_id: str, current_user_id: str) -> bool:
        self._ensure_collections()
        existing = await self.collection.find_one({"_id": ObjectId(class_id)})
        if not existing:
            return False
        if existing["teacher_id"] != current_user_id:
            user = await self.users.find_one({"_id": ObjectId(current_user_id)})
            if not user or user.get("role") != UserRole.ADMIN:
                raise PermissionError("Not authorized to delete this class")
        result = await self.collection.delete_one({"_id": ObjectId(class_id)})
        return result.deleted_count == 1

    # Phase 5.2 - Enrollment Management Methods

    async def enroll_student(self, class_id: str, user_id: str, current_user_id: str) -> EnrollmentResponse:
        """Enroll a student in a class."""
        self._ensure_collections()
        
        # Convert IDs to ObjectId for database queries
        try:
            class_oid = ObjectId(class_id)
            user_oid = ObjectId(user_id)
            current_user_oid = ObjectId(current_user_id)
        except Exception:
            raise ValueError("Invalid ID format")
        
        # Verify class exists
        class_doc = await self.collection.find_one({"_id": class_oid})
        if not class_doc:
            raise ValueError("Class not found")
        
        # Check if current user can manage enrollments (teacher or admin)
        current_user = await self.users.find_one({"_id": current_user_oid})
        if not current_user:
            raise ValueError("Current user not found")
        
        # Check permissions: admin or class teacher (using ObjectId comparison)
        if (current_user.get("role") != UserRole.ADMIN and 
            str(class_doc.get("teacher_id")) != current_user_id):
            raise PermissionError("Only class teacher or admin can manage enrollments")
        
        # Verify student exists and has correct role
        student_doc = await self.users.find_one({"_id": user_oid})
        if not student_doc:
            raise ValueError("Student not found")
        
        # Ensure user being enrolled is actually a student
        if student_doc.get("role") not in [UserRole.STUDENT, "student"]:
            raise ValueError("Can only enroll users with student role")
        
        # Check if student is already enrolled
        if user_id in class_doc.get("student_ids", []):
            raise ValueError("Student is already enrolled in this class")
        
        # Check capacity
        current_enrollment = len(class_doc.get("student_ids", []))
        max_students = class_doc.get("max_students")
        if max_students and current_enrollment >= max_students:
            raise ValueError("Class has reached maximum capacity")
        
        # Use atomic operation to prevent race conditions
        update_result = await self.collection.update_one(
            {
                "_id": class_oid,
                "student_ids": {"$ne": user_id},  # Ensure student not already enrolled
                "$expr": {
                    "$or": [
                        {"$eq": ["$max_students", None]},  # No limit
                        {"$lt": [{"$size": "$student_ids"}, "$max_students"]}  # Under capacity
                    ]
                }
            },
            {
                "$addToSet": {"student_ids": user_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if update_result.matched_count == 0:
            # Re-check what went wrong
            updated_class = await self.collection.find_one({"_id": class_oid})
            if user_id in updated_class.get("student_ids", []):
                raise ValueError("Student is already enrolled in this class")
            elif len(updated_class.get("student_ids", [])) >= updated_class.get("max_students", float('inf')):
                raise ValueError("Class has reached maximum capacity")
            else:
                raise ValueError("Failed to enroll student")
        
        # Create enrollment history record
        enrollment_record = {
            "class_id": class_id,
            "user_id": user_id,
            "enrollment_date": datetime.utcnow(),
            "enrolled_by": current_user_id,
            "status": "enrolled"
        }
        await self.db.enrollment_history.insert_one(enrollment_record)
        
        return EnrollmentResponse(
            class_id=class_id,
            user_id=user_id,
            user_name=student_doc.get("username", "Unknown"),
            enrollment_date=enrollment_record["enrollment_date"],
            status="enrolled"
        )

    async def unenroll_student(self, class_id: str, user_id: str, current_user_id: str) -> bool:
        """Unenroll a student from a class."""
        self._ensure_collections()
        
        # Convert IDs to ObjectId for database queries
        try:
            class_oid = ObjectId(class_id)
            user_oid = ObjectId(user_id)
            current_user_oid = ObjectId(current_user_id)
        except Exception:
            raise ValueError("Invalid ID format")
        
        # Verify class exists
        class_doc = await self.collection.find_one({"_id": class_oid})
        if not class_doc:
            raise ValueError("Class not found")
        
        # Check permissions
        current_user = await self.users.find_one({"_id": current_user_oid})
        if not current_user:
            raise ValueError("Current user not found")
        
        # Allow student to unenroll themselves, or teacher/admin to unenroll anyone
        if (current_user_id != user_id and 
            current_user.get("role") != UserRole.ADMIN and 
            str(class_doc.get("teacher_id")) != current_user_id):
            raise PermissionError("Insufficient permissions to unenroll student")
        
        # Use atomic operation to remove student only if enrolled
        result = await self.collection.update_one(
            {
                "_id": class_oid,
                "student_ids": user_id  # Only update if student is enrolled
            },
            {
                "$pull": {"student_ids": user_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("Student is not enrolled in this class")
        
        if result.modified_count > 0:
            # Update enrollment history
            await self.db.enrollment_history.update_one(
                {"class_id": class_id, "user_id": user_id, "status": "enrolled"},
                {
                    "$set": {
                        "status": "unenrolled",
                        "unenrollment_date": datetime.utcnow(),
                        "unenrolled_by": current_user_id
                    }
                }
            )
        
        return result.modified_count > 0

    async def get_class_students(self, class_id: str, current_user_id: str) -> ClassStudentsResponse:
        """Get list of students enrolled in a class."""
        self._ensure_collections()
        
        # Convert IDs to ObjectId for database queries
        try:
            class_oid = ObjectId(class_id)
            current_user_oid = ObjectId(current_user_id)
        except Exception:
            raise ValueError("Invalid ID format")
        
        # Verify class exists and check permissions
        class_doc = await self.collection.find_one({"_id": class_oid})
        if not class_doc:
            raise ValueError("Class not found")
        
        current_user = await self.users.find_one({"_id": current_user_oid})
        if not current_user:
            raise ValueError("Current user not found")
        
        # Check permissions - use string comparison for teacher_id
        if (current_user.get("role") != UserRole.ADMIN and 
            str(class_doc.get("teacher_id")) != current_user_id and
            current_user_id not in class_doc.get("student_ids", [])):
            raise PermissionError("Access denied")
        
        # Get student details with enrollment dates
        student_ids = class_doc.get("student_ids", [])
        students = []
        
        if student_ids:
            # Get student documents
            student_docs = await self.users.find(
                {"_id": {"$in": [ObjectId(sid) for sid in student_ids]}}
            ).to_list(None)
            
            # Create a map of student_id to student doc for easier lookup
            student_map = {str(doc["_id"]): doc for doc in student_docs}
            
            # Get enrollment dates from history
            enrollment_history = await self.db.enrollment_history.find(
                {"class_id": class_id, "user_id": {"$in": student_ids}, "status": "enrolled"}
            ).to_list(None)
            
            enrollment_date_map = {eh["user_id"]: eh.get("enrollment_date") for eh in enrollment_history}
            
            # Build student list with enrollment info
            for student_id in student_ids:
                student_doc = student_map.get(student_id)
                if student_doc:
                    students.append({
                        "id": student_id,  # Changed from user_id to id for standardization
                        "username": student_doc.get("username", "Unknown"),
                        "email": student_doc.get("email", ""),
                        "full_name": student_doc.get("full_name", ""),
                        "enrollment_date": enrollment_date_map.get(student_id)
                    })
        
        return ClassStudentsResponse(
            class_id=class_id,
            class_name=class_doc.get("name", "Unknown"),
            total_students=len(students),
            max_students=class_doc.get("max_students"),
            students=students
        )

    async def bulk_enroll_students(self, class_id: str, csv_data: str, current_user_id: str) -> BulkEnrollmentResponse:
        """Bulk enroll students via CSV data."""
        self._ensure_collections()
        
        # Convert IDs to ObjectId for database queries
        try:
            class_oid = ObjectId(class_id)
            current_user_oid = ObjectId(current_user_id)
        except Exception:
            raise ValueError("Invalid ID format")
        
        # Verify class and permissions
        class_doc = await self.collection.find_one({"_id": class_oid})
        if not class_doc:
            raise ValueError("Class not found")
        
        current_user = await self.users.find_one({"_id": current_user_oid})
        if not current_user:
            raise ValueError("Current user not found")
        
        # Check permissions - use string comparison for teacher_id
        if (current_user.get("role") != UserRole.ADMIN and 
            str(class_doc.get("teacher_id")) != current_user_id):
            raise PermissionError("Only class teacher or admin can manage enrollments")
        
        # Parse CSV data (expecting email addresses or usernames)
        import csv
        import io
        
        try:
            csv_reader = csv.reader(io.StringIO(csv_data))
            emails_or_usernames = []
            
            for row_num, row in enumerate(csv_reader, 1):
                if row and row[0].strip():  # Skip empty rows
                    identifier = row[0].strip()
                    # Basic email validation
                    if '@' in identifier or len(identifier) > 3:
                        emails_or_usernames.append(identifier)
                    else:
                        print(f"Skipping invalid identifier in row {row_num}: {identifier}")
        except Exception as e:
            raise ValueError(f"Invalid CSV format: {str(e)}")
        
        if not emails_or_usernames:
            raise ValueError("No valid identifiers found in CSV")
        
        # Process enrollments
        successful_enrollments = 0
        failed_enrollments = 0
        errors = []
        enrolled_users = []
        
        for identifier in emails_or_usernames:
            try:
                # Find user by email or username
                user_doc = await self.users.find_one({
                    "$or": [
                        {"email": identifier},
                        {"username": identifier}
                    ]
                })
                
                if not user_doc:
                    errors.append(f"User not found: {identifier}")
                    failed_enrollments += 1
                    continue
                
                # Check if user is a student
                if user_doc.get("role") not in [UserRole.STUDENT, "student"]:
                    errors.append(f"User {identifier} is not a student")
                    failed_enrollments += 1
                    continue
                
                user_id = str(user_doc["_id"])
                
                # Try to enroll
                enrollment_response = await self.enroll_student(class_id, user_id, current_user_id)
                enrolled_users.append(enrollment_response)
                successful_enrollments += 1
                
            except Exception as e:
                errors.append(f"Failed to enroll {identifier}: {str(e)}")
                failed_enrollments += 1
        
        return BulkEnrollmentResponse(
            total_processed=len(emails_or_usernames),
            successful_enrollments=successful_enrollments,
            failed_enrollments=failed_enrollments,
            errors=errors,
            enrolled_users=enrolled_users
        )

    def _serialize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to response format."""
        # Convert ObjectId to string and rename _id to id for response
        serialized = doc.copy()
        serialized["_id"] = str(doc["_id"])
        return serialized

__all__ = ["ClassService"]
