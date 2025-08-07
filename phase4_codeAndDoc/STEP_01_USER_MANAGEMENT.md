# 📝 STEP 1: USER MANAGEMENT APIs
*Extended user profiles and admin management*

## 🎯 OBJECTIVES
- Extend user profile management beyond basic auth
- Add admin capabilities for user management
- Implement profile data validation and updates

## 📋 IMPLEMENTATION CHECKLIST

### **A. User Profile Models** ⏳
- [ ] Extend User model with profile fields
- [ ] Add profile update schemas
- [ ] Implement profile validation

### **B. User Profile Service** ⏳
- [ ] Profile retrieval service
- [ ] Profile update service with validation
- [ ] Profile picture handling

### **C. User Profile Endpoints** ⏳
- [ ] `GET /api/v1/users/profile` - Get current user profile
- [ ] `PUT /api/v1/users/profile` - Update current user profile
- [ ] `POST /api/v1/users/profile/avatar` - Upload profile picture

### **D. Admin User Management** ⏳
- [ ] Admin-only user listing service
- [ ] User status management (active/inactive)
- [ ] User role management

### **E. Admin User Endpoints** ⏳
- [ ] `GET /api/v1/admin/users` - List all users (admin only)
- [ ] `GET /api/v1/admin/users/{user_id}` - Get user by ID (admin only)
- [ ] `PUT /api/v1/admin/users/{user_id}` - Update user (admin only)
- [ ] `DELETE /api/v1/admin/users/{user_id}` - Deactivate user (admin only)
- [ ] `POST /api/v1/admin/users/{user_id}/role` - Change user role (admin only)

## 🏗️ IMPLEMENTATION DETAILS

### **1. Extended User Model**
```python
# app/models/user.py - Add these fields
class User(BaseModel):
    # ... existing fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    preferred_language: str = "en"
    timezone: str = "UTC"
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
```

### **2. Profile Update Schema**
```python
# app/schemas/user.py - New file
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[datetime] = None
    preferred_language: Optional[str] = Field("en", regex="^(en|vi)$")
    timezone: Optional[str] = "UTC"
```

### **3. Profile Service**
```python
# app/services/user_service.py - New file
class UserService:
    async def get_user_profile(self, user_id: str) -> User
    async def update_user_profile(self, user_id: str, profile_data: UserProfileUpdate) -> User
    async def upload_avatar(self, user_id: str, file: UploadFile) -> str
    async def get_all_users(self, skip: int, limit: int) -> List[User]  # Admin only
    async def update_user_role(self, user_id: str, new_role: UserRole) -> User  # Admin only
    async def deactivate_user(self, user_id: str) -> bool  # Admin only
```

## 🧪 TESTING PLAN

### **Unit Tests**
- [ ] Test profile update validation
- [ ] Test admin permissions
- [ ] Test file upload validation

### **Integration Tests**
- [ ] Test complete profile update flow
- [ ] Test admin user management flow
- [ ] Test authorization for admin endpoints

### **API Tests**
- [ ] Test all profile endpoints
- [ ] Test all admin endpoints
- [ ] Test error scenarios

## 📝 FILES TO CREATE/UPDATE

### **New Files**
- `app/schemas/user.py` - User profile schemas
- `app/services/user_service.py` - User management service
- `app/routers/v1/users.py` - User profile endpoints
- `app/routers/v1/admin.py` - Admin endpoints
- `tests/test_user_management.py` - User management tests

### **Updated Files**
- `app/models/user.py` - Extended user model
- `app/main.py` - Include new routers

## ⏱️ ESTIMATED TIMELINE
**Total**: 1 day (8 hours)
- Model updates: 1 hour
- Service implementation: 3 hours
- Endpoint implementation: 2 hours
- Testing: 2 hours

## ✅ COMPLETION CRITERIA
- [ ] All user profile endpoints working
- [ ] All admin user management endpoints working
- [ ] Proper authorization implemented
- [ ] All tests passing
- [ ] Documentation updated

---

## 🔄 NEXT STEP
After completing Step 1, proceed to **Step 2: Deck Management APIs**

*Focus on one step at a time for systematic implementation*
