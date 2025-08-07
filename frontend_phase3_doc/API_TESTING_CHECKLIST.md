# 🧪 API TESTING CHECKLIST
*Comprehensive testing guide for Flashcard LMS Backend API*

## 📋 OVERVIEW

This checklist ensures thorough testing of all API endpoints from frontend perspective.

**Backend API**: http://localhost:8000  
**Test Database**: Available with 3 test users  
**Documentation**: http://localhost:8000/docs

---

## 🔐 AUTHENTICATION TESTING

### **1. User Registration Testing**

#### **✅ Valid Registration Scenarios**
- [ ] **Complete Registration**
  ```json
  POST /api/v1/auth/register
  {
    "username": "newuser123",
    "email": "newuser@test.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }
  ```
  - [ ] Returns 201 Created
  - [ ] Returns user ID and info
  - [ ] User role set to "student"
  - [ ] Email and username are unique

- [ ] **Minimal Registration**
  ```json
  {
    "username": "minimal123",
    "email": "minimal@test.com", 
    "password": "SecurePass123!"
  }
  ```
  - [ ] Returns 201 Created
  - [ ] Optional fields can be null
  - [ ] Default role assigned

#### **❌ Invalid Registration Scenarios**
- [ ] **Missing Required Fields**
  ```json
  {
    "email": "test@test.com"
    // Missing username and password
  }
  ```
  - [ ] Returns 422 Unprocessable Entity
  - [ ] Clear validation error messages

- [ ] **Duplicate Email**
  ```json
  {
    "username": "different123",
    "email": "admin@flashcard.com",  // Existing email
    "password": "SecurePass123!"
  }
  ```
  - [ ] Returns 400 Bad Request
  - [ ] Error: "Email already registered"

- [ ] **Duplicate Username**
  ```json
  {
    "username": "admin",  // Existing username
    "email": "newemail@test.com",
    "password": "SecurePass123!"
  }
  ```
  - [ ] Returns 400 Bad Request
  - [ ] Error: "Username already registered"

- [ ] **Weak Password**
  ```json
  {
    "username": "testuser",
    "email": "test@test.com",
    "password": "123"  // Too weak
  }
  ```
  - [ ] Returns 400 Bad Request
  - [ ] Error: "Password does not meet strength requirements"

### **2. User Login Testing**

#### **✅ Valid Login Scenarios**

- [ ] **Admin Login**
  ```json
  POST /api/v1/auth/login
  {
    "email": "admin@flashcard.com",
    "password": "admin123"
  }
  ```
  - [ ] Returns 200 OK
  - [ ] Contains access_token and refresh_token
  - [ ] User role is "admin"
  - [ ] Token expires_in is 1800 seconds

- [ ] **Teacher Login**
  ```json
  {
    "email": "teacher@flashcard.com", 
    "password": "teacher123"
  }
  ```
  - [ ] Returns 200 OK
  - [ ] User role is "teacher"
  - [ ] All token fields present

- [ ] **Student Login**
  ```json
  {
    "email": "test@example.com",
    "password": "test123"
  }
  ```
  - [ ] Returns 200 OK
  - [ ] User role is "student"
  - [ ] All token fields present

#### **❌ Invalid Login Scenarios**

- [ ] **Wrong Password**
  ```json
  {
    "email": "admin@flashcard.com",
    "password": "wrongpassword"
  }
  ```
  - [ ] Returns 401 Unauthorized
  - [ ] Error: "Incorrect email or password"

- [ ] **Non-existent Email**
  ```json
  {
    "email": "nonexistent@test.com",
    "password": "anypassword"
  }
  ```
  - [ ] Returns 401 Unauthorized
  - [ ] Error: "Incorrect email or password"

- [ ] **Missing Fields**
  ```json
  {
    "email": "admin@flashcard.com"
    // Missing password
  }
  ```
  - [ ] Returns 422 Unprocessable Entity
  - [ ] Validation error for missing field

### **3. Token Management Testing**

#### **✅ Valid Token Operations**

- [ ] **Get Current User**
  ```http
  GET /api/v1/auth/me
  Authorization: Bearer <valid_access_token>
  ```
  - [ ] Returns 200 OK
  - [ ] Returns complete user info
  - [ ] No sensitive data (password_hash)

- [ ] **Token Verification**
  ```http
  GET /api/v1/auth/verify
  Authorization: Bearer <valid_access_token>
  ```
  - [ ] Returns 200 OK
  - [ ] Returns { "valid": true, "user_id": "...", "role": "..." }

- [ ] **Token Refresh**
  ```json
  POST /api/v1/auth/refresh
  {
    "refresh_token": "<valid_refresh_token>"
  }
  ```
  - [ ] Returns 200 OK
  - [ ] Returns new access_token and refresh_token
  - [ ] New token has updated expiration

