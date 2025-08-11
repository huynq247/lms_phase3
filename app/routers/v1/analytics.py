"""
Analytics & Visualization API Router for Phase 6.5
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user
from app.models.user import User
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Charts"])


@router.get("/health")
async def health_check():
    """Health check for analytics service"""
    return {
        "service": "Analytics & Visualization",
        "status": "healthy", 
        "version": "6.5.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Progress Charts",
            "Accuracy Trends", 
            "Study Time Analysis",
            "Deck Performance",
            "SRS Effectiveness",
            "Learning Insights"
        ]
    }


@router.get("/progress-chart")
async def get_progress_chart(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    deck_id: Optional[str] = Query(None, description="Filter by specific deck"),
    current_user: User = Depends(get_current_user)
):
    """
    Get progress over time chart data
    
    **Permissions:** Own data only
    **Features:**
    - Daily progress tracking
    - Accuracy trend visualization
    - Configurable time period
    - Deck-specific filtering
    """
    try:
        chart_data = await analytics_service.get_progress_chart_data(
            user_id=str(current_user.id),
            days=days,
            deck_id=deck_id
        )
        
        return chart_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate progress chart: {str(e)}"
        )


@router.get("/accuracy-trend")
async def get_accuracy_trend(
    limit: int = Query(50, ge=10, le=200, description="Number of recent sessions to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get accuracy trend analysis
    
    **Permissions:** Own data only
    **Features:**
    - Session-by-session accuracy
    - Moving average calculation
    - Trend direction analysis
    - Performance improvement tracking
    """
    try:
        trend_data = await analytics_service.get_accuracy_trend_data(
            user_id=str(current_user.id),
            limit=limit
        )
        
        return trend_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate accuracy trend: {str(e)}"
        )


@router.get("/study-time")
async def get_study_time_distribution(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get study time distribution by hour
    
    **Permissions:** Own data only
    **Features:**
    - Hourly study time breakdown
    - Optimal study time identification
    - Study pattern analysis
    - Time-based recommendations
    """
    try:
        distribution_data = await analytics_service.get_study_time_distribution(
            user_id=str(current_user.id),
            days=days
        )
        
        return distribution_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study time distribution: {str(e)}"
        )


@router.get("/deck-performance")
async def get_deck_performance_comparison(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get deck performance comparison
    
    **Permissions:** Own data only
    **Features:**
    - Multi-deck performance comparison
    - Accuracy and time metrics
    - Deck effectiveness ranking
    - Study focus recommendations
    """
    try:
        performance_data = await analytics_service.get_deck_performance_comparison(
            user_id=str(current_user.id),
            days=days
        )
        
        return performance_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate deck performance data: {str(e)}"
        )


@router.get("/srs-effectiveness")
async def get_srs_effectiveness_analysis(
    current_user: User = Depends(get_current_user)
):
    """
    Get SRS (Spaced Repetition System) effectiveness analysis
    
    **Permissions:** Own data only
    **Features:**
    - Interval success rate analysis
    - Memory retention tracking
    - SRS algorithm effectiveness
    - Review timing optimization
    """
    try:
        srs_data = await analytics_service.get_srs_effectiveness_analysis(
            user_id=str(current_user.id)
        )
        
        return srs_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SRS effectiveness data: {str(e)}"
        )


