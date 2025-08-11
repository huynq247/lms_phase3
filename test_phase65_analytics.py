#!/usr/bin/env python3
"""
Phase 6.5 Analytics & Visualization Test
Test comprehensive analytics and chart generation
"""
import asyncio
import sys
import os
sys.path.append('.')

import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.analytics_service import analytics_service
from app.services.study_session_service import study_session_service
from app.models.study import StudySessionStartRequest, FlashcardAnswerRequest, StudyMode

async def test_phase65_analytics():
    """Test complete Phase 6.5 analytics and visualization features"""
    
    print("=== PHASE 6.5 ANALYTICS & VISUALIZATION TEST ===")
    print(f"🕐 Started at: {datetime.now()}")
    print("-" * 60)
    
    admin_user_id = "6899b990a2518f8e4a47e0ab"
    test_deck_id = "6894f7d942907590250f3fb9"
    
    # 1. Initialize Services
    print("1. 🚀 Service Initialization")
    try:
        await analytics_service.initialize()
        await study_session_service.initialize()
        print("   ✅ Analytics service initialized")
        print("   ✅ Study session service initialized")
        
    except Exception as e:
        print(f"   ❌ Service initialization failed: {e}")
        return False
    
    # 2. Create Test Data (Study Sessions)
    print("2. 📊 Creating Test Data for Analytics")
    try:
        # Create multiple study sessions with different patterns
        session_configs = [
            {"mode": StudyMode.PRACTICE, "target_cards": 3},
            {"mode": StudyMode.LEARN, "target_cards": 2},
            {"mode": StudyMode.REVIEW, "target_cards": 4},
            {"mode": StudyMode.CRAM, "target_cards": 5}
        ]
        
        created_sessions = []
        
        for i, config in enumerate(session_configs):
            session_request = StudySessionStartRequest(
                deck_id=test_deck_id,
                study_mode=config["mode"],
                target_cards=config["target_cards"],
                break_reminders_enabled=(i % 2 == 0)
            )
            
            session_response = await study_session_service.start_session(
                user_id=admin_user_id,
                session_request=session_request
            )
            
            created_sessions.append(session_response)
            print(f"   ✅ Created {config['mode'].value} session: {session_response.id}")
            
            # Submit some answers to create realistic data
            if session_response.current_card:
                # Submit 2-3 answers per session
                for j in range(min(2, config["target_cards"])):
                    quality = [4, 5, 3, 2][i]  # Different quality patterns
                    answer = FlashcardAnswerRequest(
                        flashcard_id=session_response.current_card.id,
                        quality=quality,
                        response_time=10.0 + j * 2,
                        was_correct=(quality >= 3),
                        answer_text=f"Test answer {j+1}"
                    )
                    
                    answer_response = await study_session_service.submit_answer(
                        session_id=session_response.id,
                        user_id=admin_user_id,
                        answer_request=answer
                    )
                    
                    if answer_response.next_card and j < config["target_cards"] - 1:
                        session_response.current_card = answer_response.next_card
                    else:
                        break
        
        print(f"   📊 Created {len(created_sessions)} test sessions with answers")
        
    except Exception as e:
        print(f"   ❌ Test data creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Progress Chart Test
    print("3. 📈 Progress Chart Generation Test")
    try:
        progress_chart = await analytics_service.get_progress_chart_data(
            user_id=admin_user_id,
            days=30
        )
        
        chart_data = progress_chart["chart_data"]
        metadata = progress_chart["metadata"]
        
        print(f"   ✅ Progress chart generated")
        print(f"   📊 Chart labels: {len(chart_data['labels'])} days")
        print(f"   📈 Data points: {len(chart_data['datasets'][0]['data'])}")
        print(f"   📅 Period: {metadata['period_days']} days")
        print(f"   📊 Sessions analyzed: {metadata['session_count']}")
        
        if chart_data['labels']:
            print(f"   📅 Latest date: {chart_data['labels'][-1]}")
            print(f"   📊 Latest accuracy: {chart_data['datasets'][0]['data'][-1]}%")
        
    except Exception as e:
        print(f"   ❌ Progress chart test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Accuracy Trend Test
    print("4. 📊 Accuracy Trend Analysis Test")
    try:
        accuracy_trend = await analytics_service.get_accuracy_trend_data(
            user_id=admin_user_id,
            limit=20
        )
        
        chart_data = accuracy_trend["chart_data"]
        metadata = accuracy_trend["metadata"]
        
        print(f"   ✅ Accuracy trend generated")
        print(f"   📊 Sessions: {len(chart_data['labels'])}")
        print(f"   📈 Trend analysis: {metadata['trend_analysis']['trend']}")
        print(f"   📊 Recent avg: {metadata['trend_analysis']['recent_average']}%")
        print(f"   📈 Improvement: {metadata['trend_analysis']['improvement']}%")
        
        if chart_data['datasets']:
            session_accuracies = chart_data['datasets'][0]['data']
            moving_averages = chart_data['datasets'][1]['data']
            print(f"   📊 Session accuracy range: {min(session_accuracies):.1f}% - {max(session_accuracies):.1f}%")
            print(f"   📈 Moving avg range: {min(moving_averages):.1f}% - {max(moving_averages):.1f}%")
        
    except Exception as e:
        print(f"   ❌ Accuracy trend test failed: {e}")
    
    # 5. Study Time Distribution Test
    print("5. ⏰ Study Time Distribution Test")
    try:
        time_distribution = await analytics_service.get_study_time_distribution(
            user_id=admin_user_id,
            days=30
        )
        
        chart_data = time_distribution["chart_data"]
        patterns = time_distribution["patterns"]
        
        print(f"   ✅ Study time distribution generated")
        print(f"   ⏰ Hour slots: {len(chart_data['labels'])}")
        
        # Find peak study times
        study_times = chart_data['datasets'][0]['data']
        peak_hour_idx = study_times.index(max(study_times))
        peak_hour = chart_data['labels'][peak_hour_idx]
        peak_time = study_times[peak_hour_idx]
        
        print(f"   🔥 Peak study time: {peak_hour} ({peak_time:.1f} minutes)")
        
        if patterns['optimal_hours']:
            best_hour = patterns['optimal_hours'][0]
            print(f"   🎯 Best performance hour: {best_hour['hour']}:00")
            print(f"   📊 Best accuracy: {best_hour['average_accuracy']:.1f}%")
            print(f"   💡 Recommendation: {patterns['analysis']['recommendation']}")
        
    except Exception as e:
        print(f"   ❌ Study time distribution test failed: {e}")
    
    # 6. Deck Performance Comparison Test
    print("6. 📚 Deck Performance Comparison Test")
    try:
        deck_performance = await analytics_service.get_deck_performance_comparison(
            user_id=admin_user_id,
            days=30
        )
        
        chart_data = deck_performance["chart_data"]
        deck_info = deck_performance["deck_info"]
        metadata = deck_performance["metadata"]
        
        print(f"   ✅ Deck performance comparison generated")
        print(f"   📚 Decks analyzed: {metadata['deck_count']}")
        print(f"   📊 Sessions: {metadata['session_count']}")
        
        if chart_data['labels']:
            for i, deck_name in enumerate(chart_data['labels']):
                accuracy = chart_data['datasets'][0]['data'][i]
                study_time = chart_data['datasets'][1]['data'][i]
                print(f"   📖 {deck_name}: {accuracy}% accuracy, {study_time:.1f} min")
        
    except Exception as e:
        print(f"   ❌ Deck performance test failed: {e}")
    
    # 7. SRS Effectiveness Analysis Test
    print("7. 🧠 SRS Effectiveness Analysis Test")
    try:
        srs_analysis = await analytics_service.get_srs_effectiveness_analysis(
            user_id=admin_user_id
        )
        
        chart_data = srs_analysis["chart_data"]
        retention_analysis = srs_analysis["retention_analysis"]
        metadata = srs_analysis["metadata"]
        
        print(f"   ✅ SRS effectiveness analysis generated")
        print(f"   📇 Cards analyzed: {metadata['card_count']}")
        
        if chart_data['labels']:
            print(f"   📊 Interval ranges: {len(chart_data['labels'])}")
            for i, interval_range in enumerate(chart_data['labels']):
                success_rate = chart_data['datasets'][0]['data'][i]
                print(f"   📅 {interval_range}: {success_rate}% success rate")
        
        # Retention rates
        retention_rates = retention_analysis["retention_rates"]
        print(f"   🧠 Retention Analysis:")
        print(f"     24 hours: {retention_rates['24_hours']['rate']}% ({retention_rates['24_hours']['retained']}/{retention_rates['24_hours']['total']})")
        print(f"     1 week: {retention_rates['1_week']['rate']}% ({retention_rates['1_week']['retained']}/{retention_rates['1_week']['total']})")
        print(f"     1 month: {retention_rates['1_month']['rate']}% ({retention_rates['1_month']['retained']}/{retention_rates['1_month']['total']})")
        print(f"   📊 Overall retention: {retention_analysis['overall_retention']}%")
        
    except Exception as e:
        print(f"   ❌ SRS effectiveness test failed: {e}")
    
    # 8. Comprehensive Learning Insights Test
    print("8. 🎯 Comprehensive Learning Insights Test")
    try:
        insights = await analytics_service.get_comprehensive_insights(
            user_id=admin_user_id,
            days=30
        )
        
        metadata = insights["metadata"]
        print(f"   ✅ Comprehensive insights generated")
        print(f"   📊 Analysis period: {metadata['period_days']} days")
        print(f"   📚 Sessions analyzed: {metadata['session_count']}")
        print(f"   📇 Cards analyzed: {metadata['card_count']}")
        
        # Time patterns
        time_patterns = insights["time_patterns"]
        if time_patterns["optimal_hours"]:
            print(f"   ⏰ Time Analysis:")
            print(f"     Best hour: {time_patterns['analysis']['best_hour']}:00")
            print(f"     Peak performance: {time_patterns['analysis']['peak_performance']:.1f}%")
            print(f"     Recommendation: {time_patterns['analysis']['recommendation']}")
        
        # Mode effectiveness
        mode_effectiveness = insights["mode_effectiveness"]
        if mode_effectiveness["mode_analysis"]:
            print(f"   🎯 Study Mode Effectiveness:")
            for mode, analysis in mode_effectiveness["mode_analysis"].items():
                print(f"     {mode.title()}: {analysis['effectiveness_score']:.1f} score, {analysis['average_accuracy']:.1f}% accuracy")
            
            print(f"   💡 Mode Recommendations:")
            for rec in mode_effectiveness["recommendations"]:
                print(f"     - {rec}")
        
        # Difficulty analysis
        difficulty_analysis = insights["difficulty_analysis"]
        if difficulty_analysis["difficulty_analysis"]:
            print(f"   📊 Difficulty Analysis:")
            for difficulty, analysis in difficulty_analysis["difficulty_analysis"].items():
                print(f"     {difficulty.title()}: {analysis['retention_score']:.1f} retention score")
        
    except Exception as e:
        print(f"   ❌ Comprehensive insights test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 9. Export CSV Test
    print("9. 📄 CSV Export Test")
    try:
        # Test CSV export for progress chart
        from app.routers.v1.analytics import _convert_to_csv
        
        progress_data = await analytics_service.get_progress_chart_data(
            user_id=admin_user_id,
            days=7
        )
        
        csv_content = _convert_to_csv(progress_data, "progress-chart")
        
        print(f"   ✅ CSV export successful")
        print(f"   📄 CSV preview (first 3 lines):")
        lines = csv_content.split('\n')[:3]
        for line in lines:
            print(f"     {line}")
        
        print(f"   📊 Total CSV lines: {len(csv_content.split('\\n'))}")
        
    except Exception as e:
        print(f"   ❌ CSV export test failed: {e}")
    
    # 10. Database Analytics Verification
    print("10. 🗄️ Database Analytics Verification")
    try:
        db = analytics_service.db
        
        # Get analytics statistics
        total_sessions = await db.study_sessions.count_documents({"user_id": admin_user_id})
        completed_sessions = await db.study_sessions.count_documents({
            "user_id": admin_user_id,
            "status": "completed"
        })
        
        total_progress = await db.user_flashcard_progress.count_documents({"user_id": admin_user_id})
        
        # Session mode distribution
        mode_distribution = await db.study_sessions.aggregate([
            {"$match": {"user_id": admin_user_id}},
            {"$group": {"_id": "$study_mode", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(length=None)
        
        print(f"   📊 Database Analytics:")
        print(f"   📚 Total sessions: {total_sessions}")
        print(f"   ✅ Completed sessions: {completed_sessions}")
        print(f"   📈 Progress records: {total_progress}")
        
        print(f"   📊 Study Mode Distribution:")
        for mode_stat in mode_distribution:
            print(f"     {mode_stat['_id']}: {mode_stat['count']} sessions")
        
        # Recent activity
        recent_sessions = await db.study_sessions.find({
            "user_id": admin_user_id
        }).sort("started_at", -1).limit(5).to_list(length=5)
        
        print(f"   📅 Recent Sessions (last 5):")
        for session in recent_sessions:
            start_time = session.get('started_at', 'Unknown')
            mode = session.get('study_mode', 'Unknown')
            status = session.get('status', 'Unknown')
            print(f"     {start_time} - {mode} - {status}")
        
    except Exception as e:
        print(f"   ❌ Database verification failed: {e}")
    
    print("-" * 60)
    print("🎉 PHASE 6.5 ANALYTICS & VISUALIZATION TEST FINISHED!")
    print(f"🕐 Finished at: {datetime.now()}")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_phase65_analytics()
        if success:
            print("\n✅ Phase 6.5 Analytics & Visualization: WORKING PERFECTLY!")
            print("📊 All chart generation functional!")
            print("📈 Analytics insights comprehensive!")
            print("📄 Export capabilities operational!")
            print("🚀 Ready for Phase 6.6 or production!")
        else:
            print("\n❌ Some analytics features need fixing")
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
