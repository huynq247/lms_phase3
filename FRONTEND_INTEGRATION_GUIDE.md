# 🌐 FRONTEND INTEGRATION GUIDE
*Complete guide for building frontend with Flashcard LMS Backend*

## 📋 OVERVIEW

This guide provides all necessary information for frontend developers to integrate with the Flashcard LMS Backend API.

**Backend Repository**: https://github.com/huynq247/lms_phase3  
**API Base URL**: `http://localhost:8000`  
**API Documentation**: `http://localhost:8000/docs`

---

## 🔌 API ENDPOINTS

### **Authentication Endpoints**

#### **1. User Registration**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "student123",
  "email": "student@example.com", 
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "student123",
  "email": "student@example.com",
  "role": "student",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2025-08-08T10:30:00Z",
  "message": "User registered successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Email already registered"
}
```

#### **2. User Login**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "student123",
    "email": "student@example.com",
    "role": "student",
    "is_active": true
  }
}
```

#### **3. Get Current User**
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "student123",
  "email": "student@example.com",
  "role": "student",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2025-08-08T10:30:00Z"
}
```

#### **4. Refresh Token**
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### **5. Logout**
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out",
  "logged_out_at": "2025-08-08T11:00:00Z"
}
```

#### **6. Token Verification**
```http
GET /api/v1/auth/verify
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "valid": true,
  "user_id": "507f1f77bcf86cd799439011",
  "username": "student123",
  "role": "student"
}
```

### **Health Check Endpoints**

#### **Basic Health Check**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-08T10:30:00Z",
  "service": "Flashcard LMS Backend",
  "version": "1.0.0"
}
```

#### **Detailed Health Check**
```http
GET /api/v1/health
```

#### **Readiness Probe**
```http
GET /api/v1/health/ready
```

#### **Liveness Probe**
```http
GET /api/v1/health/live
```

---

## 🔐 AUTHENTICATION FLOW

### **1. Complete Authentication Flow**

```javascript
// Frontend Authentication Implementation Example

class AuthService {
  constructor() {
    this.baseURL = 'http://localhost:8000';
    this.tokenKey = 'access_token';
    this.refreshKey = 'refresh_token';
    this.userKey = 'user_info';
  }

