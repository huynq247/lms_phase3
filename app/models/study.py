"""
Study Session Models for Phase 6.1
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class StudyMode(str, Enum):
    """Study modes for different learning approaches"""
    REVIEW = "review"        # SRS-based review of due cards
    PRACTICE = "practice"    # Non-SRS practice mode
    CRAM = "cram"           # Rapid review of all cards
    TEST = "test"           # Assessment mode with no hints
    LEARN = "learn"         # New card introduction mode


class SessionStatus(str, Enum):
    """Study session status"""
    ACTIVE = "active"
    PAUSED = "paused"
    BREAK = "break"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class StudySessionStartRequest(BaseModel):
    """Request to start a new study session"""
    deck_id: str = Field(..., description="Deck ID for study session")
    lesson_id: Optional[str] = Field(None, description="Optional lesson ID")
    study_mode: StudyMode = Field(..., description="Study mode")
    target_time: Optional[int] = Field(None, gt=0, description="Target time in minutes")
    target_cards: Optional[int] = Field(None, gt=0, description="Target number of cards")
    break_reminders_enabled: bool = Field(True, description="Enable break reminders")
    break_interval: int = Field(25, gt=0, description="Break reminder interval in minutes")


class FlashcardAnswerRequest(BaseModel):
    """Request to submit flashcard answer"""
    flashcard_id: str = Field(..., description="Flashcard ID")
    quality: int = Field(..., ge=0, le=5, description="SM-2 quality rating (0-5)")
    response_time: float = Field(..., gt=0, description="Response time in seconds")
    was_correct: bool = Field(..., description="Whether answer was correct")
    answer_text: Optional[str] = Field(None, description="User's answer text")


class StudySessionProgress(BaseModel):
    """Real-time session progress tracking"""
    cards_studied: int = Field(0, description="Number of cards studied")
    cards_remaining: int = Field(0, description="Number of cards remaining")
    correct_answers: int = Field(0, description="Number of correct answers")
    incorrect_answers: int = Field(0, description="Number of incorrect answers")
    total_time: int = Field(0, description="Total time spent in seconds")
    break_count: int = Field(0, description="Number of breaks taken")
    current_streak: int = Field(0, description="Current correct answer streak")
    accuracy_rate: float = Field(0.0, description="Current accuracy rate")
    average_response_time: float = Field(0.0, description="Average response time")


class StudySession(BaseModel):
    """Study session data model"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID")
    deck_id: str = Field(..., description="Deck ID")
    lesson_id: Optional[str] = Field(None, description="Lesson ID")
    
    # Session Configuration
    study_mode: StudyMode = Field(..., description="Study mode")
    target_time: Optional[int] = Field(None, description="Target time in minutes")
    target_cards: Optional[int] = Field(None, description="Target number of cards")
    break_reminders_enabled: bool = Field(True, description="Break reminders enabled")
    break_interval: int = Field(25, description="Break interval in minutes")
    
    # Session Status
    status: SessionStatus = Field(SessionStatus.ACTIVE, description="Session status")
    progress: StudySessionProgress = Field(default_factory=StudySessionProgress)
    
    # Session Tracking
    cards_scheduled: List[str] = Field(default_factory=list, description="Scheduled flashcard IDs")
    current_card_index: int = Field(0, description="Current card index")
    answers: List[Dict[str, Any]] = Field(default_factory=list, description="Answer history")
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    next_break_reminder: Optional[datetime] = Field(None)
    
    # Session Analytics
    session_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class FlashcardStudyResponse(BaseModel):
    """Flashcard data for study session"""
    id: str = Field(..., description="Flashcard ID")
    deck_id: str = Field(..., description="Deck ID")
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer text")
    hint: Optional[str] = Field(None, description="Hint text")
    explanation: Optional[str] = Field(None, description="Explanation text")
    
    # Multimedia content
    question_image: Optional[str] = Field(None, description="Question image URL")
    answer_image: Optional[str] = Field(None, description="Answer image URL")
    question_audio: Optional[str] = Field(None, description="Question audio URL")
    answer_audio: Optional[str] = Field(None, description="Answer audio URL")
    
    # Study metadata
    difficulty_level: Optional[str] = Field(None, description="Difficulty level")
    tags: List[str] = Field(default_factory=list, description="Flashcard tags")
    
    # SRS data (for review mode)
    repetitions: int = Field(0, description="Number of repetitions")
    ease_factor: float = Field(2.5, description="SM-2 ease factor")
    interval: int = Field(0, description="Current interval in days")
    next_review: Optional[datetime] = Field(None, description="Next review date")


