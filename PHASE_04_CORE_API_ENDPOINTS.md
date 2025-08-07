# 🌐 PHASE 4: CORE API ENDPOINTS  
*Main functionality implementation with 3-level hierarchy*

## 📋 Overview
**Phase Goal**: Implement fundamental CRUD operations and core API endpoints  
**Dependencies**: Phase 3 (Authentication & Authorization)  
**Estimated Time**: 4-5 days  
**Priority**: CRITICAL PATH

---

## 🎯 PHASE OBJECTIVES

### **4.1 Authentication APIs**
- [ ] User registration and login endpoints
- [ ] Token management endpoints

### **4.2 User Management APIs (Decision #4: Extended Profile)**
- [ ] User profile management
- [ ] Admin user management (Decision #3: Admin Reset)

### **4.3 Deck Management APIs**
- [ ] Deck CRUD operations (Decision #5: Advanced Privacy)
- [ ] Deck categories (Decision #7: Predefined)
- [ ] Deck privacy & assignment system

### **4.4 Flashcard APIs (Decision #6: Multimedia)**
- [ ] Flashcard CRUD operations
- [ ] Multimedia support (Decision #17: Local Storage)

---

## 🔐 AUTHENTICATION APIs

### **4.1 Authentication Endpoints**

#### **Registration & Login**
```python
# POST /api/v1/auth/register
@router.post("/register", response_model=UserRegisterResponse)
async def register_user(
    user_data: UserRegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Validate email uniqueness
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = security.hash_password(user_data.password)
    user = await user_service.create_user({
        **user_data.dict(exclude={"password"}),
        "hashed_password": hashed_password
    })
    
    return UserRegisterResponse(**user.dict())

# POST /api/v1/auth/login  
@router.post("/login", response_model=TokenResponse)
async def login_user(
    credentials: UserLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Validate credentials
    user = await auth_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate tokens
    access_token = security.create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(**user.dict())
    )
```

#### **Implementation Checklist**
- [ ] **Registration Endpoint**
  - [ ] `POST /api/v1/auth/register`
  - [ ] Email/username uniqueness validation
  - [ ] Password hashing with bcrypt
  - [ ] Role assignment (default: student)
  - [ ] Error handling and validation

- [ ] **Login Endpoint**
  - [ ] `POST /api/v1/auth/login`
  - [ ] Credential validation
  - [ ] JWT token generation
  - [ ] User info in response
  - [ ] Rate limiting protection

- [ ] **Token Management**
  - [ ] `POST /api/v1/auth/refresh`
  - [ ] `POST /api/v1/auth/logout`
  - [ ] `POST /api/v1/auth/verify-email` (optional)
  - [ ] Token blacklist on logout
  - [ ] Token validation middleware

---

## 👤 USER MANAGEMENT APIs

### **4.2 User Profile APIs (Decision #4: Extended Profile)**

#### **Profile Management**
```python
# GET /api/v1/users/profile
@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    profile = await user_service.get_user_profile(current_user.id)
    return UserProfileResponse(**profile.dict())

# PUT /api/v1/users/profile
@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    updated_profile = await user_service.update_user_profile(
        current_user.id, 
        profile_data.dict(exclude_unset=True)
    )
    return UserProfileResponse(**updated_profile.dict())
```

#### **Extended Profile Models**
```python
class UserProfileResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    avatar_url: str?
    bio: str?
    role: UserRole
    
    # Extended Profile (Decision #4)
    learning_preferences: dict?
    learning_goals: List[str] = []
    study_schedule: dict?
    achievements: List[str] = []
    
    # Stats
    total_study_time: int = 0
    cards_studied: int = 0
    study_streak: int = 0
    
    # Meta
    email_verified: bool = False
    created_at: datetime
    last_study_date: datetime?

class UserProfileUpdateRequest(BaseModel):
    full_name: str?
    bio: str?
    learning_preferences: dict?
    learning_goals: List[str]?
    study_schedule: dict?
```

#### **Implementation Checklist**
- [ ] **Profile Endpoints**
  - [ ] `GET /api/v1/users/profile`
  - [ ] `PUT /api/v1/users/profile`
  - [ ] `PUT /api/v1/users/learning-goals`
  - [ ] `PUT /api/v1/users/study-schedule`
  - [ ] `GET /api/v1/users/achievements`

- [ ] **Extended Profile Features**
  - [ ] Learning preferences management
  - [ ] Learning goals tracking
  - [ ] Study schedule configuration
  - [ ] Achievement display
  - [ ] Profile statistics

### **4.3 Admin User Management (Decision #3: Admin Reset)**

#### **Admin User Operations**
```python
# GET /api/v1/admin/users
@router.get("/users", response_model=List[UserListResponse])
@require_role(UserRole.ADMIN)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    role: UserRole? = None,
    current_user: User = Depends(get_current_user)
):
    users = await user_service.list_users(skip=skip, limit=limit, role=role)
    return [UserListResponse(**user.dict()) for user in users]

# PUT /api/v1/admin/users/{user_id}/reset-password
@router.put("/users/{user_id}/reset-password")
@require_role(UserRole.ADMIN)
async def reset_user_password(
    user_id: str,
    reset_data: PasswordResetRequest,
    current_user: User = Depends(get_current_user)
):
    await auth_service.reset_password(user_id, reset_data.new_password)
    await audit_service.log_password_reset(current_user.id, user_id, reset_data.reset_reason)
    return {"message": "Password reset successfully"}
```

#### **Implementation Checklist**
- [ ] **Admin User Management**
  - [ ] `GET /api/v1/admin/users`
  - [ ] `POST /api/v1/admin/users` (create user)
  - [ ] `PUT /api/v1/admin/users/{id}/reset-password`
  - [ ] `PUT /api/v1/admin/users/{id}/role`
  - [ ] `DELETE /api/v1/admin/users/{id}`

- [ ] **Admin Features**
  - [ ] User listing with filters
  - [ ] User creation with role assignment
  - [ ] Password reset with audit logging
  - [ ] Role modification
  - [ ] User deactivation

---

## 📚 DECK MANAGEMENT APIs

### **4.4 Deck CRUD Operations (Decision #5: Advanced Privacy)**

#### **Deck Management**
```python
# GET /api/v1/decks
@router.get("/", response_model=List[DeckListResponse])
async def list_decks(
    skip: int = 0,
    limit: int = 20,
    category: str? = None,
    privacy_level: DeckPrivacyLevel? = None,
    current_user: User = Depends(get_current_user)
):
    # Apply privacy filtering based on user role and access
    decks = await deck_service.list_accessible_decks(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        category=category,
        privacy_level=privacy_level
    )
    return [DeckListResponse(**deck.dict()) for deck in decks]

# POST /api/v1/decks
@router.post("/", response_model=DeckResponse)
async def create_deck(
    deck_data: DeckCreateRequest,
    current_user: User = Depends(get_current_user)
):
    deck = await deck_service.create_deck({
        **deck_data.dict(),
        "owner_id": current_user.id
    })
    return DeckResponse(**deck.dict())
```

#### **Deck Models**
```python
class DeckCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str? = Field(max_length=1000)
    category: str
    tags: List[str] = []
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    privacy_level: DeckPrivacyLevel = DeckPrivacyLevel.PRIVATE

class DeckResponse(BaseModel):
    id: str
    title: str
    description: str?
    owner_id: str
    owner_name: str  # Populated from user
    category: str
    tags: List[str]
    difficulty_level: DifficultyLevel
    privacy_level: DeckPrivacyLevel
    card_count: int
    study_count: int
    average_rating: float?
    supports_multimedia: bool
    created_at: datetime
    updated_at: datetime
```

#### **Implementation Checklist**
- [ ] **Deck CRUD Operations**
  - [ ] `GET /api/v1/decks` (with privacy filtering)
  - [ ] `POST /api/v1/decks`
  - [ ] `GET /api/v1/decks/{id}`
  - [ ] `PUT /api/v1/decks/{id}`
  - [ ] `DELETE /api/v1/decks/{id}`

- [ ] **Advanced Privacy Features**
  - [ ] Privacy-based deck filtering
  - [ ] Access permission validation
  - [ ] Owner-only modification
  - [ ] Assignment-based access

### **4.5 Deck Categories (Decision #7: Predefined)**

#### **Category Management**
```python
# GET /api/v1/decks/categories
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories():
    categories = await category_service.list_categories()
    return [CategoryResponse(**cat.dict()) for cat in categories]

# POST /api/v1/admin/categories (Admin only)
@router.post("/categories", response_model=CategoryResponse)
@require_role(UserRole.ADMIN)
async def create_category(
    category_data: CategoryCreateRequest,
    current_user: User = Depends(get_current_user)
):
    category = await category_service.create_category(category_data.dict())
    return CategoryResponse(**category.dict())
```

#### **Predefined Categories**
```python
DEFAULT_CATEGORIES = [
    {"name": "Language Learning", "description": "Foreign language vocabulary and grammar"},
    {"name": "Mathematics", "description": "Math formulas, theorems, and concepts"},
    {"name": "Science", "description": "Biology, Chemistry, Physics concepts"},
    {"name": "History", "description": "Historical facts, dates, and events"},
    {"name": "Literature", "description": "Literary terms, quotes, and analysis"},
    {"name": "Computer Science", "description": "Programming, algorithms, and CS concepts"},
    {"name": "Medical", "description": "Medical terminology and procedures"},
    {"name": "Business", "description": "Business terms and concepts"},
    {"name": "Geography", "description": "Countries, capitals, and geographical facts"},
    {"name": "General Knowledge", "description": "Miscellaneous facts and trivia"}
]
```

#### **Implementation Checklist**
- [ ] **Category System**
  - [ ] `GET /api/v1/decks/categories`
  - [ ] `POST /api/v1/admin/categories` (admin only)
  - [ ] `PUT /api/v1/admin/categories/{id}`
  - [ ] `DELETE /api/v1/admin/categories/{id}`

- [ ] **Category Features**
  - [ ] Predefined category seeding
  - [ ] Custom category creation (admin)
  - [ ] Category-based deck filtering
  - [ ] Tag system integration

### **4.6 Deck Privacy & Assignment**

#### **Assignment Management**
```python
# POST /api/v1/decks/{deck_id}/assign/class/{class_id}
@router.post("/assign/class/{class_id}")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def assign_deck_to_class(
    deck_id: str,
    class_id: str,
    assignment_data: DeckAssignmentRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate permissions
    await permission_service.validate_class_access(current_user.id, class_id)
    
    assignment = await assignment_service.create_assignment({
        "deck_id": deck_id,
        "class_id": class_id,
        "assigned_by": current_user.id,
        "assignment_type": "class",
        **assignment_data.dict()
    })
    
    return {"message": "Deck assigned to class successfully", "assignment_id": assignment.id}
```

#### **Implementation Checklist**
- [ ] **Privacy Management**
  - [ ] `PUT /api/v1/decks/{id}/privacy`
  - [ ] Privacy level validation
  - [ ] Access control enforcement

- [ ] **Assignment System**
  - [ ] `POST /api/v1/decks/{id}/assign/class/{class_id}`
  - [ ] `POST /api/v1/decks/{id}/assign/course/{course_id}`
  - [ ] `POST /api/v1/decks/{id}/assign/lesson/{lesson_id}`
  - [ ] `DELETE /api/v1/deck-assignments/{id}`

---

## 🃏 FLASHCARD APIs

### **4.7 Flashcard CRUD (Decision #6: Multimedia)**

#### **Flashcard Management**
```python
# GET /api/v1/decks/{deck_id}/flashcards
@router.get("/{deck_id}/flashcards", response_model=List[FlashcardResponse])
async def list_flashcards(
    deck_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    # Validate deck access
    await permission_service.validate_deck_access(current_user.id, deck_id)
    
    flashcards = await flashcard_service.list_flashcards(deck_id, skip=skip, limit=limit)
    return [FlashcardResponse(**card.dict()) for card in flashcards]

# POST /api/v1/decks/{deck_id}/flashcards
@router.post("/{deck_id}/flashcards", response_model=FlashcardResponse)
async def create_flashcard(
    deck_id: str,
    flashcard_data: FlashcardCreateRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate deck ownership
    await permission_service.validate_deck_ownership(current_user.id, deck_id)
    
    flashcard = await flashcard_service.create_flashcard({
        **flashcard_data.dict(),
        "deck_id": deck_id
    })
    
    return FlashcardResponse(**flashcard.dict())
```

#### **Flashcard Models**
```python
class FlashcardCreateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=2000)
    hint: str? = Field(max_length=500)
    explanation: str? = Field(max_length=1000)
    formatting_data: dict? = None

class FlashcardResponse(BaseModel):
    id: str
    deck_id: str
    question: str
    answer: str
    hint: str?
    explanation: str?
    
    # Multimedia fields
    question_image: str?
    answer_image: str?
    question_audio: str?
    answer_audio: str?
    formatting_data: dict?
    
    # SM-2 Algorithm data
    repetitions: int = 0
    ease_factor: float = 2.5
    interval: int = 0
    next_review: datetime?
    
    # Statistics
    review_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    
    created_at: datetime
    updated_at: datetime
```

#### **Implementation Checklist**
- [ ] **Flashcard CRUD**
  - [ ] `GET /api/v1/decks/{deck_id}/flashcards`
  - [ ] `POST /api/v1/decks/{deck_id}/flashcards`
  - [ ] `GET /api/v1/flashcards/{id}`
  - [ ] `PUT /api/v1/flashcards/{id}`
  - [ ] `DELETE /api/v1/flashcards/{id}`

- [ ] **Content Management**
  - [ ] Rich text support
  - [ ] Formatting data handling
  - [ ] Hint and explanation fields
  - [ ] Validation and sanitization

### **4.8 Multimedia Support (Decision #17: Local Storage)**

#### **File Upload Endpoints**
```python
# POST /api/v1/flashcards/{flashcard_id}/upload/question-image
@router.post("/{flashcard_id}/upload/question-image")
async def upload_question_image(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate flashcard ownership
    await permission_service.validate_flashcard_ownership(current_user.id, flashcard_id)
    
    # Validate file type and size
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Save file and update flashcard
    file_path = await file_service.save_upload(file, "images")
    await flashcard_service.update_flashcard(flashcard_id, {"question_image": file_path})
    
    return {"message": "Image uploaded successfully", "file_path": file_path}
```

#### **Implementation Checklist**
- [ ] **Multimedia Upload**
  - [ ] `POST /api/v1/flashcards/{id}/upload/question-image`
  - [ ] `POST /api/v1/flashcards/{id}/upload/answer-image`
  - [ ] `POST /api/v1/flashcards/{id}/upload/question-audio`
  - [ ] `POST /api/v1/flashcards/{id}/upload/answer-audio`
  - [ ] `DELETE /api/v1/flashcards/{id}/media/{media_type}`

- [ ] **File Management**
  - [ ] File type validation (images: jpg, png, gif; audio: mp3, wav)
  - [ ] File size limits enforcement
  - [ ] Secure file storage
  - [ ] File cleanup on deletion

---

## 🧪 TESTING CHECKLIST

### **Authentication API Tests**
- [ ] **Registration Tests**
  - [ ] Valid registration flow
  - [ ] Duplicate email handling
  - [ ] Password validation
  - [ ] Role assignment

- [ ] **Login Tests**
  - [ ] Valid login flow
  - [ ] Invalid credentials
  - [ ] Token generation
  - [ ] Token validation

### **User Management Tests**
- [ ] **Profile Tests**
  - [ ] Profile retrieval
  - [ ] Profile updates
  - [ ] Extended profile fields
  - [ ] Permission validation

- [ ] **Admin Tests**
  - [ ] User listing
  - [ ] Password reset
  - [ ] Role management
  - [ ] Permission enforcement

### **Deck Management Tests**
- [ ] **CRUD Tests**
  - [ ] Deck creation
  - [ ] Deck listing with privacy
  - [ ] Deck updates
  - [ ] Deck deletion

- [ ] **Privacy Tests**
  - [ ] Access control validation
  - [ ] Assignment-based access
  - [ ] Owner permissions
  - [ ] Role-based filtering

### **Flashcard Tests**
- [ ] **CRUD Tests**
  - [ ] Flashcard creation
  - [ ] Flashcard listing
  - [ ] Flashcard updates
  - [ ] Permission validation

- [ ] **Multimedia Tests**
  - [ ] File upload validation
  - [ ] File type restrictions
  - [ ] File size limits
  - [ ] File serving

---

## 📋 COMPLETION CRITERIA

✅ **Phase 4 Complete When:**
- [ ] All authentication endpoints implemented
- [ ] User management APIs functional
- [ ] Deck CRUD operations working
- [ ] Flashcard management complete
- [ ] Multimedia upload system functional
- [ ] Privacy and permission system working
- [ ] Category system implemented
- [ ] Comprehensive API testing completed
- [ ] Error handling and validation in place
- [ ] API documentation generated

---

## 🔄 NEXT PHASE
**PHASE 5**: 3-Level Hierarchy Management
- Implement class, course, and lesson management
- Build enrollment system
- Create assignment workflows

---

*Part of comprehensive Flashcard LMS implementation*  
*Based on 20 decisions from DECISION_FRAMEWORK.md*
