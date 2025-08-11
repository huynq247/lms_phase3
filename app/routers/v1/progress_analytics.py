"""
Progress Tracking & Analytics API Router for Phase 6.4
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from app.core.deps import get_current_user
from app.models.user import User
from app.models.progress import (
    SessionProgressResponse, SessionHistoryResponse, UserStatistics,
    ProgressDashboard, AnalyticsQuery, ProgressMetrics
)
from app.services.progress_analytics_service import (
    progress_tracker, historical_analytics, achievement_system
)
from app.services.study_session_service import study_session_service

router = APIRouter(prefix="/study", tags=["Progress Analytics"])


@router.get("/sessions/{session_id}/progress", response_model=SessionProgressResponse)
async def get_session_progress(
    session_id: str = Path(..., description="Study session ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time progress for active study session
    
    **Permissions:** Session owner only
    **Features:**
    - Cards completed vs remaining counter
    - Time elapsed tracking  
    - Current accuracy percentage
    - Active streak counter
    - Session completion percentage
    - Performance indicators
    """
    try:
        # Validate session access
        await study_session_service.initialize()
        session = await study_session_service.validator.validate_session_access(
            study_session_service.db, session_id, str(current_user.id)
        )
        
        # Get session data from database
        session_data = await study_session_service.db.study_sessions.find_one(
            {"_id": session.id if hasattr(session.id, '_id') else session_id}
        )
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Calculate real-time progress metrics
        metrics_data = progress_tracker.calculate_session_progress(session_data)
        metrics = ProgressMetrics(**metrics_data)
        
        response = SessionProgressResponse(
            session_id=session_id,
            metrics=metrics,
            last_updated=datetime.utcnow()
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session progress: {str(e)}"
        )


@router.get("/sessions/history", response_model=SessionHistoryResponse)
async def get_session_history(
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of sessions"),
    include_abandoned: bool = Query(True, description="Include abandoned sessions"),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's study session history with analytics
    
    **Permissions:** Own sessions only
    **Features:**
    - Session completion records
    - Performance trends over time
    - Study mode preferences
    - Time spent per deck
    - Learning pattern analysis
    """
    try:
        # Get session history
        history_data = await historical_analytics.get_session_history(
            user_id=str(current_user.id),
            limit=limit,
            days_back=days_back
        )
        
        # Filter abandoned sessions if requested
        if not include_abandoned:
            history_data = [
                session for session in history_data 
                if session["status"] != "abandoned"
            ]
        
        # Convert to response model
        from app.models.progress import SessionHistoryItem
        sessions = [SessionHistoryItem(**session) for session in history_data]
        
        response = SessionHistoryResponse(
            sessions=sessions,
            total_count=len(sessions),
            period_days=days_back
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session history: {str(e)}"
        )


@router.get("/sessions/stats", response_model=UserStatistics)
async def get_user_statistics(
    days_back: int = Query(30, ge=1, le=365, description="Days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive user study statistics
    
    **Permissions:** Own statistics only  
    **Features:**
    - Session completion metrics
    - Overall performance analysis
    - Study time tracking
    - Accuracy and quality trends
    - Study mode preferences
    - Deck usage patterns
    """
    try:
        # Get user statistics
        stats_data = await historical_analytics.get_user_statistics(
            user_id=str(current_user.id),
            days_back=days_back
        )
        
        response = UserStatistics(**stats_data)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user statistics: {str(e)}"
        )


