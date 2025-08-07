# 🃏 STEP 2: DECK MANAGEMENT APIs
*Complete deck CRUD with privacy controls*

## 🎯 OBJECTIVES
- Implement complete deck CRUD operations
- Add deck categories and tagging system
- Implement privacy controls (public/private/shared)
- Add deck search and filtering capabilities

## 📋 IMPLEMENTATION CHECKLIST

### **A. Deck Models & Schemas** ⏳
- [ ] Create Deck model with all fields
- [ ] Create deck CRUD schemas
- [ ] Add deck category/tag models
- [ ] Implement privacy enums

### **B. Deck Service Layer** ⏳
- [ ] Deck CRUD operations
- [ ] Privacy permission checking
- [ ] Deck search and filtering
- [ ] Category management

### **C. Deck CRUD Endpoints** ⏳
- [ ] `GET /api/v1/decks` - List user's decks
- [ ] `POST /api/v1/decks` - Create new deck
- [ ] `GET /api/v1/decks/{deck_id}` - Get deck by ID
- [ ] `PUT /api/v1/decks/{deck_id}` - Update deck
- [ ] `DELETE /api/v1/decks/{deck_id}` - Delete deck

### **D. Deck Discovery Endpoints** ⏳
- [ ] `GET /api/v1/decks/public` - Browse public decks
- [ ] `GET /api/v1/decks/search` - Search decks
- [ ] `GET /api/v1/decks/categories` - Get all categories
- [ ] `POST /api/v1/decks/{deck_id}/clone` - Clone public deck

### **E. Deck Sharing Endpoints** ⏳
- [ ] `POST /api/v1/decks/{deck_id}/share` - Share deck with users
- [ ] `GET /api/v1/decks/shared` - Get shared decks
- [ ] `DELETE /api/v1/decks/{deck_id}/share/{user_id}` - Remove sharing

## 🏗️ IMPLEMENTATION DETAILS

### **1. Deck Model**
```python
# app/models/deck.py - New file
from enum import Enum

class DeckPrivacy(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public" 
    SHARED = "shared"

class Deck(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    tags: List[str] = []
    privacy: DeckPrivacy = DeckPrivacy.PRIVATE
    owner_id: PyObjectId
    shared_with: List[PyObjectId] = []
    flashcard_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_studied: Optional[datetime] = None
    is_active: bool = True
```

### **2. Deck Schemas**
```python
# app/schemas/deck.py - New file
class DeckCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    tags: List[str] = []
    privacy: DeckPrivacy = DeckPrivacy.PRIVATE

class DeckUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy: Optional[DeckPrivacy] = None

class DeckShare(BaseModel):
    user_emails: List[str] = Field(..., min_items=1)

class DeckResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    category: Optional[str]
    tags: List[str]
    privacy: DeckPrivacy
    owner_id: str
    flashcard_count: int
    created_at: datetime
    updated_at: datetime
    last_studied: Optional[datetime]
    can_edit: bool
    can_study: bool
```

### **3. Deck Service**
```python
# app/services/deck_service.py - New file
class DeckService:
    async def create_deck(self, deck_data: DeckCreate, owner_id: str) -> Deck
    async def get_deck_by_id(self, deck_id: str, user_id: str) -> Deck
    async def update_deck(self, deck_id: str, deck_data: DeckUpdate, user_id: str) -> Deck
    async def delete_deck(self, deck_id: str, user_id: str) -> bool
    async def get_user_decks(self, user_id: str, skip: int, limit: int) -> List[Deck]
    async def get_public_decks(self, skip: int, limit: int, category: str = None) -> List[Deck]
    async def search_decks(self, query: str, user_id: str) -> List[Deck]
    async def share_deck(self, deck_id: str, user_emails: List[str], owner_id: str) -> bool
    async def clone_deck(self, deck_id: str, user_id: str) -> Deck
    async def check_deck_permission(self, deck_id: str, user_id: str) -> dict
```

### **4. Privacy Permission Logic**
```python
# In deck_service.py
async def check_deck_permission(self, deck_id: str, user_id: str) -> dict:
    """
    Returns:
    {
        "can_view": bool,
        "can_edit": bool,
        "can_study": bool,
        "can_delete": bool
    }
    """
    deck = await self.get_deck_by_id(deck_id)
    
    # Owner has all permissions
    if deck.owner_id == user_id:
        return {"can_view": True, "can_edit": True, "can_study": True, "can_delete": True}
    
    # Public decks - can view and study only
    if deck.privacy == DeckPrivacy.PUBLIC:
        return {"can_view": True, "can_edit": False, "can_study": True, "can_delete": False}
    
    # Shared decks - can view and study only
    if user_id in deck.shared_with:
        return {"can_view": True, "can_edit": False, "can_study": True, "can_delete": False}
    
    # Private decks - no access
    return {"can_view": False, "can_edit": False, "can_study": False, "can_delete": False}
```

## 🧪 TESTING PLAN

### **Unit Tests**
- [ ] Test deck CRUD operations
- [ ] Test privacy permission logic
- [ ] Test deck search functionality
- [ ] Test deck sharing mechanisms

### **Integration Tests**
- [ ] Test complete deck workflow
- [ ] Test privacy controls end-to-end
- [ ] Test deck cloning process
- [ ] Test multi-user sharing scenarios

### **API Tests**
- [ ] Test all deck endpoints
- [ ] Test authorization for different privacy levels
- [ ] Test search and filtering
- [ ] Test error scenarios

## 📝 FILES TO CREATE/UPDATE

### **New Files**
- `app/models/deck.py` - Deck model and enums
- `app/schemas/deck.py` - Deck schemas
- `app/services/deck_service.py` - Deck management service
- `app/routers/v1/decks.py` - Deck endpoints
- `tests/test_deck_management.py` - Deck tests

### **Updated Files**
- `app/main.py` - Include deck router
- `app/utils/database.py` - Add deck collection

## ⏱️ ESTIMATED TIMELINE
**Total**: 1-2 days (12 hours)
- Models and schemas: 2 hours
- Service layer: 4 hours
- API endpoints: 3 hours
- Privacy logic: 2 hours
- Testing: 3 hours

## ✅ COMPLETION CRITERIA
- [ ] All deck CRUD operations working
- [ ] Privacy controls properly enforced
- [ ] Deck sharing functionality working
- [ ] Search and filtering operational
- [ ] All tests passing
- [ ] Proper error handling implemented

---

## 🔄 NEXT STEP
After completing Step 2, proceed to **Step 3: Flashcard Management APIs**

*Ensure deck privacy logic is solid before moving to flashcards*