- [ ] **Logout**
  ```http
  POST /api/v1/auth/logout
  Authorization: Bearer <valid_access_token>
  ```
  - [ ] Returns 200 OK
  - [ ] Returns logout confirmation message

#### **❌ Invalid Token Operations**

- [ ] **Missing Authorization Header**
  ```http
  GET /api/v1/auth/me
  // No Authorization header
  ```
  - [ ] Returns 401 Unauthorized
  - [ ] Error about missing credentials

- [ ] **Invalid Token Format**
  ```http
  GET /api/v1/auth/me
  Authorization: Bearer invalid_token_format
  ```
  - [ ] Returns 401 Unauthorized
  - [ ] Error about invalid credentials

- [ ] **Expired Token**
  ```http
  GET /api/v1/auth/me
  Authorization: Bearer <expired_access_token>
  ```
  - [ ] Returns 401 Unauthorized
  - [ ] Should trigger token refresh flow

- [ ] **Invalid Refresh Token**
  ```json
  POST /api/v1/auth/refresh
  {
    "refresh_token": "invalid_or_expired_refresh_token"
  }
  ```
  - [ ] Returns 422 Unprocessable Entity
  - [ ] Should force user to login again

---

## 🏥 HEALTH CHECK TESTING

### **System Health Endpoints**

- [ ] **Basic Health Check**
  ```http
  GET /health
  ```
  - [ ] Returns 200 OK
  - [ ] Contains status, timestamp, service, version
  - [ ] Response time < 100ms

- [ ] **API Health Check**
  ```http
  GET /api/v1/health
  ```
  - [ ] Returns 200 OK
  - [ ] Contains status and timestamp
  - [ ] Indicates API is ready

- [ ] **Readiness Probe**
  ```http
  GET /api/v1/health/ready
  ```
  - [ ] Returns 200 OK when ready
  - [ ] May return 503 if database unavailable
  - [ ] Used for load balancer health checks

- [ ] **Liveness Probe** 
  ```http
  GET /api/v1/health/live
  ```
  - [ ] Returns 200 OK when alive
  - [ ] Should always return 200 unless critical failure
  - [ ] Used for container orchestration

---

## 🔒 ROLE-BASED ACCESS TESTING

### **Admin Role Testing**
Using: admin@flashcard.com / admin123

- [ ] **Admin Login**
  - [ ] Can login successfully
  - [ ] Receives admin role in token
  - [ ] Can access all endpoints

- [ ] **Admin Permissions**
  - [ ] Can view all user information
  - [ ] Can reset any user's password (future endpoint)
  - [ ] Can manage system settings (future endpoint)

### **Teacher Role Testing**
Using: teacher@flashcard.com / teacher123

- [ ] **Teacher Login**
  - [ ] Can login successfully
  - [ ] Receives teacher role in token
  - [ ] Has extended permissions

- [ ] **Teacher Permissions**
  - [ ] Can manage assigned classes (future endpoint)
  - [ ] Can reset student passwords (future endpoint)
  - [ ] Cannot access admin functions

### **Student Role Testing**
Using: test@example.com / test123

- [ ] **Student Login**
  - [ ] Can login successfully
  - [ ] Receives student role in token
  - [ ] Has basic permissions

- [ ] **Student Permissions**
  - [ ] Can access learning features (future endpoint)
  - [ ] Can update own profile (future endpoint)
  - [ ] Cannot access admin or teacher functions

---

## 🌐 NETWORK & ERROR TESTING

### **HTTP Status Code Testing**

- [ ] **Success Codes**
  - [ ] 200 OK - Successful GET requests
  - [ ] 201 Created - Successful POST requests
  - [ ] 204 No Content - Successful DELETE requests

- [ ] **Client Error Codes**
  - [ ] 400 Bad Request - Invalid request data
  - [ ] 401 Unauthorized - Missing/invalid authentication
  - [ ] 403 Forbidden - Insufficient permissions
  - [ ] 404 Not Found - Resource not found
  - [ ] 422 Unprocessable Entity - Validation errors

- [ ] **Server Error Codes**
  - [ ] 500 Internal Server Error - Server failures
  - [ ] 503 Service Unavailable - Temporary unavailability

### **Content Type Testing**

- [ ] **Request Headers**
  - [ ] Content-Type: application/json for POST requests
  - [ ] Authorization: Bearer <token> for protected endpoints
  - [ ] Accept: application/json for responses

- [ ] **Response Headers**
  - [ ] Content-Type: application/json returned
  - [ ] CORS headers present
  - [ ] Security headers included

### **Rate Limiting Testing**

- [ ] **Normal Usage**
  - [ ] Normal API calls succeed
  - [ ] No rate limiting for reasonable usage

- [ ] **High Volume Testing**
  - [ ] Excessive requests handled gracefully
  - [ ] Rate limiting responses (if implemented)
  - [ ] Proper error messages for rate limits

