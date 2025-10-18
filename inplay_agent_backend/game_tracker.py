"""
Game Tracker - Orchestrates API polling, database updates, and AI analysis.
"""

import logging
import threading
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from api_connector import APIConnector
from database import Database
from inplay_agent import INPLAYAgent, PlayTracker

logger = logging.getLogger(__name__)


class GameTracker:
    """Main orchestrator for tracking NFL games in real-time."""
    
    def __init__(self, database: Database, api_connector: APIConnector, 
                 inplay_agent: INPLAYAgent, poll_interval: int = 15):
        self.database = database
        self.api_connector = api_connector
        self.inplay_agent = inplay_agent
        self.poll_interval = poll_interval
        
        self.play_tracker = PlayTracker()
        self.is_tracking = False
        self.tracking_thread = None
        self.current_event_id = None
        
        self.callbacks = []
        
        logger.info(f"GameTracker initialized with {poll_interval}s poll interval")
    
    def register_callback(self, callback: Callable):
        """Register a callback function to be called on updates."""
        self.callbacks.append(callback)
        logger.debug(f"Callback registered: {callback.__name__}")
    
    def start_tracking(self, event_id: str) -> bool:
        """Start tracking a game."""
        
        if self.is_tracking:
            logger.warning(f"Already tracking game: {self.current_event_id}")
            return False
        
        # Verify game exists
        game_event = self.api_connector.find_game_by_id(event_id)
        if not game_event:
            logger.error(f"Game not found: {event_id}")
            return False
        
        self.current_event_id = event_id
        self.is_tracking = True
        self.play_tracker.reset()
        
        # Start tracking in a separate thread
        self.tracking_thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True
        )
        self.tracking_thread.start()
        
        logger.info(f"Started tracking game: {event_id}")
        return True
    
    def stop_tracking(self):
        """Stop tracking the current game."""
        self.is_tracking = False
        
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5)
        
        logger.info(f"Stopped tracking game: {self.current_event_id}")
        self.current_event_id = None
    
    def _tracking_loop(self):
        """Main tracking loop that polls and updates data."""
        
        import time
        
        while self.is_tracking:
            try:
                # Fetch game data
                game_event = self.api_connector.find_game_by_id(self.current_event_id)
                
                if not game_event:
                    logger.error(f"Game not found: {self.current_event_id}")
                    time.sleep(self.poll_interval)
                    continue
                
                # Parse game event
                parsed_game = self.api_connector.parse_game_event(game_event)
                
                # Fetch detailed summary
                game_summary = self.api_connector.get_game_summary(self.current_event_id)
                if game_summary:
                    summary_data = self.api_connector.parse_game_summary(game_summary)
                    parsed_game['summary'] = summary_data
                
                # Process the update
                self._process_game_update(parsed_game)
                
                # Check if game is complete
                if parsed_game.get('game_status') == 'post':
                    logger.info(f"Game completed: {self.current_event_id}")
                    self._on_game_complete(parsed_game)
                    self.stop_tracking()
                    break
                
                # Wait for next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)
    
    def _process_game_update(self, game_data: Dict[str, Any]):
        """Process a game update."""
        
        try:
            # Save game state
            self.database.save_game_state(game_data)
            
            # Update quarter scores
            self._update_quarter_scores(game_data)
            
            # Process scoring plays
            if 'summary' in game_data and 'scoring_plays' in game_data['summary']:
                for scoring_play in game_data['summary']['scoring_plays']:
                    self._process_scoring_play(scoring_play, game_data)
            
            # Run AI analysis on game state
            game_insights = self.inplay_agent.analyze_game_state(game_data)
            
            # Save AI analysis
            if game_insights.get('game_commentary'):
                self.database.save_ai_analysis(
                    event_id=game_data['event_id'],
                    analysis_type='game_summary',
                    content=game_insights['game_commentary'],
                    metadata=game_insights
                )
            
            # Notify callbacks
            self._notify_callbacks({
                'type': 'game_update',
                'game_data': game_data,
                'insights': game_insights
            })
            
            logger.info(f"Processed update: {game_data['short_name']} - Q{game_data['quarter']} {game_data['clock']}")
            
        except Exception as e:
            logger.error(f"Error processing game update: {e}", exc_info=True)
    
    def _update_quarter_scores(self, game_data: Dict[str, Any]):
        """Update quarter-by-quarter scores."""
        
        try:
            quarter_scores = game_data.get('quarter_scores', {})
            home_scores = quarter_scores.get('home', [])
            away_scores = quarter_scores.get('away', [])
            
            # Save each quarter's score
            for quarter_num in range(1, len(home_scores) + 1):
                if quarter_num <= len(home_scores) and quarter_num <= len(away_scores):
                    self.database.save_quarter_score(
                        event_id=game_data['event_id'],
                        quarter=quarter_num,
                        home_score=home_scores[quarter_num - 1],
                        away_score=away_scores[quarter_num - 1]
                    )
            
            logger.debug(f"Updated quarter scores: {len(home_scores)} quarters")
            
        except Exception as e:
            logger.error(f"Error updating quarter scores: {e}")
    
    def _process_scoring_play(self, scoring_play: Dict[str, Any], game_data: Dict[str, Any]):
        """Process a scoring play and generate AI commentary."""
        
        try:
            play_id = scoring_play.get('play_id')
            
            # Check if we've already processed this play
            if not self.play_tracker.is_new_play(play_id):
                return
            
            # Build play data structure
            play_data = {
                'event_id': game_data['event_id'],
                'play_id': play_id,
                'quarter': scoring_play.get('quarter'),
                'clock': scoring_play.get('clock'),
                'play_type': scoring_play.get('play_type'),
                'play_text': scoring_play.get('play_text'),
                'team_id': scoring_play.get('team_id'),
                'team_name': self._get_team_name(scoring_play.get('team_id'), game_data),
                'yards_gained': None,  # Not available in scoring play summary
                'is_scoring_play': True,
                'score_value': scoring_play.get('score_value', 0),
                'home_score': scoring_play.get('home_score'),
                'away_score': scoring_play.get('away_score'),
                'raw_data': scoring_play
            }
            
            # Analyze the play with INPLAY Agent
            analysis = self.inplay_agent.analyze_play(play_data, game_data)
            
            # Add analysis to play data
            play_data['ai_commentary'] = analysis.get('ai_commentary')
            play_data['significance_score'] = analysis.get('significance_score')
            play_data['momentum_shift'] = analysis.get('momentum_shift')
            
            # Save to database
            self.database.save_play(play_data)
            
            # Notify callbacks
            self._notify_callbacks({
                'type': 'new_play',
                'play_data': play_data,
                'analysis': analysis
            })
            
            logger.info(f"Processed scoring play: {play_data['play_text'][:50]}")
            
        except Exception as e:
            logger.error(f"Error processing scoring play: {e}", exc_info=True)
    
    def _get_team_name(self, team_id: str, game_data: Dict[str, Any]) -> str:
        """Get team name from team ID."""
        if str(team_id) == str(game_data.get('home_team_id')):
            return game_data.get('home_team', 'Home')
        elif str(team_id) == str(game_data.get('away_team_id')):
            return game_data.get('away_team', 'Away')
        return 'Unknown'
    
    def _on_game_complete(self, game_data: Dict[str, Any]):
        """Handle game completion."""
        
        try:
            # Generate final game analysis
            final_insights = self.inplay_agent.analyze_game_state(game_data)
            
            # Save final analysis
            self.database.save_ai_analysis(
                event_id=game_data['event_id'],
                analysis_type='game_final',
                content=final_insights.get('game_commentary', 'Game completed.'),
                metadata=final_insights
            )
            
            # Notify callbacks
            self._notify_callbacks({
                'type': 'game_complete',
                'game_data': game_data,
                'final_insights': final_insights
            })
            
            logger.info(f"Game complete: {game_data['game_name']} - Final: {game_data['away_team']} {game_data['away_score']}, {game_data['home_team']} {game_data['home_score']}")
            
        except Exception as e:
            logger.error(f"Error on game complete: {e}", exc_info=True)
    
    def _notify_callbacks(self, data: Dict[str, Any]):
        """Notify all registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback {callback.__name__}: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current tracking status."""
        return {
            'is_tracking': self.is_tracking,
            'event_id': self.current_event_id,
            'poll_interval': self.poll_interval,
            'plays_tracked': self.play_tracker.get_play_count()
        }
    
    def update_poll_interval(self, interval: int):
        """Update polling interval."""
        self.poll_interval = interval
        logger.info(f"Poll interval updated to {interval}s")