@router.get("/progress/dashboard", response_model=ProgressDashboard)
async def get_progress_dashboard(
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive analytics dashboard
    
    **Permissions:** Own dashboard only
    **Features:**
    - Weekly/monthly study statistics
    - Deck mastery progress
    - SRS scheduling overview
    - Goal achievement tracking
    - Recent achievements
    - Study pattern analysis
    - Performance insights
    """
    try:
        # Get comprehensive dashboard data
        dashboard_data = await historical_analytics.get_progress_dashboard(
            user_id=str(current_user.id)
        )
        
        response = ProgressDashboard(**dashboard_data)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate progress dashboard: {str(e)}"
        )


@router.get("/achievements")
async def get_user_achievements(
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's achievements and milestones
    
    **Permissions:** Own achievements only
    **Features:**
    - Daily study streaks
    - Cards mastered badges
    - Time-based achievements
    - Accuracy milestones
    - Deck completion rewards
    """
    try:
        await achievement_system.initialize()
        
        # Get achievements from database
        achievements = await achievement_system.db.user_achievements.find({
            "user_id": str(current_user.id),
            "achieved_at": {"$gte": datetime.utcnow() - timedelta(days=days_back)}
        }).sort("achieved_at", -1).to_list(length=None)
        
        # Convert to response format
        from app.models.progress import Achievement
        achievement_list = []
        for ach in achievements:
            achievement_list.append(Achievement(
                type=ach["type"],
                title=ach["title"],
                description=ach["description"],
                icon=ach["icon"],
                achieved_at=ach["achieved_at"],
                points=ach.get("points", 0)
            ))
        
        return {
            "achievements": achievement_list,
            "total_count": len(achievement_list),
            "period_days": days_back,
            "total_points": sum(ach.points or 0 for ach in achievement_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get achievements: {str(e)}"
        )


@router.get("/progress/trends")
async def get_progress_trends(
    metric: str = Query("accuracy", description="Metric to analyze (accuracy, response_time, quality)"),
    days_back: int = Query(30, ge=7, le=90, description="Days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get progress trends for specific metrics
    
    **Permissions:** Own trends only
    **Features:**
    - Accuracy trends over time
    - Response time improvements
    - Quality score progression
    - Learning velocity analysis
    """
    try:
        await historical_analytics.initialize()
        
        # Get sessions for trend analysis
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        sessions = await historical_analytics.db.study_sessions.find({
            "user_id": str(current_user.id),
            "started_at": {"$gte": start_date, "$lte": end_date},
            "status": "completed"
        }).sort("started_at", 1).to_list(length=None)
        
        # Calculate trends based on metric
        trends = []
        for session in sessions:
            progress = progress_tracker.calculate_session_progress(session)
            
            data_point = {
                "date": session["started_at"].date().isoformat(),
                "session_id": str(session["_id"]),
                "value": 0
            }
            
            if metric == "accuracy":
                data_point["value"] = progress["accuracy_percentage"]
            elif metric == "response_time":
                data_point["value"] = progress["average_response_time"]
            elif metric == "quality":
                data_point["value"] = progress["average_quality"]
            elif metric == "learning_velocity":
                data_point["value"] = progress["learning_velocity"]
            
            trends.append(data_point)
        
        # Calculate trend statistics
        values = [point["value"] for point in trends if point["value"] > 0]
        trend_stats = {
            "average": sum(values) / len(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "improvement": (values[-1] - values[0]) if len(values) >= 2 else 0
        }
        
        return {
            "metric": metric,
            "period_days": days_back,
            "data_points": trends,
            "statistics": trend_stats,
            "total_sessions": len(trends)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress trends: {str(e)}"
        )


@router.get("/progress/insights")
async def get_learning_insights(
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered learning insights and recommendations
    
    **Permissions:** Own insights only
    **Features:**
    - Personalized study recommendations
    - Optimal study time suggestions
    - Difficulty level adjustments
    - Performance improvement tips
    """
    try:
        # Get user statistics for insights
        monthly_stats = await historical_analytics.get_user_statistics(
            user_id=str(current_user.id),
            days_back=30
        )
        
        # Generate insights based on data
        insights = {
            "study_performance": {
                "overall_rating": "good" if monthly_stats["overall_accuracy"] >= 75 else "needs_improvement",
                "accuracy_trend": "improving" if monthly_stats["overall_accuracy"] >= 70 else "stable",
                "consistency_score": min(100, monthly_stats["daily_study_streak"] * 10)
            },
            "recommendations": [],
            "optimal_settings": {
                "session_length": 25,  # minutes
                "break_frequency": 25,  # minutes
                "cards_per_session": 20,
                "preferred_time": "morning"
            },
            "areas_for_improvement": [],
            "strengths": []
        }
        
        # Generate recommendations based on performance
        if monthly_stats["overall_accuracy"] < 70:
            insights["recommendations"].append("Focus on review mode to strengthen weak cards")
            insights["areas_for_improvement"].append("accuracy")
        
        if monthly_stats["average_response_time"] > 10:
            insights["recommendations"].append("Practice speed drills to improve response time")
            insights["areas_for_improvement"].append("speed")
        
        if monthly_stats["daily_study_streak"] < 7:
            insights["recommendations"].append("Establish a daily study routine")
            insights["areas_for_improvement"].append("consistency")
        
        # Identify strengths
        if monthly_stats["overall_accuracy"] >= 85:
            insights["strengths"].append("high_accuracy")
        
        if monthly_stats["completion_rate"] >= 90:
            insights["strengths"].append("session_completion")
        
        if monthly_stats["daily_study_streak"] >= 7:
            insights["strengths"].append("consistency")
        
        return insights
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning insights: {str(e)}"
        )