@router.get("/learning-insights")
async def get_comprehensive_learning_insights(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive learning insights and recommendations
    
    **Permissions:** Own data only
    **Features:**
    - Optimal study time analysis
    - Difficulty progression insights
    - Study mode effectiveness
    - Retention rate analysis
    - Personalized recommendations
    """
    try:
        insights = await analytics_service.get_comprehensive_insights(
            user_id=str(current_user.id),
            days=days
        )
        
        return insights
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning insights: {str(e)}"
        )


@router.get("/export/csv")
async def export_analytics_csv(
    chart_type: str = Query(..., description="Chart type to export"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Export analytics data as CSV
    
    **Permissions:** Own data only
    **Supported Types:**
    - progress-chart
    - accuracy-trend
    - study-time
    - deck-performance
    - srs-effectiveness
    """
    try:
        # Get data based on chart type
        if chart_type == "progress-chart":
            data = await analytics_service.get_progress_chart_data(
                user_id=str(current_user.id),
                days=days
            )
        elif chart_type == "accuracy-trend":
            data = await analytics_service.get_accuracy_trend_data(
                user_id=str(current_user.id),
                limit=100
            )
        elif chart_type == "study-time":
            data = await analytics_service.get_study_time_distribution(
                user_id=str(current_user.id),
                days=days
            )
        elif chart_type == "deck-performance":
            data = await analytics_service.get_deck_performance_comparison(
                user_id=str(current_user.id),
                days=days
            )
        elif chart_type == "srs-effectiveness":
            data = await analytics_service.get_srs_effectiveness_analysis(
                user_id=str(current_user.id)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported chart type: {chart_type}"
            )
        
        # Convert to CSV format
        csv_data = _convert_to_csv(data, chart_type)
        
        return JSONResponse(
            content={
                "csv_data": csv_data,
                "filename": f"{chart_type}_{datetime.utcnow().strftime('%Y%m%d')}.csv",
                "chart_type": chart_type,
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CSV data: {str(e)}"
        )


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=90, description="Number of days to summarize"),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics summary for dashboard
    
    **Permissions:** Own data only
    **Features:**
    - Key performance indicators
    - Recent trends summary
    - Quick insights
    - Recommendation highlights
    """
    try:
        # Get key analytics data
        insights = await analytics_service.get_comprehensive_insights(
            user_id=str(current_user.id),
            days=days
        )
        
        # Extract summary metrics
        summary = {
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "key_metrics": {
                "optimal_study_hour": insights["time_patterns"]["analysis"]["best_hour"],
                "peak_performance": insights["time_patterns"]["analysis"]["peak_performance"],
                "overall_retention": insights["retention_analysis"]["overall_retention"],
                "most_effective_mode": max(
                    insights["mode_effectiveness"]["mode_analysis"].keys(),
                    key=lambda x: insights["mode_effectiveness"]["mode_analysis"][x]["effectiveness_score"]
                ) if insights["mode_effectiveness"]["mode_analysis"] else "unknown"
            },
            "quick_insights": {
                "time_recommendation": insights["time_patterns"]["analysis"]["recommendation"],
                "mode_recommendations": insights["mode_effectiveness"]["recommendations"][:2],
                "difficulty_recommendations": insights["difficulty_analysis"]["recommendations"][:2]
            },
            "retention_breakdown": insights["retention_analysis"]["retention_rates"]
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics summary: {str(e)}"
        )


def _convert_to_csv(data: dict, chart_type: str) -> str:
    """Convert chart data to CSV format"""
    
    try:
        if chart_type == "progress-chart":
            chart_data = data["chart_data"]
            header = "Date,Average_Accuracy"
            rows = []
            
            for i, label in enumerate(chart_data["labels"]):
                accuracy = chart_data["datasets"][0]["data"][i]
                rows.append(f"{label},{accuracy}")
            
            return header + "\n" + "\n".join(rows)
        
        elif chart_type == "accuracy-trend":
            chart_data = data["chart_data"]
            header = "Session,Accuracy,Moving_Average"
            rows = []
            
            for i, label in enumerate(chart_data["labels"]):
                accuracy = chart_data["datasets"][0]["data"][i]
                moving_avg = chart_data["datasets"][1]["data"][i]
                rows.append(f"{label},{accuracy},{moving_avg}")
            
            return header + "\n" + "\n".join(rows)
        
        elif chart_type == "study-time":
            chart_data = data["chart_data"]
            header = "Hour,Study_Time_Minutes"
            rows = []
            
            for i, label in enumerate(chart_data["labels"]):
                time_minutes = chart_data["datasets"][0]["data"][i]
                rows.append(f"{label},{time_minutes}")
            
            return header + "\n" + "\n".join(rows)
        
        elif chart_type == "deck-performance":
            chart_data = data["chart_data"]
            header = "Deck,Average_Accuracy,Total_Study_Time_Minutes"
            rows = []
            
            for i, label in enumerate(chart_data["labels"]):
                accuracy = chart_data["datasets"][0]["data"][i]
                time_minutes = chart_data["datasets"][1]["data"][i]
                rows.append(f"{label},{accuracy},{time_minutes}")
            
            return header + "\n" + "\n".join(rows)
        
        elif chart_type == "srs-effectiveness":
            chart_data = data["chart_data"]
            header = "Interval_Range,Success_Rate"
            rows = []
            
            for i, label in enumerate(chart_data["labels"]):
                success_rate = chart_data["datasets"][0]["data"][i]
                rows.append(f"{label},{success_rate}")
            
            return header + "\n" + "\n".join(rows)
        
        else:
            return "Unsupported chart type for CSV export"
    
    except Exception as e:
        return f"Error converting to CSV: {str(e)}"
