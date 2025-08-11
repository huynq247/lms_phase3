#!/usr/bin/env python3
"""
Script thêm dữ liệu test vào database cho Phase 6.5 Analytics
"""
import asyncio
import sys
import random
sys.path.append('.')

from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def add_test_data():
    """Thêm dữ liệu test vào database"""
    
    print("=== THÊM DỮ LIỆU TEST CHO PHASE 6.5 ===")
    print(f"🕐 Started at: {datetime.now()}")
    print("-" * 60)
    
    try:
        # Kết nối database
        client = AsyncIOMotorClient('mongodb://admin:Root%40123@113.161.118.17:27017')
        db = client['flashcard_lms_dev']
        
        # Test user ID
        user_id = "6899b990a2518f8e4a47e0ab"
        deck_id = "6894f7d942907590250f3fb9"
        
        print("1. 📇 Thêm flashcards mới để có đủ data")
        
        # Lấy deck hiện tại
        deck = await db.decks.find_one({"_id": ObjectId(deck_id)})
        if not deck:
            print("   ❌ Deck không tồn tại")
            return
        
        # Thêm flashcards mới
        new_cards = []
        card_contents = [
            {"front": {"text": "What is JavaScript?"}, "back": {"text": "A programming language for web development"}},
            {"front": {"text": "What is React?"}, "back": {"text": "A JavaScript library for building user interfaces"}},
            {"front": {"text": "What is Node.js?"}, "back": {"text": "A JavaScript runtime for server-side development"}},
            {"front": {"text": "What is MongoDB?"}, "back": {"text": "A NoSQL document database"}},
            {"front": {"text": "What is API?"}, "back": {"text": "Application Programming Interface"}},
            {"front": {"text": "What is HTTP?"}, "back": {"text": "HyperText Transfer Protocol"}},
            {"front": {"text": "What is JSON?"}, "back": {"text": "JavaScript Object Notation"}},
            {"front": {"text": "What is Git?"}, "back": {"text": "A version control system"}},
            {"front": {"text": "What is Docker?"}, "back": {"text": "A containerization platform"}},
            {"front": {"text": "What is AWS?"}, "back": {"text": "Amazon Web Services cloud platform"}},
        ]
        
        for content in card_contents:
            card = {
                "deck_id": deck_id,
                "created_by": user_id,
                "front": content["front"],
                "back": content["back"],
                "hint": "Think about technology",
                "explanation": "This is a technology term",
                "difficulty_level": random.choice(["easy", "medium", "hard"]),
                "tags": ["technology", "programming"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            new_cards.append(card)
        
        if new_cards:
            result = await db.flashcards.insert_many(new_cards)
            print(f"   ✅ Thêm {len(result.inserted_ids)} flashcards mới")
            new_card_ids = [str(id) for id in result.inserted_ids]
        else:
            new_card_ids = []
        
        # Lấy tất cả cards trong deck
        all_cards = await db.flashcards.find({"deck_id": deck_id}).to_list(length=None)
        all_card_ids = [str(card["_id"]) for card in all_cards]
        print(f"   📊 Total cards in deck: {len(all_card_ids)}")
        
        print("2. 📈 Thêm progress records với SM-2 data")
        
        # Thêm progress records cho các cards
        progress_records = []
        base_time = datetime.utcnow() - timedelta(days=30)
        
        for i, card_id in enumerate(all_card_ids[:15]):  # Limit to 15 cards
            # Tạo random study history
            study_count = random.randint(1, 10)
            ease_factor = round(random.uniform(1.3, 3.0), 2)
            repetitions = random.randint(0, 5)
            interval = random.randint(1, 30)
            
            last_studied = base_time + timedelta(days=random.randint(0, 30))
            next_review = last_studied + timedelta(days=interval)
            
            quality_history = []
            for j in range(study_count):
                quality_history.append({
                    "quality": random.randint(1, 5),
                    "timestamp": last_studied - timedelta(days=study_count-j),
                    "response_time": round(random.uniform(2.0, 30.0), 1)
                })
            
            progress = {
                "user_id": user_id,
                "flashcard_id": card_id,
                "first_studied": base_time + timedelta(days=random.randint(0, 5)),
                "last_studied": last_studied,
                "times_studied": study_count,
                "ease_factor": ease_factor,
                "interval": interval,
                "repetitions": repetitions,
                "last_quality": quality_history[-1]["quality"] if quality_history else 3,
                "next_review": next_review,
                "quality_history": quality_history,
                "mastery_level": random.choice(["learning", "practicing", "mastered"]),
                "success_rate": round(random.uniform(0.4, 1.0), 2)
            }
            progress_records.append(progress)
        
        if progress_records:
            # Xóa progress cũ để tránh duplicate
            await db.user_flashcard_progress.delete_many({
                "user_id": user_id,
                "flashcard_id": {"$in": [p["flashcard_id"] for p in progress_records]}
            })
            
            result = await db.user_flashcard_progress.insert_many(progress_records)
            print(f"   ✅ Thêm {len(result.inserted_ids)} progress records")
        
        print("3. 📚 Thêm study sessions với data đa dạng")
        
        # Thêm study sessions trong 30 ngày qua
        sessions = []
        study_modes = ["review", "practice", "learn", "test", "cram"]
        
        for day in range(30):
            session_date = base_time + timedelta(days=day)
            
            # Random 0-3 sessions per day
            sessions_per_day = random.randint(0, 3)
            
            for session_num in range(sessions_per_day):
                session_cards = random.sample(all_card_ids, min(random.randint(3, 8), len(all_card_ids)))
                
                # Create session answers
                answers = []
                correct_count = 0
                total_time = 0
                
                for card_id in session_cards:
                    was_correct = random.choice([True, False, True, True])  # 75% correct rate
                    quality = random.randint(3, 5) if was_correct else random.randint(1, 2)
                    response_time = round(random.uniform(2.0, 25.0), 1)
                    
                    answers.append({
                        "flashcard_id": card_id,
                        "quality": quality,
                        "response_time": response_time,
                        "was_correct": was_correct,
                        "answer_text": "Test answer",
                        "timestamp": session_date + timedelta(minutes=len(answers) * 2)
                    })
                    
                    if was_correct:
                        correct_count += 1
                    total_time += response_time
                
                accuracy_rate = (correct_count / len(answers)) * 100 if answers else 0
                
                session = {
                    "user_id": user_id,
                    "deck_id": deck_id,
                    "study_mode": random.choice(study_modes),
                    "status": random.choice(["completed", "completed", "completed", "abandoned"]),  # 75% completed
                    "target_cards": len(session_cards),
                    "target_time": random.randint(10, 30),
                    "break_reminders_enabled": random.choice([True, False]),
                    "break_interval": 25,
                    "cards_scheduled": session_cards,
                    "current_card_index": len(session_cards),
                    "started_at": session_date,
                    "completed_at": session_date + timedelta(minutes=random.randint(5, 30)),
                    "last_activity_at": session_date + timedelta(minutes=random.randint(5, 30)),
                    "answers": answers,
                    "progress": {
                        "cards_studied": len(answers),
                        "cards_remaining": 0,
                        "correct_answers": correct_count,
                        "incorrect_answers": len(answers) - correct_count,
                        "total_time": int(total_time),
                        "break_count": random.randint(0, 2),
                        "current_streak": random.randint(0, 5),
                        "accuracy_rate": accuracy_rate,
                        "average_response_time": total_time / len(answers) if answers else 0
                    }
                }
                sessions.append(session)
        
        if sessions:
            result = await db.study_sessions.insert_many(sessions)
            print(f"   ✅ Thêm {len(result.inserted_ids)} study sessions")
        
        print("4. 🏆 Thêm achievements")
        
        # Thêm achievements
        achievements = [
            {
                "user_id": user_id,
                "achievement_type": "streak_milestone",
                "achievement_name": "Study Streak 5",
                "description": "Completed 5 consecutive study sessions",
                "earned_at": base_time + timedelta(days=5),
                "metadata": {"streak_count": 5}
            },
            {
                "user_id": user_id,
                "achievement_type": "accuracy_milestone",
                "achievement_name": "Accuracy Master",
                "description": "Achieved 90% accuracy in a session",
                "earned_at": base_time + timedelta(days=10),
                "metadata": {"accuracy": 92.5}
            },
            {
                "user_id": user_id,
                "achievement_type": "time_milestone",
                "achievement_name": "Study Marathon",
                "description": "Studied for 60 minutes in one session",
                "earned_at": base_time + timedelta(days=15),
                "metadata": {"study_time": 65}
            }
        ]
        
        # Xóa achievements cũ
        await db.achievements.delete_many({"user_id": user_id})
        
        result = await db.achievements.insert_many(achievements)
        print(f"   ✅ Thêm {len(result.inserted_ids)} achievements")
        
        print("5. 📊 Tóm tắt dữ liệu đã thêm")
        
        # Kiểm tra tổng số records
        total_cards = await db.flashcards.count_documents({"deck_id": deck_id})
        total_progress = await db.user_flashcard_progress.count_documents({"user_id": user_id})
        total_sessions = await db.study_sessions.count_documents({"user_id": user_id})
        total_achievements = await db.achievements.count_documents({"user_id": user_id})
        
        print(f"   📇 Total flashcards: {total_cards}")
        print(f"   📈 Total progress records: {total_progress}")
        print(f"   📚 Total study sessions: {total_sessions}")
        print(f"   🏆 Total achievements: {total_achievements}")
        
        client.close()
        
        print("-" * 60)
        print("✅ DỮ LIỆU TEST ĐÃ ĐƯỢC THÊM THÀNH CÔNG!")
        print("🚀 Sẵn sàng test Phase 6.5 Analytics!")
        
    except Exception as e:
        print(f"❌ Lỗi thêm dữ liệu: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await add_test_data()

if __name__ == "__main__":
    asyncio.run(main())
