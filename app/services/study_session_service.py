"""
Study Session Management Service for Phase 6.1
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging

from app.core.deps import get_database
from app.models.study import (
    StudySession, StudySessionStartRequest, StudySessionResponse,
    FlashcardAnswerRequest, SessionAnswerResponse, StudyMode,
    SessionStatus, StudySessionProgress, FlashcardStudyResponse,
    SessionBreakRequest, SessionBreakResponse, SessionCompletionResponse
)
from app.models.user import User
from app.services.sm2_algorithm import SM2Algorithm, SM2ProgressUpdater

logger = logging.getLogger(__name__)


class StudyModeHandler:
    """Handles different study modes and card selection logic"""
    
    @staticmethod
    async def get_cards_for_mode(
        db,
        user_id: str,
        deck_id: str,
        mode: StudyMode,
        lesson_id: Optional[str] = None,
        target_cards: Optional[int] = None
    ) -> List[str]:
        """Get flashcard IDs based on study mode"""
        
        try:
            # Base query for deck cards
            query = {"deck_id": deck_id}
            
            # Filter by lesson if specified
            if lesson_id:
                query["lesson_id"] = lesson_id
            
            if mode == StudyMode.REVIEW:
                # SRS-based: only due cards using SM-2 algorithm
                current_time = datetime.utcnow()
                due_query = SM2Algorithm.get_due_cards_query(user_id, current_time)
                
                # Get all card IDs from deck first
                all_deck_card_ids = await _get_deck_card_ids(db, query)
                
                # Find due cards within this deck
                due_query["flashcard_id"] = {"$in": all_deck_card_ids}
                
                user_progress = await db.user_flashcard_progress.find(due_query).sort(
                    SM2Algorithm.get_overdue_priority_sort()
                ).to_list(length=target_cards)
                
                card_ids = [progress["flashcard_id"] for progress in user_progress]
                
                # If no due cards, get some new cards
                if not card_ids and target_cards:
                    studied_card_ids = {progress["flashcard_id"] for progress in await db.user_flashcard_progress.find({
                        "user_id": user_id,
                        "flashcard_id": {"$in": all_deck_card_ids}
                    }).to_list(length=None)}
                    
                    new_card_ids = [card_id for card_id in all_deck_card_ids if card_id not in studied_card_ids]
                    card_ids = new_card_ids[:target_cards] if target_cards else new_card_ids[:10]  # Limit to 10 new cards
                
            elif mode == StudyMode.PRACTICE:
                # Non-SRS: random selection from deck
                cards = await db.flashcards.find(query).to_list(length=None)
                import random
                random.shuffle(cards)
                card_ids = [str(card["_id"]) for card in cards[:target_cards]] if target_cards else [str(card["_id"]) for card in cards]
                
            elif mode == StudyMode.CRAM:
                # All cards in deck for rapid review
                cards = await db.flashcards.find(query).to_list(length=target_cards)
                card_ids = [str(card["_id"]) for card in cards]
                
            elif mode == StudyMode.TEST:
                # Assessment mode: random selection, no hints
                cards = await db.flashcards.find(query).to_list(length=None)
                import random
                random.shuffle(cards)
                card_ids = [str(card["_id"]) for card in cards[:target_cards]] if target_cards else [str(card["_id"]) for card in cards]
                
            elif mode == StudyMode.LEARN:
                # New cards only (never studied by user)
                all_card_ids = await _get_deck_card_ids(db, query)
                studied_cards = await db.user_flashcard_progress.find({
                    "user_id": user_id,
                    "flashcard_id": {"$in": all_card_ids}
                }).to_list(length=None)
                
                studied_card_ids = {progress["flashcard_id"] for progress in studied_cards}
                new_card_ids = [card_id for card_id in all_card_ids if card_id not in studied_card_ids]
                
                card_ids = new_card_ids[:target_cards] if target_cards else new_card_ids
                
            else:
                raise ValueError(f"Unknown study mode: {mode}")
            
            logger.info(f"Selected {len(card_ids)} cards for mode {mode}")
            return card_ids
            
        except Exception as e:
            logger.error(f"Error getting cards for mode {mode}: {str(e)}")
            raise


async def _get_deck_card_ids(db, query) -> List[str]:
    """Helper to get all card IDs from deck query"""
    cards = await db.flashcards.find(query, {"_id": 1}).to_list(length=None)
    return [str(card["_id"]) for card in cards]


class SessionValidator:
    """Validates session access and state"""
    
    @staticmethod
    async def validate_deck_access(db, deck_id: str, user_id: str) -> bool:
        """Validate user has access to deck"""
        deck = await db.decks.find_one({"_id": ObjectId(deck_id)})
        if not deck:
            raise ValueError(f"Deck {deck_id} not found")
        
        # Check if user owns deck or has access
        if deck.get("created_by") != user_id:
            # Could add more complex permission logic here
            pass
        
        return True
    
    @staticmethod
    async def validate_session_access(db, session_id: str, user_id: str) -> StudySession:
        """Validate user has access to session"""
        session_data = await db.study_sessions.find_one({"_id": ObjectId(session_id)})
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        
        if session_data.get("user_id") != user_id:
            raise ValueError("Access denied to this session")
        
        # Convert ObjectId to string before creating StudySession
        session_data["_id"] = str(session_data["_id"])
        
        # Convert to StudySession object
        session = StudySession(**session_data)
        session.id = session_data["_id"]
        
        return session


class BreakReminderService:
    """Handles break reminders and tracking"""
    
    @staticmethod
    async def check_break_reminder(session: StudySession) -> Optional[str]:
        """Check if break reminder should be triggered"""
        if not session.break_reminders_enabled:
            return None
        
        if not session.next_break_reminder:
            return None
        
        now = datetime.utcnow()
        if now >= session.next_break_reminder:
            return f"Time for a break! You've been studying for {session.break_interval} minutes."
        
        return None


class AnswerProcessor:
    """Process flashcard answers and update progress"""
    
    async def process_answer(
        self,
        db,
        user_id: str,
        session: StudySession,
        answer_request: FlashcardAnswerRequest
    ) -> Dict[str, Any]:
        """Process answer and update all relevant data"""
        
        try:
            # Update user progress
            await self._update_user_progress(db, user_id, answer_request)
            
            # Update session progress
            session.progress.cards_studied += 1
            session.progress.cards_remaining = len(session.cards_scheduled) - session.current_card_index - 1
            
            # Update accuracy tracking
            if answer_request.was_correct:
                session.progress.correct_answers += 1
                session.progress.current_streak += 1
            else:
                session.progress.incorrect_answers += 1
                session.progress.current_streak = 0
            
            # Calculate accuracy rate
            total_answers = session.progress.correct_answers + session.progress.incorrect_answers
            if total_answers > 0:
                session.progress.accuracy_rate = (session.progress.correct_answers / total_answers) * 100
            
            # Update average response time
            current_avg = session.progress.average_response_time
            if current_avg == 0:
                session.progress.average_response_time = answer_request.response_time
            else:
                # Moving average
                session.progress.average_response_time = (
                    (current_avg * (total_answers - 1) + answer_request.response_time) / total_answers
                )
            
            # Add answer to session history
            session.answers.append({
                "flashcard_id": answer_request.flashcard_id,
                "quality": answer_request.quality,
                "response_time": answer_request.response_time,
                "was_correct": answer_request.was_correct,
                "answer_text": answer_request.answer_text,
                "timestamp": datetime.utcnow()
            })
            
            # Move to next card
            session.current_card_index += 1
            session.last_activity_at = datetime.utcnow()
            
            # Check if session completed
            session_completed = session.current_card_index >= len(session.cards_scheduled)
            if session_completed:
                session.status = SessionStatus.COMPLETED
                session.completed_at = datetime.utcnow()
            
            # Check milestones
            streak_bonus = self._check_streak_milestone(session.progress.current_streak)
            accuracy_milestone = self._check_accuracy_milestone(session.answers)
            
            return {
                "session_completed": session_completed,
                "streak_count": session.progress.current_streak,
                "streak_bonus": streak_bonus,
                "accuracy_milestone": accuracy_milestone
            }
            
        except Exception as e:
            logger.error(f"Error processing answer: {str(e)}")
            raise
    
    async def _update_user_progress(self, db, user_id: str, answer_request: FlashcardAnswerRequest):
        """Update user progress for flashcard using SM-2 algorithm"""
        try:
            # Use SM-2 algorithm for progress update
            sm2_result = await SM2ProgressUpdater.update_flashcard_progress(
                db=db,
                user_id=user_id,
                flashcard_id=answer_request.flashcard_id,
                quality=answer_request.quality,
                response_time=answer_request.response_time
            )
            
            logger.info(f"SM-2 update completed: EF={sm2_result['ease_factor']}, I={sm2_result['interval']}, R={sm2_result['repetitions']}")
            return sm2_result
                
        except Exception as e:
            logger.error(f"Error updating user progress with SM-2: {str(e)}")
            raise
    
    @staticmethod
    def _check_streak_milestone(streak: int) -> Optional[str]:
        """Check if user achieved streak milestone"""
        if streak == 5:
            return "streak_5"
        elif streak == 10:
            return "streak_10"
        elif streak == 20:
            return "streak_20"
        elif streak == 50:
            return "streak_50"
        
        return None
    
    @staticmethod
    def _check_accuracy_milestone(answers: List[Dict[str, Any]]) -> Optional[str]:
        """Check if user achieved accuracy milestone"""
        if len(answers) < 10:
            return None
        
        # Check last 10 answers
        recent_answers = answers[-10:]
        correct_count = sum(1 for answer in recent_answers if answer.get("was_correct", False))
        accuracy = correct_count / len(recent_answers)
        
        if accuracy >= 0.9:
            return "excellent_accuracy"
        elif accuracy >= 0.8:
            return "good_accuracy"
        elif accuracy >= 0.7:
            return "fair_accuracy"
        
        return None


class StudySessionService:
    """Core study session management service"""
    
    def __init__(self):
        self.db = None
        self.mode_handler = StudyModeHandler()
        self.validator = SessionValidator()
        self.break_service = BreakReminderService()
        self.answer_processor = AnswerProcessor()
    
    async def initialize(self):
        """Initialize database connection"""
        if self.db is None:
            self.db = await get_database()
    
    async def start_session(
        self,
        user_id: str,
        session_request: StudySessionStartRequest
    ) -> StudySessionResponse:
        """Start a new study session"""
        await self.initialize()
        
        try:
            # Validate deck access
            await self.validator.validate_deck_access(
                self.db, session_request.deck_id, user_id
            )
            
            # Get cards for session based on study mode
            card_ids = await self.mode_handler.get_cards_for_mode(
                db=self.db,
                user_id=user_id,
                deck_id=session_request.deck_id,
                mode=session_request.study_mode,
                lesson_id=session_request.lesson_id,
                target_cards=session_request.target_cards
            )
            
            if not card_ids:
                raise ValueError("No cards available for selected study mode")
            
            # Calculate break reminder time
            next_break_reminder = None
            if session_request.break_reminders_enabled:
                next_break_reminder = datetime.utcnow() + timedelta(
                    minutes=session_request.break_interval
                )
            
            # Create session
            session = StudySession(
                user_id=user_id,
                deck_id=session_request.deck_id,
                lesson_id=session_request.lesson_id,
                study_mode=session_request.study_mode,
                target_time=session_request.target_time,
                target_cards=session_request.target_cards,
                break_reminders_enabled=session_request.break_reminders_enabled,
                break_interval=session_request.break_interval,
                cards_scheduled=card_ids,
                next_break_reminder=next_break_reminder,
                progress=StudySessionProgress(
                    cards_studied=0,
                    cards_remaining=len(card_ids),
                    correct_answers=0,
                    incorrect_answers=0,
                    total_time=0,
                    break_count=0,
                    current_streak=0,
                    accuracy_rate=0.0,
                    average_response_time=0.0
                )
            )
            
            # Save to database
            session_dict = session.dict(by_alias=True, exclude={"id", "_id"})
            result = await self.db.study_sessions.insert_one(session_dict)
            session.id = str(result.inserted_id)
            
            # Get first card
            current_card = await self._get_flashcard_for_study(card_ids[0])
            
            response = StudySessionResponse(
                id=session.id,
                user_id=session.user_id,
                deck_id=session.deck_id,
                lesson_id=session.lesson_id,
                study_mode=session.study_mode,
                target_time=session.target_time,
                target_cards=session.target_cards,
                status=session.status,
                progress=session.progress,
                current_card=current_card,
                started_at=session.started_at,
                last_activity_at=session.last_activity_at,
                next_break_reminder=session.next_break_reminder,
                completion_percentage=0.0
            )
            
            logger.info(f"Started study session {session.id} for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error starting study session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str, user_id: str) -> StudySessionResponse:
        """Get current session state"""
        await self.initialize()
        
        try:
            session = await self.validator.validate_session_access(
                self.db, session_id, user_id
            )
            
            # Get current card if session is active
            current_card = None
            if (session.status == SessionStatus.ACTIVE and 
                session.current_card_index < len(session.cards_scheduled)):
                
                current_flashcard_id = session.cards_scheduled[session.current_card_index]
                current_card = await self._get_flashcard_for_study(current_flashcard_id)
            
            # Calculate completion percentage
            completion_percentage = 0.0
            if session.cards_scheduled:
                completion_percentage = (session.current_card_index / len(session.cards_scheduled)) * 100
            
            response = StudySessionResponse(
                id=session.id,
                user_id=session.user_id,
                deck_id=session.deck_id,
                lesson_id=session.lesson_id,
                study_mode=session.study_mode,
                target_time=session.target_time,
                target_cards=session.target_cards,
                status=session.status,
                progress=session.progress,
                current_card=current_card,
                started_at=session.started_at,
                last_activity_at=session.last_activity_at,
                next_break_reminder=session.next_break_reminder,
                is_completed=(session.status == SessionStatus.COMPLETED),
                completion_percentage=completion_percentage
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            raise
    
    async def submit_answer(
        self,
        session_id: str,
        user_id: str,
        answer_request: FlashcardAnswerRequest
    ) -> SessionAnswerResponse:
        """Submit answer for current flashcard"""
        await self.initialize()
        
        try:
            # Validate session
            session = await self.validator.validate_session_access(
                self.db, session_id, user_id
            )
            
            if session.status != SessionStatus.ACTIVE:
                raise ValueError("Session is not active")
            
            # Validate current card
            if session.current_card_index >= len(session.cards_scheduled):
                raise ValueError("No more cards in session")
            
            current_card_id = session.cards_scheduled[session.current_card_index]
            if current_card_id != answer_request.flashcard_id:
                raise ValueError("Answer flashcard ID doesn't match current card")
            
            # Process answer
            answer_result = await self.answer_processor.process_answer(
                self.db, user_id, session, answer_request
            )
            
            # Update session in database
            session_dict = session.dict(by_alias=True, exclude={"id", "_id"})
            await self.db.study_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": session_dict}
            )
            
            # Get next card if session not completed
            next_card = None
            if not answer_result["session_completed"] and session.current_card_index < len(session.cards_scheduled):
                next_flashcard_id = session.cards_scheduled[session.current_card_index]
                next_card = await self._get_flashcard_for_study(next_flashcard_id)
            
            # Check break reminder
            break_reminder_msg = await self.break_service.check_break_reminder(session)
            break_reminder = break_reminder_msg is not None
            
            # Calculate completion percentage
            completion_percentage = (session.current_card_index / len(session.cards_scheduled)) * 100
            
            # Build response
            response = SessionAnswerResponse(
                session_id=session_id,
                flashcard_id=answer_request.flashcard_id,
                was_correct=answer_request.was_correct,
                quality=answer_request.quality,
                next_card=next_card,
                session_completed=answer_result["session_completed"],
                progress=session.progress,
                break_reminder=break_reminder,
                streak_bonus=answer_result["streak_bonus"] is not None,
                accuracy_milestone=answer_result["accuracy_milestone"],
                completion_percentage=completion_percentage,
                cards_remaining=session.progress.cards_remaining,
                current_streak=answer_result["streak_count"]
            )
            
            logger.info(f"Processed answer for session {session_id}, card {answer_request.flashcard_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}")
            raise
    
    async def _get_flashcard_for_study(self, flashcard_id: str) -> FlashcardStudyResponse:
        """Get flashcard data formatted for study"""
        try:
            flashcard_data = await self.db.flashcards.find_one({"_id": ObjectId(flashcard_id)})
            if not flashcard_data:
                raise ValueError(f"Flashcard {flashcard_id} not found")
            
            # Extract question and answer from front/back structure
            question = flashcard_data.get("front", {}).get("text", "")
            answer = flashcard_data.get("back", {}).get("text", "")
            
            # Get multimedia from front/back
            question_image = flashcard_data.get("front", {}).get("image")
            answer_image = flashcard_data.get("back", {}).get("image")
            question_audio = flashcard_data.get("front", {}).get("audio")
            answer_audio = flashcard_data.get("back", {}).get("audio")
            
            # Get user progress for this flashcard (for SRS data)
            progress_data = await self.db.user_flashcard_progress.find_one({
                "user_id": str(flashcard_data.get("created_by", "")),
                "flashcard_id": flashcard_id
            })
            
            # Extract SM-2 data if available
            repetitions = progress_data.get("repetitions", 0) if progress_data else 0
            ease_factor = progress_data.get("ease_factor", SM2Algorithm.INITIAL_EASE_FACTOR) if progress_data else SM2Algorithm.INITIAL_EASE_FACTOR
            interval = progress_data.get("interval", SM2Algorithm.MINIMUM_INTERVAL) if progress_data else SM2Algorithm.MINIMUM_INTERVAL
            next_review = progress_data.get("next_review") if progress_data else None
            
            flashcard = FlashcardStudyResponse(
                id=str(flashcard_data["_id"]),
                deck_id=str(flashcard_data["deck_id"]),
                question=question,
                answer=answer,
                hint=flashcard_data.get("hint"),
                explanation=flashcard_data.get("explanation"),
                question_image=question_image,
                answer_image=answer_image,
                question_audio=question_audio,
                answer_audio=answer_audio,
                difficulty_level=flashcard_data.get("difficulty_level"),
                tags=flashcard_data.get("tags", []),
                repetitions=repetitions,
                ease_factor=ease_factor,
                interval=interval,
                next_review=next_review
            )
            
            return flashcard
            
        except Exception as e:
            logger.error(f"Error getting flashcard for study: {str(e)}")
            raise
    
    async def take_break(
        self,
        session_id: str,
        user_id: str,
        break_request: SessionBreakRequest
    ) -> SessionBreakResponse:
        """Handle break request during study session"""
        await self.initialize()
        
        try:
            # Validate session access
            session = await self.validator.validate_session_access(
                self.db, session_id, user_id
            )
            
            if session.status != SessionStatus.ACTIVE:
                raise ValueError("Can only take breaks during active sessions")
            
            break_started = datetime.utcnow()
            resume_time = break_started + timedelta(minutes=break_request.break_duration)
            
            # Update session with break information
            update_data = {
                "status": SessionStatus.BREAK.value,
                "last_activity_at": break_started,
                "break_started_at": break_started,
                "break_duration": break_request.break_duration,
                "progress.break_count": session.progress.break_count + 1
            }
            
            # Calculate next break reminder if enabled
            if session.break_reminders_enabled:
                update_data["next_break_reminder"] = resume_time + timedelta(
                    minutes=session.break_interval
                )
            
            await self.db.study_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": update_data}
            )
            
            response = SessionBreakResponse(
                session_id=session_id,
                break_started_at=break_started,
                break_duration=break_request.break_duration,
                resume_time=resume_time,
                break_count=session.progress.break_count + 1
            )
            
            logger.info(f"Break started for session {session_id}, duration: {break_request.break_duration} minutes")
            return response
            
        except Exception as e:
            logger.error(f"Error taking break for session {session_id}: {str(e)}")
            raise
    
    async def complete_session(
        self,
        session_id: str,
        user_id: str,
        completion_type: str = "manual"
    ) -> SessionCompletionResponse:
        """Complete study session with comprehensive statistics"""
        await self.initialize()
        
        try:
            session = await self.validator.validate_session_access(
                self.db, session_id, user_id
            )
            
            if session.status == SessionStatus.COMPLETED:
                raise ValueError("Session is already completed")
            
            # Calculate session statistics
            completion_time = datetime.utcnow()
            total_time = int((completion_time - session.started_at).total_seconds())
            
            # Get all session answers for detailed stats
            session_data = await self.db.study_sessions.find_one({"_id": ObjectId(session_id)})
            answers = session_data.get("answers", [])
            
            # Calculate performance metrics
            total_answers = len(answers)
            correct_answers = sum(1 for answer in answers if answer.get("was_correct", False))
            incorrect_answers = total_answers - correct_answers
            
            accuracy_rate = (correct_answers / total_answers * 100) if total_answers > 0 else 0.0
            
            # Calculate average response time
            response_times = [answer.get("response_time", 0) for answer in answers if answer.get("response_time")]
            average_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Find best streak from session progress
            best_streak = session.progress.current_streak
            
            # Check goal achievements
            goals_achieved = []
            if session.target_cards and total_answers >= session.target_cards:
                goals_achieved.append("target_cards")
            if session.target_time and total_time >= (session.target_time * 60):
                goals_achieved.append("target_time")
            if accuracy_rate >= 80:
                goals_achieved.append("high_accuracy")
            if best_streak >= 5:
                goals_achieved.append("streak_master")
            
            # Calculate performance rating
            performance_rating = "poor"
            if accuracy_rate >= 90:
                performance_rating = "excellent"
            elif accuracy_rate >= 80:
                performance_rating = "good"
            elif accuracy_rate >= 60:
                performance_rating = "fair"
            
            # Recommend next study mode
            recommended_mode = StudyMode.REVIEW
            if accuracy_rate < 60:
                recommended_mode = StudyMode.LEARN
            elif accuracy_rate < 80:
                recommended_mode = StudyMode.PRACTICE
            elif accuracy_rate >= 90:
                recommended_mode = StudyMode.CRAM
            
            # Count cards due tomorrow
            tomorrow = datetime.utcnow() + timedelta(days=1)
            cards_due_tomorrow = await self.db.user_flashcard_progress.count_documents({
                "user_id": user_id,
                "next_review": {"$lte": tomorrow}
            })
            
            # Update session as completed
            await self.db.study_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {
                    "status": SessionStatus.COMPLETED.value,
                    "completed_at": completion_time,
                    "completion_type": completion_type,
                    "progress.total_time": total_time,
                    "progress.accuracy_rate": accuracy_rate,
                    "progress.average_response_time": average_response_time,
                    "last_activity_at": completion_time
                }}
            )
            
            response = SessionCompletionResponse(
                session_id=session_id,
                completion_type=completion_type,
                total_time=total_time,
                cards_studied=total_answers,
                accuracy_rate=accuracy_rate,
                correct_answers=correct_answers,
                incorrect_answers=incorrect_answers,
                average_response_time=average_response_time,
                best_streak=best_streak,
                break_count=session.progress.break_count,
                goals_achieved=goals_achieved,
                performance_rating=performance_rating,
                recommended_mode=recommended_mode,
                cards_due_tomorrow=cards_due_tomorrow
            )
            
            logger.info(f"Session {session_id} completed with {accuracy_rate:.1f}% accuracy")
            return response
            
        except Exception as e:
            logger.error(f"Error completing session {session_id}: {str(e)}")
            raise
    
    async def get_active_sessions(self, user_id: str) -> List[StudySessionResponse]:
        """Get all active sessions for user"""
        await self.initialize()
        
        try:
            # Find active and break sessions
            sessions_data = await self.db.study_sessions.find({
                "user_id": user_id,
                "status": {"$in": [SessionStatus.ACTIVE.value, SessionStatus.BREAK.value]}
            }).to_list(length=None)
            
            sessions = []
            for session_data in sessions_data:
                # Convert ObjectId to string for validation
                session_data["_id"] = str(session_data["_id"])
                
                session = StudySession(**session_data)
                session.id = session_data["_id"]
                
                # Get current card if available
                current_card = None
                if (session.status == SessionStatus.ACTIVE and 
                    session.current_card_index < len(session.cards_scheduled)):
                    
                    current_flashcard_id = session.cards_scheduled[session.current_card_index]
                    current_card = await self._get_flashcard_for_study(current_flashcard_id)
                
                # Calculate completion percentage
                completion_percentage = 0.0
                if session.cards_scheduled:
                    completion_percentage = (session.current_card_index / len(session.cards_scheduled)) * 100
                
                response = StudySessionResponse(
                    id=session.id,
                    user_id=session.user_id,
                    deck_id=session.deck_id,
                    lesson_id=session.lesson_id,
                    study_mode=session.study_mode,
                    target_time=session.target_time,
                    target_cards=session.target_cards,
                    status=session.status,
                    progress=session.progress,
                    current_card=current_card,
                    started_at=session.started_at,
                    last_activity_at=session.last_activity_at,
                    next_break_reminder=session.next_break_reminder,
                    is_completed=(session.status == SessionStatus.COMPLETED),
                    completion_percentage=completion_percentage
                )
                
                sessions.append(response)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions for user {user_id}: {str(e)}")
            raise
    
    async def abandon_session(self, session_id: str, user_id: str) -> bool:
        """Abandon session without completing"""
        await self.initialize()
        
        try:
            session = await self.validator.validate_session_access(
                self.db, session_id, user_id
            )
            
            if session.status == SessionStatus.COMPLETED:
                raise ValueError("Cannot abandon completed session")
            
            # Mark as abandoned
            await self.db.study_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {
                    "status": SessionStatus.ABANDONED.value,
                    "abandoned_at": datetime.utcnow(),
                    "last_activity_at": datetime.utcnow()
                }}
            )
            
            logger.info(f"Session {session_id} abandoned by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error abandoning session {session_id}: {str(e)}")
            raise


# Create service instance
study_session_service = StudySessionService()
