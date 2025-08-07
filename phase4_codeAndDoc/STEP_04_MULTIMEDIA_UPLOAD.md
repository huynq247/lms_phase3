# 📁 STEP 4: MULTIMEDIA UPLOAD SUPPORT
*File upload system for images and audio*

## 🎯 OBJECTIVES
- Implement secure file upload system
- Support image and audio files for flashcards
- Add file validation and processing
- Implement file storage and URL generation

## 📋 IMPLEMENTATION CHECKLIST

### **A. File Upload Infrastructure** ⏳
- [ ] Configure file storage (local/cloud)
- [ ] Set up file validation
- [ ] Implement file processing
- [ ] Add file cleanup mechanisms

### **B. Upload Service Layer** ⏳
- [ ] File upload service
- [ ] File validation logic
- [ ] Image processing (resize, compress)
- [ ] Audio processing (format conversion)

### **C. Upload Endpoints** ⏳
- [ ] `POST /api/v1/upload/image` - Upload image file
- [ ] `POST /api/v1/upload/audio` - Upload audio file
- [ ] `GET /api/v1/files/{file_id}` - Get file by ID
- [ ] `DELETE /api/v1/files/{file_id}` - Delete file

### **D. File Management** ⏳
- [ ] File metadata storage
- [ ] File access control
- [ ] File cleanup scheduler
- [ ] Storage quota management

### **E. Integration with Flashcards** ⏳
- [ ] Update flashcard creation to handle file uploads
- [ ] File reference validation
- [ ] Orphaned file cleanup
- [ ] File URL generation

## 🏗️ IMPLEMENTATION DETAILS

### **1. File Models**
```python
# app/models/file.py - New file
from enum import Enum

class FileType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"

class FileStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class UploadedFile(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    filename: str
    original_filename: str
    file_type: FileType
    file_size: int
    mime_type: str
    file_path: str
    file_url: str
    thumbnail_url: Optional[str] = None
    status: FileStatus = FileStatus.UPLOADING
    uploaded_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = {}
    is_active: bool = True
```

### **2. Upload Schemas**
```python
# app/schemas/upload.py - New file
class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: FileType
    file_size: int
    file_url: str
    thumbnail_url: Optional[str]
    status: FileStatus
    created_at: datetime

class FileValidationError(BaseModel):
    field: str
    message: str
    code: str

class BulkUploadResponse(BaseModel):
    successful_uploads: List[FileUploadResponse]
    failed_uploads: List[FileValidationError]
```

### **3. Upload Service**
```python
# app/services/upload_service.py - New file
import os
import uuid
import aiofiles
from PIL import Image
import mimetypes

class UploadService:
    def __init__(self):
        self.upload_dir = "uploads"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_image_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        self.allowed_audio_types = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/m4a"}
    
    async def upload_image(self, file: UploadFile, user_id: str) -> UploadedFile:
        """Upload and process image file"""
        # Validate file
        await self._validate_image_file(file)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_extension}"
        
        # Save file
        file_path = await self._save_file(file, unique_filename, "images")
        
        # Process image (resize, create thumbnail)
        processed_data = await self._process_image(file_path)
        
        # Create file record
        uploaded_file = UploadedFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_type=FileType.IMAGE,
            file_size=file.size,
            mime_type=file.content_type,
            file_path=file_path,
            file_url=f"/api/v1/files/{file_id}",
            thumbnail_url=processed_data.get("thumbnail_url"),
            uploaded_by=ObjectId(user_id),
            metadata=processed_data.get("metadata", {})
        )
        
        # Save to database
        result = await self.file_collection.insert_one(uploaded_file.dict(by_alias=True))
        uploaded_file.id = result.inserted_id
        
        return uploaded_file
    
    async def upload_audio(self, file: UploadFile, user_id: str) -> UploadedFile:
        """Upload and process audio file"""
        # Validate file
        await self._validate_audio_file(file)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_extension}"
        
        # Save file
        file_path = await self._save_file(file, unique_filename, "audio")
        
        # Process audio (convert format if needed)
        processed_data = await self._process_audio(file_path)
        
        # Create file record
        uploaded_file = UploadedFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_type=FileType.AUDIO,
            file_size=file.size,
            mime_type=file.content_type,
            file_path=file_path,
            file_url=f"/api/v1/files/{file_id}",
            uploaded_by=ObjectId(user_id),
            metadata=processed_data.get("metadata", {})
        )
        
        # Save to database
        result = await self.file_collection.insert_one(uploaded_file.dict(by_alias=True))
        uploaded_file.id = result.inserted_id
        
        return uploaded_file
```

### **4. File Validation**
```python
# In upload_service.py
async def _validate_image_file(self, file: UploadFile):
    """Validate image file"""
    # Check file size
    if file.size > self.max_file_size:
        raise HTTPException(400, "File size too large")
    
    # Check content type
    if file.content_type not in self.allowed_image_types:
        raise HTTPException(400, "Invalid image format")
    
    # Check file extension
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(400, "Invalid file extension")
    
    # Read file header to verify it's actually an image
    content = await file.read(1024)
    await file.seek(0)
    
    try:
        import imghdr
        image_type = imghdr.what(None, h=content)
        if not image_type:
            raise HTTPException(400, "File is not a valid image")
    except Exception:
        raise HTTPException(400, "Unable to validate image file")

async def _validate_audio_file(self, file: UploadFile):
    """Validate audio file"""
    # Check file size
    if file.size > self.max_file_size:
        raise HTTPException(400, "File size too large")
    
    # Check content type
    if file.content_type not in self.allowed_audio_types:
        raise HTTPException(400, "Invalid audio format")
    
    # Check file extension
    allowed_extensions = {".mp3", ".wav", ".ogg", ".m4a"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(400, "Invalid file extension")
```

