# 🔐 PHASE 3: AUTHENTICATION & AUTHORIZATION
*Security implementation (Decision #19: Basic Auth + Decision #3: Admin Reset)*

## 📋 Overview
**Phase Goal**: Implement comprehensive authentication and authorization system  
**Dependencies**: Phase 2 (Database Schema)  
**Estimated Time**: 3-4 days  
**Priority**: CRITICAL PATH

---

## 🎯 PHASE OBJECTIVES

### **3.1 Authentication System**
- [ ] User Registration (Decision #2: Optional Email)
- [ ] Login System (Decision #19: Basic Auth)  
- [ ] Password Reset (Decision #3: Admin Reset)

### **3.2 Authorization & Permissions (Decision #1: Full Role System)**
- [ ] Role-Based Access Control
- [ ] Resource-Based Permissions (3-level Hierarchy)
- [ ] Advanced Privacy Controls (Decision #5: Advanced)

### **3.3 Security Implementation**
- [ ] JWT Token Management
- [ ] Password Security
- [ ] Permission Decorators
- [ ] Security Middleware

---

## 🔑 AUTHENTICATION SYSTEM

### **3.1 User Registration (Decision #2: Optional Email)**

#### **Registration Endpoint**
```python
# POST /api/v1/auth/register
class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.STUDENT  # Default to student
    
class UserRegisterResponse(BaseModel):
    user_id: str
    email: str
    username: str
    role: UserRole
    email_verified: bool = False
    message: str = "Registration successful"
```

#### **Implementation Checklist**
- [ ] **Registration Logic**
  - [ ] Email uniqueness validation
  - [ ] Username uniqueness validation
  - [ ] Password strength validation
  - [ ] Password hashing with bcrypt
  - [ ] Default role assignment (student)

- [ ] **Optional Email Verification**
  - [ ] Email verification token generation
  - [ ] Email verification endpoint
  - [ ] Email template system (optional)
  - [ ] Verification status tracking

- [ ] **Role Assignment Logic**
  - [ ] Student auto-assignment
  - [ ] Teacher role (admin approval required)
  - [ ] Admin role (manual assignment only)
  - [ ] Role validation rules

### **3.2 Login System (Decision #19: Basic Auth)**

#### **Login Endpoints**
```python
# POST /api/v1/auth/login
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserInfo

class UserInfo(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: UserRole
    email_verified: bool
```

#### **JWT Implementation**
```python
# JWT Token Structure
{
  "sub": "user_id",           # Subject (user ID)
  "email": "user@example.com",
  "username": "username",
  "role": "student",          # student, teacher, admin
  "exp": 1234567890,          # Expiration timestamp
  "iat": 1234567890,          # Issued at timestamp
  "type": "access"            # Token type
}
```

#### **Implementation Checklist**
- [ ] **JWT Token Management**
  - [ ] Access token generation (30 min expiry)
  - [ ] Refresh token generation (7 days expiry)
  - [ ] Token validation middleware
  - [ ] Token blacklist system (logout)

- [ ] **Login Validation**
  - [ ] Email/password verification
  - [ ] Account status checking (is_active)
  - [ ] Failed attempt tracking
  - [ ] Rate limiting protection

- [ ] **Token Refresh System**
  - [ ] Refresh token endpoint
  - [ ] Token rotation on refresh
  - [ ] Refresh token validation

### **3.3 Password Reset (Decision #3: Admin Reset)**

#### **Admin Reset Endpoints**
```python
# PUT /api/v1/admin/users/{user_id}/reset-password
class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8)
    reset_reason: str?

# PUT /api/v1/teachers/students/{user_id}/reset-password  
class TeacherPasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8)
    student_id: str
```

#### **Implementation Checklist**
- [ ] **Admin Password Reset**
  - [ ] Admin can reset any user password
  - [ ] Password reset audit logging
  - [ ] Force password change on next login
  - [ ] Reset notification to user

- [ ] **Teacher Password Reset**
  - [ ] Teachers can reset student passwords
  - [ ] Validate teacher-student relationship
  - [ ] Class membership verification
  - [ ] Permission checking

- [ ] **Security Measures**
  - [ ] Password reset logging
  - [ ] Permission validation
  - [ ] Rate limiting on reset attempts
  - [ ] Secure password generation option

---

## 🛡️ AUTHORIZATION SYSTEM

### **3.4 Role-Based Access Control (Decision #1: Full Role System)**

#### **Role Hierarchy**
```python
class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher" 
    ADMIN = "admin"

# Permission Matrix
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "user:create", "user:read", "user:update", "user:delete",
        "class:create", "class:read", "class:update", "class:delete",
        "course:create", "course:read", "course:update", "course:delete",
        "deck:create", "deck:read", "deck:update", "deck:delete",
        "system:manage"
    ],
    UserRole.TEACHER: [
        "class:create", "class:read", "class:update",
        "course:create", "course:read", "course:update", 
        "deck:create", "deck:read", "deck:update",
        "student:manage", "assignment:create"
    ],
    UserRole.STUDENT: [
        "deck:read", "study:all", "progress:read",
        "profile:update"
    ]
}
```

#### **Implementation Checklist**
- [ ] **Permission System**
  - [ ] Define comprehensive permission matrix
  - [ ] Create permission checking functions
  - [ ] Role hierarchy validation
  - [ ] Permission inheritance logic

- [ ] **Decorators**
  - [ ] `@require_role(UserRole.ADMIN)`
  - [ ] `@require_permission("deck:create")`
  - [ ] `@require_ownership(resource="deck")`
  - [ ] `@require_membership(resource="class")`

### **3.5 Resource-Based Permissions (3-level Hierarchy)**

#### **Ownership Validation**
```python
# Deck Ownership
async def check_deck_ownership(user_id: str, deck_id: str) -> bool:
    deck = await deck_service.get_deck(deck_id)
    return deck.owner_id == user_id

# Class Membership  
async def check_class_membership(user_id: str, class_id: str) -> bool:
    enrollment = await enrollment_service.get_enrollment(user_id, class_id)
    return enrollment is not None

# Course Access
async def check_course_access(user_id: str, course_id: str) -> bool:
    # Check direct enrollment or class-based access
    return await has_course_access(user_id, course_id)
```

#### **Implementation Checklist**
- [ ] **Ownership Validation**
  - [ ] Deck ownership checking
  - [ ] Class ownership (teacher)
  - [ ] Course ownership (creator)
  - [ ] Lesson access validation

- [ ] **Membership Validation**
  - [ ] Class membership checking
  - [ ] Course enrollment verification
  - [ ] Lesson access through course
  - [ ] Cross-level permission inheritance

- [ ] **Assignment-Based Access**
  - [ ] Assigned deck access validation
  - [ ] Assignment-specific permissions
  - [ ] Due date and requirement checking

### **3.6 Advanced Privacy Controls (Decision #5: Advanced)**

#### **Deck Privacy Levels**
```python
class DeckPrivacyLevel(str, Enum):
    PRIVATE = "private"                    # Owner only
    CLASS_ASSIGNED = "class-assigned"      # Assigned to specific class
    COURSE_ASSIGNED = "course-assigned"    # Assigned to specific course  
    LESSON_ASSIGNED = "lesson-assigned"    # Assigned to specific lesson
    PUBLIC = "public"                      # Everyone can access

async def check_deck_access(user_id: str, deck_id: str) -> bool:
    deck = await deck_service.get_deck(deck_id)
    user = await user_service.get_user(user_id)
    
    # Admin can access everything
    if user.role == UserRole.ADMIN:
        return True
        
    # Owner can always access
    if deck.owner_id == user_id:
        return True
        
    # Public decks
    if deck.privacy_level == DeckPrivacyLevel.PUBLIC:
        return True
        
    # Check assignment-based access
    return await check_assignment_access(user_id, deck_id)
```

#### **Implementation Checklist**
- [ ] **Privacy Level Validation**
  - [ ] Private deck access (owner only)
  - [ ] Class-assigned deck access
  - [ ] Course-assigned deck access  
  - [ ] Lesson-assigned deck access
  - [ ] Public deck access (unrestricted)

- [ ] **Assignment Access**
  - [ ] Check class assignments
  - [ ] Check course assignments
  - [ ] Check lesson assignments
  - [ ] Validate assignment status

---

## 🔧 SECURITY MIDDLEWARE

### **3.7 Authentication Middleware**

#### **JWT Authentication**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await user_service.get_user(user_id)
    if user is None:
        raise credentials_exception
    return user
```

#### **Implementation Checklist**
- [ ] **JWT Middleware**
  - [ ] Token validation
  - [ ] User extraction from token
  - [ ] Token expiration checking
  - [ ] Blacklist validation

- [ ] **Security Headers**
  - [ ] CORS configuration
  - [ ] Security headers (CSRF, XSS)
  - [ ] Rate limiting middleware
  - [ ] Request validation

### **3.8 Permission Decorators**

#### **Role-Based Decorators**
```python
def require_role(*allowed_roles: UserRole):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_ownership(resource_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check resource ownership
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

#### **Implementation Checklist**
- [ ] **Permission Decorators**
  - [ ] Role requirement decorators
  - [ ] Resource ownership decorators
  - [ ] Membership requirement decorators
  - [ ] Assignment access decorators

- [ ] **Security Utilities**
  - [ ] Password hashing utilities
  - [ ] Token generation utilities
  - [ ] Permission checking utilities
  - [ ] Audit logging utilities

---

## 🧪 TESTING CHECKLIST

### **Authentication Tests**
- [ ] **Registration Tests**
  - [ ] Valid registration flow
  - [ ] Duplicate email/username handling
  - [ ] Password validation
  - [ ] Role assignment

- [ ] **Login Tests**
  - [ ] Valid login flow
  - [ ] Invalid credentials handling
  - [ ] JWT token generation
  - [ ] Token refresh flow

- [ ] **Password Reset Tests**
  - [ ] Admin reset functionality
  - [ ] Teacher reset permissions
  - [ ] Security validations
  - [ ] Audit logging

### **Authorization Tests**
- [ ] **Role-Based Tests**
  - [ ] Admin access validation
  - [ ] Teacher permission checking
  - [ ] Student access restrictions
  - [ ] Cross-role scenarios

- [ ] **Resource-Based Tests**
  - [ ] Deck ownership validation
  - [ ] Class membership checking
  - [ ] Course access validation
  - [ ] Privacy level enforcement

- [ ] **3-Level Hierarchy Tests**
  - [ ] Class-course-lesson access
  - [ ] Assignment-based permissions
  - [ ] Cross-level inheritance
  - [ ] Edge case scenarios

---

## 📋 COMPLETION CRITERIA

✅ **Phase 3 Complete When:**
- [ ] User registration system working
- [ ] JWT authentication implemented
- [ ] Password reset system functional
- [ ] Role-based access control working
- [ ] Resource-based permissions implemented
- [ ] Advanced privacy controls functional
- [ ] All security middleware in place
- [ ] Permission decorators created
- [ ] Comprehensive test coverage
- [ ] Security audit completed

---

## 🔄 NEXT PHASE
**PHASE 4**: Core API Endpoints
- Implement basic CRUD operations
- Build user management APIs
- Create deck and flashcard endpoints

---

*Part of comprehensive Flashcard LMS implementation*  
*Based on 20 decisions from DECISION_FRAMEWORK.md*