  // Register new user
  async register(userData) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  }

  // User login
  async login(email, password) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    const data = await response.json();
    
    // Store tokens and user info
    localStorage.setItem(this.tokenKey, data.access_token);
    localStorage.setItem(this.refreshKey, data.refresh_token);
    localStorage.setItem(this.userKey, JSON.stringify(data.user));
    
    return data;
  }

  // Get current user
  async getCurrentUser() {
    const token = localStorage.getItem(this.tokenKey);
    if (!token) throw new Error('No token found');
    
    const response = await fetch(`${this.baseURL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        await this.refreshToken();
        return this.getCurrentUser(); // Retry with new token
      }
      throw new Error('Failed to get user info');
    }
    
    return await response.json();
  }

  // Refresh access token
  async refreshToken() {
    const refreshToken = localStorage.getItem(this.refreshKey);
    if (!refreshToken) throw new Error('No refresh token');
    
    const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (!response.ok) {
      this.logout(); // Clear invalid tokens
      throw new Error('Token refresh failed');
    }
    
    const data = await response.json();
    localStorage.setItem(this.tokenKey, data.access_token);
    localStorage.setItem(this.refreshKey, data.refresh_token);
    
    return data;
  }

  // Logout
  async logout() {
    const token = localStorage.getItem(this.tokenKey);
    
    if (token) {
      try {
        await fetch(`${this.baseURL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (error) {
        console.warn('Logout request failed:', error);
      }
    }
    
    // Clear local storage
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshKey);
    localStorage.removeItem(this.userKey);
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!localStorage.getItem(this.tokenKey);
  }

  // Get stored user info
  getUser() {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  // Get authorization header
  getAuthHeader() {
    const token = localStorage.getItem(this.tokenKey);
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
}
```

### **2. Axios Interceptor Setup**

```javascript
// Setup Axios interceptors for automatic token handling
import axios from 'axios';

const authService = new AuthService();

// Request interceptor to add auth header
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        await authService.refreshToken();
        const token = localStorage.getItem('access_token');
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        authService.logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

---

## 👥 USER ROLES & PERMISSIONS

### **Role Types**
- **student**: Default role, learning access
- **teacher**: Class and student management  
- **admin**: Full system access

### **Test Accounts Available**

| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| **Admin** | admin@flashcard.com | admin123 | System administration |
| **Teacher** | teacher@flashcard.com | teacher123 | Class management |
| **Student** | test@example.com | test123 | Learning activities |

### **Permission Matrix**

| Feature | Student | Teacher | Admin |
|---------|---------|---------|-------|
| Register/Login | ✅ | ✅ | ✅ |
| View Profile | ✅ | ✅ | ✅ |
| Update Profile | ✅ | ✅ | ✅ |
| Create Classes | ❌ | ✅ | ✅ |
| Manage Students | ❌ | ✅ | ✅ |
| System Settings | ❌ | ❌ | ✅ |
| Reset Passwords | ❌ | ✅ (students only) | ✅ (all users) |

---

## 🛠️ FRONTEND REQUIREMENTS

### **Environment Variables**
```bash
# .env file for frontend
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_APP_NAME=Flashcard LMS
REACT_APP_VERSION=1.0.0

# For production
REACT_APP_API_BASE_URL=https://your-api-domain.com
```

### **Required Dependencies**

```json
{
  "dependencies": {
    "axios": "^1.5.0",
    "react-router-dom": "^6.0.0",
    "react-hook-form": "^7.0.0",
    "@hookform/resolvers": "^3.0.0",
    "yup": "^1.0.0",
    "react-query": "^4.0.0",
    "js-cookie": "^3.0.0"
  }
}
```

### **CORS Configuration**
Backend đã được cấu hình CORS cho:
- `http://localhost:3000` (React dev server)
- `http://localhost:8080` (Vue dev server)

---

## 🧪 TESTING CHECKLIST

### **Authentication Testing**

#### **Registration Flow**
- [ ] **Valid Registration**
  - [ ] All required fields filled
  - [ ] Strong password validation
  - [ ] Success message displayed
  - [ ] Redirect to login or dashboard

- [ ] **Invalid Registration** 
  - [ ] Missing required fields
  - [ ] Weak password handling
  - [ ] Duplicate email/username
  - [ ] Proper error messages

#### **Login Flow**
- [ ] **Valid Login**
  - [ ] Correct credentials accepted
  - [ ] Token stored securely
  - [ ] User info cached
  - [ ] Redirect to dashboard

- [ ] **Invalid Login**
  - [ ] Wrong password rejected
  - [ ] Non-existent email handled
  - [ ] Clear error messages
  - [ ] No sensitive data leaked

#### **Token Management**
- [ ] **Token Refresh**
  - [ ] Automatic refresh on expiry
  - [ ] Seamless user experience
  - [ ] Failed refresh handling
  - [ ] Logout on refresh failure

- [ ] **Token Security**
  - [ ] Tokens stored securely
  - [ ] HttpOnly cookies (recommended)
  - [ ] Logout clears all tokens
  - [ ] No tokens in console/logs

### **User Role Testing**

#### **Student Role**
- [ ] **Basic Access**
  - [ ] Can login successfully
  - [ ] Access to learning features
  - [ ] Cannot access admin features
  - [ ] Profile management works

#### **Teacher Role** 
- [ ] **Extended Access**
  - [ ] All student features
  - [ ] Class management access
  - [ ] Student password reset
  - [ ] Cannot access admin features

#### **Admin Role**
- [ ] **Full Access**
  - [ ] All features accessible
  - [ ] User management functions
  - [ ] System configuration access
  - [ ] Password reset for all users

### **API Integration Testing**

#### **Network Scenarios**
- [ ] **Success Responses**
  - [ ] 200/201 responses handled
  - [ ] Data displayed correctly
  - [ ] Success messages shown
  - [ ] UI updated appropriately

- [ ] **Error Responses**
  - [ ] 400 Bad Request handling
  - [ ] 401 Unauthorized handling
  - [ ] 403 Forbidden handling
  - [ ] 500 Server Error handling

- [ ] **Network Issues**
  - [ ] Connection timeout handling
  - [ ] Offline state management
  - [ ] Retry mechanisms
  - [ ] Loading states

#### **Data Validation**
- [ ] **Form Validation**
  - [ ] Client-side validation
  - [ ] Server-side error handling
  - [ ] Field-specific errors
  - [ ] Form state management

- [ ] **Data Integrity**
  - [ ] Required fields enforced
  - [ ] Data format validation
  - [ ] Sanitization applied
  - [ ] Security checks passed

---

## 🚀 DEPLOYMENT CHECKLIST

### **Development Environment**
- [ ] Backend running on localhost:8000
- [ ] Frontend connected to dev API
- [ ] CORS configured properly
- [ ] Test accounts available

### **Production Environment**
- [ ] Environment variables configured
- [ ] HTTPS endpoints used
- [ ] Secure token storage
- [ ] Error tracking setup
- [ ] Performance monitoring

### **Security Checklist**
- [ ] No sensitive data in localStorage
- [ ] HttpOnly cookies for tokens (recommended)
- [ ] CSRF protection implemented
- [ ] XSS prevention measures
- [ ] Input sanitization active

---

## 📞 SUPPORT & RESOURCES

### **Backend Repository**
- **GitHub**: https://github.com/huynq247/lms_phase3
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### **Contact Information**
- **Developer**: Huy Nguyen
- **Email**: huynq247@gmail.com

### **Troubleshooting**
- Check backend server is running: `curl http://localhost:8000/health`
- Verify API documentation: `http://localhost:8000/docs`
- Test authentication: Use provided test accounts
- Monitor network requests in browser dev tools

---

*Ready for frontend integration! Backend Phase 3 complete.* ✅
