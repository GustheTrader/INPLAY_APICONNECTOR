"""
INPLAY Agent - Analyzes game plays and generates AI commentary.
Tracks momentum shifts, key events, and betting implications.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)


class INPLAYAgent:
    """AI agent that analyzes NFL plays and generates commentary."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
            self.ai_enabled = True
            logger.info("INPLAY Agent initialized with AI capabilities")
        else:
            self.client = None
            self.ai_enabled = False
            logger.warning("INPLAY Agent initialized without AI (no API key)")
        
        self.previous_score = None
        self.previous_quarter = None
    
    def analyze_play(self, play_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single play and generate commentary."""
        
        # Calculate basic significance
        significance = self._calculate_significance(play_data, game_state)
        
        # Determine momentum shift
        momentum = self._determine_momentum(play_data, game_state)
        
        # Generate AI commentary if enabled
        commentary = None
        if self.ai_enabled:
            commentary = self._generate_ai_commentary(play_data, game_state, significance, momentum)
        else:
            commentary = self._generate_basic_commentary(play_data, game_state, significance, momentum)
        
        analysis = {
            'play_text': play_data.get('play_text'),
            'significance_score': significance,
            'momentum_shift': momentum,
            'ai_commentary': commentary,
            'is_scoring_play': play_data.get('is_scoring_play', False),
            'quarter': play_data.get('quarter'),
            'clock': play_data.get('clock')
        }
        
        logger.debug(f"Play analyzed: significance={significance}, momentum={momentum}")
        return analysis
    
    def _calculate_significance(self, play_data: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate play significance score (0-10)."""
        score = 5.0  # Base score
        
        # Scoring plays are highly significant
        if play_data.get('is_scoring_play'):
            score += 3.0
        
        # Big yardage plays
        yards_gained = play_data.get('yards_gained', 0)
        if yards_gained >= 25:
            score += 2.0
        elif yards_gained >= 15:
            score += 1.0
        elif yards_gained < 0:
            score += 0.5  # Negative plays are notable
        
        # Turnovers (detected by play type)
        play_text = play_data.get('play_text', '').lower()
        if 'interception' in play_text or 'fumble' in play_text:
            score += 2.5
        
        # Fourth down conversions
        if play_data.get('down') == 4 and yards_gained >= play_data.get('distance', 0):
            score += 1.5
        
        # Late game situations (Q4 or OT)
        quarter = play_data.get('quarter', 1)
        if quarter >= 4:
            score += 1.0
        
        # Close game (within one score)
        home_score = game_state.get('home_score', 0)
        away_score = game_state.get('away_score', 0)
        score_diff = abs(home_score - away_score)
        if score_diff <= 8 and quarter >= 3:
            score += 0.5
        
        # Cap at 10
        return min(score, 10.0)
    
    def _determine_momentum(self, play_data: Dict[str, Any], game_state: Dict[str, Any]) -> str:
        """Determine momentum shift from the play."""
        
        # Check for scoring plays
        if play_data.get('is_scoring_play'):
            team_name = play_data.get('team_name', 'Unknown')
            score_value = play_data.get('score_value', 0)
            
            if score_value >= 6:  # Touchdown
                return f"Major shift to {team_name}"
            else:
                return f"Shift to {team_name}"
        
        # Big plays
        yards_gained = play_data.get('yards_gained', 0)
        if yards_gained >= 25:
            return f"Momentum building for {play_data.get('team_name', 'offense')}"
        
        # Turnovers
        play_text = play_data.get('play_text', '').lower()
        if 'interception' in play_text or 'fumble' in play_text:
            return "Major momentum swing"
        
        # Sacks
        if 'sack' in play_text:
            return "Defensive momentum"
        
        # Fourth down stops
        if play_data.get('down') == 4 and yards_gained < play_data.get('distance', 0):
            return "Defensive stand"
        
        return "Neutral"
    
    def _generate_ai_commentary(self, play_data: Dict[str, Any], game_state: Dict[str, Any], 
                                 significance: float, momentum: str) -> str:
        """Generate AI-powered commentary using OpenAI."""
        
        try:
            # Build context for AI
            context = self._build_context(play_data, game_state)
            
            prompt = f"""You are an expert NFL analyst providing live game commentary.

Game Context:
{context}

Current Play:
Quarter: {play_data.get('quarter', 'N/A')}
Clock: {play_data.get('clock', 'N/A')}
Play: {play_data.get('play_text', 'N/A')}
Significance Score: {significance}/10
Momentum: {momentum}

Provide a brief, insightful commentary (2-3 sentences) about this play. Focus on:
1. What makes this play important in the game context
2. Impact on momentum or game flow
3. Betting implications if relevant (spread/total)

Keep it concise, professional, and engaging."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert NFL analyst providing concise, insightful game commentary."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            commentary = response.choices[0].message.content.strip()
            logger.debug(f"Generated AI commentary: {commentary[:50]}...")
            return commentary
            
        except Exception as e:
            logger.error(f"Error generating AI commentary: {e}")
            return self._generate_basic_commentary(play_data, game_state, significance, momentum)
    
    def _generate_basic_commentary(self, play_data: Dict[str, Any], game_state: Dict[str, Any],
                                    significance: float, momentum: str) -> str:
        """Generate basic rule-based commentary when AI is unavailable."""
        
        play_text = play_data.get('play_text', 'Unknown play')
        quarter = play_data.get('quarter', 'N/A')
        clock = play_data.get('clock', 'N/A')
        
        commentary_parts = []
        
        # Opening
        commentary_parts.append(f"Q{quarter} - {clock}:")
        
        # Scoring play
        if play_data.get('is_scoring_play'):
            score_value = play_data.get('score_value', 0)
            if score_value >= 6:
                commentary_parts.append("TOUCHDOWN!")
            elif score_value == 3:
                commentary_parts.append("Field goal is good.")
            
            home_score = play_data.get('home_score', 0)
            away_score = play_data.get('away_score', 0)
            commentary_parts.append(f"Score: {away_score}-{home_score}.")
        
        # Big play
        yards_gained = play_data.get('yards_gained', 0)
        if yards_gained >= 25:
            commentary_parts.append(f"Big play of {yards_gained} yards!")
        
        # Significance
        if significance >= 8.0:
            commentary_parts.append("This is a crucial moment in the game.")
        
        # Momentum
        if momentum != "Neutral":
            commentary_parts.append(f"{momentum}.")
        
        return " ".join(commentary_parts)
    
    def _build_context(self, play_data: Dict[str, Any], game_state: Dict[str, Any]) -> str:
        """Build context string for AI analysis."""
        
        context_parts = [
            f"Game: {game_state.get('game_name', 'Unknown')}",
            f"Score: {game_state.get('away_team', 'Away')} {game_state.get('away_score', 0)} - {game_state.get('home_team', 'Home')} {game_state.get('home_score', 0)}",
            f"Quarter: {game_state.get('quarter', 'N/A')}",
            f"Clock: {game_state.get('clock', 'N/A')}"
        ]
        
        # Add betting context if available
        if game_state.get('spread'):
            context_parts.append(f"Spread: {game_state.get('spread')}")
        if game_state.get('total_line'):
            current_total = game_state.get('home_score', 0) + game_state.get('away_score', 0)
            context_parts.append(f"Total: O/U {game_state.get('total_line')} (Current: {current_total})")
        
        # Add situation if available
        if game_state.get('down'):
            context_parts.append(f"Down: {game_state.get('down')} & {game_state.get('distance', 0)}")
        
        return "\n".join(context_parts)
    
    def analyze_game_state(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall game state and generate insights."""
        
        home_score = game_state.get('home_score', 0)
        away_score = game_state.get('away_score', 0)
        quarter = game_state.get('quarter', 1)
        
        insights = {
            'score_differential': abs(home_score - away_score),
            'leading_team': game_state.get('home_team') if home_score > away_score else game_state.get('away_team'),
            'game_phase': self._determine_game_phase(quarter),
            'game_competitiveness': self._determine_competitiveness(home_score, away_score, quarter)
        }
        
        # Betting analysis
        if game_state.get('spread'):
            insights['betting_analysis'] = self._analyze_betting(game_state)
        
        # Generate overall commentary
        if self.ai_enabled:
            insights['game_commentary'] = self._generate_game_commentary(game_state, insights)
        
        return insights
    
    def _determine_game_phase(self, quarter: int) -> str:
        """Determine current game phase."""
        if quarter <= 1:
            return "Early Game"
        elif quarter == 2:
            return "Late First Half"
        elif quarter == 3:
            return "Second Half Start"
        elif quarter == 4:
            return "Fourth Quarter"
        else:
            return "Overtime"
    
    def _determine_competitiveness(self, home_score: int, away_score: int, quarter: int) -> str:
        """Determine how competitive the game is."""
        diff = abs(home_score - away_score)
        
        if diff <= 3:
            return "Very Close"
        elif diff <= 7:
            return "One Score Game"
        elif diff <= 14:
            return "Two Score Game"
        else:
            return "Blowout" if quarter >= 3 else "Developing Lead"
    
    def _analyze_betting(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze betting implications."""
        
        home_score = game_state.get('home_score', 0)
        away_score = game_state.get('away_score', 0)
        total = home_score + away_score
        
        analysis = {
            'current_total': total
        }
        
        # Spread analysis
        if game_state.get('spread'):
            spread_str = game_state.get('spread', '')
            # Parse spread (e.g., "SEA -3.5")
            try:
                parts = spread_str.split()
                if len(parts) >= 2:
                    spread_value = float(parts[1])
                    favored_team = parts[0]
                    
                    # Determine if favorite is covering
                    home_team_abbr = game_state.get('home_team_abbr', '')
                    
                    if favored_team in home_team_abbr:
                        cover_margin = home_score - away_score - spread_value
                    else:
                        cover_margin = away_score - home_score - spread_value
                    
                    analysis['spread_status'] = {
                        'spread': spread_str,
                        'cover_margin': cover_margin,
                        'status': 'Covering' if cover_margin > 0 else 'Not Covering'
                    }
            except (ValueError, IndexError) as e:
                logger.debug(f"Could not parse spread: {spread_str}")
        
        # Total analysis
        if game_state.get('total_line'):
            total_line = game_state.get('total_line')
            over_under = total - total_line
            
            analysis['total_status'] = {
                'line': total_line,
                'current': total,
                'difference': over_under,
                'status': 'Over' if over_under > 0 else 'Under'
            }
        
        return analysis
    
    def _generate_game_commentary(self, game_state: Dict[str, Any], insights: Dict[str, Any]) -> str:
        """Generate overall game commentary using AI."""
        
        try:
            context = f"""Game: {game_state.get('game_name')}
Score: {game_state.get('away_team')} {game_state.get('away_score')} - {game_state.get('home_team')} {game_state.get('home_score')}
Quarter: {game_state.get('quarter')}
Clock: {game_state.get('clock')}
Game Phase: {insights.get('game_phase')}
Competitiveness: {insights.get('game_competitiveness')}
Leading Team: {insights.get('leading_team', 'Tied')}"""

            if insights.get('betting_analysis'):
                betting = insights['betting_analysis']
                if betting.get('spread_status'):
                    context += f"\nSpread: {betting['spread_status']['spread']} ({betting['spread_status']['status']})"
                if betting.get('total_status'):
                    context += f"\nTotal: O/U {betting['total_status']['line']} (Currently {betting['total_status']['status']} by {abs(betting['total_status']['difference']):.1f})"
            
            prompt = f"""Provide a brief game summary and analysis (3-4 sentences) based on the current state:

{context}

Focus on: 
1. Current game narrative and key storylines
2. What to watch for in the remainder of the game
3. Betting implications if relevant"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert NFL analyst providing concise game analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating game commentary: {e}")
            return f"Game is {insights.get('game_competitiveness')} in {insights.get('game_phase')}. {insights.get('leading_team', 'Teams are tied')} currently ahead."


class PlayTracker:
    """Tracks plays and detects new plays."""
    
    def __init__(self):
        self.seen_plays = set()
        logger.info("PlayTracker initialized")
    
    def is_new_play(self, play_id: str) -> bool:
        """Check if a play is new (not seen before)."""
        if play_id in self.seen_plays:
            return False
        
        self.seen_plays.add(play_id)
        return True
    
    def reset(self):
        """Reset tracker for a new game."""
        self.seen_plays.clear()
        logger.info("PlayTracker reset")
    
    def get_play_count(self) -> int:
        """Get total number of plays tracked."""
        return len(self.seen_plays)
