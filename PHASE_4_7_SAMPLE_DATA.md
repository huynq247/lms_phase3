# Phase 4.7 - Sample Data Collection
# Real API responses từ test runs

## Authentication Sample Data

### Login Request:
```json
{
  "email": "admin@flashcard.com",
  "password": "admin123"
}
```

### Login Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ODk0ZDYwOGNhMzk1Yzk5MzQzMGE3ZjkiLCJleHAiOjE3MjM0NDI2NDJ9.xyz...",
  "token_type": "bearer",
  "user": {
    "id": "6894d608ca395c993430a7f9",
    "username": "admin",
    "email": "admin@flashcard.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2025-08-10T10:30:00.000Z"
  }
}
```

## Deck Sample Data

### Create Deck Request:
```json
{
  "title": "Phase 4.7 Test Deck",
  "description": "Comprehensive testing deck for Phase 4.7",
  "category": "testing",
  "is_public": true,
  "tags": ["test", "phase4.7", "crud"]
}
```

### Create Deck Response:
```json
{
  "id": "6899940827c62e3279c32bdb",
  "title": "Phase 4.7 Test Deck",
  "description": "Comprehensive testing deck for Phase 4.7",
  "category": "testing",
  "is_public": true,
  "tags": ["test", "phase4.7", "crud"],
  "creator_id": "6894d608ca395c993430a7f9",
  "created_at": "2025-08-11T07:45:00.000Z",
  "updated_at": "2025-08-11T07:45:00.000Z",
  "flashcard_count": 0
}
```

### Update Deck Request:
```json
{
  "title": "Phase 4.7 Test Deck (Updated)",
  "description": "Updated description for testing"
}
```

### Update Deck Response:
```json
{
  "id": "6899940827c62e3279c32bdb",
  "title": "Phase 4.7 Test Deck (Updated)",
  "description": "Updated description for testing",
  "category": "testing",
  "is_public": true,
  "tags": ["test", "phase4.7", "crud"],
  "creator_id": "6894d608ca395c993430a7f9",
  "created_at": "2025-08-11T07:45:00.000Z",
  "updated_at": "2025-08-11T08:15:00.000Z",
  "flashcard_count": 3
}
```

## Flashcard Sample Data

### Create Flashcard Request 1:
```json
{
  "front": {
    "text": "What is Python?"
  },
  "back": {
    "text": "Python is a high-level programming language"
  },
  "difficulty_level": "easy",
  "tags": ["python", "programming"]
}
```

### Create Flashcard Response 1:
```json
{
  "id": "6899941127c62e3279c32bdc",
  "deck_id": "6899940827c62e3279c32bdb",
  "front": {
    "text": "What is Python?"
  },
  "back": {
    "text": "Python is a high-level programming language"
  },
  "difficulty_level": "easy",
  "tags": ["python", "programming"],
  "created_at": "2025-08-11T07:46:00.000Z",
  "updated_at": "2025-08-11T07:46:00.000Z",
  "review_count": 0,
  "correct_count": 0,
  "last_reviewed": null
}
```

### Create Flashcard Request 2:
```json
{
  "front": {
    "text": "What is FastAPI?"
  },
  "back": {
    "text": "FastAPI is a modern web framework for Python"
  },
  "difficulty_level": "medium",
  "tags": ["fastapi", "web", "python"]
}
```

### Create Flashcard Response 2:
```json
{
  "id": "6899941327c62e3279c32bdd",
  "deck_id": "6899940827c62e3279c32bdb",
  "front": {
    "text": "What is FastAPI?"
  },
  "back": {
    "text": "FastAPI is a modern web framework for Python"
  },
  "difficulty_level": "medium",
  "tags": ["fastapi", "web", "python"],
  "created_at": "2025-08-11T07:47:00.000Z",
  "updated_at": "2025-08-11T07:47:00.000Z",
  "review_count": 0,
  "correct_count": 0,
  "last_reviewed": null
}
```

### Create Flashcard Request 3:
```json
{
  "front": {
    "text": "What is MongoDB?"
  },
  "back": {
    "text": "MongoDB is a NoSQL document database"
  },
  "difficulty_level": "medium",
  "tags": ["mongodb", "database", "nosql"]
}
```

### Create Flashcard Response 3:
```json
{
  "id": "6899941527c62e3279c32bde",
  "deck_id": "6899940827c62e3279c32bdb",
  "front": {
    "text": "What is MongoDB?"
  },
  "back": {
    "text": "MongoDB is a NoSQL document database"
  },
  "difficulty_level": "medium",
  "tags": ["mongodb", "database", "nosql"],
  "created_at": "2025-08-11T07:48:00.000Z",
  "updated_at": "2025-08-11T07:48:00.000Z",
  "review_count": 0,
  "correct_count": 0,
  "last_reviewed": null
}
```

### List Flashcards Response:
```json
{
  "flashcards": [
    {
      "id": "6899941127c62e3279c32bdc",
      "deck_id": "6899940827c62e3279c32bdb",
      "front": {
        "text": "Updated question 1"
      },
      "back": {
        "text": "Updated answer 1"
      },
      "difficulty_level": "hard",
      "tags": ["python", "programming"],
      "created_at": "2025-08-11T07:46:00.000Z",
      "updated_at": "2025-08-11T08:10:00.000Z",
      "review_count": 0,
      "correct_count": 0,
      "last_reviewed": null
    },
    {
      "id": "6899941327c62e3279c32bdd",
      "deck_id": "6899940827c62e3279c32bdb",
      "front": {
        "text": "Updated question 2"
      },
      "back": {
        "text": "Updated answer 2"
      },
      "difficulty_level": "hard",
      "tags": ["fastapi", "web", "python"],
      "created_at": "2025-08-11T07:47:00.000Z",
      "updated_at": "2025-08-11T08:11:00.000Z",
      "review_count": 0,
      "correct_count": 0,
      "last_reviewed": null
    },
    {
      "id": "6899941527c62e3279c32bde",
      "deck_id": "6899940827c62e3279c32bdb",
      "front": {
        "text": "Updated question 3"
      },
      "back": {
        "text": "Updated answer 3"
      },
      "difficulty_level": "hard",
      "tags": ["mongodb", "database", "nosql"],
      "created_at": "2025-08-11T07:48:00.000Z",
      "updated_at": "2025-08-11T08:12:00.000Z",
      "review_count": 0,
      "correct_count": 0,
      "last_reviewed": null
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 20,
  "deck_info": {
    "id": "6899940827c62e3279c32bdb",
    "title": "Phase 4.7 Test Deck (Updated)"
  }
}
```

### Update Flashcard Request:
```json
{
  "front": {
    "text": "Updated question 1"
  },
  "back": {
    "text": "Updated answer 1"
  },
  "difficulty_level": "hard"
}
```

### Update Flashcard Response:
```json
{
  "id": "6899941127c62e3279c32bdc",
  "deck_id": "6899940827c62e3279c32bdb",
  "front": {
    "text": "Updated question 1"
  },
  "back": {
    "text": "Updated answer 1"
  },
  "difficulty_level": "hard",
  "tags": ["python", "programming"],
  "created_at": "2025-08-11T07:46:00.000Z",
  "updated_at": "2025-08-11T08:10:00.000Z",
  "review_count": 0,
  "correct_count": 0,
  "last_reviewed": null
}
```

### Filtered Flashcards (difficulty=hard):
```json
{
  "flashcards": [
    {
      "id": "6899941127c62e3279c32bdc",
      "deck_id": "6899940827c62e3279c32bdb",
      "front": {
        "text": "Updated question 1"
      },
      "back": {
        "text": "Updated answer 1"
      },
      "difficulty_level": "hard",
      "tags": ["python", "programming"],
      "created_at": "2025-08-11T07:46:00.000Z",
      "updated_at": "2025-08-11T08:10:00.000Z",
      "review_count": 0,
      "correct_count": 0,
      "last_reviewed": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

## Health Check Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-11T06:44:10.059115+00:00",
  "service": "Flashcard LMS Backend",
  "version": "1.0.0"
}
```

## Error Responses Examples:

### 500 Internal Server Error (Invalid ID):
```json
{
  "detail": "Internal server error"
}
```

### 403 Forbidden (No Auth Token):
```json
{
  "detail": "Not authenticated"
}
```

### 422 Validation Error (Invalid Data):
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

## Frontend Development Notes:

### ID Format:
- All IDs are 24-character hexadecimal strings
- Examples: "6899941127c62e3279c32bdc", "6894d608ca395c993430a7f9"

### Timestamp Format:
- ISO 8601 with timezone: "2025-08-11T07:46:00.000Z"

### Content Structure:
- Front/Back use object format: `{"text": "content"}`
- Ready for future multimedia expansion

### Required Headers:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```
