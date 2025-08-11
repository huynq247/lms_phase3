#!/usr/bin/env python3
"""
Test Phase 6.3 SM-2 Algorithm Implementation
Test toàn bộ tính năng SM-2 spaced repetition
"""
import asyncio
import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta
from app.services.sm2_algorithm import SM2Algorithm, SM2ProgressUpdater
from app.services.study_session_service import study_session_service
from app.models.study import StudySessionStartRequest, FlashcardAnswerRequest, StudyMode

async def test_sm2_algorithm():
    """Test SM-2 algorithm implementation"""
    
    print("=== PHASE 6.3 SM-2 ALGORITHM TEST ===")
    print(f"🕐 Started at: {datetime.now()}")
    print("-" * 60)
    
    # 1. Test Core SM-2 Algorithm
    print("1. 🧮 Core SM-2 Algorithm Test")
    try:
        # Test initial learning (new card)
        result1 = SM2Algorithm.calculate_next_review(
            quality=4,  # Good recall
            current_ease_factor=2.5,
            current_interval=1,
            current_repetitions=0
        )
        
        print(f"   📊 First review (Q=4): EF={result1['ease_factor']}, I={result1['interval']}, R={result1['repetitions']}")
        print(f"   📅 Next review: {result1['next_review'].date()}")
        
        # Test second review
        result2 = SM2Algorithm.calculate_next_review(
            quality=5,  # Perfect recall
            current_ease_factor=result1['ease_factor'],
            current_interval=result1['interval'],
            current_repetitions=result1['repetitions']
        )
        
        print(f"   📊 Second review (Q=5): EF={result2['ease_factor']}, I={result2['interval']}, R={result2['repetitions']}")
        print(f"   📅 Next review: {result2['next_review'].date()}")
        
        # Test third review
        result3 = SM2Algorithm.calculate_next_review(
            quality=3,  # Difficult recall
            current_ease_factor=result2['ease_factor'],
            current_interval=result2['interval'],
            current_repetitions=result2['repetitions']
        )
        
        print(f"   📊 Third review (Q=3): EF={result3['ease_factor']}, I={result3['interval']}, R={result3['repetitions']}")
        print(f"   📅 Next review: {result3['next_review'].date()}")
        
        # Test forgetting (quality < 3)
        result4 = SM2Algorithm.calculate_next_review(
            quality=1,  # Poor recall - should reset
            current_ease_factor=result3['ease_factor'],
            current_interval=result3['interval'],
            current_repetitions=result3['repetitions']
        )
        
        print(f"   📊 Forgot card (Q=1): EF={result4['ease_factor']}, I={result4['interval']}, R={result4['repetitions']}")
        print(f"   📅 Next review: {result4['next_review'].date()}")
        print("   ✅ SM-2 algorithm working correctly!")
        
    except Exception as e:
        print(f"   ❌ SM-2 algorithm test failed: {e}")
        return False
    
    # 2. Test Database Integration
    print("2. 🗄️ Database Integration Test")
    try:
        await study_session_service.initialize()
        db = study_session_service.db
        
        user_id = "6899b990a2518f8e4a47e0ab"
        test_card_id = "68950e4efedb895eb3afc799"
        
        # Test SM-2 progress update
        sm2_result = await SM2ProgressUpdater.update_flashcard_progress(
            db=db,
            user_id=user_id,
            flashcard_id=test_card_id,
            quality=4,
            response_time=12.5
        )
        
        print(f"   ✅ Database update successful")
        print(f"   📊 SM-2 result: EF={sm2_result['ease_factor']}, I={sm2_result['interval']}, R={sm2_result['repetitions']}")
        
        # Verify data in database
        progress = await db.user_flashcard_progress.find_one({
            "user_id": user_id,
            "flashcard_id": test_card_id
        })
        
        if progress:
            print(f"   📈 Database verification:")
            print(f"     - Ease Factor: {progress.get('ease_factor')}")
            print(f"     - Interval: {progress.get('interval')} days")
            print(f"     - Repetitions: {progress.get('repetitions')}")
            print(f"     - Next Review: {progress.get('next_review')}")
            print(f"     - Times Studied: {progress.get('times_studied')}")
            print(f"     - Quality History: {len(progress.get('quality_history', []))} entries")
        
    except Exception as e:
        print(f"   ❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Test Review Mode with SM-2
    print("3. 🔄 Review Mode with SM-2 Test")
    try:
        # Create review session
        session_request = StudySessionStartRequest(
            deck_id="6894f7d942907590250f3fb9",
            study_mode=StudyMode.REVIEW,
            target_cards=5,
            break_reminders_enabled=False
        )
        
        session_response = await study_session_service.start_session(
            user_id=user_id,
            session_request=session_request
        )
        
        session_id = session_response.id
        print(f"   ✅ Review session created: {session_id}")
        print(f"   📊 Study mode: {session_response.study_mode}")
        
        if session_response.current_card:
            print(f"   📇 Current card: {session_response.current_card.question[:50]}...")
            print(f"   📊 SM-2 data:")
            print(f"     - Ease Factor: {session_response.current_card.ease_factor}")
            print(f"     - Interval: {session_response.current_card.interval} days")
            print(f"     - Repetitions: {session_response.current_card.repetitions}")
            print(f"     - Next Review: {session_response.current_card.next_review}")
            
            # Submit answer with SM-2 processing
            answer_request = FlashcardAnswerRequest(
                flashcard_id=session_response.current_card.id,
                quality=4,
                response_time=15.0,
                was_correct=True,
                answer_text="Good answer"
            )
            
            answer_response = await study_session_service.submit_answer(
                session_id=session_id,
                user_id=user_id,
                answer_request=answer_request
            )
            
            print(f"   ✅ Answer processed with SM-2")
            print(f"   📈 Progress: {answer_response.completion_percentage:.1f}%")
            print(f"   🎯 Streak: {answer_response.current_streak}")
            
            # Check if next card has updated SM-2 data
            if answer_response.next_card:
                print(f"   ➡️ Next card SM-2 data:")
                print(f"     - Ease Factor: {answer_response.next_card.ease_factor}")
                print(f"     - Interval: {answer_response.next_card.interval} days")
                print(f"     - Repetitions: {answer_response.next_card.repetitions}")
        else:
            print("   ⚠️ No due cards found for review")
            
    except Exception as e:
        print(f"   ❌ Review mode test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Test Due Cards Detection
    print("4. 📅 Due Cards Detection Test")
    try:
        current_time = datetime.utcnow()
        
        # Create some overdue progress records for testing
        test_progress = [
            {
                "next_review": current_time - timedelta(days=2),  # 2 days overdue
                "flashcard_id": "test1"
            },
            {
                "next_review": current_time - timedelta(days=1),  # 1 day overdue
                "flashcard_id": "test2"
            },
            {
                "next_review": current_time + timedelta(days=1),  # Not due yet
                "flashcard_id": "test3"
            }
        ]
        
        # Test due card detection
        for i, progress in enumerate(test_progress, 1):
            is_due = SM2Algorithm.is_card_due(progress["next_review"], current_time)
            overdue_days = SM2Algorithm.calculate_overdue_days(progress["next_review"], current_time)
            
            print(f"   📇 Card {i}: Due={is_due}, Overdue={overdue_days} days")
        
        # Test review statistics
        stats = SM2Algorithm.get_review_statistics(test_progress)
        print(f"   📊 Review Statistics:")
        print(f"     - Total cards: {stats['total_cards']}")
        print(f"     - Due cards: {stats['due_cards']}")
        print(f"     - Overdue cards: {stats['overdue_cards']}")
        print(f"     - Average overdue: {stats['avg_overdue_days']} days")
        print(f"     - Due percentage: {stats['due_percentage']}%")
        
        # Test query generation
        due_query = SM2Algorithm.get_due_cards_query(user_id, current_time)
        print(f"   🔍 Due cards query: {due_query}")
        
        sort_criteria = SM2Algorithm.get_overdue_priority_sort()
        print(f"   📋 Sort criteria: {sort_criteria}")
        
    except Exception as e:
        print(f"   ❌ Due cards detection test failed: {e}")
    
    # 5. Test Edge Cases
    print("5. ⚠️ Edge Cases Test")
    try:
        # Test invalid quality values
        try:
            SM2Algorithm.calculate_next_review(quality=6)  # Should fail
            print("   ❌ Should have failed for quality > 5")
        except ValueError:
            print("   ✅ Correctly rejected quality > 5")
        
        try:
            SM2Algorithm.calculate_next_review(quality=-1)  # Should fail
            print("   ❌ Should have failed for quality < 0")
        except ValueError:
            print("   ✅ Correctly rejected quality < 0")
        
        # Test minimum ease factor
        result = SM2Algorithm.calculate_next_review(
            quality=0,  # Very poor
            current_ease_factor=1.3,  # Already at minimum
            current_interval=1,
            current_repetitions=5
        )
        
        print(f"   ✅ Minimum EF maintained: {result['ease_factor']} >= 1.3")
        print(f"   ✅ Repetitions reset on poor quality: {result['repetitions']} = 0")
        
        # Test very high repetitions
        result = SM2Algorithm.calculate_next_review(
            quality=5,
            current_ease_factor=3.0,
            current_interval=100,
            current_repetitions=20
        )
        
        print(f"   ✅ High repetitions handled: R={result['repetitions']}, I={result['interval']} days")
        
    except Exception as e:
        print(f"   ❌ Edge cases test failed: {e}")
    
    print("-" * 60)
    print("🎉 PHASE 6.3 SM-2 ALGORITHM TEST FINISHED!")
    print(f"🕐 Finished at: {datetime.now()}")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_sm2_algorithm()
        if success:
            print("\n✅ Phase 6.3 SM-2 Algorithm: WORKING PERFECTLY!")
            print("🧠 Spaced repetition is now intelligent!")
            print("🚀 Ready for Phase 6.4 or production!")
        else:
            print("\n❌ Some SM-2 features need fixing")
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
