
"""
Database module for storing game state, play-by-play events, and configurations.
Uses SQLite for simple, file-based storage.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """Handles all database operations for the INPLAY Agent."""
    
    def __init__(self, db_path: str = "inplay_agent.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database schema."""
        logger.info(f"Initializing database at {self.db_path}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # API Configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_type TEXT NOT NULL,
                    endpoint_url TEXT NOT NULL,
                    auth_key TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Game State table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    game_name TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    home_score INTEGER DEFAULT 0,
                    away_score INTEGER DEFAULT 0,
                    quarter INTEGER DEFAULT 1,
                    clock TEXT,
                    game_status TEXT,
                    game_status_detail TEXT,
                    possession_team TEXT,
                    down INTEGER,
                    distance INTEGER,
                    yard_line INTEGER,
                    venue TEXT,
                    attendance INTEGER,
                    weather TEXT,
                    spread TEXT,
                    total_line REAL,
                    raw_data TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Quarter Scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarter_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    quarter INTEGER NOT NULL,
                    home_score INTEGER DEFAULT 0,
                    away_score INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES game_state(event_id),
                    UNIQUE(event_id, quarter)
                )
            """)
            
            # Play-by-Play table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    play_id TEXT UNIQUE,
                    quarter INTEGER NOT NULL,
                    clock TEXT NOT NULL,
                    play_type TEXT,
                    play_text TEXT NOT NULL,
                    team_id TEXT,
                    team_name TEXT,
                    yards_gained INTEGER,
                    down INTEGER,
                    distance INTEGER,
                    yard_line INTEGER,
                    is_scoring_play INTEGER DEFAULT 0,
                    score_value INTEGER DEFAULT 0,
                    home_score INTEGER,
                    away_score INTEGER,
                    ai_commentary TEXT,
                    significance_score REAL,
                    momentum_shift TEXT,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES game_state(event_id)
                )
            """)
            
            # AI Commentary Analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES game_state(event_id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_plays_event_id 
                ON plays(event_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_plays_quarter 
                ON plays(event_id, quarter)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_game_state_event_id 
                ON game_state(event_id)
            """)
            
            logger.info("Database initialized successfully")
    
    # API Configuration methods
    def save_api_config(self, api_type: str, endpoint_url: str, auth_key: Optional[str] = None) -> int:
        """Save or update API configuration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Deactivate all existing configs of this type
            cursor.execute("""
                UPDATE api_config 
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
                WHERE api_type = ?
            """, (api_type,))
            
            # Insert new config
            cursor.execute("""
                INSERT INTO api_config (api_type, endpoint_url, auth_key, is_active)
                VALUES (?, ?, ?, 1)
            """, (api_type, endpoint_url, auth_key))
            
            config_id = cursor.lastrowid
            logger.info(f"Saved API config: {api_type} - {endpoint_url}")
            return config_id
    
    def get_active_api_config(self, api_type: str = "espn") -> Optional[Dict[str, Any]]:
        """Get the active API configuration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM api_config 
                WHERE api_type = ? AND is_active = 1 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (api_type,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Game State methods
    def save_game_state(self, game_data: Dict[str, Any]) -> int:
        """Save or update game state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO game_state (
                    event_id, game_name, home_team, away_team, 
                    home_score, away_score, quarter, clock,
                    game_status, game_status_detail, possession_team,
                    down, distance, yard_line, venue, attendance,
                    weather, spread, total_line, raw_data, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(event_id) DO UPDATE SET
                    home_score = excluded.home_score,
                    away_score = excluded.away_score,
                    quarter = excluded.quarter,
                    clock = excluded.clock,
                    game_status = excluded.game_status,
                    game_status_detail = excluded.game_status_detail,
                    possession_team = excluded.possession_team,
                    down = excluded.down,
                    distance = excluded.distance,
                    yard_line = excluded.yard_line,
                    attendance = excluded.attendance,
                    weather = excluded.weather,
                    spread = excluded.spread,
                    total_line = excluded.total_line,
                    raw_data = excluded.raw_data,
                    last_updated = CURRENT_TIMESTAMP
            """, (
                game_data.get('event_id'),
                game_data.get('game_name'),
                game_data.get('home_team'),
                game_data.get('away_team'),
                game_data.get('home_score', 0),
                game_data.get('away_score', 0),
                game_data.get('quarter', 1),
                game_data.get('clock'),
                game_data.get('game_status'),
                game_data.get('game_status_detail'),
                game_data.get('possession_team'),
                game_data.get('down'),
                game_data.get('distance'),
                game_data.get('yard_line'),
                game_data.get('venue'),
                game_data.get('attendance'),
                game_data.get('weather'),
                game_data.get('spread'),
                game_data.get('total_line'),
                json.dumps(game_data.get('raw_data', {}))
            ))
            
            game_id = cursor.lastrowid
            logger.info(f"Saved game state: {game_data.get('event_id')} - {game_data.get('game_name')}")
            return game_id
    
    def get_game_state(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM game_state WHERE event_id = ?
            """, (event_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('raw_data'):
                    try:
                        result['raw_data'] = json.loads(result['raw_data'])
                    except json.JSONDecodeError:
                        result['raw_data'] = {}
                return result
            return None
    
    # Quarter Scores methods
    def save_quarter_score(self, event_id: str, quarter: int, home_score: int, away_score: int):
        """Save quarter-by-quarter scores."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO quarter_scores (event_id, quarter, home_score, away_score)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(event_id, quarter) DO UPDATE SET
                    home_score = excluded.home_score,
                    away_score = excluded.away_score
            """, (event_id, quarter, home_score, away_score))
            
            logger.debug(f"Saved Q{quarter} scores: Home {home_score}, Away {away_score}")
    
    def get_quarter_scores(self, event_id: str) -> List[Dict[str, Any]]:
        """Get all quarter scores for a game."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM quarter_scores 
                WHERE event_id = ? 
                ORDER BY quarter ASC
            """, (event_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Play-by-Play methods
    def save_play(self, play_data: Dict[str, Any]) -> int:
        """Save a play-by-play event."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO plays (
                    event_id, play_id, quarter, clock, play_type, play_text,
                    team_id, team_name, yards_gained, down, distance, yard_line,
                    is_scoring_play, score_value, home_score, away_score,
                    ai_commentary, significance_score, momentum_shift, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(play_id) DO UPDATE SET
                    ai_commentary = excluded.ai_commentary,
                    significance_score = excluded.significance_score,
                    momentum_shift = excluded.momentum_shift
            """, (
                play_data.get('event_id'),
                play_data.get('play_id'),
                play_data.get('quarter'),
                play_data.get('clock'),
                play_data.get('play_type'),
                play_data.get('play_text'),
                play_data.get('team_id'),
                play_data.get('team_name'),
                play_data.get('yards_gained'),
                play_data.get('down'),
                play_data.get('distance'),
                play_data.get('yard_line'),
                play_data.get('is_scoring_play', 0),
                play_data.get('score_value', 0),
                play_data.get('home_score'),
                play_data.get('away_score'),
                play_data.get('ai_commentary'),
                play_data.get('significance_score'),
                play_data.get('momentum_shift'),
                json.dumps(play_data.get('raw_data', {}))
            ))
            
            play_id = cursor.lastrowid
            logger.debug(f"Saved play: {play_data.get('play_text')[:50]}")
            return play_id
    
    def get_plays(self, event_id: str, limit: Optional[int] = None, quarter: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get play-by-play events for a game."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM plays 
                WHERE event_id = ?
            """
            params = [event_id]
            
            if quarter is not None:
                query += " AND quarter = ?"
                params.append(quarter)
            
            query += " ORDER BY id DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            
            plays = []
            for row in cursor.fetchall():
                play = dict(row)
                if play.get('raw_data'):
                    try:
                        play['raw_data'] = json.loads(play['raw_data'])
                    except json.JSONDecodeError:
                        play['raw_data'] = {}
                plays.append(play)
            
            return plays
    
    def get_latest_play(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent play for a game."""
        plays = self.get_plays(event_id, limit=1)
        return plays[0] if plays else None
    
    # AI Analysis methods
    def save_ai_analysis(self, event_id: str, analysis_type: str, content: str, metadata: Optional[Dict] = None):
        """Save AI-generated analysis."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ai_analysis (event_id, analysis_type, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                event_id,
                analysis_type,
                content,
                json.dumps(metadata) if metadata else None
            ))
            
            logger.debug(f"Saved AI analysis: {analysis_type}")
    
    def get_ai_analysis(self, event_id: str, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get AI analysis for a game."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if analysis_type:
                cursor.execute("""
                    SELECT * FROM ai_analysis 
                    WHERE event_id = ? AND analysis_type = ?
                    ORDER BY created_at DESC
                """, (event_id, analysis_type))
            else:
                cursor.execute("""
                    SELECT * FROM ai_analysis 
                    WHERE event_id = ?
                    ORDER BY created_at DESC
                """, (event_id,))
            
            analyses = []
            for row in cursor.fetchall():
                analysis = dict(row)
                if analysis.get('metadata'):
                    try:
                        analysis['metadata'] = json.loads(analysis['metadata'])
                    except json.JSONDecodeError:
                        analysis['metadata'] = {}
                analyses.append(analysis)
            
            return analyses
    
    # Utility methods
    def clear_game_data(self, event_id: str):
        """Clear all data for a specific game."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM plays WHERE event_id = ?", (event_id,))
            cursor.execute("DELETE FROM quarter_scores WHERE event_id = ?", (event_id,))
            cursor.execute("DELETE FROM ai_analysis WHERE event_id = ?", (event_id,))
            cursor.execute("DELETE FROM game_state WHERE event_id = ?", (event_id,))
            
            logger.info(f"Cleared all data for game: {event_id}")
    
    def get_all_tracked_games(self) -> List[Dict[str, Any]]:
        """Get all games currently being tracked."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM game_state 
                ORDER BY last_updated DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
