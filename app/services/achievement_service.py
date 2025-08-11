"""
Achievement service for managing user achievements.
"""
from typing import Dict, List
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.profile import AchievementsResponse, Achievement
from app.services.profile_service import ProfileService


class AchievementService:
    """Service for managing user achievements."""
    
    def __init__(self, db):
        self.db = db
        self.users_collection = db.users
        self.profile_service = ProfileService(db)
    
    async def get_user_achievements(self, user_id: str) -> AchievementsResponse:
        """Get user achievements with category breakdown."""
        try:
            user = await self.users_collection.find_one(
                {"_id": ObjectId(user_id)},
                {"achievements": 1}
            )
            
            achievements = []
            if user and "achievements" in user:
                for ach_data in user["achievements"]:
                    achievements.append(Achievement(**ach_data))
            
            # Calculate category breakdown
            categories = {}
            for achievement in achievements:
                category = achievement.category
                categories[category] = categories.get(category, 0) + 1
            
            # Total available achievements (hardcoded for now)
            total_available = 15  # Profile, Goal, Schedule, Consistency, Volume, Accuracy achievements
            
            return AchievementsResponse(
                achievements=achievements,
                total_achievements=total_available,
                unlocked_count=len(achievements),
                categories=categories
            )
            
        except Exception as e:
            print(f"Error getting user achievements: {e}")
            return AchievementsResponse(
                achievements=[],
                total_achievements=15,
                unlocked_count=0,
                categories={}
            )
    
    async def check_and_award_profile_achievement(self, user_id: str) -> bool:
        """Award achievement for first profile update."""
        try:
            achievement_id = "profile_first_update"
            
            success = await self.profile_service.add_achievement(
                user_id=user_id,
                achievement_id=achievement_id,
                title="Profile Master",
                description="Updated your profile for the first time",
                icon="👤",
                category="profile"
            )
            
            return success
            
        except Exception as e:
            print(f"Error awarding profile achievement: {e}")
            return False
    
    async def check_and_award_goal_achievement(self, user_id: str) -> bool:
        """Award achievement for setting first learning goal."""
        try:
            achievement_id = "goal_first_set"
            
            success = await self.profile_service.add_achievement(
                user_id=user_id,
                achievement_id=achievement_id,
                title="Goal Setter",
                description="Set your first learning goal",
                icon="🎯",
                category="goals"
            )
            
            return success
            
        except Exception as e:
            print(f"Error awarding goal achievement: {e}")
            return False
    
    async def check_and_award_schedule_achievement(self, user_id: str) -> bool:
        """Award achievement for setting study schedule."""
        try:
            achievement_id = "schedule_first_set"
            
            success = await self.profile_service.add_achievement(
                user_id=user_id,
                achievement_id=achievement_id,
                title="Scheduler",
                description="Created your first study schedule",
                icon="📅",
                category="schedule"
            )
            
            return success
            
        except Exception as e:
            print(f"Error awarding schedule achievement: {e}")
            return False
    
    async def check_and_award_consistency_achievement(self, user_id: str, streak_days: int) -> bool:
        """Award achievement for study consistency."""
        try:
            achievement_id = None
            title = ""
            description = ""
            icon = "🔥"
            
            if streak_days >= 7:
                achievement_id = "consistency_week"
                title = "Week Warrior"
                description = "Studied for 7 days in a row"
            elif streak_days >= 30:
                achievement_id = "consistency_month"
                title = "Monthly Master"
                description = "Studied for 30 days in a row"
            elif streak_days >= 100:
                achievement_id = "consistency_hundred"
                title = "Century Scholar"
                description = "Studied for 100 days in a row"
            
            if achievement_id:
                success = await self.profile_service.add_achievement(
                    user_id=user_id,
                    achievement_id=achievement_id,
                    title=title,
                    description=description,
                    icon=icon,
                    category="consistency"
                )
                return success
            
            return False
            
        except Exception as e:
            print(f"Error awarding consistency achievement: {e}")
            return False
    
    async def check_and_award_volume_achievement(self, user_id: str, cards_studied: int) -> bool:
        """Award achievement for study volume."""
        try:
            achievement_id = None
            title = ""
            description = ""
            icon = "📚"
            
            if cards_studied >= 100:
                achievement_id = "volume_hundred"
                title = "Card Collector"
                description = "Studied 100 flashcards"
            elif cards_studied >= 500:
                achievement_id = "volume_five_hundred"
                title = "Knowledge Seeker"
                description = "Studied 500 flashcards"
            elif cards_studied >= 1000:
                achievement_id = "volume_thousand"
                title = "Learning Legend"
                description = "Studied 1000 flashcards"
            
            if achievement_id:
                success = await self.profile_service.add_achievement(
                    user_id=user_id,
                    achievement_id=achievement_id,
                    title=title,
                    description=description,
                    icon=icon,
                    category="volume"
                )
                return success
            
            return False
            
        except Exception as e:
            print(f"Error awarding volume achievement: {e}")
            return False
    
    async def check_and_award_accuracy_achievement(self, user_id: str, accuracy: float) -> bool:
        """Award achievement for high accuracy."""
        try:
            achievement_id = None
            title = ""
            description = ""
            icon = "🎯"
            
            if accuracy >= 80.0:
                achievement_id = "accuracy_eighty"
                title = "Sharp Shooter"
                description = "Achieved 80% accuracy"
            elif accuracy >= 90.0:
                achievement_id = "accuracy_ninety"
                title = "Precision Pro"
                description = "Achieved 90% accuracy"
            elif accuracy >= 95.0:
                achievement_id = "accuracy_ninety_five"
                title = "Perfect Performer"
                description = "Achieved 95% accuracy"
            
            if achievement_id:
                success = await self.profile_service.add_achievement(
                    user_id=user_id,
                    achievement_id=achievement_id,
                    title=title,
                    description=description,
                    icon=icon,
                    category="accuracy"
                )
                return success
            
            return False
            
        except Exception as e:
            print(f"Error awarding accuracy achievement: {e}")
            return False
