"""
Progress Tracking & Analytics Service for Phase 6.4
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging

from app.core.deps import get_database
from app.models.study import StudyMode, SessionStatus

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Real-time progress tracking for study sessions"""
    
    @staticmethod
    def calculate_session_progress(session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate real-time session progress metrics"""
        try:
            answers = session_data.get("answers", [])
            cards_scheduled = session_data.get("cards_scheduled", [])
            started_at = session_data.get("started_at", datetime.utcnow())
            
            # Basic counters
            cards_completed = len(answers)
            cards_remaining = len(cards_scheduled) - cards_completed
            total_cards = len(cards_scheduled)
            
            # Time tracking
            time_elapsed = int((datetime.utcnow() - started_at).total_seconds())
            time_elapsed_minutes = time_elapsed // 60
            
            # Accuracy calculation
            correct_answers = sum(1 for answer in answers if answer.get("was_correct", False))
            accuracy_percentage = (correct_answers / cards_completed * 100) if cards_completed > 0 else 0.0
            
            # Current streak
            current_streak = 0
            for answer in reversed(answers):
                if answer.get("was_correct", False):
                    current_streak += 1
                else:
                    break
            
            # Session completion percentage
            completion_percentage = (cards_completed / total_cards * 100) if total_cards > 0 else 0.0
            
            # Average response time
            response_times = [answer.get("response_time", 0) for answer in answers if answer.get("response_time")]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Quality score trend (last 5 answers)
            recent_qualities = [answer.get("quality", 3) for answer in answers[-5:]]
            avg_quality = sum(recent_qualities) / len(recent_qualities) if recent_qualities else 3.0
            
            # Learning velocity (cards per minute)
            learning_velocity = cards_completed / time_elapsed_minutes if time_elapsed_minutes > 0 else 0.0
            
            return {
                "cards_completed": cards_completed,
                "cards_remaining": cards_remaining,
                "total_cards": total_cards,
                "time_elapsed_seconds": time_elapsed,
                "time_elapsed_minutes": time_elapsed_minutes,
                "accuracy_percentage": round(accuracy_percentage, 1),
                "current_streak": current_streak,
                "completion_percentage": round(completion_percentage, 1),
                "average_response_time": round(avg_response_time, 2),
                "average_quality": round(avg_quality, 1),
                "learning_velocity": round(learning_velocity, 2),
                "correct_answers": correct_answers,
                "incorrect_answers": cards_completed - correct_answers
            }
            
        except Exception as e:
            logger.error(f"Error calculating session progress: {str(e)}")
            raise


class HistoricalAnalytics:
    """Historical data analysis and trends"""
    
    def __init__(self):
        self.db = None
    
    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()
    
    async def get_session_history(
        self,
        user_id: str,
        limit: int = 20,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get user's session history with analytics"""
        await self.initialize()
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Query sessions
            sessions = await self.db.study_sessions.find({
                "user_id": user_id,
                "started_at": {"$gte": start_date, "$lte": end_date},
                "status": {"$in": [SessionStatus.COMPLETED.value, SessionStatus.ABANDONED.value]}
            }).sort("started_at", -1).limit(limit).to_list(length=limit)
            
            history = []
            for session in sessions:
                # Calculate session analytics
                progress = ProgressTracker.calculate_session_progress(session)
                
                session_summary = {
                    "session_id": str(session["_id"]),
                    "deck_id": session["deck_id"],
                    "study_mode": session["study_mode"],
                    "started_at": session["started_at"],
                    "completed_at": session.get("completed_at"),
                    "status": session["status"],
                    "duration_minutes": progress["time_elapsed_minutes"],
                    "cards_studied": progress["cards_completed"],
                    "accuracy": progress["accuracy_percentage"],
                    "average_response_time": progress["average_response_time"],
                    "best_streak": self._calculate_best_streak(session.get("answers", [])),
                    "performance_rating": self._calculate_performance_rating(progress["accuracy_percentage"])
                }
                
                history.append(session_summary)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}")
            raise
    
    async def get_user_statistics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        await self.initialize()
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Get all sessions in period
            sessions = await self.db.study_sessions.find({
                "user_id": user_id,
                "started_at": {"$gte": start_date, "$lte": end_date}
            }).to_list(length=None)
            
            # Calculate overall statistics
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s["status"] == SessionStatus.COMPLETED.value])
            abandoned_sessions = len([s for s in sessions if s["status"] == SessionStatus.ABANDONED.value])
            
            # Time statistics
            total_study_time = 0
            all_answers = []
            study_mode_counts = {}
            deck_usage = {}
            
            for session in sessions:
                if session.get("started_at") and session.get("completed_at"):
                    duration = (session["completed_at"] - session["started_at"]).total_seconds() / 60
                    total_study_time += duration
                
                # Collect answers
                all_answers.extend(session.get("answers", []))
                
                # Study mode preferences
                mode = session["study_mode"]
                study_mode_counts[mode] = study_mode_counts.get(mode, 0) + 1
                
                # Deck usage
                deck_id = session["deck_id"]
                deck_usage[deck_id] = deck_usage.get(deck_id, 0) + 1
            
            # Answer statistics
            total_cards_studied = len(all_answers)
            correct_answers = sum(1 for answer in all_answers if answer.get("was_correct", False))
            overall_accuracy = (correct_answers / total_cards_studied * 100) if total_cards_studied > 0 else 0.0
            
            # Response time statistics
            response_times = [answer.get("response_time", 0) for answer in all_answers if answer.get("response_time")]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Quality statistics
            qualities = [answer.get("quality", 3) for answer in all_answers if answer.get("quality")]
            avg_quality = sum(qualities) / len(qualities) if qualities else 3.0
            
            # Daily study streak
            daily_streak = await self._calculate_daily_streak(user_id)
            
            # Most used study mode
            preferred_mode = max(study_mode_counts, key=study_mode_counts.get) if study_mode_counts else None
            
            # Most studied deck
            top_deck = max(deck_usage, key=deck_usage.get) if deck_usage else None
            
            return {
                "period_days": days_back,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "abandoned_sessions": abandoned_sessions,
                "completion_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0.0,
                "total_study_time_minutes": round(total_study_time, 1),
                "total_cards_studied": total_cards_studied,
                "overall_accuracy": round(overall_accuracy, 1),
                "average_response_time": round(avg_response_time, 2),
                "average_quality": round(avg_quality, 1),
                "daily_study_streak": daily_streak,
                "preferred_study_mode": preferred_mode,
                "study_mode_distribution": study_mode_counts,
                "most_studied_deck": top_deck,
                "deck_usage_distribution": deck_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            raise
    
    async def get_progress_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data"""
        await self.initialize()
        
        try:
            # Get statistics for different periods
            weekly_stats = await self.get_user_statistics(user_id, days_back=7)
            monthly_stats = await self.get_user_statistics(user_id, days_back=30)
            
            # Get deck mastery progress
            deck_mastery = await self._get_deck_mastery_progress(user_id)
            
            # Get SRS scheduling overview
            srs_overview = await self._get_srs_overview(user_id)
            
            # Get recent achievements
            achievements = await self._get_recent_achievements(user_id)
            
            # Get study pattern analysis
            study_patterns = await self._analyze_study_patterns(user_id)
            
            return {
                "weekly_stats": weekly_stats,
                "monthly_stats": monthly_stats,
                "deck_mastery": deck_mastery,
                "srs_overview": srs_overview,
                "achievements": achievements,
                "study_patterns": study_patterns,
                "dashboard_generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating progress dashboard: {str(e)}")
            raise
    
    def _calculate_best_streak(self, answers: List[Dict[str, Any]]) -> int:
        """Calculate best streak from answers"""
        best_streak = 0
        current_streak = 0
        
        for answer in answers:
            if answer.get("was_correct", False):
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0
        
        return best_streak
    
    def _calculate_performance_rating(self, accuracy: float) -> str:
        """Calculate performance rating based on accuracy"""
        if accuracy >= 90:
            return "excellent"
        elif accuracy >= 80:
            return "good"
        elif accuracy >= 60:
            return "fair"
        else:
            return "needs_improvement"
    
    async def _calculate_daily_streak(self, user_id: str) -> int:
        """Calculate consecutive daily study streak"""
        try:
            today = datetime.utcnow().date()
            streak = 0
            current_date = today
            
            for i in range(365):  # Check up to 1 year back
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = day_start + timedelta(days=1)
                
                # Check if user studied on this day
                sessions_count = await self.db.study_sessions.count_documents({
                    "user_id": user_id,
                    "started_at": {"$gte": day_start, "$lt": day_end},
                    "status": {"$in": [SessionStatus.COMPLETED.value, SessionStatus.ABANDONED.value]}
                })
                
                if sessions_count > 0:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating daily streak: {str(e)}")
            return 0
    
    async def _get_deck_mastery_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Get mastery progress for all user's decks"""
        try:
            # Get user's progress across all decks
            progress_records = await self.db.user_flashcard_progress.find({
                "user_id": user_id
            }).to_list(length=None)
            
            # Group by deck
            deck_progress = {}
            for progress in progress_records:
                flashcard = await self.db.flashcards.find_one({"_id": ObjectId(progress["flashcard_id"])})
                if not flashcard:
                    continue
                
                deck_id = flashcard["deck_id"]
                if deck_id not in deck_progress:
                    deck_progress[deck_id] = {
                        "total_cards": 0,
                        "studied_cards": 0,
                        "mastered_cards": 0,
                        "average_ease_factor": 0,
                        "total_ease_factor": 0
                    }
                
                deck_progress[deck_id]["studied_cards"] += 1
                deck_progress[deck_id]["total_ease_factor"] += progress.get("ease_factor", 2.5)
                
                # Consider mastered if EF > 2.5 and repetitions > 2
                if progress.get("ease_factor", 0) > 2.5 and progress.get("repetitions", 0) > 2:
                    deck_progress[deck_id]["mastered_cards"] += 1
            
            # Get total cards per deck and calculate percentages
            mastery_data = []
            for deck_id, progress in deck_progress.items():
                total_cards_in_deck = await self.db.flashcards.count_documents({"deck_id": deck_id})
                
                deck_info = await self.db.decks.find_one({"_id": ObjectId(deck_id)})
                
                progress["total_cards"] = total_cards_in_deck
                progress["average_ease_factor"] = progress["total_ease_factor"] / progress["studied_cards"] if progress["studied_cards"] > 0 else 2.5
                
                mastery_data.append({
                    "deck_id": deck_id,
                    "deck_title": deck_info.get("title", "Unknown") if deck_info else "Unknown",
                    "total_cards": total_cards_in_deck,
                    "studied_cards": progress["studied_cards"],
                    "mastered_cards": progress["mastered_cards"],
                    "study_percentage": round(progress["studied_cards"] / total_cards_in_deck * 100, 1) if total_cards_in_deck > 0 else 0.0,
                    "mastery_percentage": round(progress["mastered_cards"] / total_cards_in_deck * 100, 1) if total_cards_in_deck > 0 else 0.0,
                    "average_ease_factor": round(progress["average_ease_factor"], 2)
                })
            
            return mastery_data
            
        except Exception as e:
            logger.error(f"Error getting deck mastery progress: {str(e)}")
            return []
    
    async def _get_srs_overview(self, user_id: str) -> Dict[str, Any]:
        """Get SRS scheduling overview"""
        try:
            now = datetime.utcnow()
            today = now.date()
            tomorrow = today + timedelta(days=1)
            week_later = today + timedelta(days=7)
            
            # Count cards by review status
            overdue_count = await self.db.user_flashcard_progress.count_documents({
                "user_id": user_id,
                "next_review": {"$lt": now}
            })
            
            due_today_count = await self.db.user_flashcard_progress.count_documents({
                "user_id": user_id,
                "next_review": {
                    "$gte": datetime.combine(today, datetime.min.time()),
                    "$lt": datetime.combine(tomorrow, datetime.min.time())
                }
            })
            
            due_tomorrow_count = await self.db.user_flashcard_progress.count_documents({
                "user_id": user_id,
                "next_review": {
                    "$gte": datetime.combine(tomorrow, datetime.min.time()),
                    "$lt": datetime.combine(tomorrow + timedelta(days=1), datetime.min.time())
                }
            })
            
            due_this_week_count = await self.db.user_flashcard_progress.count_documents({
                "user_id": user_id,
                "next_review": {
                    "$gte": datetime.combine(tomorrow, datetime.min.time()),
                    "$lt": datetime.combine(week_later, datetime.min.time())
                }
            })
            
            total_cards_in_srs = await self.db.user_flashcard_progress.count_documents({
                "user_id": user_id
            })
            
            return {
                "total_cards_in_srs": total_cards_in_srs,
                "overdue_cards": overdue_count,
                "due_today": due_today_count,
                "due_tomorrow": due_tomorrow_count,
                "due_this_week": due_this_week_count,
                "review_load": overdue_count + due_today_count
            }
            
        except Exception as e:
            logger.error(f"Error getting SRS overview: {str(e)}")
            return {}
    
    async def _get_recent_achievements(self, user_id: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """Get recent achievements and milestones"""
        try:
            # This is a simplified version - you can expand with more sophisticated achievement tracking
            achievements = []
            
            # Check for study streak achievements
            daily_streak = await self._calculate_daily_streak(user_id)
            if daily_streak >= 7:
                achievements.append({
                    "type": "study_streak",
                    "title": f"{daily_streak} Day Study Streak",
                    "description": f"Studied for {daily_streak} consecutive days",
                    "icon": "🔥",
                    "achieved_at": datetime.utcnow()
                })
            
            # Check for cards studied milestone
            week_stats = await self.get_user_statistics(user_id, days_back=7)
            cards_this_week = week_stats.get("total_cards_studied", 0)
            if cards_this_week >= 100:
                achievements.append({
                    "type": "cards_milestone",
                    "title": "Century Scholar",
                    "description": f"Studied {cards_this_week} cards this week",
                    "icon": "📚",
                    "achieved_at": datetime.utcnow()
                })
            
            # Check for accuracy achievements
            accuracy = week_stats.get("overall_accuracy", 0)
            if accuracy >= 90:
                achievements.append({
                    "type": "accuracy_milestone",
                    "title": "Precision Master",
                    "description": f"Achieved {accuracy:.1f}% accuracy this week",
                    "icon": "🎯",
                    "achieved_at": datetime.utcnow()
                })
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error getting recent achievements: {str(e)}")
            return []
    
    async def _analyze_study_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's study patterns"""
        try:
            # Get recent sessions for pattern analysis
            recent_sessions = await self.db.study_sessions.find({
                "user_id": user_id,
                "started_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }).to_list(length=None)
            
            # Analyze study times (hour of day)
            hour_distribution = {}
            day_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}  # Monday=0, Sunday=6
            
            for session in recent_sessions:
                if session.get("started_at"):
                    hour = session["started_at"].hour
                    day = session["started_at"].weekday()
                    
                    hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
                    day_distribution[day] += 1
            
            # Find peak study time
            peak_hour = max(hour_distribution, key=hour_distribution.get) if hour_distribution else None
            peak_day = max(day_distribution, key=day_distribution.get)
            
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            return {
                "peak_study_hour": peak_hour,
                "peak_study_day": day_names[peak_day],
                "hour_distribution": hour_distribution,
                "day_distribution": {day_names[k]: v for k, v in day_distribution.items()},
                "total_sessions_analyzed": len(recent_sessions)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing study patterns: {str(e)}")
            return {}


class AchievementSystem:
    """Achievement and milestone tracking system"""
    
    def __init__(self):
        self.db = None
    
    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()
    
    async def check_achievements(self, user_id: str, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for new achievements after session completion"""
        await self.initialize()
        
        achievements = []
        
        try:
            # Session-based achievements
            session_achievements = self._check_session_achievements(session_data)
            achievements.extend(session_achievements)
            
            # Cumulative achievements
            cumulative_achievements = await self._check_cumulative_achievements(user_id)
            achievements.extend(cumulative_achievements)
            
            # Save achievements to database (implement achievements collection)
            for achievement in achievements:
                await self._save_achievement(user_id, achievement)
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error checking achievements: {str(e)}")
            return []
    
    def _check_session_achievements(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check achievements based on single session performance"""
        achievements = []
        
        # Calculate session progress
        progress = ProgressTracker.calculate_session_progress(session_data)
        
        # Perfect session (100% accuracy)
        if progress["accuracy_percentage"] == 100.0 and progress["cards_completed"] >= 5:
            achievements.append({
                "type": "perfect_session",
                "title": "Flawless Victory",
                "description": f"Perfect accuracy on {progress['cards_completed']} cards",
                "icon": "⭐",
                "points": 50
            })
        
        # Speed demon (fast response times)
        if progress["average_response_time"] <= 3.0 and progress["cards_completed"] >= 10:
            achievements.append({
                "type": "speed_demon",
                "title": "Speed Demon",
                "description": f"Average response time of {progress['average_response_time']:.1f}s",
                "icon": "⚡",
                "points": 30
            })
        
        # Long study session
        if progress["time_elapsed_minutes"] >= 60:
            achievements.append({
                "type": "marathon_session",
                "title": "Marathon Learner",
                "description": f"Studied for {progress['time_elapsed_minutes']} minutes",
                "icon": "🏃",
                "points": 40
            })
        
        # High streak
        if progress["current_streak"] >= 20:
            achievements.append({
                "type": "streak_master",
                "title": "Streak Master",
                "description": f"Achieved {progress['current_streak']} correct answers in a row",
                "icon": "🔥",
                "points": 35
            })
        
        return achievements
    
    async def _check_cumulative_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Check achievements based on cumulative progress"""
        achievements = []
        
        try:
            # Total cards studied milestone
            total_progress = await self.db.user_flashcard_progress.count_documents({"user_id": user_id})
            
            milestones = [100, 500, 1000, 5000, 10000]
            for milestone in milestones:
                if total_progress >= milestone:
                    # Check if this achievement was already awarded
                    existing = await self.db.user_achievements.find_one({
                        "user_id": user_id,
                        "type": "cards_studied_milestone",
                        "milestone": milestone
                    })
                    
                    if not existing:
                        achievements.append({
                            "type": "cards_studied_milestone",
                            "title": f"Scholar Level {milestone}",
                            "description": f"Studied {milestone} flashcards",
                            "icon": "📚",
                            "points": milestone // 10,
                            "milestone": milestone
                        })
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error checking cumulative achievements: {str(e)}")
            return []
    
    async def _save_achievement(self, user_id: str, achievement: Dict[str, Any]):
        """Save achievement to database"""
        try:
            achievement_record = {
                "user_id": user_id,
                "type": achievement["type"],
                "title": achievement["title"],
                "description": achievement["description"],
                "icon": achievement["icon"],
                "points": achievement.get("points", 0),
                "achieved_at": datetime.utcnow(),
                "milestone": achievement.get("milestone")
            }
            
            # Create achievements collection if it doesn't exist
            await self.db.user_achievements.insert_one(achievement_record)
            
        except Exception as e:
            logger.error(f"Error saving achievement: {str(e)}")


# Create service instances
progress_tracker = ProgressTracker()
historical_analytics = HistoricalAnalytics()
achievement_system = AchievementSystem()