### **5. Image Processing**
```python
# In upload_service.py
async def _process_image(self, file_path: str) -> dict:
    """Process uploaded image"""
    try:
        with Image.open(file_path) as img:
            # Get image metadata
            width, height = img.size
            format_name = img.format
            
            # Resize if too large (max 1920x1080)
            max_size = (1920, 1080)
            if width > max_size[0] or height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(file_path, format=format_name, quality=85, optimize=True)
            
            # Create thumbnail (300x300)
            thumbnail = img.copy()
            thumbnail.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            thumbnail_path = file_path.replace(".", "_thumb.")
            thumbnail.save(thumbnail_path, format=format_name, quality=80)
            
            return {
                "thumbnail_url": thumbnail_path.replace(self.upload_dir, "/api/v1/files"),
                "metadata": {
                    "width": img.size[0],
                    "height": img.size[1],
                    "format": format_name,
                    "has_thumbnail": True
                }
            }
    except Exception as e:
        raise HTTPException(500, f"Error processing image: {str(e)}")
```

### **6. File Endpoints**
```python
# app/routers/v1/upload.py - New file
@router.post("/image", response_model=FileUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service)
):
    """Upload image file"""
    return await upload_service.upload_image(file, str(current_user.id))

@router.post("/audio", response_model=FileUploadResponse)
async def upload_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service)
):
    """Upload audio file"""
    return await upload_service.upload_audio(file, str(current_user.id))

@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    upload_service: UploadService = Depends(get_upload_service)
):
    """Serve uploaded file"""
    file_record = await upload_service.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(404, "File not found")
    
    return FileResponse(file_record.file_path)

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service)
):
    """Delete uploaded file"""
    return await upload_service.delete_file(file_id, str(current_user.id))

# Flashcard-specific upload endpoints
@router.post("/flashcards/{flashcard_id}/upload/image", response_model=FileUploadResponse)
async def upload_flashcard_image(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
):
    """Upload image for flashcard question or answer"""
    # Verify flashcard ownership
    flashcard = await flashcard_service.get_flashcard(flashcard_id, str(current_user.id))
    if not flashcard:
        raise HTTPException(404, "Flashcard not found")
    
    # Upload image
    uploaded_file = await upload_service.upload_image(file, str(current_user.id))
    
    # Link to flashcard
    await flashcard_service.add_media_to_flashcard(
        flashcard_id, uploaded_file.id, "image"
    )
    
    return uploaded_file

@router.post("/flashcards/{flashcard_id}/upload/question-audio", response_model=FileUploadResponse)
async def upload_flashcard_question_audio(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
):
    """Upload audio for flashcard question"""
    # Verify flashcard ownership
    flashcard = await flashcard_service.get_flashcard(flashcard_id, str(current_user.id))
    if not flashcard:
        raise HTTPException(404, "Flashcard not found")
    
    # Upload audio
    uploaded_file = await upload_service.upload_audio(file, str(current_user.id))
    
    # Link to flashcard question
    await flashcard_service.add_media_to_flashcard(
        flashcard_id, uploaded_file.id, "question_audio"
    )
    
    return uploaded_file

@router.post("/flashcards/{flashcard_id}/upload/answer-audio", response_model=FileUploadResponse)
async def upload_flashcard_answer_audio(
    flashcard_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
):
    """Upload audio for flashcard answer"""
    # Verify flashcard ownership
    flashcard = await flashcard_service.get_flashcard(flashcard_id, str(current_user.id))
    if not flashcard:
        raise HTTPException(404, "Flashcard not found")
    
    # Upload audio
    uploaded_file = await upload_service.upload_audio(file, str(current_user.id))
    
    # Link to flashcard answer
    await flashcard_service.add_media_to_flashcard(
        flashcard_id, uploaded_file.id, "answer_audio"
    )
    
    return uploaded_file
```

## 🧪 TESTING PLAN

### **Unit Tests**
- [ ] Test file validation logic
- [ ] Test image processing functions
- [ ] Test audio processing functions
- [ ] Test file cleanup mechanisms

### **Integration Tests**
- [ ] Test complete upload workflow
- [ ] Test file serving endpoints
- [ ] Test file deletion
- [ ] Test integration with flashcards

### **API Tests**
- [ ] Test upload endpoints with various file types
- [ ] Test file size limits
- [ ] Test invalid file types
- [ ] Test file access permissions

## 📝 FILES TO CREATE/UPDATE

### **New Files**
- `app/models/file.py` - File models
- `app/schemas/upload.py` - Upload schemas
- `app/services/upload_service.py` - Upload service
- `app/routers/v1/upload.py` - Upload endpoints
- `tests/test_file_upload.py` - Upload tests

### **Updated Files**
- `app/main.py` - Include upload router
- `app/utils/database.py` - Add file collection
- `requirements.txt` - Add Pillow, python-multipart

### **Dependencies to Add**
```txt
Pillow==10.0.1
python-multipart==0.0.6
aiofiles==23.2.1
```

## ⏱️ ESTIMATED TIMELINE
**Total**: 1 day (8 hours)
- File upload infrastructure: 2 hours
- Image/audio processing: 2 hours
- API endpoints: 2 hours
- Testing: 2 hours

## ✅ COMPLETION CRITERIA
- [ ] File upload system working for images and audio
- [ ] File validation and processing working
- [ ] File serving endpoints functional
- [ ] File cleanup mechanisms in place
- [ ] Integration with flashcards working
- [ ] All tests passing

---

## 🔄 NEXT STEP
After completing Step 4, proceed to **Step 5: Testing & Integration**

*Ensure file security and validation are robust*
