# 🎴 STEP 3: FLASHCARD MANAGEMENT APIs
*Flashcard CRUD with content management*

## 🎯 OBJECTIVES
- Implement complete flashcard CRUD operations
- Add content validation and formatting
- Support different flashcard types (text, image, audio)
- Implement flashcard ordering within decks

## 📋 IMPLEMENTATION CHECKLIST

### **A. Flashcard Models & Schemas** ⏳
- [ ] Create Flashcard model with content fields
- [ ] Create flashcard CRUD schemas
- [ ] Add flashcard type enums
- [ ] Implement content validation

### **B. Flashcard Service Layer** ⏳
- [ ] Flashcard CRUD operations
- [ ] Content validation and sanitization
- [ ] Flashcard ordering within decks
- [ ] Bulk operations support

### **C. Flashcard CRUD Endpoints** ⏳
- [ ] `GET /api/v1/decks/{deck_id}/flashcards` - List deck flashcards
- [ ] `POST /api/v1/decks/{deck_id}/flashcards` - Create flashcard
- [ ] `GET /api/v1/flashcards/{flashcard_id}` - Get flashcard by ID
- [ ] `PUT /api/v1/flashcards/{flashcard_id}` - Update flashcard
- [ ] `DELETE /api/v1/flashcards/{flashcard_id}` - Delete flashcard

### **D. Flashcard Management Endpoints** ⏳
- [ ] `POST /api/v1/decks/{deck_id}/flashcards/bulk` - Bulk create flashcards
- [ ] `PUT /api/v1/decks/{deck_id}/flashcards/reorder` - Reorder flashcards
- [ ] `POST /api/v1/flashcards/{flashcard_id}/duplicate` - Duplicate flashcard
- [ ] `GET /api/v1/flashcards/{flashcard_id}/history` - Get edit history

### **E. Content Management** ⏳
- [ ] Text content with formatting support
- [ ] Image content validation
- [ ] Audio content validation
- [ ] Mixed content handling

## 🏗️ IMPLEMENTATION DETAILS

### **1. Flashcard Model**
```python
# app/models/flashcard.py - New file
from enum import Enum

class FlashcardType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    MIXED = "mixed"

class ContentType(str, Enum):
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    IMAGE_URL = "image_url"
    AUDIO_URL = "audio_url"

class FlashcardContent(BaseModel):
    type: ContentType
    content: str
    metadata: Optional[dict] = {}

class Flashcard(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    deck_id: PyObjectId
    front_content: List[FlashcardContent]
    back_content: List[FlashcardContent]
    flashcard_type: FlashcardType = FlashcardType.TEXT
    order_index: int = 0
    tags: List[str] = []
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: PyObjectId
    is_active: bool = True
```

### **2. Flashcard Schemas**
```python
# app/schemas/flashcard.py - New file
class FlashcardContentCreate(BaseModel):
    type: ContentType
    content: str = Field(..., min_length=1, max_length=5000)
    metadata: Optional[dict] = {}

class FlashcardCreate(BaseModel):
    front_content: List[FlashcardContentCreate] = Field(..., min_items=1)
    back_content: List[FlashcardContentCreate] = Field(..., min_items=1)
    flashcard_type: FlashcardType = FlashcardType.TEXT
    tags: List[str] = []
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)

class FlashcardUpdate(BaseModel):
    front_content: Optional[List[FlashcardContentCreate]] = None
    back_content: Optional[List[FlashcardContentCreate]] = None
    flashcard_type: Optional[FlashcardType] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)

class FlashcardBulkCreate(BaseModel):
    flashcards: List[FlashcardCreate] = Field(..., min_items=1, max_items=100)

class FlashcardReorder(BaseModel):
    flashcard_orders: List[dict] = Field(..., min_items=1)
    # [{"flashcard_id": "...", "order_index": 1}, ...]

class FlashcardResponse(BaseModel):
    id: str
    deck_id: str
    front_content: List[FlashcardContent]
    back_content: List[FlashcardContent]
    flashcard_type: FlashcardType
    order_index: int
    tags: List[str]
    difficulty: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    can_edit: bool
```

### **3. Flashcard Service**
```python
# app/services/flashcard_service.py - New file
class FlashcardService:
    async def create_flashcard(self, deck_id: str, flashcard_data: FlashcardCreate, user_id: str) -> Flashcard
    async def get_flashcard_by_id(self, flashcard_id: str, user_id: str) -> Flashcard
    async def update_flashcard(self, flashcard_id: str, flashcard_data: FlashcardUpdate, user_id: str) -> Flashcard
    async def delete_flashcard(self, flashcard_id: str, user_id: str) -> bool
    async def get_deck_flashcards(self, deck_id: str, user_id: str, skip: int, limit: int) -> List[Flashcard]
    async def bulk_create_flashcards(self, deck_id: str, flashcards_data: FlashcardBulkCreate, user_id: str) -> List[Flashcard]
    async def reorder_flashcards(self, deck_id: str, reorder_data: FlashcardReorder, user_id: str) -> bool
    async def duplicate_flashcard(self, flashcard_id: str, user_id: str) -> Flashcard
    async def validate_content(self, content: List[FlashcardContent]) -> bool
    async def sanitize_content(self, content: str, content_type: ContentType) -> str
```

