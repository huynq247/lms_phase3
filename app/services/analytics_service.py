"""
Analytics Service for Phase 6.5
Advanced analytics and data visualization for study insights
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId
import logging
from statistics import mean, median
from collections import defaultdict, Counter

from app.core.deps import get_database
from app.models.study import StudyMode, SessionStatus

logger = logging.getLogger(__name__)


class ChartDataGenerator:
    """Generate chart data for various analytics"""
    
    @staticmethod
    def generate_progress_chart_data(sessions: List[Dict]) -> Dict[str, Any]:
        """Generate progress over time chart data"""
        
        # Group sessions by date
        daily_progress = defaultdict(list)
        for session in sessions:
            date = session['started_at'].date() if session.get('started_at') else datetime.now().date()
            accuracy = session.get('progress', {}).get('accuracy_rate', 0)
            daily_progress[date].append(accuracy)
        
        # Calculate daily averages
        chart_data = {
            "labels": [],
            "datasets": [{
                "label": "Daily Average Accuracy",
                "data": [],
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "tension": 0.1
            }]
        }
        
        # Sort dates and generate chart points
        sorted_dates = sorted(daily_progress.keys())
        for date in sorted_dates:
            accuracies = daily_progress[date]
            avg_accuracy = mean(accuracies) if accuracies else 0
            
            chart_data["labels"].append(date.strftime("%Y-%m-%d"))
            chart_data["datasets"][0]["data"].append(round(avg_accuracy, 2))
        
        return chart_data
    
    @staticmethod
    def generate_accuracy_trend_data(sessions: List[Dict]) -> Dict[str, Any]:
        """Generate accuracy trend analysis"""
        
        # Sort sessions by time
        sorted_sessions = sorted(sessions, key=lambda x: x.get('started_at', datetime.now()))
        
        chart_data = {
            "labels": [],
            "datasets": [
                {
                    "label": "Session Accuracy",
                    "data": [],
                    "borderColor": "rgb(255, 99, 132)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "type": "line"
                },
                {
                    "label": "Moving Average (5 sessions)",
                    "data": [],
                    "borderColor": "rgb(54, 162, 235)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "type": "line"
                }
            ]
        }
        
        accuracies = []
        moving_averages = []
        
        for i, session in enumerate(sorted_sessions):
            accuracy = session.get('progress', {}).get('accuracy_rate', 0)
            accuracies.append(accuracy)
            
            # Calculate moving average
            window_size = min(5, i + 1)
            moving_avg = mean(accuracies[-window_size:])
            moving_averages.append(moving_avg)
            
            chart_data["labels"].append(f"Session {i + 1}")
            chart_data["datasets"][0]["data"].append(round(accuracy, 2))
            chart_data["datasets"][1]["data"].append(round(moving_avg, 2))
        
        return chart_data
    
    @staticmethod
    def generate_study_time_distribution(sessions: List[Dict]) -> Dict[str, Any]:
        """Generate study time distribution chart"""
        
        # Group by hour of day
        hourly_study_time = defaultdict(float)
        
        for session in sessions:
            if session.get('started_at'):
                hour = session['started_at'].hour
                duration = session.get('progress', {}).get('total_time', 0) / 60  # Convert to minutes
                hourly_study_time[hour] += duration
        
        chart_data = {
            "labels": [f"{h:02d}:00" for h in range(24)],
            "datasets": [{
                "label": "Study Time (minutes)",
                "data": [round(hourly_study_time.get(h, 0), 2) for h in range(24)],
                "backgroundColor": "rgba(153, 102, 255, 0.2)",
                "borderColor": "rgb(153, 102, 255)",
                "borderWidth": 1
            }]
        }
        
        return chart_data
    
    @staticmethod
    def generate_deck_performance_data(sessions: List[Dict], deck_info: Dict) -> Dict[str, Any]:
        """Generate deck performance comparison"""
        
        deck_performance = defaultdict(lambda: {"sessions": 0, "total_accuracy": 0, "total_time": 0})
        
        for session in sessions:
            deck_id = session.get('deck_id')
            if deck_id:
                deck_performance[deck_id]["sessions"] += 1
                deck_performance[deck_id]["total_accuracy"] += session.get('progress', {}).get('accuracy_rate', 0)
                deck_performance[deck_id]["total_time"] += session.get('progress', {}).get('total_time', 0)
        
        chart_data = {
            "labels": [],
            "datasets": [
                {
                    "label": "Average Accuracy (%)",
                    "data": [],
                    "backgroundColor": "rgba(255, 206, 86, 0.2)",
                    "borderColor": "rgb(255, 206, 86)",
                    "yAxisID": "y"
                },
                {
                    "label": "Total Study Time (minutes)",
                    "data": [],
                    "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    "borderColor": "rgb(75, 192, 192)",
                    "yAxisID": "y1"
                }
            ]
        }
        
        for deck_id, performance in deck_performance.items():
            deck_name = deck_info.get(deck_id, f"Deck {deck_id[:8]}...")
            avg_accuracy = performance["total_accuracy"] / performance["sessions"] if performance["sessions"] > 0 else 0
            total_time_minutes = performance["total_time"] / 60
            
            chart_data["labels"].append(deck_name)
            chart_data["datasets"][0]["data"].append(round(avg_accuracy, 2))
            chart_data["datasets"][1]["data"].append(round(total_time_minutes, 2))
        
        return chart_data
    
    @staticmethod
    def generate_srs_effectiveness_data(progress_records: List[Dict]) -> Dict[str, Any]:
        """Generate SRS effectiveness analysis"""
        
        # Analyze interval success rates
        interval_performance = defaultdict(lambda: {"total": 0, "success": 0})
        
        for record in progress_records:
            quality_history = record.get('quality_history', [])
            
            for i, entry in enumerate(quality_history):
                if i > 0:  # Skip first entry
                    prev_interval = record.get('interval', 1)
                    quality = entry.get('quality', 0)
                    
                    interval_range = ChartDataGenerator._get_interval_range(prev_interval)
                    interval_performance[interval_range]["total"] += 1
                    
                    if quality >= 3:  # Success if quality >= 3
                        interval_performance[interval_range]["success"] += 1
        
        chart_data = {
            "labels": [],
            "datasets": [{
                "label": "Success Rate (%)",
                "data": [],
                "backgroundColor": "rgba(255, 159, 64, 0.2)",
                "borderColor": "rgb(255, 159, 64)",
                "borderWidth": 1
            }]
        }
        
        # Sort intervals and calculate success rates
        sorted_intervals = sorted(interval_performance.keys())
        for interval_range in sorted_intervals:
            perf = interval_performance[interval_range]
            success_rate = (perf["success"] / perf["total"] * 100) if perf["total"] > 0 else 0
            
            chart_data["labels"].append(interval_range)
            chart_data["datasets"][0]["data"].append(round(success_rate, 2))
        
        return chart_data
    
    @staticmethod
    def _get_interval_range(interval: int) -> str:
        """Get interval range label"""
        if interval <= 1:
            return "1 day"
        elif interval <= 3:
            return "2-3 days"
        elif interval <= 7:
            return "4-7 days"
        elif interval <= 14:
            return "1-2 weeks"
        elif interval <= 30:
            return "2-4 weeks"
        else:
            return "1+ months"


class LearningPatternAnalyzer:
    """Analyze learning patterns and generate insights"""
    
    @staticmethod
    async def analyze_optimal_study_times(sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze optimal study times"""
        
        hourly_performance = defaultdict(lambda: {"sessions": 0, "total_accuracy": 0})
        
        for session in sessions:
            if session.get('started_at'):
                hour = session['started_at'].hour
                accuracy = session.get('progress', {}).get('accuracy_rate', 0)
                
                hourly_performance[hour]["sessions"] += 1
                hourly_performance[hour]["total_accuracy"] += accuracy
        
        # Calculate average accuracy by hour
        optimal_hours = []
        for hour in range(24):
            if hourly_performance[hour]["sessions"] > 0:
                avg_accuracy = hourly_performance[hour]["total_accuracy"] / hourly_performance[hour]["sessions"]
                optimal_hours.append({
                    "hour": hour,
                    "average_accuracy": avg_accuracy,
                    "session_count": hourly_performance[hour]["sessions"]
                })
        
        # Sort by accuracy and get top performing hours
        optimal_hours.sort(key=lambda x: x["average_accuracy"], reverse=True)
        
        return {
            "optimal_hours": optimal_hours[:3],  # Top 3 hours
            "analysis": {
                "best_hour": optimal_hours[0]["hour"] if optimal_hours else None,
                "peak_performance": optimal_hours[0]["average_accuracy"] if optimal_hours else 0,
                "recommendation": LearningPatternAnalyzer._generate_time_recommendation(optimal_hours)
            }
        }
    
    @staticmethod
    def analyze_difficulty_progression(progress_records: List[Dict]) -> Dict[str, Any]:
        """Analyze difficulty progression patterns"""
        
        difficulty_trends = defaultdict(lambda: {"total_quality": 0, "count": 0, "intervals": []})
        
        for record in progress_records:
            # Get card difficulty (could be from flashcard metadata)
            difficulty = "medium"  # Default, could be enhanced with actual card difficulty
            
            quality_history = record.get('quality_history', [])
            interval = record.get('interval', 1)
            
            if quality_history:
                avg_quality = mean([entry.get('quality', 0) for entry in quality_history])
                
                difficulty_trends[difficulty]["total_quality"] += avg_quality
                difficulty_trends[difficulty]["count"] += 1
                difficulty_trends[difficulty]["intervals"].append(interval)
        
        analysis = {}
        for difficulty, data in difficulty_trends.items():
            if data["count"] > 0:
                avg_quality = data["total_quality"] / data["count"]
                avg_interval = mean(data["intervals"]) if data["intervals"] else 0
                
                analysis[difficulty] = {
                    "average_quality": avg_quality,
                    "average_interval": avg_interval,
                    "card_count": data["count"],
                    "retention_score": avg_quality * avg_interval  # Combined metric
                }
        
        return {
            "difficulty_analysis": analysis,
            "recommendations": LearningPatternAnalyzer._generate_difficulty_recommendations(analysis)
        }
    
    @staticmethod
    def calculate_retention_rates(progress_records: List[Dict]) -> Dict[str, Any]:
        """Calculate retention rates over different time periods"""
        
        retention_analysis = {
            "24_hours": {"total": 0, "retained": 0},
            "1_week": {"total": 0, "retained": 0},
            "1_month": {"total": 0, "retained": 0}
        }
        
        now = datetime.utcnow()
        
        for record in progress_records:
            last_studied = record.get('last_studied')
            quality_history = record.get('quality_history', [])
            
            if last_studied and quality_history:
                time_diff = now - last_studied
                last_quality = quality_history[-1].get('quality', 0) if quality_history else 0
                
                # 24 hours retention
                if time_diff >= timedelta(hours=24):
                    retention_analysis["24_hours"]["total"] += 1
                    if last_quality >= 3:
                        retention_analysis["24_hours"]["retained"] += 1
                
                # 1 week retention
                if time_diff >= timedelta(weeks=1):
                    retention_analysis["1_week"]["total"] += 1
                    if last_quality >= 3:
                        retention_analysis["1_week"]["retained"] += 1
                
                # 1 month retention
                if time_diff >= timedelta(days=30):
                    retention_analysis["1_month"]["total"] += 1
                    if last_quality >= 3:
                        retention_analysis["1_month"]["retained"] += 1
        
        # Calculate retention rates
        retention_rates = {}
        for period, data in retention_analysis.items():
            rate = (data["retained"] / data["total"] * 100) if data["total"] > 0 else 0
            retention_rates[period] = {
                "rate": round(rate, 2),
                "retained": data["retained"],
                "total": data["total"]
            }
        
        return {
            "retention_rates": retention_rates,
            "overall_retention": round(mean([r["rate"] for r in retention_rates.values()]), 2)
        }
    
    @staticmethod
    def analyze_study_mode_effectiveness(sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze effectiveness of different study modes"""
        
        mode_performance = defaultdict(lambda: {
            "sessions": 0,
            "total_accuracy": 0,
            "total_time": 0,
            "total_cards": 0
        })
        
        for session in sessions:
            mode = session.get('study_mode', 'unknown')
            progress = session.get('progress', {})
            
            mode_performance[mode]["sessions"] += 1
            mode_performance[mode]["total_accuracy"] += progress.get('accuracy_rate', 0)
            mode_performance[mode]["total_time"] += progress.get('total_time', 0)
            mode_performance[mode]["total_cards"] += progress.get('cards_studied', 0)
        
        effectiveness_analysis = {}
        for mode, data in mode_performance.items():
            if data["sessions"] > 0:
                avg_accuracy = data["total_accuracy"] / data["sessions"]
                avg_time = data["total_time"] / data["sessions"]
                avg_cards = data["total_cards"] / data["sessions"]
                efficiency = avg_cards / (avg_time / 60) if avg_time > 0 else 0  # Cards per minute
                
                effectiveness_analysis[mode] = {
                    "session_count": data["sessions"],
                    "average_accuracy": round(avg_accuracy, 2),
                    "average_time_seconds": round(avg_time, 2),
                    "average_cards_studied": round(avg_cards, 2),
                    "efficiency_cards_per_minute": round(efficiency, 2),
                    "effectiveness_score": round(avg_accuracy * efficiency, 2)
                }
        
        return {
            "mode_analysis": effectiveness_analysis,
            "recommendations": LearningPatternAnalyzer._generate_mode_recommendations(effectiveness_analysis)
        }
    
    @staticmethod
    def _generate_time_recommendation(optimal_hours: List[Dict]) -> str:
        """Generate time-based study recommendations"""
        if not optimal_hours:
            return "Insufficient data for time recommendations"
        
        best_hour = optimal_hours[0]["hour"]
        
        if 6 <= best_hour <= 10:
            return "Morning study sessions show best performance. Consider studying between 6-10 AM."
        elif 14 <= best_hour <= 18:
            return "Afternoon sessions are most effective. Try studying between 2-6 PM."
        elif 19 <= best_hour <= 22:
            return "Evening study sessions work well for you. Schedule sessions between 7-10 PM."
        else:
            return f"Your peak performance is at {best_hour}:00. Consider scheduling study sessions around this time."
    
    @staticmethod
    def _generate_difficulty_recommendations(analysis: Dict) -> List[str]:
        """Generate difficulty-based recommendations"""
        recommendations = []
        
        if analysis:
            # Find best performing difficulty
            best_difficulty = max(analysis.keys(), key=lambda x: analysis[x]["retention_score"])
            recommendations.append(f"Focus on {best_difficulty} difficulty cards for optimal retention.")
            
            # Check for struggling areas
            for difficulty, data in analysis.items():
                if data["average_quality"] < 3:
                    recommendations.append(f"Consider more practice with {difficulty} cards (low quality scores).")
        
        return recommendations or ["Continue with current difficulty progression."]
    
    @staticmethod
    def _generate_mode_recommendations(analysis: Dict) -> List[str]:
        """Generate study mode recommendations"""
        recommendations = []
        
        if analysis:
            # Find most effective mode
            best_mode = max(analysis.keys(), key=lambda x: analysis[x]["effectiveness_score"])
            recommendations.append(f"{best_mode.title()} mode shows highest effectiveness for you.")
            
            # Find most efficient mode
            most_efficient = max(analysis.keys(), key=lambda x: analysis[x]["efficiency_cards_per_minute"])
            if most_efficient != best_mode:
                recommendations.append(f"Use {most_efficient.title()} mode for quick review sessions.")
            
            # Check for underperforming modes
            for mode, data in analysis.items():
                if data["average_accuracy"] < 50:
                    recommendations.append(f"Consider additional practice before using {mode.title()} mode.")
        
        return recommendations or ["Continue with current study mode mix."]


class AnalyticsService:
    """Main analytics service for data aggregation and insights"""
    
    def __init__(self):
        self.db = None
        self.chart_generator = ChartDataGenerator()
        self.pattern_analyzer = LearningPatternAnalyzer()
    
    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()
    
    async def get_progress_chart_data(
        self,
        user_id: str,
        days: int = 30,
        deck_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get progress over time chart data"""
        await self.initialize()
        
        try:
            # Build query
            query = {
                "user_id": user_id,
                "started_at": {"$gte": datetime.utcnow() - timedelta(days=days)}
            }
            
            if deck_id:
                query["deck_id"] = deck_id
            
            # Get sessions
            sessions = await self.db.study_sessions.find(query).to_list(length=None)
            
            # Generate chart data
            chart_data = self.chart_generator.generate_progress_chart_data(sessions)
            
            return {
                "chart_data": chart_data,
                "metadata": {
                    "period_days": days,
                    "session_count": len(sessions),
                    "deck_id": deck_id,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating progress chart data: {str(e)}")
            raise
    
    async def get_accuracy_trend_data(
        self,
        user_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get accuracy trend analysis"""
        await self.initialize()
        
        try:
            # Get recent sessions
            sessions = await self.db.study_sessions.find({
                "user_id": user_id,
                "status": SessionStatus.COMPLETED.value
            }).sort("started_at", -1).limit(limit).to_list(length=limit)
            
            # Reverse to get chronological order
            sessions.reverse()
            
            # Generate trend data
            chart_data = self.chart_generator.generate_accuracy_trend_data(sessions)
            
            return {
                "chart_data": chart_data,
                "metadata": {
                    "session_count": len(sessions),
                    "trend_analysis": self._analyze_trend(sessions),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating accuracy trend data: {str(e)}")
            raise
    
    async def get_study_time_distribution(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get study time distribution by hour"""
        await self.initialize()
        
        try:
            # Get sessions in time period
            sessions = await self.db.study_sessions.find({
                "user_id": user_id,
                "started_at": {"$gte": datetime.utcnow() - timedelta(days=days)}
            }).to_list(length=None)
            
            # Generate distribution data
            chart_data = self.chart_generator.generate_study_time_distribution(sessions)
            
            # Analyze patterns
            patterns = await self.pattern_analyzer.analyze_optimal_study_times(sessions)
            
            return {
                "chart_data": chart_data,
                "patterns": patterns,
                "metadata": {
                    "period_days": days,
                    "session_count": len(sessions),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating study time distribution: {str(e)}")
            raise
    
    async def get_deck_performance_comparison(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get deck performance comparison"""
        await self.initialize()
        
        try:
            # Get sessions
            sessions = await self.db.study_sessions.find({
                "user_id": user_id,
                "started_at": {"$gte": datetime.utcnow() - timedelta(days=days)}
            }).to_list(length=None)
            
            # Get deck information
            deck_ids = list(set(session.get('deck_id') for session in sessions if session.get('deck_id')))
            decks = await self.db.decks.find({"_id": {"$in": [ObjectId(deck_id) for deck_id in deck_ids]}}).to_list(length=None)
            
            deck_info = {str(deck["_id"]): deck.get("title", "Unknown Deck") for deck in decks}
            
            # Generate comparison data
            chart_data = self.chart_generator.generate_deck_performance_data(sessions, deck_info)
            
            return {
                "chart_data": chart_data,
                "deck_info": deck_info,
                "metadata": {
                    "period_days": days,
                    "deck_count": len(deck_ids),
                    "session_count": len(sessions),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating deck performance data: {str(e)}")
            raise
    
    async def get_srs_effectiveness_analysis(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get SRS effectiveness analysis"""
        await self.initialize()
        
        try:
            # Get progress records with quality history
            progress_records = await self.db.user_flashcard_progress.find({
                "user_id": user_id,
                "quality_history": {"$exists": True, "$ne": []}
            }).to_list(length=None)
            
            # Generate SRS analysis
            chart_data = self.chart_generator.generate_srs_effectiveness_data(progress_records)
            
            # Calculate retention rates
            retention_analysis = self.pattern_analyzer.calculate_retention_rates(progress_records)
            
            return {
                "chart_data": chart_data,
                "retention_analysis": retention_analysis,
                "metadata": {
                    "card_count": len(progress_records),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating SRS effectiveness data: {str(e)}")
            raise
    
    async def get_comprehensive_insights(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive learning insights"""
        await self.initialize()
        
        try:
            # Get data
            sessions = await self.db.study_sessions.find({
                "user_id": user_id,
                "started_at": {"$gte": datetime.utcnow() - timedelta(days=days)}
            }).to_list(length=None)
            
            progress_records = await self.db.user_flashcard_progress.find({
                "user_id": user_id
            }).to_list(length=None)
            
            # Generate all analyses
            time_patterns = await self.pattern_analyzer.analyze_optimal_study_times(sessions)
            difficulty_analysis = self.pattern_analyzer.analyze_difficulty_progression(progress_records)
            mode_effectiveness = self.pattern_analyzer.analyze_study_mode_effectiveness(sessions)
            retention_rates = self.pattern_analyzer.calculate_retention_rates(progress_records)
            
            return {
                "time_patterns": time_patterns,
                "difficulty_analysis": difficulty_analysis,
                "mode_effectiveness": mode_effectiveness,
                "retention_analysis": retention_rates,
                "metadata": {
                    "period_days": days,
                    "session_count": len(sessions),
                    "card_count": len(progress_records),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive insights: {str(e)}")
            raise
    
    def _analyze_trend(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Analyze accuracy trend direction"""
        if len(sessions) < 2:
            return {"trend": "insufficient_data"}
        
        accuracies = [s.get('progress', {}).get('accuracy_rate', 0) for s in sessions]
        
        # Simple linear trend analysis
        recent_avg = mean(accuracies[-5:]) if len(accuracies) >= 5 else mean(accuracies)
        early_avg = mean(accuracies[:5]) if len(accuracies) >= 5 else mean(accuracies[:len(accuracies)//2])
        
        if recent_avg > early_avg + 5:
            trend = "improving"
        elif recent_avg < early_avg - 5:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "recent_average": round(recent_avg, 2),
            "early_average": round(early_avg, 2),
            "improvement": round(recent_avg - early_avg, 2)
        }


# Create service instance
analytics_service = AnalyticsService()
