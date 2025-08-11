# Phase 4.7 - Flashcard CRUD API Documentation

**Last Updated**: August 11, 2025  
**Phase**: 4.7 - Flashcard CRUD with ID Standardization  
**Base URL**: `http://localhost:8000/api/v1`

---

## 🔐 Authentication

### POST /auth/login
**Purpose**: User authentication and token generation

**Request Body**:
```json
{
  "email": "admin@flashcard.com",
  "password": "admin123"
}
```

**Response (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "6894d608ca395c993430a7f9",
    "username": "admin",
    "email": "admin@flashcard.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2025-08-11T06:00:00.000Z"
  }
}
```

**Headers Required for Protected Routes**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📚 Deck Management

### POST /decks
**Purpose**: Create a new deck

**Request Body**:
```json
{
  "title": "Python Programming Basics",
  "description": "Learn fundamental Python concepts",
  "category": "programming",
  "is_public": true,
  "tags": ["python", "programming", "basics"]
}
```

**Response (201)**:
```json
{
  "id": "689993bc77a5be2b2f592e0d",
  "title": "Python Programming Basics",
  "description": "Learn fundamental Python concepts",
  "category": "programming",
  "is_public": true,
  "tags": ["python", "programming", "basics"],
  "creator_id": "6894d608ca395c993430a7f9",
  "created_at": "2025-08-11T07:30:00.000Z",
  "updated_at": "2025-08-11T07:30:00.000Z",
  "flashcard_count": 0
}
```

### GET /decks/{deck_id}
**Purpose**: Get deck details

**Response (200)**:
```json
{
  "id": "689993bc77a5be2b2f592e0d",
  "title": "Python Programming Basics",
  "description": "Learn fundamental Python concepts",
  "category": "programming",
  "is_public": true,
  "tags": ["python", "programming", "basics"],
  "creator_id": "6894d608ca395c993430a7f9",
  "created_at": "2025-08-11T07:30:00.000Z",
  "updated_at": "2025-08-11T07:30:00.000Z",
  "flashcard_count": 3
}
```

### GET /decks
**Purpose**: List user's decks

**Response (200)**:
```json
{
  "decks": [
    {
      "id": "689993bc77a5be2b2f592e0d",
      "title": "Python Programming Basics",
      "description": "Learn fundamental Python concepts",
      "category": "programming",
      "is_public": true,
      "tags": ["python", "programming", "basics"],
      "creator_id": "6894d608ca395c993430a7f9",
      "created_at": "2025-08-11T07:30:00.000Z",
      "updated_at": "2025-08-11T07:30:00.000Z",
      "flashcard_count": 3
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### PUT /decks/{deck_id}
**Purpose**: Update deck information

**Request Body**:
```json
{
  "title": "Advanced Python Programming",
  "description": "Master advanced Python concepts and patterns",
  "category": "programming",
  "is_public": false
}
```

**Response (200)**:
```json
{
  "id": "689993bc77a5be2b2f592e0d",
  "title": "Advanced Python Programming",
  "description": "Master advanced Python concepts and patterns",
  "category": "programming",
  "is_public": false,
  "tags": ["python", "programming", "basics"],
  "creator_id": "6894d608ca395c993430a7f9",
  "created_at": "2025-08-11T07:30:00.000Z",
  "updated_at": "2025-08-11T08:15:00.000Z",
  "flashcard_count": 3
}
```

### DELETE /decks/{deck_id}
**Purpose**: Delete a deck

**Response (200)**:
```json
{
  "message": "Deck deleted successfully",
  "id": "689993bc77a5be2b2f592e0d"
}
```

---

## 🆕 Flashcard Management

### POST /flashcards/deck/{deck_id}
**Purpose**: Create a new flashcard in a deck

**Request Body**:
```json
{
  "front": {
    "text": "What is a Python list comprehension?"
  },
  "back": {
    "text": "A concise way to create lists using a single line of code. Syntax: [expression for item in iterable if condition]"
  },
  "difficulty_level": "medium",
  "tags": ["python", "lists", "comprehension"]
}
```

**Response (201)**:
```json
{
  "id": "689993c477a5be2b2f592e0e",
  "deck_id": "689993bc77a5be2b2f592e0d",
  "front": {
    "text": "What is a Python list comprehension?"
  },
  "back": {
    "text": "A concise way to create lists using a single line of code. Syntax: [expression for item in iterable if condition]"
  },
  "difficulty_level": "medium",
  "tags": ["python", "lists", "comprehension"],
  "created_at": "2025-08-11T07:45:00.000Z",
  "updated_at": "2025-08-11T07:45:00.000Z",
  "review_count": 0,
  "correct_count": 0,
  "last_reviewed": null
}
```

### GET /flashcards/deck/{deck_id}
**Purpose**: Get all flashcards in a deck

**Query Parameters**:
- `difficulty` (optional): Filter by difficulty level
- `tags` (optional): Filter by tags
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response (200)**:
```json
{
  "flashcards": [
    {
      "id": "689993c477a5be2b2f592e0e",
      "deck_id": "689993bc77a5be2b2f592e0d",
      "front": {
        "text": "What is a Python list comprehension?"
      },
      "back": {
        "text": "A concise way to create lists using a single line of code. Syntax: [expression for item in iterable if condition]"
      },
      "difficulty_level": "medium",
      "tags": ["python", "lists", "comprehension"],
      "created_at": "2025-08-11T07:45:00.000Z",
      "updated_at": "2025-08-11T07:45:00.000Z",
      "review_count": 0,
      "correct_count": 0,
      "last_reviewed": null
    },
    {
      "id": "689993c677a5be2b2f592e0f",
      "deck_id": "689993bc77a5be2b2f592e0d",
      "front": {
        "text": "What is the difference between == and is in Python?"
      },
      "back": {
        "text": "== compares values, while 'is' compares object identity (memory location). Use == for value comparison, 'is' for identity comparison."
      },
      "difficulty_level": "hard",
      "tags": ["python", "operators", "comparison"],
      "created_at": "2025-08-11T07:46:00.000Z",
      "updated_at": "2025-08-11T07:46:00.000Z",
      "review_count": 2,
      "correct_count": 1,
      "last_reviewed": "2025-08-11T08:00:00.000Z"
    }
  ],
  "total": 2,
  "page": 1,
  "per_page": 20,
  "deck_info": {
    "id": "689993bc77a5be2b2f592e0d",
    "title": "Python Programming Basics"
  }
}
```

### GET /flashcards/{flashcard_id}
**Purpose**: Get a specific flashcard

**Response (200)**:
```json
{
  "id": "689993c477a5be2b2f592e0e",
  "deck_id": "689993bc77a5be2b2f592e0d",
  "front": {
    "text": "What is a Python list comprehension?"
  },
  "back": {
    "text": "A concise way to create lists using a single line of code. Syntax: [expression for item in iterable if condition]"
  },
  "difficulty_level": "medium",
  "tags": ["python", "lists", "comprehension"],
  "created_at": "2025-08-11T07:45:00.000Z",
  "updated_at": "2025-08-11T07:45:00.000Z",
  "review_count": 0,
  "correct_count": 0,
  "last_reviewed": null
}
```

### PUT /flashcards/{flashcard_id}
**Purpose**: Update a flashcard

**Request Body**:
```json
{
  "front": {
    "text": "What is a Python list comprehension and when should you use it?"
  },
  "back": {
    "text": "A concise way to create lists using a single line of code. Syntax: [expression for item in iterable if condition]. Use when you need to transform or filter data into a new list."
  },
  "difficulty_level": "easy",
  "tags": ["python", "lists", "comprehension", "best-practices"]
}
```

**Response (200)**:
```json
{
  "id": "689993c477a5be2b2f592e0e",
  "deck_id": "689993bc77a5be2b2f592e0d",
  "front": {
    "text": "What is a Python list comprehension and when should you use it?"
  },
  "back": {
    "text": "A concise way to create lists using a single line of code. Syntax: [expression for item in iterable if condition]. Use when you need to transform or filter data into a new list."
  },
  "difficulty_level": "easy",
  "tags": ["python", "lists", "comprehension", "best-practices"],
  "created_at": "2025-08-11T07:45:00.000Z",
  "updated_at": "2025-08-11T08:30:00.000Z",
  "review_count": 0,
  "correct_count": 0,
  "last_reviewed": null
}
```

### DELETE /flashcards/{flashcard_id}
**Purpose**: Delete a flashcard

**Response (200)**:
```json
{
  "message": "Flashcard deleted successfully",
  "id": "689993c477a5be2b2f592e0e"
}
```

---

## 🏥 Health Check

### GET /health
**Purpose**: Check API health status

**Response (200)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-11T06:44:10.059115+00:00",
  "service": "Flashcard LMS Backend",
  "version": "1.0.0"
}
```

---

## 🚨 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "front", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## 🎯 Frontend Integration Notes

### Key Features for Frontend:
1. **ID Standardization**: All responses use `id` field (no `_id`)
2. **Consistent Response Format**: All endpoints follow same structure
3. **Comprehensive Error Handling**: Clear error messages with status codes
4. **Flexible Content**: Front/back support both text and future multimedia
5. **Filtering & Pagination**: Built-in support for large datasets

### Sample Frontend Workflow:
1. **Login** → Get token
2. **List Decks** → Show user's decks
3. **Select Deck** → Show flashcards in deck
4. **CRUD Operations** → Create/Edit/Delete flashcards
5. **Study Session** → Use flashcard data for learning

### Content Structure:
- **Front/Back**: Flexible object structure (currently text, future: images/audio)
- **Tags**: Array of strings for categorization
- **Difficulty**: "easy", "medium", "hard"
- **Timestamps**: ISO format for all dates

---

## 🔧 Development Notes

- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: Bearer token in Authorization header
- **Content-Type**: `application/json`
- **All IDs**: 24-character hexadecimal strings (MongoDB ObjectId format)
- **Timestamps**: ISO 8601 format with timezone
- **Status Codes**: RESTful conventions (200, 201, 400, 401, 403, 404, 422, 500)
