"""
SM-2 Spaced Repetition Algorithm Implementation for Phase 6.3
Based on the original SuperMemo SM-2 algorithm
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class SM2Algorithm:
    """
    SM-2 Spaced Repetition Algorithm Implementation
    
    The SM-2 algorithm determines when to review flashcards based on:
    - Quality of recall (0-5 scale)
    - Ease Factor (E-Factor) 
    - Number of repetitions
    - Current interval
    """
    
    # SM-2 Algorithm Constants
    INITIAL_EASE_FACTOR = 2.5
    MINIMUM_EASE_FACTOR = 1.3
    MINIMUM_INTERVAL = 1
    
    @classmethod
    def calculate_next_review(
        cls,
        quality: int,
        current_ease_factor: float = INITIAL_EASE_FACTOR,
        current_interval: int = MINIMUM_INTERVAL,
        current_repetitions: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate next review parameters based on SM-2 algorithm
        
        Args:
            quality: Quality rating (0-5)
                0: Complete blackout
                1: Incorrect response; correct one remembered
                2: Incorrect response; correct one seemed easy to recall
                3: Correct response recalled with serious difficulty
                4: Correct response after hesitation
                5: Perfect response
            current_ease_factor: Current E-Factor (default: 2.5)
            current_interval: Current interval in days (default: 1)
            current_repetitions: Number of consecutive successful repetitions
        
        Returns:
            Dictionary with next review parameters:
            - ease_factor: New E-Factor
            - interval: Next interval in days
            - repetitions: New repetition count
            - next_review: Next review datetime
        """
        
        try:
            # Validate input parameters
            if not (0 <= quality <= 5):
                raise ValueError("Quality must be between 0 and 5")
            
            # Initialize return values
            new_ease_factor = current_ease_factor
            new_interval = current_interval
            new_repetitions = current_repetitions
            
            # SM-2 Algorithm Logic
            if quality < 3:
                # Poor recall (quality 0, 1, 2)
                # Reset repetitions and set interval to 1 day
                new_repetitions = 0
                new_interval = cls.MINIMUM_INTERVAL
                
                # Decrease ease factor for poor performance
                new_ease_factor = max(
                    cls.MINIMUM_EASE_FACTOR,
                    current_ease_factor - 0.2
                )
                
            else:
                # Good recall (quality 3, 4, 5)
                new_repetitions = current_repetitions + 1
                
                # Calculate new interval based on repetition count
                if new_repetitions == 1:
                    new_interval = 1
                elif new_repetitions == 2:
                    new_interval = 6
                else:
                    # For repetitions >= 3, use ease factor
                    new_interval = round(current_interval * current_ease_factor)
                
                # Update ease factor based on quality
                new_ease_factor = cls._calculate_new_ease_factor(
                    current_ease_factor, quality
                )
            
            # Ensure minimum values
            new_ease_factor = max(cls.MINIMUM_EASE_FACTOR, new_ease_factor)
            new_interval = max(cls.MINIMUM_INTERVAL, new_interval)
            
            # Calculate next review date
            next_review = datetime.utcnow() + timedelta(days=new_interval)
            
            result = {
                "ease_factor": round(new_ease_factor, 2),
                "interval": new_interval,
                "repetitions": new_repetitions,
                "next_review": next_review,
                "quality": quality,
                "algorithm_version": "SM-2"
            }
            
            logger.info(
                f"SM-2 calculation: Q={quality}, EF={new_ease_factor:.2f}, "
                f"I={new_interval}, R={new_repetitions}, Next={next_review.date()}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in SM-2 calculation: {str(e)}")
            raise
    
    @classmethod
    def _calculate_new_ease_factor(cls, current_ef: float, quality: int) -> float:
        """
        Calculate new ease factor based on quality rating
        
        Formula: EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        Where q is quality (0-5)
        """
        try:
            # SM-2 ease factor formula
            new_ef = current_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            
            # Ensure minimum ease factor
            return max(cls.MINIMUM_EASE_FACTOR, new_ef)
            
        except Exception as e:
            logger.error(f"Error calculating ease factor: {str(e)}")
            return current_ef
    
    @classmethod
    def get_due_cards_query(cls, user_id: str, current_time: datetime = None) -> Dict[str, Any]:
        """
        Generate MongoDB query for due cards
        
        Args:
            user_id: User ID
            current_time: Current time (default: now)
        
        Returns:
            MongoDB query for due cards
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        return {
            "user_id": user_id,
            "next_review": {"$lte": current_time}
        }
    
    @classmethod
    def get_overdue_priority_sort(cls) -> list:
        """
        Get sort criteria for prioritizing overdue cards
        
        Returns:
            MongoDB sort criteria (most overdue first)
        """
        return [("next_review", 1)]  # Oldest due date first
    
    @classmethod
    def calculate_overdue_days(cls, next_review: datetime, current_time: datetime = None) -> int:
        """
        Calculate how many days a card is overdue
        
        Args:
            next_review: Scheduled review date
            current_time: Current time (default: now)
        
        Returns:
            Number of days overdue (0 if not overdue)
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        if next_review <= current_time:
            delta = current_time - next_review
            return delta.days
        
        return 0
    
    @classmethod
    def is_card_due(cls, next_review: datetime, current_time: datetime = None) -> bool:
        """
        Check if a card is due for review
        
        Args:
            next_review: Scheduled review date
            current_time: Current time (default: now)
        
        Returns:
            True if card is due for review
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        return next_review <= current_time
    
    @classmethod
    def get_review_statistics(cls, progress_records: list) -> Dict[str, Any]:
        """
        Calculate review statistics from progress records
        
        Args:
            progress_records: List of user progress records
        
        Returns:
            Dictionary with review statistics
        """
        try:
            current_time = datetime.utcnow()
            
            total_cards = len(progress_records)
            due_cards = 0
            overdue_cards = 0
            total_overdue_days = 0
            
            for record in progress_records:
                next_review = record.get("next_review")
                if next_review and cls.is_card_due(next_review, current_time):
                    due_cards += 1
                    overdue_days = cls.calculate_overdue_days(next_review, current_time)
                    if overdue_days > 0:
                        overdue_cards += 1
                        total_overdue_days += overdue_days
            
            avg_overdue_days = total_overdue_days / overdue_cards if overdue_cards > 0 else 0
            
            return {
                "total_cards": total_cards,
                "due_cards": due_cards,
                "overdue_cards": overdue_cards,
                "avg_overdue_days": round(avg_overdue_days, 1),
                "due_percentage": round((due_cards / total_cards * 100), 1) if total_cards > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating review statistics: {str(e)}")
            return {
                "total_cards": 0,
                "due_cards": 0,
                "overdue_cards": 0,
                "avg_overdue_days": 0,
                "due_percentage": 0
            }


class SM2ProgressUpdater:
    """
    Handles updating user progress with SM-2 calculations
    """
    
    @staticmethod
    async def update_flashcard_progress(
        db,
        user_id: str,
        flashcard_id: str,
        quality: int,
        response_time: float
    ) -> Dict[str, Any]:
        """
        Update flashcard progress using SM-2 algorithm
        
        Args:
            db: Database connection
            user_id: User ID
            flashcard_id: Flashcard ID
            quality: Quality rating (0-5)
            response_time: Response time in seconds
        
        Returns:
            Updated progress data
        """
        try:
            # Get existing progress
            progress = await db.user_flashcard_progress.find_one({
                "user_id": user_id,
                "flashcard_id": flashcard_id
            })
            
            # Get current parameters
            current_ease_factor = progress.get("ease_factor", SM2Algorithm.INITIAL_EASE_FACTOR) if progress else SM2Algorithm.INITIAL_EASE_FACTOR
            current_interval = progress.get("interval", SM2Algorithm.MINIMUM_INTERVAL) if progress else SM2Algorithm.MINIMUM_INTERVAL
            current_repetitions = progress.get("repetitions", 0) if progress else 0
            
            # Calculate new SM-2 parameters
            sm2_result = SM2Algorithm.calculate_next_review(
                quality=quality,
                current_ease_factor=current_ease_factor,
                current_interval=current_interval,
                current_repetitions=current_repetitions
            )
            
            now = datetime.utcnow()
            
            # Prepare progress data
            progress_data = {
                "user_id": user_id,
                "flashcard_id": flashcard_id,
                "last_studied": now,
                "ease_factor": sm2_result["ease_factor"],
                "interval": sm2_result["interval"],
                "repetitions": sm2_result["repetitions"],
                "next_review": sm2_result["next_review"],
                "last_quality": quality,
                "times_studied": (progress.get("times_studied", 0) + 1) if progress else 1,
                "algorithm_version": sm2_result["algorithm_version"]
            }
            
            # Add to quality history
            quality_entry = {
                "quality": quality,
                "timestamp": now,
                "response_time": response_time,
                "ease_factor": sm2_result["ease_factor"],
                "interval": sm2_result["interval"],
                "repetitions": sm2_result["repetitions"]
            }
            
            if progress:
                # Update existing progress
                await db.user_flashcard_progress.update_one(
                    {"user_id": user_id, "flashcard_id": flashcard_id},
                    {
                        "$set": progress_data,
                        "$push": {"quality_history": quality_entry}
                    }
                )
            else:
                # Create new progress record
                progress_data["first_studied"] = now
                progress_data["quality_history"] = [quality_entry]
                
                await db.user_flashcard_progress.insert_one(progress_data)
            
            logger.info(f"Updated SM-2 progress for user {user_id}, card {flashcard_id}")
            return sm2_result
            
        except Exception as e:
            logger.error(f"Error updating SM-2 progress: {str(e)}")
            raise


# Create instances for easy import
sm2_algorithm = SM2Algorithm()
sm2_progress_updater = SM2ProgressUpdater()