---

## 🧪 INTEGRATION TESTING SCENARIOS

### **Complete Authentication Flow**

- [ ] **Full User Journey**
  1. [ ] Register new user account
  2. [ ] Verify registration success
  3. [ ] Login with new credentials
  4. [ ] Receive and store tokens
  5. [ ] Access protected endpoint (/auth/me)
  6. [ ] Refresh token before expiry
  7. [ ] Continue using refreshed token
  8. [ ] Logout and clear tokens
  9. [ ] Verify logout by accessing protected endpoint (should fail)

### **Token Lifecycle Testing**

- [ ] **Token Expiration Flow**
  1. [ ] Login and get tokens
  2. [ ] Wait for access token to expire (30 minutes)
  3. [ ] Attempt to access protected endpoint
  4. [ ] Automatically refresh token
  5. [ ] Retry original request with new token
  6. [ ] Verify seamless user experience

### **Error Recovery Testing**

- [ ] **Network Interruption**
  1. [ ] Start authentication request
  2. [ ] Simulate network failure
  3. [ ] Verify appropriate error handling
  4. [ ] Retry when network restored
  5. [ ] Verify successful completion

- [ ] **Server Restart**
  1. [ ] Login and obtain tokens
  2. [ ] Restart backend server
  3. [ ] Attempt API calls
  4. [ ] Verify graceful degradation
  5. [ ] Verify recovery when server returns

---

## 📊 PERFORMANCE TESTING

### **Response Time Testing**

- [ ] **Authentication Endpoints**
  - [ ] Registration: < 2 seconds
  - [ ] Login: < 1 second
  - [ ] Token refresh: < 500ms
  - [ ] Get current user: < 200ms

- [ ] **Health Endpoints**
  - [ ] Basic health: < 100ms
  - [ ] Readiness check: < 300ms
  - [ ] Liveness check: < 100ms

### **Concurrent User Testing**

- [ ] **Multiple Simultaneous Logins**
  - [ ] 10 concurrent login requests
  - [ ] All requests succeed
  - [ ] No token conflicts
  - [ ] Reasonable response times maintained

### **Load Testing**

- [ ] **Sustained Load**
  - [ ] 100 requests over 1 minute
  - [ ] Response times remain stable
  - [ ] No memory leaks observed
  - [ ] No connection errors

---

## 🔧 AUTOMATION TESTING

### **Test Data Setup**

- [ ] **Test Users Available**
  - [ ] Admin: admin@flashcard.com / admin123
  - [ ] Teacher: teacher@flashcard.com / teacher123
  - [ ] Student: test@example.com / test123

- [ ] **Test Data Cleanup**
  - [ ] Temporary test users cleaned up
  - [ ] Test data isolated from production
  - [ ] Database state consistent

### **Automated Test Suite**

- [ ] **Unit Tests**
  - [ ] All authentication functions tested
  - [ ] Edge cases covered
  - [ ] Mocked dependencies

- [ ] **Integration Tests**
  - [ ] End-to-end authentication flows
  - [ ] Real database interactions
  - [ ] Cross-role permission testing

- [ ] **Regression Tests**
  - [ ] All existing functionality verified
  - [ ] New changes don't break existing features
  - [ ] Performance benchmarks maintained

---

## ✅ COMPLETION CRITERIA

### **Ready for Frontend Integration When:**

- [ ] All authentication endpoints tested and working
- [ ] All three user roles tested successfully
- [ ] Token lifecycle completely functional
- [ ] Error handling comprehensive and user-friendly
- [ ] Performance meets requirements
- [ ] Security measures validated
- [ ] Documentation complete and accurate
- [ ] Test accounts available and verified
- [ ] CORS properly configured
- [ ] Health checks responding correctly

### **Sign-off Requirements:**

- [ ] **Backend Developer**: All endpoints implemented and tested
- [ ] **Frontend Developer**: API integration requirements clear
- [ ] **QA Engineer**: Test scenarios executed and passed
- [ ] **DevOps Engineer**: Deployment and monitoring ready

---

## 📞 SUPPORT

### **Getting Help**
- **API Documentation**: http://localhost:8000/docs
- **Health Status**: http://localhost:8000/health
- **Repository**: https://github.com/huynq247/lms_phase3
- **Contact**: huynq247@gmail.com

### **Common Issues & Solutions**

**Issue**: 401 Unauthorized errors  
**Solution**: Check token format and expiration

**Issue**: CORS errors in browser  
**Solution**: Verify frontend URL in CORS settings

**Issue**: 422 Validation errors  
**Solution**: Check request body format and required fields

**Issue**: Connection refused  
**Solution**: Ensure backend server is running on port 8000

---

*Complete API testing checklist for production-ready frontend integration* ✅
