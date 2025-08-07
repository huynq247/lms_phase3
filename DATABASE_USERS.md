# 🗄️ DATABASE USERS REGISTRY
*Ghi chép tất cả users đã tạo trong database để tránh trùng lặp*

## 📊 Database Information
- **Host**: 113.161.118.17:27017
- **Database**: flashcard_lms_dev
- **Connection**: mongodb://admin:Root%40123@113.161.118.17:27017

## 👥 ACTIVE USERS IN DATABASE

### 🔑 ADMIN USERS
| Username | Email | Password | Role | Full Name | Created | Status |
|----------|-------|----------|------|-----------|---------|---------|
| admin | admin@flashcard.com | admin123 | admin | System Administrator | 2025-08-07 | ✅ Active |

### 👨‍🏫 TEACHER USERS
| Username | Email | Password | Role | Full Name | Created | Status |
|----------|-------|----------|------|-----------|---------|---------|
| teacher_user | teacher@flashcard.com | teacher123 | teacher | Teacher User | 2025-08-07 | ✅ Active |

### 👤 STUDENT USERS  
| Username | Email | Password | Role | Full Name | Created | Status |
|----------|-------|----------|------|-----------|---------|---------|
| testuser | test@example.com | test123 | student | Test User | 2025-08-07 | ✅ Active |

### 🧪 TEMPORARY TEST USERS
*Users created during testing (auto-cleaned):*
- test_simple_auth_* (various)
- test_auth_* (various)

## 📋 RESERVED USERNAMES/EMAILS
*To avoid conflicts in future tests:*

### Emails Reserved:
- admin@flashcard.com ✅ USED
- test@example.com ✅ USED
- test.auth@example.com (for auth testing)
- simple.auth@example.com (for simple testing)

### Usernames Reserved:
- admin_user ✅ USED
- test_user ✅ USED
- test_simple_auth (for testing)
- test_auth_endpoints (for testing)

## 🔄 NEXT AVAILABLE FOR TESTING
*Safe to use for new tests:*
- teacher2@example.com / teacher2_user
- student1@example.com / student1_user
- student2@example.com / student2_user
- demo@example.com / demo_user

## 🧹 CLEANUP NOTES
- Temporary test users are auto-cleaned after tests
- Production users (admin, teacher, test) are persistent
- Always check this list before creating new users

---
*Last Updated: August 8, 2025*

## 🎯 ALL ROLES TESTED ✅
**Login Status**: All 3 roles working perfectly
- 👑 Admin: admin@flashcard.com / admin123 ✅
- 👨‍🏫 Teacher: teacher@flashcard.com / teacher123 ✅
- 👤 Student: test@example.com / test123 ✅

## 🧪 LATEST TEST RESULTS
**Date**: August 8, 2025  
**Test Status**: ✅ ALL AUTHENTICATION WORKING  
**Authentication**: ✅ All endpoints working  
**Database Users**: ✅ All 3 roles verified  
**Token System**: ✅ JWT working properly  
**Test Coverage**: ✅ 100% authentication flow tested
**Rate Limiting**: ✅ 5 requests/minute working properly
**Step 4.1 Status**: ✅ COMPLETED - Authentication APIs fully functional

### 📝 Test Details:
- **Admin User**: ✅ Login, Get Profile, Logout - ALL WORKING
- **Teacher User**: ✅ Login, Get Profile, Logout - ALL WORKING  
- **Student User**: ✅ Login, Get Profile, Logout - ALL WORKING
- **Rate Limiting**: ✅ 5/minute limit enforced
- **Email Verification**: ✅ Endpoint available
- **Token Refresh**: ✅ Working properly
