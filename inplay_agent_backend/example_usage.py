
"""
Example usage of the INPLAY Agent Backend.
Demonstrates how to use the Python client to interact with the API.
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def find_and_track_game():
    """Find live games and start tracking one."""
    
    print_section("INPLAY Agent Backend - Example Usage")
    
    # 1. Check API health
    print("1. Checking API health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        health = response.json()
        print(f"✓ API Status: {health['status']}")
        print(f"  Timestamp: {health['timestamp']}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: Could not connect to API. Is the server running?")
        print(f"  Run: python app.py")
        return
    
    # 2. Get live games
    print_section("Finding Live Games")
    
    try:
        response = requests.get(f"{BASE_URL}/api/games/live")
        live_games = response.json()
        
        print(f"Found {live_games['count']} live games:")
        
        if live_games['count'] == 0:
            print("\n⚠ No live games at the moment.")
            print("  This example works best during NFL game days.")
            print("\n  You can test with a recent game ID:")
            print("  Example: 401671746 (SEA vs TB - Oct 18, 2025)")
            
            event_id = input("\nEnter a game event ID to track (or press Enter to skip): ").strip()
            
            if not event_id:
                print("\nSkipping game tracking. Showing API documentation instead...")
                show_api_docs()
                return
        else:
            # Show live games
            for i, game in enumerate(live_games['games'], 1):
                print(f"\n{i}. {game['name']}")
                print(f"   Score: {game['away_team']} {game['away_score']} - {game['home_team']} {game['home_score']}")
                print(f"   Status: Q{game['quarter']} {game['clock']}")
                print(f"   Event ID: {game['event_id']}")
            
            # Select game to track
            choice = input(f"\nSelect game to track (1-{live_games['count']}): ").strip()
            
            try:
                index = int(choice) - 1
                event_id = live_games['games'][index]['event_id']
            except (ValueError, IndexError):
                print("Invalid selection. Using first game.")
                event_id = live_games['games'][0]['event_id']
        
        # 3. Start tracking
        print_section(f"Starting Game Tracking: {event_id}")
        
        response = requests.get(
            f"{BASE_URL}/api/game/start",
            params={'event_id': event_id, 'poll_interval': 15}
        )
        
        result = response.json()
        
        if result.get('success'):
            print(f"✓ Started tracking game: {event_id}")
            print(f"  Poll interval: {result['poll_interval']}s")
        else:
            print(f"✗ Failed to start tracking: {result.get('message')}")
            return
        
        # 4. Monitor game for a while
        print_section("Live Game Monitoring")
        print("Monitoring game state (will check 5 times)...\n")
        
        for i in range(5):
            time.sleep(10)  # Wait 10 seconds between checks
            
            # Get current game state
            response = requests.get(
                f"{BASE_URL}/api/game/current",
                params={'event_id': event_id}
            )
            
            data = response.json()
            
            if not data.get('success'):
                print(f"✗ Error getting game data: {data.get('error')}")
                continue
            
            game = data['game']
            
            print(f"\n[Check {i+1}/5] {datetime.now().strftime('%H:%M:%S')}")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"{game['name']}")
            print(f"Status: {game['status_detail']}")
            print(f"Quarter: {game['quarter']} | Clock: {game['clock']}")
            print(f"\nScore:")
            print(f"  {game['away_team']}: {game['away_score']}")
            print(f"  {game['home_team']}: {game['home_score']}")
            
            if game.get('spread'):
                print(f"\nBetting:")
                print(f"  Spread: {game['spread']}")
                if game.get('total_line'):
                    current_total = game['home_score'] + game['away_score']
                    print(f"  Total: O/U {game['total_line']} (Current: {current_total})")
            
            # Get quarter scores
            if data.get('quarter_scores'):
                print(f"\nQuarter-by-Quarter:")
                print(f"  {'Quarter':<10} {'Home':<6} {'Away':<6}")
                for q in data['quarter_scores']:
                    print(f"  Q{q['quarter']:<9} {q['home_score']:<6} {q['away_score']:<6}")
            
            # Get recent plays
            response = requests.get(
                f"{BASE_URL}/api/game/plays",
                params={'event_id': event_id, 'limit': 3}
            )
            
            plays_data = response.json()
            
            if plays_data.get('success') and plays_data['plays']:
                print(f"\nRecent Plays:")
                for play in plays_data['plays'][:3]:
                    print(f"\n  Q{play['quarter']} - {play['clock']}")
                    print(f"  {play['play_text'][:70]}")
                    
                    if play.get('is_scoring_play'):
                        print(f"  🏈 SCORING PLAY (+{play['score_value']} pts)")
                    
                    if play.get('ai_commentary'):
                        print(f"  💬 AI: {play['ai_commentary'][:100]}...")
                    
                    if play.get('momentum_shift') and play['momentum_shift'] != 'Neutral':
                        print(f"  📊 Momentum: {play['momentum_shift']}")
        
        # 5. Get AI analysis
        print_section("AI Analysis")
        
        response = requests.get(
            f"{BASE_URL}/api/game/analysis",
            params={'event_id': event_id, 'type': 'game_summary'}
        )
        
        analysis_data = response.json()
        
        if analysis_data.get('success') and analysis_data['analyses']:
            print("Latest AI Game Analysis:")
            analysis = analysis_data['analyses'][0]
            print(f"\n{analysis['content']}\n")
            print(f"Generated: {analysis['created_at']}")
        else:
            print("No AI analysis available yet.")
            print("(Make sure OPENAI_API_KEY is set in .env)")
        
        # 6. Stop tracking (optional)
        print_section("Cleanup")
        
        stop = input("Stop tracking this game? (y/n): ").lower().strip()
        
        if stop == 'y':
            response = requests.get(
                f"{BASE_URL}/api/game/stop",
                params={'event_id': event_id}
            )
            
            result = response.json()
            if result.get('success'):
                print(f"✓ Stopped tracking game: {event_id}")
            else:
                print(f"Note: {result.get('message')}")
        else:
            print("Game tracking continues in background.")
            print(f"To stop later: curl \"http://localhost:5000/api/game/stop?event_id={event_id}\"")
        
        print("\n✓ Example completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error communicating with API: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


def show_api_docs():
    """Show API documentation."""
    try:
        response = requests.get(f"{BASE_URL}/api")
        docs = response.json()
        
        print("\nAPI Endpoints:")
        for name, endpoint in docs['endpoints'].items():
            print(f"\n• {endpoint['method']} {endpoint['path']}")
            print(f"  {endpoint['description']}")
        
    except Exception as e:
        print(f"Error getting API docs: {e}")


if __name__ == "__main__":
    try:
        find_and_track_game()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