class StudySessionResponse(BaseModel):
    """Study session response with current state"""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    deck_id: str = Field(..., description="Deck ID")
    lesson_id: Optional[str] = Field(None, description="Lesson ID")
    
    # Configuration
    study_mode: StudyMode = Field(..., description="Study mode")
    target_time: Optional[int] = Field(None, description="Target time in minutes")
    target_cards: Optional[int] = Field(None, description="Target number of cards")
    
    # Status and Progress
    status: SessionStatus = Field(..., description="Session status")
    progress: StudySessionProgress = Field(..., description="Session progress")
    
    # Current Card
    current_card: Optional[FlashcardStudyResponse] = Field(None, description="Current flashcard")
    
    # Session Info
    started_at: datetime = Field(..., description="Session start time")
    last_activity_at: datetime = Field(..., description="Last activity time")
    next_break_reminder: Optional[datetime] = Field(None, description="Next break reminder")
    
    # Completion info
    is_completed: bool = Field(False, description="Session completed")
    completion_percentage: float = Field(0.0, description="Completion percentage")


class SessionAnswerResponse(BaseModel):
    """Response after submitting flashcard answer"""
    session_id: str = Field(..., description="Session ID")
    flashcard_id: str = Field(..., description="Flashcard ID")
    was_correct: bool = Field(..., description="Answer correctness")
    quality: int = Field(..., description="Quality rating")
    
    # Next card info
    next_card: Optional[FlashcardStudyResponse] = Field(None, description="Next flashcard")
    session_completed: bool = Field(False, description="Session completed")
    
    # Updated progress
    progress: StudySessionProgress = Field(..., description="Updated progress")
    completion_percentage: float = Field(0.0, description="Completion percentage")
    cards_remaining: int = Field(0, description="Cards remaining")
    
    # Performance tracking
    current_streak: int = Field(0, description="Current correct streak")
    streak_bonus: bool = Field(False, description="Streak bonus achieved")
    accuracy_milestone: Optional[str] = Field(None, description="Accuracy milestone")
    
    # Session management
    break_reminder: bool = Field(False, description="Break reminder triggered")


class SessionBreakRequest(BaseModel):
    """Request to take a break"""
    break_duration: int = Field(5, gt=0, description="Break duration in minutes")
    break_type: str = Field("manual", description="Break type (manual/reminder)")


class SessionBreakResponse(BaseModel):
    """Response for break request"""
    session_id: str = Field(..., description="Session ID")
    break_started_at: datetime = Field(..., description="Break start time")
    break_duration: int = Field(..., description="Break duration in minutes")
    resume_time: datetime = Field(..., description="Resume time")
    break_count: int = Field(..., description="Total break count")


class SessionCompletionResponse(BaseModel):
    """Response for session completion"""
    session_id: str = Field(..., description="Session ID")
    completion_type: str = Field(..., description="Completion type (goal/manual)")
    
    # Session Summary
    total_time: int = Field(..., description="Total time in seconds")
    cards_studied: int = Field(..., description="Cards studied")
    accuracy_rate: float = Field(..., description="Overall accuracy")
    correct_answers: int = Field(..., description="Correct answers")
    incorrect_answers: int = Field(..., description="Incorrect answers")
    
    # Performance Metrics
    average_response_time: float = Field(..., description="Average response time")
    best_streak: int = Field(..., description="Best correct streak")
    break_count: int = Field(..., description="Number of breaks")
    
    # Achievements
    goals_achieved: List[str] = Field(default_factory=list, description="Goals achieved")
    performance_rating: str = Field(..., description="Performance rating")
    
    # Next Session Recommendation
    recommended_mode: StudyMode = Field(..., description="Recommended next mode")
    cards_due_tomorrow: int = Field(0, description="Cards due tomorrow")
