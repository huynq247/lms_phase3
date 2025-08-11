"""
User profile service for managing extended profile features.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import User
from app.models.profile import (
    UserProfileResponse,
    UserProfileUpdate,
    LearningGoal,
    StudySession,
    LearningPreferences,
    StudyStatistics
)


class ProfileService:
    """Service for managing user profiles."""
    
    def __init__(self, db):
        self.db = db
        self.users_collection = db.users
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """Get user profile with extended features."""
        try:
            user_data = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user_data:
                return None
            
            # Convert ObjectId to string for response
            user_data["_id"] = str(user_data["_id"])
            
            # Ensure extended fields exist with defaults
            user_data.setdefault("learning_preferences", None)
            user_data.setdefault("learning_goals", [])
            user_data.setdefault("study_schedule", [])
            user_data.setdefault("achievements", [])
            user_data.setdefault("study_statistics", {
                "total_study_time_minutes": 0,
                "total_cards_studied": 0,
                "total_decks_created": 0,
                "current_streak_days": 0,
                "longest_streak_days": 0,
                "accuracy_percentage": 0.0,
                "last_study_date": None
            })
            
            return UserProfileResponse(**user_data)
            
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    async def update_user_profile(
        self, 
        user_id: str, 
        profile_update: UserProfileUpdate
    ) -> Optional[UserProfileResponse]:
        """Update user profile with extended features."""
        try:
            update_data = {}
            
            # Basic profile fields
            if profile_update.first_name is not None:
                update_data["first_name"] = profile_update.first_name
            if profile_update.last_name is not None:
                update_data["last_name"] = profile_update.last_name
            if profile_update.avatar_url is not None:
                update_data["avatar_url"] = profile_update.avatar_url
            
            # Extended profile fields
            if profile_update.learning_preferences is not None:
                update_data["learning_preferences"] = profile_update.learning_preferences.model_dump()
            if profile_update.learning_goals is not None:
                update_data["learning_goals"] = [goal.model_dump() for goal in profile_update.learning_goals]
            if profile_update.study_schedule is not None:
                update_data["study_schedule"] = [session.model_dump() for session in profile_update.study_schedule]
            if profile_update.achievements is not None:
                update_data["achievements"] = [achievement.model_dump() for achievement in profile_update.achievements]
            if profile_update.study_statistics is not None:
                update_data["study_statistics"] = profile_update.study_statistics.model_dump()
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            if not update_data:
                # No fields to update, return current profile
                return await self.get_user_profile(user_id)
            
            # Update user document
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return None
    
    async def update_learning_goals(
        self, 
        user_id: str, 
        learning_goals: List[dict]  # Accept list of dicts directly
    ) -> Optional[UserProfileResponse]:
        """Update user's learning goals."""
        try:
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "learning_goals": learning_goals,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            print(f"Error updating learning goals: {e}")
            return None
    
    async def update_study_schedule(
        self, 
        user_id: str, 
        study_schedule: List[StudySession]
    ) -> Optional[UserProfileResponse]:
        """Update user's study schedule."""
        try:
            # Convert schedule to dict format for MongoDB
            schedule_data = []
            for session in study_schedule:
                session_dict = session.model_dump()
                # Convert time object to string for MongoDB storage
                if "start_time" in session_dict:
                    session_dict["start_time"] = session_dict["start_time"].strftime("%H:%M")
                schedule_data.append(session_dict)
            
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "study_schedule": schedule_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            print(f"Error updating study schedule: {e}")
            return None
    
    async def add_achievement(
        self, 
        user_id: str, 
        achievement_id: str,
        title: str,
        description: str,
        icon: str,
        category: str = "general"
    ) -> bool:
        """Add achievement to user profile."""
        try:
            # Check if achievement already exists
            user = await self.users_collection.find_one(
                {"_id": ObjectId(user_id)},
                {"achievements": 1}
            )
            
            if user and "achievements" in user:
                existing_achievements = [ach.get("id") for ach in user["achievements"]]
                if achievement_id in existing_achievements:
                    return True  # Achievement already exists
            
            # Add new achievement
            new_achievement = {
                "id": achievement_id,
                "title": title,
                "description": description,
                "icon": icon,
                "category": category,
                "unlocked_at": datetime.utcnow()
            }
            
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$push": {"achievements": new_achievement},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error adding achievement: {e}")
            return False
    
    async def update_study_statistics(
        self, 
        user_id: str, 
        stats_update: Dict[str, Any]
    ) -> bool:
        """Update user's study statistics."""
        try:
            # Prepare update data with dot notation for nested fields
            update_data = {}
            for key, value in stats_update.items():
                update_data[f"study_statistics.{key}"] = value
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating study statistics: {e}")
            return False
