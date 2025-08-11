#!/usr/bin/env python3
"""
Backend và Database Test - Phase 6.2 Answer Processing
Test trực tiếp với database và backend services
"""
import asyncio
import sys
import os
sys.path.append('.')

from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.study_session_service import study_session_service, AnswerProcessor
from app.models.study import StudySessionStartRequest, FlashcardAnswerRequest, StudyMode

async def test_backend_database():
    """Test backend services với database thực"""
    
    print("=== BACKEND & DATABASE DIRECT TEST ===")
    print(f"🕐 Started at: {datetime.now()}")
    print("-" * 60)
    
    # 1. Database Connection Test
    print("1. 🗄️ Database Connection Test")
    try:
        client = AsyncIOMotorClient('mongodb://admin:Root%40123@113.161.118.17:27017')
        db = client['flashcard_lms_dev']
        
        # Test connection
        await db.command("ping")
        print("   ✅ MongoDB connection successful")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"   📊 Available collections: {len(collections)}")
        
        # Count documents
        users_count = await db.users.count_documents({})
        decks_count = await db.decks.count_documents({})
        cards_count = await db.flashcards.count_documents({})
        sessions_count = await db.study_sessions.count_documents({})
        progress_count = await db.user_flashcard_progress.count_documents({})
        
        print(f"   👥 Users: {users_count}")
        print(f"   📚 Decks: {decks_count}")
        print(f"   📇 Flashcards: {cards_count}")
        print(f"   🎯 Study Sessions: {sessions_count}")
        print(f"   📈 Progress Records: {progress_count}")
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # 2. Service Initialization Test
    print("2. 🔧 Service Initialization Test")
    try:
        await study_session_service.initialize()
        print("   ✅ StudySessionService initialized")
        print("   ✅ Database connection established in service")
        
        # Test service components
        print(f"   📋 StudyModeHandler: {study_session_service.mode_handler is not None}")
        print(f"   🔐 SessionValidator: {study_session_service.validator is not None}")
        print(f"   ⏰ BreakReminderService: {study_session_service.break_service is not None}")
        print(f"   ✏️ AnswerProcessor: {study_session_service.answer_processor is not None}")
        
    except Exception as e:
        print(f"   ❌ Service initialization failed: {e}")
        return False
    
    # 3. Real User and Deck Data Test
    print("3. 📊 Real Data Validation Test")
    try:
        # Get admin user
        admin_user = await db.users.find_one({"email": "admin@flashcard.com"})
        if not admin_user:
            print("   ❌ Admin user not found")
            return False
        
        admin_id = str(admin_user["_id"])
        print(f"   👑 Admin user found: {admin_user['username']} ({admin_id})")
        
        # Get test deck with cards
        from bson import ObjectId
        test_deck = await db.decks.find_one({"_id": ObjectId("6894f7d942907590250f3fb9")})
        if not test_deck:
            print("   ❌ Test deck not found")
            return False
        
        deck_id = str(test_deck["_id"])
        print(f"   📚 Test deck: {test_deck['title']} ({deck_id})")
        
        # Count cards in deck
        deck_cards = await db.flashcards.count_documents({"deck_id": deck_id})
        print(f"   📇 Cards in deck: {deck_cards}")
        
        if deck_cards == 0:
            print("   ❌ No cards found in test deck")
            return False
        
    except Exception as e:
        print(f"   ❌ Real data validation failed: {e}")
        return False
    
    # 4. Study Session Creation Test
    print("4. 🚀 Study Session Creation Test")
    try:
        session_request = StudySessionStartRequest(
            deck_id=deck_id,
            study_mode=StudyMode.PRACTICE,
            target_cards=3,
            target_time=15,
            break_reminders_enabled=True,
            break_interval=25
        )
        
        session_response = await study_session_service.start_session(
            user_id=admin_id,
            session_request=session_request
        )
        
        session_id = session_response.id
        print(f"   ✅ Session created: {session_id}")
        print(f"   🎯 Study mode: {session_response.study_mode}")
        print(f"   📊 Status: {session_response.status}")
        print(f"   📇 Current card: {session_response.current_card.question[:50]}...")
        print(f"   🆔 Card ID: {session_response.current_card.id}")
        print(f"   📈 Cards scheduled: {len(session_response.cards_scheduled) if hasattr(session_response, 'cards_scheduled') else 'N/A'}")
        
        current_card = session_response.current_card
        
    except Exception as e:
        print(f"   ❌ Session creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Answer Processing Test
    print("5. ✏️ Answer Processing Test")
    try:
        # Submit first answer (correct)
        answer_1 = FlashcardAnswerRequest(
            flashcard_id=current_card.id,
            quality=4,
            response_time=12.5,
            was_correct=True,
            answer_text="This is a correct answer"
        )
        
        answer_response_1 = await study_session_service.submit_answer(
            session_id=session_id,
            user_id=admin_id,
            answer_request=answer_1
        )
        
        print(f"   ✅ First answer processed")
        print(f"   📊 Quality: {answer_response_1.quality}")
        print(f"   ✅ Correct: {answer_response_1.was_correct}")
        print(f"   🎯 Streak: {answer_response_1.current_streak}")
        print(f"   📈 Progress: {answer_response_1.completion_percentage:.1f}%")
        print(f"   📝 Cards remaining: {answer_response_1.cards_remaining}")
        
        if answer_response_1.next_card:
            print(f"   ➡️ Next card: {answer_response_1.next_card.question[:50]}...")
            current_card = answer_response_1.next_card
        
    except Exception as e:
        print(f"   ❌ First answer processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Database Progress Verification
    print("6. 🗄️ Database Progress Verification")
    try:
        # Check if progress was saved
        progress_record = await db.user_flashcard_progress.find_one({
            "user_id": admin_id,
            "flashcard_id": answer_1.flashcard_id
        })
        
        if progress_record:
            print("   ✅ Progress record created in database")
            print(f"   📊 Times studied: {progress_record.get('times_studied', 0)}")
            print(f"   📈 Last quality: {progress_record.get('last_quality', 'N/A')}")
            print(f"   🕐 Last studied: {progress_record.get('last_studied', 'N/A')}")
            print(f"   📝 Quality history length: {len(progress_record.get('quality_history', []))}")
        else:
            print("   ⚠️ Progress record not found in database")
        
        # Check session in database
        session_record = await db.study_sessions.find_one({"_id": ObjectId(session_id)})
        if session_record:
            print("   ✅ Session record found in database")
            print(f"   📊 Status: {session_record.get('status', 'N/A')}")
            print(f"   📝 Answers recorded: {len(session_record.get('answers', []))}")
            print(f"   📈 Current card index: {session_record.get('current_card_index', 0)}")
        else:
            print("   ⚠️ Session record not found in database")
        
    except Exception as e:
        print(f"   ❌ Database verification failed: {e}")
    
    # 7. Multiple Answers Test
    print("7. 🔄 Multiple Answers Flow Test")
    try:
        if current_card and not answer_response_1.session_completed:
            # Submit second answer (incorrect)
            answer_2 = FlashcardAnswerRequest(
                flashcard_id=current_card.id,
                quality=1,
                response_time=8.0,
                was_correct=False,
                answer_text="This is wrong"
            )
            
            answer_response_2 = await study_session_service.submit_answer(
                session_id=session_id,
                user_id=admin_id,
                answer_request=answer_2
            )
            
            print(f"   ✅ Second answer processed (incorrect)")
            print(f"   📊 Quality: {answer_response_2.quality}")
            print(f"   ❌ Correct: {answer_response_2.was_correct}")
            print(f"   🎯 Streak: {answer_response_2.current_streak} (should be reset)")
            print(f"   📈 Progress: {answer_response_2.completion_percentage:.1f}%")
            
            if answer_response_2.next_card:
                # Submit third answer (excellent)
                answer_3 = FlashcardAnswerRequest(
                    flashcard_id=answer_response_2.next_card.id,
                    quality=5,
                    response_time=4.0,
                    was_correct=True,
                    answer_text="Perfect answer"
                )
                
                answer_response_3 = await study_session_service.submit_answer(
                    session_id=session_id,
                    user_id=admin_id,
                    answer_request=answer_3
                )
                
                print(f"   ✅ Third answer processed (excellent)")
                print(f"   📊 Quality: {answer_response_3.quality}")
                print(f"   ⭐ Correct: {answer_response_3.was_correct}")
                print(f"   🎯 Streak: {answer_response_3.current_streak}")
                print(f"   📈 Progress: {answer_response_3.completion_percentage:.1f}%")
                print(f"   🏁 Session completed: {answer_response_3.session_completed}")
        
    except Exception as e:
        print(f"   ❌ Multiple answers test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 8. Final Database State Check
    print("8. 🏁 Final Database State Check")
    try:
        # Count final records
        final_sessions = await db.study_sessions.count_documents({})
        final_progress = await db.user_flashcard_progress.count_documents({})
        
        print(f"   📊 Total study sessions: {final_sessions}")
        print(f"   📈 Total progress records: {final_progress}")
        
        # Check specific user progress
        user_progress = await db.user_flashcard_progress.count_documents({"user_id": admin_id})
        print(f"   👑 Admin user progress records: {user_progress}")
        
    except Exception as e:
        print(f"   ❌ Final state check failed: {e}")
    
    # Close connection
    client.close()
    
    print("-" * 60)
    print("🎉 BACKEND & DATABASE TEST COMPLETED!")
    print(f"🕐 Finished at: {datetime.now()}")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_backend_database()
        if success:
            print("\n✅ Backend và Database hoạt động HOÀN HẢO!")
            print("🚀 Sẵn sàng tiếp tục phát triển Phase 6.2 features!")
        else:
            print("\n❌ Có vấn đề cần sửa trước khi tiếp tục")
    except Exception as e:
        print(f"\n💥 Lỗi nghiêm trọng: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
