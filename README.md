# 🎓 Flashcard LMS Backend - Phase 3: Authentication & Authorization

A comprehensive learning management system focused on flashcard-based learning with spaced repetition algorithm (SM-2).

**Current Phase**: ✅ **Phase 3 Complete** - Authentication & Authorization System

## 🎯 Phase 3 Achievements

### ✅ Completed Features
- **JWT Authentication System**: Complete login/logout flow
- **Multi-Role Support**: Admin, Teacher, Student roles
- **Secure Password Management**: bcrypt hashing + strength validation  
- **Token Management**: Access tokens with refresh capability
- **Role-Based Access Control**: Permission-based endpoint protection
- **Comprehensive Testing**: 25 tests, 100% pass rate
- **Real Database Integration**: MongoDB with production-ready setup

### 🧪 Test Results
- **All Tests Passing**: 25/25 ✅
- **Authentication Flow**: Complete coverage
- **All Roles Tested**: Admin, Teacher, Student verified
- **Database Integration**: Real MongoDB testing successful

## � Quick Start

### Prerequisites
- Python 3.11+
- MongoDB 4.4+

### Installation
```bash
git clone https://github.com/huynq247/lms_phase3.git
cd lms_phase3
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API Available at: http://localhost:8000

## 🔑 Test Users Available

| Role | Email | Password | Status |
|------|-------|----------|---------|
| Admin | admin@flashcard.com | admin123 | ✅ Active |
| Teacher | teacher@flashcard.com | teacher123 | ✅ Active |
| Student | test@example.com | test123 | ✅ Active |

## 📚 API Documentation
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Documentation**: Auto-generated OpenAPI/Swagger

## 🏗️ Project Structure

```
flashcard_lms_backend/
├── app/
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   ├── routers/         # API endpoints
│   └── utils/           # Utilities and helpers
├── uploads/             # File storage
├── tests/               # Test suite
└── requirements.txt     # Dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB (local or Atlas)
- Virtual environment tool

### Installation

1. **Clone the repository**
   ```bash
   cd flashcard_lms_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment**
   ```bash
   # Copy .env and update with your settings
   cp .env.example .env
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📚 API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Versioning
All API endpoints are versioned under `/api/v1/`

### Main Endpoints
- `/api/v1/auth/` - Authentication
- `/api/v1/users/` - User management
- `/api/v1/classes/` - Class management
- `/api/v1/courses/` - Course management
- `/api/v1/lessons/` - Lesson management
- `/api/v1/decks/` - Deck management
- `/api/v1/flashcards/` - Flashcard management
- `/api/v1/study/` - Study sessions and progress

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `flashcard_lms_db` |
| `SECRET_KEY` | JWT secret key | Required |
| `DEBUG` | Debug mode | `false` |

### File Upload Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_FILE_SIZE` | Maximum file size in bytes | `10485760` (10MB) |
| `ALLOWED_IMAGE_TYPES` | Allowed image formats | `jpg,jpeg,png,gif` |
| `ALLOWED_AUDIO_TYPES` | Allowed audio formats | `mp3,wav,m4a` |

## 🧪 Testing

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

## 🔐 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Input validation with Pydantic
- File upload security
- Environment variable configuration

## 📈 Performance

- Async/await throughout
- MongoDB indexing for fast queries
- Efficient file serving
- Pagination for large datasets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For support and questions, please open an issue in the repository.

---

**Built with ❤️ for effective learning through spaced repetition**
