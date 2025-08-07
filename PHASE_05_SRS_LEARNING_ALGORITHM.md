# 🏫 PHASE 5: 3-LEVEL HIERARCHY MANAGEMENT
*Classroom management implementation (Decision #20: 3-level Structure)*

## 📋 Overview
**Phase Goal**: Implement comprehensive 3-level hierarchy (Classes → Courses → Lessons)  
**Dependencies**: Phase 4 (Core API Endpoints)  
**Estimated Time**: 4-5 days  
**Priority**: CRITICAL PATH

---

## 🎯 PHASE OBJECTIVES

### **5.1 Class Management APIs**
- [ ] Class CRUD operations
- [ ] Class enrollment management

### **5.2 Course Management APIs**  
- [ ] Course CRUD operations
- [ ] Course-class assignment

### **5.3 Lesson Management APIs**
- [ ] Lesson CRUD operations
- [ ] Lesson ordering & structure

### **5.4 Enrollment Management APIs**
- [ ] Multi-level enrollment system

---

## 🏛️ CLASS MANAGEMENT

### **5.1 Class CRUD Operations**

#### **Class Management Endpoints**
```python
# GET /api/v1/classes
@router.get("/", response_model=List[ClassListResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_classes(
    skip: int = 0,
    limit: int = 20,
    teacher_id: str? = None,
    is_active: bool? = None,
    current_user: User = Depends(get_current_user)
):
    # Teachers can only see their own classes
    if current_user.role == UserRole.TEACHER:
        teacher_id = current_user.id
    
    classes = await class_service.list_classes(
        skip=skip, 
        limit=limit, 
        teacher_id=teacher_id,
        is_active=is_active
    )
    return [ClassListResponse(**cls.dict()) for cls in classes]

# POST /api/v1/classes
@router.post("/", response_model=ClassResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_class(
    class_data: ClassCreateRequest,
    current_user: User = Depends(get_current_user)
):
    class_obj = await class_service.create_class({
        **class_data.dict(),
        "teacher_id": current_user.id
    })
    return ClassResponse(**class_obj.dict())
```

#### **Class Data Models**
```python
class ClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str? = Field(max_length=1000)
    max_students: int? = Field(gt=0, le=1000)
    start_date: datetime?
    end_date: datetime?

class ClassResponse(BaseModel):
    id: str
    name: str
    description: str?
    teacher_id: str
    teacher_name: str  # Populated from user
    student_ids: List[str] = []
    course_ids: List[str] = []
    max_students: int?
    current_enrollment: int = 0
    start_date: datetime?
    end_date: datetime?
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class ClassListResponse(BaseModel):
    id: str
    name: str
    description: str?
    teacher_name: str
    current_enrollment: int
    max_students: int?
    is_active: bool
    created_at: datetime
```

#### **Implementation Checklist**
- [ ] **Class CRUD Operations**
  - [ ] `GET /api/v1/classes` (teacher/admin)
  - [ ] `POST /api/v1/classes` (teacher/admin)
  - [ ] `GET /api/v1/classes/{id}`
  - [ ] `PUT /api/v1/classes/{id}`
  - [ ] `DELETE /api/v1/classes/{id}`

- [ ] **Class Features**
  - [ ] Teacher ownership validation
  - [ ] Student capacity management
  - [ ] Active/inactive status
  - [ ] Date range validation

### **5.2 Class Enrollment Management**

#### **Enrollment Endpoints**
```python
# POST /api/v1/classes/{class_id}/enroll/{user_id}
@router.post("/{class_id}/enroll/{user_id}")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def enroll_student(
    class_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    # Validate class ownership for teachers
    if current_user.role == UserRole.TEACHER:
        await permission_service.validate_class_ownership(current_user.id, class_id)
    
    # Validate user is a student
    user = await user_service.get_user(user_id)
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Can only enroll students")
    
    # Check class capacity
    class_obj = await class_service.get_class(class_id)
    if class_obj.max_students and class_obj.current_enrollment >= class_obj.max_students:
        raise HTTPException(status_code=400, detail="Class is at capacity")
    
    enrollment = await enrollment_service.enroll_in_class(user_id, class_id)
    return {"message": "Student enrolled successfully", "enrollment_id": enrollment.id}

# POST /api/v1/classes/{class_id}/bulk-enroll
@router.post("/{class_id}/bulk-enroll")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def bulk_enroll_students(
    class_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate CSV format and process enrollments
    results = await enrollment_service.bulk_enroll_from_csv(class_id, file)
    return {
        "message": "Bulk enrollment completed",
        "successful": results["successful"],
        "failed": results["failed"]
    }
```

#### **Implementation Checklist**
- [ ] **Enrollment Management**
  - [ ] `POST /api/v1/classes/{id}/enroll/{user_id}`
  - [ ] `DELETE /api/v1/classes/{id}/unenroll/{user_id}`
  - [ ] `GET /api/v1/classes/{id}/students`
  - [ ] `POST /api/v1/classes/{id}/bulk-enroll` (CSV upload)

- [ ] **Enrollment Features**
  - [ ] Student capacity checking
  - [ ] Duplicate enrollment prevention
  - [ ] Bulk enrollment via CSV
  - [ ] Enrollment history tracking

---

## 📚 COURSE MANAGEMENT

### **5.3 Course CRUD Operations**

#### **Course Management Endpoints**
```python
# GET /api/v1/courses
@router.get("/", response_model=List[CourseListResponse])
async def list_courses(
    skip: int = 0,
    limit: int = 20,
    category: str? = None,
    difficulty_level: str? = None,
    is_public: bool? = None,
    current_user: User = Depends(get_current_user)
):
    courses = await course_service.list_accessible_courses(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        category=category,
        difficulty_level=difficulty_level,
        is_public=is_public
    )
    return [CourseListResponse(**course.dict()) for course in courses]

# POST /api/v1/courses
@router.post("/", response_model=CourseResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_course(
    course_data: CourseCreateRequest,
    current_user: User = Depends(get_current_user)
):
    course = await course_service.create_course({
        **course_data.dict(),
        "creator_id": current_user.id
    })
    return CourseResponse(**course.dict())
```

#### **Course Data Models**
```python
class CourseCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str? = Field(max_length=2000)
    category: str
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_duration: int? = Field(gt=0)  # minutes
    is_public: bool = False
    requires_approval: bool = False

class CourseResponse(BaseModel):
    id: str
    title: str
    description: str?
    creator_id: str
    creator_name: str  # Populated from user
    lesson_ids: List[str] = []
    category: str
    difficulty_level: DifficultyLevel
    estimated_duration: int?
    is_public: bool
    requires_approval: bool
    enrollment_count: int = 0
    completion_rate: float = 0.0
    created_at: datetime
    updated_at: datetime

class CourseListResponse(BaseModel):
    id: str
    title: str
    description: str?
    creator_name: str
    category: str
    difficulty_level: DifficultyLevel
    estimated_duration: int?
    enrollment_count: int
    completion_rate: float
    lesson_count: int  # Calculated field
```

#### **Implementation Checklist**
- [ ] **Course CRUD Operations**
  - [ ] `GET /api/v1/courses`
  - [ ] `POST /api/v1/courses`
  - [ ] `GET /api/v1/courses/{id}`
  - [ ] `PUT /api/v1/courses/{id}`
  - [ ] `DELETE /api/v1/courses/{id}`

- [ ] **Course Features**
  - [ ] Creator ownership validation
  - [ ] Public/private course visibility
  - [ ] Category-based organization
  - [ ] Difficulty level classification

### **5.4 Course-Class Assignment**

#### **Course Assignment Endpoints**
```python
# POST /api/v1/classes/{class_id}/assign-course/{course_id}
@router.post("/{class_id}/assign-course/{course_id}")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def assign_course_to_class(
    class_id: str,
    course_id: str,
    assignment_data: CourseAssignmentRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate class ownership for teachers
    if current_user.role == UserRole.TEACHER:
        await permission_service.validate_class_ownership(current_user.id, class_id)
    
    # Validate course access
    await permission_service.validate_course_access(current_user.id, course_id)
    
    assignment = await class_service.assign_course(
        class_id, 
        course_id, 
        assignment_data.dict()
    )
    
    return {"message": "Course assigned to class successfully"}

# GET /api/v1/classes/{class_id}/courses
@router.get("/{class_id}/courses", response_model=List[CourseListResponse])
async def list_class_courses(
    class_id: str,
    current_user: User = Depends(get_current_user)
):
    # Validate access to class
    await permission_service.validate_class_access(current_user.id, class_id)
    
    courses = await class_service.get_assigned_courses(class_id)
    return [CourseListResponse(**course.dict()) for course in courses]
```

#### **Implementation Checklist**
- [ ] **Course-Class Assignment**
  - [ ] `POST /api/v1/classes/{class_id}/assign-course/{course_id}`
  - [ ] `DELETE /api/v1/classes/{class_id}/unassign-course/{course_id}`
  - [ ] `GET /api/v1/classes/{id}/courses`

- [ ] **Assignment Features**
  - [ ] Assignment date tracking
  - [ ] Assignment status management
  - [ ] Permission validation
  - [ ] Duplicate assignment prevention

---

## 📖 LESSON MANAGEMENT

### **5.5 Lesson CRUD Operations**

#### **Lesson Management Endpoints**
```python
# GET /api/v1/courses/{course_id}/lessons
@router.get("/{course_id}/lessons", response_model=List[LessonListResponse])
async def list_lessons(
    course_id: str,
    current_user: User = Depends(get_current_user)
):
    # Validate course access
    await permission_service.validate_course_access(current_user.id, course_id)
    
    lessons = await lesson_service.list_lessons(course_id)
    return [LessonListResponse(**lesson.dict()) for lesson in lessons]

# POST /api/v1/courses/{course_id}/lessons
@router.post("/{course_id}/lessons", response_model=LessonResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_lesson(
    course_id: str,
    lesson_data: LessonCreateRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate course ownership/access
    await permission_service.validate_course_modification_access(current_user.id, course_id)
    
    lesson = await lesson_service.create_lesson({
        **lesson_data.dict(),
        "course_id": course_id
    })
    return LessonResponse(**lesson.dict())
```

#### **Lesson Data Models**
```python
class LessonCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str? = Field(max_length=2000)
    learning_objectives: List[str] = []
    estimated_time: int? = Field(gt=0)  # minutes
    prerequisite_lessons: List[str] = []
    completion_criteria: dict? = None
    pass_threshold: float = Field(ge=0.0, le=1.0, default=0.7)

class LessonResponse(BaseModel):
    id: str
    title: str
    description: str?
    course_id: str
    deck_ids: List[str] = []
    order_index: int
    learning_objectives: List[str] = []
    estimated_time: int?
    prerequisite_lessons: List[str] = []
    completion_criteria: dict?
    pass_threshold: float
    created_at: datetime
    updated_at: datetime

class LessonListResponse(BaseModel):
    id: str
    title: str
    description: str?
    order_index: int
    estimated_time: int?
    deck_count: int  # Calculated field
    completion_criteria: dict?
    pass_threshold: float
```

#### **Implementation Checklist**
- [ ] **Lesson CRUD Operations**
  - [ ] `GET /api/v1/courses/{course_id}/lessons`
  - [ ] `POST /api/v1/courses/{course_id}/lessons`
  - [ ] `GET /api/v1/lessons/{id}`
  - [ ] `PUT /api/v1/lessons/{id}`
  - [ ] `DELETE /api/v1/lessons/{id}`

- [ ] **Lesson Features**
  - [ ] Learning objectives management
  - [ ] Prerequisite lesson tracking
  - [ ] Completion criteria configuration
  - [ ] Pass threshold settings

### **5.6 Lesson Ordering & Structure**

#### **Lesson Structure Endpoints**
```python
# PUT /api/v1/lessons/{lesson_id}/reorder
@router.put("/{lesson_id}/reorder")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def reorder_lesson(
    lesson_id: str,
    reorder_data: LessonReorderRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate lesson modification access
    await permission_service.validate_lesson_modification_access(current_user.id, lesson_id)
    
    await lesson_service.reorder_lesson(lesson_id, reorder_data.new_order_index)
    return {"message": "Lesson reordered successfully"}

# POST /api/v1/lessons/{lesson_id}/assign-deck/{deck_id}
@router.post("/{lesson_id}/assign-deck/{deck_id}")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def assign_deck_to_lesson(
    lesson_id: str,
    deck_id: str,
    assignment_data: DeckLessonAssignmentRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate permissions
    await permission_service.validate_lesson_modification_access(current_user.id, lesson_id)
    await permission_service.validate_deck_access(current_user.id, deck_id)
    
    assignment = await lesson_service.assign_deck(
        lesson_id, 
        deck_id, 
        assignment_data.dict()
    )
    
    return {"message": "Deck assigned to lesson successfully"}
```

#### **Implementation Checklist**
- [ ] **Lesson Ordering & Structure**
  - [ ] `PUT /api/v1/lessons/{id}/reorder`
  - [ ] `POST /api/v1/lessons/{id}/assign-deck/{deck_id}`
  - [ ] `DELETE /api/v1/lessons/{id}/unassign-deck/{deck_id}`

- [ ] **Structure Features**
  - [ ] Lesson ordering within course
  - [ ] Deck assignment to lessons
  - [ ] Prerequisite validation
  - [ ] Structural integrity checks

---

## 📝 ENROLLMENT MANAGEMENT

### **5.7 Multi-level Enrollment**

#### **Enrollment Endpoints**
```python
# GET /api/v1/enrollments/my
@router.get("/my", response_model=List[EnrollmentResponse])
async def get_my_enrollments(
    enrollment_type: str? = None,
    status: str? = None,
    current_user: User = Depends(get_current_user)
):
    enrollments = await enrollment_service.get_user_enrollments(
        current_user.id,
        enrollment_type=enrollment_type,
        status=status
    )
    return [EnrollmentResponse(**enrollment.dict()) for enrollment in enrollments]

# POST /api/v1/enrollments/class/{class_id}
@router.post("/class/{class_id}")
async def enroll_in_class(
    class_id: str,
    current_user: User = Depends(get_current_user)
):
    # Validate student role
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can enroll in classes")
    
    enrollment = await enrollment_service.enroll_in_class(current_user.id, class_id)
    return {"message": "Enrolled in class successfully", "enrollment_id": enrollment.id}
```

#### **Enrollment Data Models**
```python
class EnrollmentResponse(BaseModel):
    id: str
    user_id: str
    class_id: str?
    course_id: str?
    lesson_id: str?
    enrollment_type: EnrollmentType  # class, course, lesson
    enrollment_date: datetime
    completion_date: datetime?
    status: EnrollmentStatus  # enrolled, in_progress, completed, dropped
    progress_percentage: float = 0.0
    last_activity: datetime?
    
    # Populated fields
    class_name: str?
    course_title: str?
    lesson_title: str?

class EnrollmentListResponse(BaseModel):
    id: str
    enrollment_type: EnrollmentType
    target_name: str  # class name, course title, or lesson title
    status: EnrollmentStatus
    progress_percentage: float
    enrollment_date: datetime
    last_activity: datetime?
```

#### **Implementation Checklist**
- [ ] **Multi-level Enrollment**
  - [ ] `GET /api/v1/enrollments/my`
  - [ ] `POST /api/v1/enrollments/class/{class_id}`
  - [ ] `POST /api/v1/enrollments/course/{course_id}`
  - [ ] `GET /api/v1/enrollments/class/{class_id}/students`
  - [ ] `GET /api/v1/enrollments/course/{course_id}/students`

- [ ] **Enrollment Features**
  - [ ] Multi-level enrollment support
  - [ ] Enrollment status tracking
  - [ ] Progress percentage calculation
  - [ ] Activity timestamp tracking

### **5.8 Enrollment Reporting**

#### **Enrollment Reports**
```python
# GET /api/v1/enrollments/class/{class_id}/students
@router.get("/class/{class_id}/students", response_model=List[StudentEnrollmentResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_class_students(
    class_id: str,
    status: str? = None,
    current_user: User = Depends(get_current_user)
):
    # Validate class access
    await permission_service.validate_class_access(current_user.id, class_id)
    
    students = await enrollment_service.get_class_students(class_id, status=status)
    return [StudentEnrollmentResponse(**student.dict()) for student in students]

# GET /api/v1/enrollments/course/{course_id}/students
@router.get("/course/{course_id}/students", response_model=List[StudentEnrollmentResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_course_students(
    course_id: str,
    current_user: User = Depends(get_current_user)
):
    students = await enrollment_service.get_course_students(course_id)
    return [StudentEnrollmentResponse(**student.dict()) for student in students]
```

#### **Implementation Checklist**
- [ ] **Enrollment Reporting**
  - [ ] Class enrollment reports
  - [ ] Course enrollment reports
  - [ ] Progress tracking reports
  - [ ] Activity summaries

---

## 🧪 TESTING CHECKLIST

### **Class Management Tests**
- [ ] **Class CRUD Tests**
  - [ ] Class creation by teachers
  - [ ] Class listing with permissions
  - [ ] Class updates and validation
  - [ ] Class deletion with constraints

- [ ] **Enrollment Tests**
  - [ ] Student enrollment validation
  - [ ] Capacity limit enforcement
  - [ ] Bulk enrollment processing
  - [ ] Enrollment permission checks

### **Course Management Tests**
- [ ] **Course CRUD Tests**
  - [ ] Course creation and ownership
  - [ ] Course visibility (public/private)
  - [ ] Course assignment to classes
  - [ ] Course access validation

### **Lesson Management Tests**
- [ ] **Lesson CRUD Tests**
  - [ ] Lesson creation within courses
  - [ ] Lesson ordering and reordering
  - [ ] Deck assignment to lessons
  - [ ] Prerequisite validation

### **Enrollment System Tests**
- [ ] **Multi-level Enrollment Tests**
  - [ ] Class enrollment flow
  - [ ] Course enrollment flow
  - [ ] Progress tracking accuracy
  - [ ] Cross-level access validation

---

## 📋 COMPLETION CRITERIA

✅ **Phase 5 Complete When:**
- [ ] All class management APIs implemented
- [ ] Course management system functional
- [ ] Lesson management with ordering working
- [ ] Multi-level enrollment system operational
- [ ] 3-level hierarchy relationships validated
- [ ] Permission system working across all levels
- [ ] Assignment system functional
- [ ] Comprehensive testing completed
- [ ] Documentation for hierarchy system created

---

## 🔄 NEXT PHASE
**PHASE 6**: Study System Implementation
- Implement spaced repetition algorithm (SM-2)
- Build study session management
- Create progress tracking system

---

*Part of comprehensive Flashcard LMS implementation*  
*Based on 20 decisions from DECISION_FRAMEWORK.md*