class GameManager:
    """Manages multiple game trackers and configurations."""
    
    def __init__(self):
        self.database = Database()
        self.game_trackers = {}
        
        logger.info("GameManager initialized")
    
    def configure_api(self, api_type: str, endpoint_url: str, auth_key: Optional[str] = None) -> int:
        """Configure API settings."""
        config_id = self.database.save_api_config(api_type, endpoint_url, auth_key)
        logger.info(f"API configured: {api_type}")
        return config_id
    
    def get_api_connector(self) -> APIConnector:
        """Get configured API connector."""
        # Try to get custom config first
        config = self.database.get_active_api_config("custom")
        
        if config:
            return APIConnector(
                api_type="custom",
                custom_endpoint=config['endpoint_url'],
                auth_key=config.get('auth_key')
            )
        
        # Default to ESPN
        return APIConnector(api_type="espn")
    
    def start_tracking_game(self, event_id: str, poll_interval: int = 15) -> bool:
        """Start tracking a game."""
        
        if event_id in self.game_trackers:
            logger.warning(f"Already tracking game: {event_id}")
            return False
        
        # Create components
        api_connector = self.get_api_connector()
        inplay_agent = INPLAYAgent()
        
        # Create game tracker
        tracker = GameTracker(
            database=self.database,
            api_connector=api_connector,
            inplay_agent=inplay_agent,
            poll_interval=poll_interval
        )
        
        # Start tracking
        success = tracker.start_tracking(event_id)
        
        if success:
            self.game_trackers[event_id] = tracker
            logger.info(f"Started tracking: {event_id}")
        
        return success
    
    def stop_tracking_game(self, event_id: str):
        """Stop tracking a game."""
        if event_id in self.game_trackers:
            tracker = self.game_trackers[event_id]
            tracker.stop_tracking()
            del self.game_trackers[event_id]
            logger.info(f"Stopped tracking: {event_id}")
    
    def get_game_state(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state."""
        return self.database.get_game_state(event_id)
    
    def get_game_plays(self, event_id: str, limit: Optional[int] = None) -> list:
        """Get game plays."""
        return self.database.get_plays(event_id, limit=limit)
    
    def get_quarter_scores(self, event_id: str) -> list:
        """Get quarter-by-quarter scores."""
        return self.database.get_quarter_scores(event_id)
    
    def get_tracked_games(self) -> list:
        """Get all tracked games."""
        return self.database.get_all_tracked_games()
    
    def find_live_games(self) -> list:
        """Find currently live games."""
        api_connector = self.get_api_connector()
        return api_connector.find_live_games()