### **4. Content Validation Logic**
```python
# In flashcard_service.py
async def validate_content(self, content_list: List[FlashcardContent]) -> bool:
    """Validate flashcard content based on type"""
    for content in content_list:
        if content.type == ContentType.PLAIN_TEXT:
            if not content.content.strip():
                raise ValueError("Plain text content cannot be empty")
        
        elif content.type == ContentType.IMAGE_URL:
            if not self._is_valid_url(content.content):
                raise ValueError("Invalid image URL")
            if not content.content.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                raise ValueError("Unsupported image format")
        
        elif content.type == ContentType.AUDIO_URL:
            if not self._is_valid_url(content.content):
                raise ValueError("Invalid audio URL")
            if not content.content.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                raise ValueError("Unsupported audio format")
        
        elif content.type == ContentType.MARKDOWN:
            # Basic markdown validation
            if len(content.content) > 5000:
                raise ValueError("Markdown content too long")
        
        elif content.type == ContentType.HTML:
            # HTML sanitization
            content.content = await self.sanitize_html(content.content)
    
    return True

async def sanitize_html(self, html_content: str) -> str:
    """Sanitize HTML content to prevent XSS"""
    import bleach
    
    allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'br', 'p', 'ul', 'ol', 'li']
    allowed_attributes = {}
    
    return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attributes)
```

### **5. Flashcard Ordering System**
```python
# In flashcard_service.py
async def reorder_flashcards(self, deck_id: str, reorder_data: FlashcardReorder, user_id: str) -> bool:
    """Reorder flashcards within a deck"""
    # Check deck permission
    deck_permission = await self.deck_service.check_deck_permission(deck_id, user_id)
    if not deck_permission.get("can_edit"):
        raise HTTPException(status_code=403, detail="No permission to edit this deck")
    
    # Update order indexes
    bulk_operations = []
    for item in reorder_data.flashcard_orders:
        bulk_operations.append(
            UpdateOne(
                {"_id": ObjectId(item["flashcard_id"]), "deck_id": ObjectId(deck_id)},
                {"$set": {"order_index": item["order_index"], "updated_at": datetime.utcnow()}}
            )
        )
    
    result = await self.flashcard_collection.bulk_write(bulk_operations)
    return result.modified_count > 0
```

## 🧪 TESTING PLAN

### **Unit Tests**
- [ ] Test flashcard CRUD operations
- [ ] Test content validation logic
- [ ] Test flashcard ordering
- [ ] Test bulk operations

### **Integration Tests**
- [ ] Test flashcard workflow with deck permissions
- [ ] Test content sanitization
- [ ] Test flashcard duplication
- [ ] Test bulk flashcard creation

### **API Tests**
- [ ] Test all flashcard endpoints
- [ ] Test content validation errors
- [ ] Test ordering functionality
- [ ] Test permission checking

## 📝 FILES TO CREATE/UPDATE

### **New Files**
- `app/models/flashcard.py` - Flashcard model and enums
- `app/schemas/flashcard.py` - Flashcard schemas
- `app/services/flashcard_service.py` - Flashcard service
- `app/routers/v1/flashcards.py` - Flashcard endpoints
- `tests/test_flashcard_management.py` - Flashcard tests

### **Updated Files**
- `app/main.py` - Include flashcard router
- `app/utils/database.py` - Add flashcard collection
- `app/services/deck_service.py` - Update flashcard count

### **Dependencies to Add**
- `bleach` - HTML sanitization
- `python-multipart` - File upload support

## ⏱️ ESTIMATED TIMELINE
**Total**: 1 day (8 hours)
- Models and schemas: 2 hours
- Service layer: 3 hours
- API endpoints: 2 hours
- Testing: 2 hours

## ✅ COMPLETION CRITERIA
- [ ] All flashcard CRUD operations working
- [ ] Content validation and sanitization working
- [ ] Flashcard ordering system functional
- [ ] Bulk operations working
- [ ] All tests passing
- [ ] Proper permission checking implemented

---

## 🔄 NEXT STEP
After completing Step 3, proceed to **Step 4: Multimedia Upload Support**

*Ensure content validation is robust before adding file uploads*
