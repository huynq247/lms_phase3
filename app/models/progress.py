"""
Progress Tracking & Analytics Models for Phase 6.4
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProgressMetrics(BaseModel):
    """Real-time session progress metrics"""
    cards_completed: int = Field(..., description="Number of cards completed")
    cards_remaining: int = Field(..., description="Number of cards remaining")
    total_cards: int = Field(..., description="Total cards in session")
    time_elapsed_seconds: int = Field(..., description="Time elapsed in seconds")
    time_elapsed_minutes: int = Field(..., description="Time elapsed in minutes")
    accuracy_percentage: float = Field(..., description="Current accuracy percentage")
    current_streak: int = Field(..., description="Current correct answer streak")
    completion_percentage: float = Field(..., description="Session completion percentage")
    average_response_time: float = Field(..., description="Average response time in seconds")
    average_quality: float = Field(..., description="Average quality rating")
    learning_velocity: float = Field(..., description="Cards per minute")
    correct_answers: int = Field(..., description="Number of correct answers")
    incorrect_answers: int = Field(..., description="Number of incorrect answers")


class SessionProgressResponse(BaseModel):
    """Response for real-time session progress"""
    session_id: str = Field(..., description="Session ID")
    metrics: ProgressMetrics = Field(..., description="Progress metrics")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class SessionHistoryItem(BaseModel):
    """Individual session history item"""
    session_id: str = Field(..., description="Session ID")
    deck_id: str = Field(..., description="Deck ID")
    study_mode: str = Field(..., description="Study mode used")
    started_at: datetime = Field(..., description="Session start time")
    completed_at: Optional[datetime] = Field(None, description="Session completion time")
    status: str = Field(..., description="Session status")
    duration_minutes: int = Field(..., description="Session duration in minutes")
    cards_studied: int = Field(..., description="Number of cards studied")
    accuracy: float = Field(..., description="Session accuracy percentage")
    average_response_time: float = Field(..., description="Average response time")
    best_streak: int = Field(..., description="Best streak achieved")
    performance_rating: str = Field(..., description="Performance rating")


class SessionHistoryResponse(BaseModel):
    """Response for session history"""
    sessions: List[SessionHistoryItem] = Field(..., description="List of sessions")
    total_count: int = Field(..., description="Total number of sessions")
    period_days: int = Field(..., description="Period in days")


class UserStatistics(BaseModel):
    """Comprehensive user statistics"""
    period_days: int = Field(..., description="Statistics period in days")
    total_sessions: int = Field(..., description="Total number of sessions")
    completed_sessions: int = Field(..., description="Number of completed sessions")
    abandoned_sessions: int = Field(..., description="Number of abandoned sessions")
    completion_rate: float = Field(..., description="Session completion rate percentage")
    total_study_time_minutes: float = Field(..., description="Total study time in minutes")
    total_cards_studied: int = Field(..., description="Total cards studied")
    overall_accuracy: float = Field(..., description="Overall accuracy percentage")
    average_response_time: float = Field(..., description="Average response time")
    average_quality: float = Field(..., description="Average quality rating")
    daily_study_streak: int = Field(..., description="Current daily study streak")
    preferred_study_mode: Optional[str] = Field(None, description="Most used study mode")
    study_mode_distribution: Dict[str, int] = Field(..., description="Study mode usage distribution")
    most_studied_deck: Optional[str] = Field(None, description="Most studied deck ID")
    deck_usage_distribution: Dict[str, int] = Field(..., description="Deck usage distribution")


class DeckMasteryProgress(BaseModel):
    """Deck mastery progress information"""
    deck_id: str = Field(..., description="Deck ID")
    deck_title: str = Field(..., description="Deck title")
    total_cards: int = Field(..., description="Total cards in deck")
    studied_cards: int = Field(..., description="Number of cards studied")
    mastered_cards: int = Field(..., description="Number of mastered cards")
    study_percentage: float = Field(..., description="Percentage of cards studied")
    mastery_percentage: float = Field(..., description="Percentage of cards mastered")
    average_ease_factor: float = Field(..., description="Average ease factor")


class SRSOverview(BaseModel):
    """SRS scheduling overview"""
    total_cards_in_srs: int = Field(..., description="Total cards in SRS system")
    overdue_cards: int = Field(..., description="Number of overdue cards")
    due_today: int = Field(..., description="Cards due today")
    due_tomorrow: int = Field(..., description="Cards due tomorrow")
    due_this_week: int = Field(..., description="Cards due this week")
    review_load: int = Field(..., description="Current review load (overdue + today)")


class Achievement(BaseModel):
    """Achievement/milestone information"""
    type: str = Field(..., description="Achievement type")
    title: str = Field(..., description="Achievement title")
    description: str = Field(..., description="Achievement description")
    icon: str = Field(..., description="Achievement icon")
    achieved_at: datetime = Field(..., description="Achievement timestamp")
    points: Optional[int] = Field(None, description="Points awarded")


class StudyPattern(BaseModel):
    """Study pattern analysis"""
    peak_study_hour: Optional[int] = Field(None, description="Peak study hour (0-23)")
    peak_study_day: str = Field(..., description="Peak study day")
    hour_distribution: Dict[int, int] = Field(..., description="Study sessions by hour")
    day_distribution: Dict[str, int] = Field(..., description="Study sessions by day")
    total_sessions_analyzed: int = Field(..., description="Number of sessions analyzed")


class ProgressDashboard(BaseModel):
    """Comprehensive progress dashboard"""
    weekly_stats: UserStatistics = Field(..., description="Weekly statistics")
    monthly_stats: UserStatistics = Field(..., description="Monthly statistics")
    deck_mastery: List[DeckMasteryProgress] = Field(..., description="Deck mastery progress")
    srs_overview: SRSOverview = Field(..., description="SRS scheduling overview")
    achievements: List[Achievement] = Field(..., description="Recent achievements")
    study_patterns: StudyPattern = Field(..., description="Study pattern analysis")
    dashboard_generated_at: datetime = Field(..., description="Dashboard generation timestamp")


class AnalyticsQuery(BaseModel):
    """Query parameters for analytics"""
    days_back: int = Field(30, ge=1, le=365, description="Number of days to look back")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    include_abandoned: bool = Field(True, description="Include abandoned sessions")


class PerformanceIndicators(BaseModel):
    """Performance indicators for analytics"""
    learning_velocity_trend: List[float] = Field(..., description="Learning velocity over time")
    accuracy_trend: List[float] = Field(..., description="Accuracy trend over time")
    response_time_trend: List[float] = Field(..., description="Response time trend")
    quality_score_trend: List[float] = Field(..., description="Quality score trend")
    difficulty_progression: Dict[str, int] = Field(..., description="Difficulty level progression")


class StudySessionAnalytics(BaseModel):
    """Study session analytics data for database storage"""
    session_id: str = Field(..., description="Associated session ID")
    user_id: str = Field(..., description="User ID")
    performance_metrics: ProgressMetrics = Field(..., description="Performance metrics")
    time_tracking: Dict[str, Any] = Field(..., description="Detailed time tracking")
    accuracy_stats: List[Dict[str, Any]] = Field(..., description="Accuracy statistics")
    response_patterns: Dict[str, Any] = Field(..., description="Response pattern analysis")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class MilestoneType(str, Enum):
    """Types of milestones/achievements"""
    DAILY_STREAK = "daily_streak"
    CARDS_STUDIED = "cards_studied"
    ACCURACY_MILESTONE = "accuracy_milestone"
    TIME_MILESTONE = "time_milestone"
    DECK_COMPLETION = "deck_completion"
    PERFECT_SESSION = "perfect_session"
    SPEED_DEMON = "speed_demon"
    MARATHON_SESSION = "marathon_session"
    STREAK_MASTER = "streak_master"


class GoalType(str, Enum):
    """Types of study goals"""
    DAILY_CARDS = "daily_cards"
    DAILY_TIME = "daily_time"
    WEEKLY_CARDS = "weekly_cards"
    WEEKLY_TIME = "weekly_time"
    ACCURACY_TARGET = "accuracy_target"
    STREAK_TARGET = "streak_target"
    DECK_MASTERY = "deck_mastery"


class StudyGoal(BaseModel):
    """Study goal definition"""
    goal_id: str = Field(..., description="Goal ID")
    user_id: str = Field(..., description="User ID")
    goal_type: GoalType = Field(..., description="Type of goal")
    target_value: float = Field(..., description="Target value to achieve")
    current_progress: float = Field(0.0, description="Current progress towards goal")
    deadline: Optional[datetime] = Field(None, description="Goal deadline")
    is_active: bool = Field(True, description="Whether goal is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Goal creation time")
    achieved_at: Optional[datetime] = Field(None, description="Goal achievement time")


class GoalProgress(BaseModel):
    """Goal progress tracking"""
    goal: StudyGoal = Field(..., description="Goal definition")
    progress_percentage: float = Field(..., description="Progress percentage")
    is_achieved: bool = Field(..., description="Whether goal is achieved")
    days_remaining: Optional[int] = Field(None, description="Days remaining to deadline")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion date")


class LearningInsights(BaseModel):
    """AI-powered learning insights"""
    strengths: List[str] = Field(..., description="User's learning strengths")
    areas_for_improvement: List[str] = Field(..., description="Areas needing improvement")
    recommended_study_times: List[int] = Field(..., description="Recommended study hours")
    optimal_session_length: int = Field(..., description="Optimal session length in minutes")
    difficulty_recommendations: Dict[str, str] = Field(..., description="Difficulty recommendations per deck")
    study_mode_recommendations: List[str] = Field(..., description="Recommended study modes")
    break_frequency_suggestion: int = Field(..., description="Suggested break frequency in minutes")
    predicted_retention_rate: float = Field(..., description="Predicted retention rate")


class ComprehensiveAnalytics(BaseModel):
    """Complete analytics package"""
    user_statistics: UserStatistics = Field(..., description="User statistics")
    progress_dashboard: ProgressDashboard = Field(..., description="Progress dashboard")
    performance_indicators: PerformanceIndicators = Field(..., description="Performance indicators")
    goals_progress: List[GoalProgress] = Field(..., description="Goals progress")
    learning_insights: LearningInsights = Field(..., description="Learning insights")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Analytics generation time")
