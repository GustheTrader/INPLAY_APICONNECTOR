"""
API Connector module for fetching NFL game data.
Supports ESPN API and custom API endpoints.
"""

import requests
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class APIConnector:
    """Handles API requests to ESPN or custom endpoints."""
    
    def __init__(self, api_type: str = "espn", custom_endpoint: Optional[str] = None, auth_key: Optional[str] = None):
        self.api_type = api_type
        self.custom_endpoint = custom_endpoint
        self.auth_key = auth_key
        self.session = requests.Session()
        
        # ESPN API base URLs
        self.espn_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.espn_core_url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
        
        # Request timeout
        self.timeout = 10
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests
        
        logger.info(f"APIConnector initialized: type={api_type}")
    
    def _rate_limit(self):
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request with error handling and retry logic."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"Request successful: {url}")
                return data
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                if response.status_code == 404:
                    logger.error(f"Resource not found: {url}")
                    return None
                if response.status_code == 429:
                    logger.warning("Rate limit hit, backing off...")
                    time.sleep(retry_delay * 2)
                
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error on attempt {attempt + 1}: {e}")
                
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                
            except ValueError as e:
                logger.error(f"JSON decode error: {e}")
                return None
            
            if attempt < max_retries - 1:
                wait_time = retry_delay ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        logger.error(f"All retry attempts failed for: {url}")
        return None
    
    # ESPN API Methods
    def get_scoreboard(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Get scoreboard data from ESPN API."""
        url = f"{self.espn_base_url}/scoreboard"
        params = {"limit": 100}
        
        if date:
            params["dates"] = date.strftime("%Y%m%d")
        
        logger.info(f"Fetching scoreboard: {url}")
        return self._make_request(url, params=params)
    
    def get_game_summary(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed game summary from ESPN API."""
        url = f"{self.espn_base_url}/summary"
        params = {"event": event_id}
        
        logger.info(f"Fetching game summary: event_id={event_id}")
        return self._make_request(url, params=params)
    
    def find_game_by_id(self, event_id: str, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Find a specific game in the scoreboard."""
        scoreboard = self.get_scoreboard(date)
        
        if not scoreboard or 'events' not in scoreboard:
            logger.warning("No events found in scoreboard")
            return None
        
        for event in scoreboard['events']:
            if event['id'] == event_id:
                logger.info(f"Found game: {event['name']}")
                return event
        
        logger.warning(f"Game not found: {event_id}")
        return None
    
    def find_live_games(self) -> List[Dict[str, Any]]:
        """Find all currently live games."""
        scoreboard = self.get_scoreboard()
        
        if not scoreboard or 'events' not in scoreboard:
            return []
        
        live_games = []
        for event in scoreboard['events']:
            competition = event['competitions'][0]
            status = competition['status']['type']['state']
            
            if status == 'in':  # Game in progress
                live_games.append(event)
        
        logger.info(f"Found {len(live_games)} live games")
        return live_games
    
    # Custom API Methods
    def get_custom_data(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make request to custom API endpoint."""
        url = self.custom_endpoint if self.custom_endpoint else endpoint
        
        headers = {}
        if self.auth_key:
            headers["Authorization"] = f"Bearer {self.auth_key}"
        
        logger.info(f"Fetching custom data: {url}")
        return self._make_request(url, params=params, headers=headers)
    
    # Parser Methods
    def parse_game_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ESPN game event into standardized format."""
        try:
            competition = event['competitions'][0]
            status = competition['status']
            
            # Get competitors
            competitors = competition['competitors']
            home_team = next((c for c in competitors if c['homeAway'] == 'home'), competitors[0])
            away_team = next((c for c in competitors if c['homeAway'] == 'away'), competitors[1])
            
            # Parse situation (current play info)
            situation = competition.get('situation', {})
            
            # Parse odds
            odds = competition.get('odds', [])
            spread = odds[0].get('details') if odds else None
            total_line = odds[0].get('overUnder') if odds else None
            
            # Parse venue
            venue = competition.get('venue', {})
            venue_name = venue.get('fullName', 'Unknown Venue')
            
            parsed_data = {
                'event_id': event['id'],
                'game_name': event['name'],
                'short_name': event.get('shortName', event['name']),
                'home_team': home_team['team']['displayName'],
                'home_team_abbr': home_team['team']['abbreviation'],
                'home_team_id': home_team['team']['id'],
                'away_team': away_team['team']['displayName'],
                'away_team_abbr': away_team['team']['abbreviation'],
                'away_team_id': away_team['team']['id'],
                'home_score': int(home_team.get('score', 0)),
                'away_score': int(away_team.get('score', 0)),
                'quarter': status.get('period', 1),
                'clock': status.get('displayClock', '0:00'),
                'game_status': status['type']['state'],
                'game_status_detail': status['type']['detail'],
                'possession_team': situation.get('possession'),
                'down': situation.get('down'),
                'distance': situation.get('distance'),
                'yard_line': situation.get('yardLine'),
                'venue': venue_name,
                'attendance': competition.get('attendance'),
                'spread': spread,
                'total_line': total_line,
                'raw_data': event
            }
            
            # Parse quarter scores
            parsed_data['quarter_scores'] = {
                'home': [ls.get('value', 0) for ls in home_team.get('linescores', [])],
                'away': [ls.get('value', 0) for ls in away_team.get('linescores', [])]
            }
            
            return parsed_data
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing game event: {e}")
            return {}
    
    def parse_game_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ESPN game summary into standardized format."""
        try:
            # Extract header info
            header = summary.get('header', {})
            competition = header.get('competitions', [{}])[0]
            
            # Parse scoring plays
            scoring_plays = []
            for play in summary.get('scoringPlays', []):
                scoring_plays.append({
                    'play_id': play.get('id'),
                    'quarter': play['period']['number'],
                    'clock': play['clock']['displayValue'],
                    'team_id': play['team']['id'],
                    'play_type': play['scoringType']['name'],
                    'play_text': play['text'],
                    'home_score': play.get('homeScore', 0),
                    'away_score': play.get('awayScore', 0),
                    'score_value': play.get('scoreValue', 0)
                })
            
            # Parse team statistics
            team_stats = {}
            if 'boxscore' in summary:
                for team in summary['boxscore'].get('teams', []):
                    team_id = team['team']['id']
                    team_stats[team_id] = {}
                    
                    for stat in team.get('statistics', []):
                        team_stats[team_id][stat['name']] = {
                            'value': stat.get('displayValue', '0'),
                            'label': stat.get('label', stat['name'])
                        }
            
            # Parse drives
            drives = []
            drive_data = summary.get('drives', {})
            for drive in drive_data.get('previous', []):
                drives.append({
                    'id': drive.get('id'),
                    'team_id': drive['team']['id'],
                    'description': drive.get('description'),
                    'plays': drive.get('plays', 0),
                    'yards': drive.get('yards', 0),
                    'result': drive.get('result'),
                    'start_quarter': drive['start']['period']['number'],
                    'start_clock': drive['start']['clock']['displayValue'],
                    'end_quarter': drive['end']['period']['number'],
                    'end_clock': drive['end']['clock']['displayValue']
                })
            
            return {
                'scoring_plays': scoring_plays,
                'team_stats': team_stats,
                'drives': drives,
                'raw_data': summary
            }
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing game summary: {e}")
            return {
                'scoring_plays': [],
                'team_stats': {},
                'drives': []
            }


class GamePoller:
    """Polls game data at regular intervals."""
    
    def __init__(self, api_connector: APIConnector, poll_interval: int = 15):
        self.api_connector = api_connector
        self.poll_interval = poll_interval  # seconds
        self.is_polling = False
        self.event_id = None
        
        logger.info(f"GamePoller initialized: interval={poll_interval}s")
    
    def start_polling(self, event_id: str, callback):
        """Start polling for a specific game."""
        self.event_id = event_id
        self.is_polling = True
        
        logger.info(f"Starting polling for game: {event_id}")
        
        while self.is_polling:
            try:
                # Fetch game data
                game_event = self.api_connector.find_game_by_id(event_id)
                
                if game_event:
                    parsed_data = self.api_connector.parse_game_event(game_event)
                    
                    # Fetch detailed summary
                    game_summary = self.api_connector.get_game_summary(event_id)
                    if game_summary:
                        summary_data = self.api_connector.parse_game_summary(game_summary)
                        parsed_data['summary'] = summary_data
                    
                    # Call the callback function with the data
                    callback(parsed_data)
                    
                    # Check if game is complete
                    if parsed_data.get('game_status') == 'post':
                        logger.info(f"Game completed: {event_id}")
                        self.stop_polling()
                        break
                else:
                    logger.warning(f"Game not found: {event_id}")
                
                # Wait for next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error during polling: {e}")
                time.sleep(self.poll_interval)
    
    def stop_polling(self):
        """Stop polling."""
        self.is_polling = False
        logger.info("Polling stopped")
    
    def update_poll_interval(self, interval: int):
        """Update polling interval."""
        self.poll_interval = interval
        logger.info(f"Polling interval updated: {interval}s")
