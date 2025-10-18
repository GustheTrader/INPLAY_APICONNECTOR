"""
Flask REST API for INPLAY Agent Backend.
Provides endpoints for game tracking, play-by-play, and configuration.
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv

from game_tracker import GameManager
from api_connector import APIConnector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inplay_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Game Manager
game_manager = GameManager()

# Configuration
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL_SECONDS', 15))


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


# API Configuration endpoints
@app.route('/api/config/api', methods=['POST'])
def configure_api():
    """Configure custom API endpoint.
    
    Request body:
    {
        "api_type": "custom",
        "endpoint_url": "https://api.example.com/nfl",
        "auth_key": "optional_auth_key"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        api_type = data.get('api_type', 'custom')
        endpoint_url = data.get('endpoint_url')
        auth_key = data.get('auth_key')
        
        if not endpoint_url:
            return jsonify({'error': 'endpoint_url is required'}), 400
        
        config_id = game_manager.configure_api(api_type, endpoint_url, auth_key)
        
        logger.info(f"API configured: {api_type} - {endpoint_url}")
        
        return jsonify({
            'success': True,
            'config_id': config_id,
            'message': 'API configuration saved',
            'api_type': api_type,
            'endpoint_url': endpoint_url
        })
        
    except Exception as e:
        logger.error(f"Error configuring API: {e}", exc_info=True)
        return jsonify({'error': 'Failed to configure API', 'message': str(e)}), 500


@app.route('/api/config/api', methods=['GET'])
def get_api_config():
    """Get current API configuration."""
    try:
        config = game_manager.database.get_active_api_config('custom')
        
        if config:
            return jsonify({
                'success': True,
                'config': {
                    'api_type': config['api_type'],
                    'endpoint_url': config['endpoint_url'],
                    'has_auth_key': bool(config.get('auth_key')),
                    'created_at': config['created_at']
                }
            })
        else:
            return jsonify({
                'success': True,
                'config': {
                    'api_type': 'espn',
                    'endpoint_url': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl',
                    'message': 'Using default ESPN API'
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting API config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get API config', 'message': str(e)}), 500


# Game tracking endpoints
@app.route('/api/game/start', methods=['GET'])
def start_game_tracking():
    """Start tracking a game by ID.
    
    Query parameters:
    - event_id: ESPN game ID (required)
    - poll_interval: Polling interval in seconds (optional, default: 15)
    
    Example: /api/game/start?event_id=401671746&poll_interval=20
    """
    try:
        event_id = request.args.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'event_id parameter is required'}), 400
        
        poll_interval = int(request.args.get('poll_interval', POLL_INTERVAL))
        
        # Validate poll interval
        if poll_interval < 5 or poll_interval > 60:
            return jsonify({'error': 'poll_interval must be between 5 and 60 seconds'}), 400
        
        success = game_manager.start_tracking_game(event_id, poll_interval)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Started tracking game {event_id}',
                'event_id': event_id,
                'poll_interval': poll_interval
            })
        else:
            return jsonify({
                'error': 'Failed to start tracking',
                'message': 'Game not found or already being tracked'
            }), 400
        
    except ValueError as e:
        return jsonify({'error': 'Invalid parameter', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error starting game tracking: {e}", exc_info=True)
        return jsonify({'error': 'Failed to start tracking', 'message': str(e)}), 500


@app.route('/api/game/stop', methods=['GET'])
def stop_game_tracking():
    """Stop tracking a game.
    
    Query parameters:
    - event_id: ESPN game ID (required)
    
    Example: /api/game/stop?event_id=401671746
    """
    try:
        event_id = request.args.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'event_id parameter is required'}), 400
        
        game_manager.stop_tracking_game(event_id)
        
        return jsonify({
            'success': True,
            'message': f'Stopped tracking game {event_id}',
            'event_id': event_id
        })
        
    except Exception as e:
        logger.error(f"Error stopping game tracking: {e}", exc_info=True)
        return jsonify({'error': 'Failed to stop tracking', 'message': str(e)}), 500


@app.route('/api/game/current', methods=['GET'])
def get_current_game():
    """Get current game state.
    
    Query parameters:
    - event_id: ESPN game ID (required)
    
    Example: /api/game/current?event_id=401671746
    """
    try:
        event_id = request.args.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'event_id parameter is required'}), 400
        
        game_state = game_manager.get_game_state(event_id)
        
        if not game_state:
            return jsonify({'error': 'Game not found', 'message': f'No data for game {event_id}'}), 404
        
        # Get quarter scores
        quarter_scores = game_manager.get_quarter_scores(event_id)
        
        # Get latest AI analysis
        ai_analysis = game_manager.database.get_ai_analysis(event_id, 'game_summary')
        latest_analysis = ai_analysis[0] if ai_analysis else None
        
        response = {
            'success': True,
            'game': {
                'event_id': game_state['event_id'],
                'name': game_state['game_name'],
                'home_team': game_state['home_team'],
                'away_team': game_state['away_team'],
                'home_score': game_state['home_score'],
                'away_score': game_state['away_score'],
                'quarter': game_state['quarter'],
                'clock': game_state['clock'],
                'status': game_state['game_status'],
                'status_detail': game_state['game_status_detail'],
                'venue': game_state['venue'],
                'spread': game_state['spread'],
                'total_line': game_state['total_line'],
                'last_updated': game_state['last_updated']
            },
            'quarter_scores': quarter_scores,
            'situation': {
                'possession_team': game_state.get('possession_team'),
                'down': game_state.get('down'),
                'distance': game_state.get('distance'),
                'yard_line': game_state.get('yard_line')
            }
        }
        
        if latest_analysis:
            response['ai_analysis'] = {
                'content': latest_analysis['content'],
                'created_at': latest_analysis['created_at']
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting current game: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get game data', 'message': str(e)}), 500


@app.route('/api/game/plays', methods=['GET'])
def get_game_plays():
    """Get play-by-play list.
    
    Query parameters:
    - event_id: ESPN game ID (required)
    - limit: Number of plays to return (optional, default: 50)
    - quarter: Filter by quarter (optional)
    
    Example: /api/game/plays?event_id=401671746&limit=20&quarter=4
    """
    try:
        event_id = request.args.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'event_id parameter is required'}), 400
        
        limit = request.args.get('limit', 50, type=int)
        quarter = request.args.get('quarter', type=int)
        
        plays = game_manager.get_game_plays(event_id, limit=limit)
        
        # Filter by quarter if specified
        if quarter:
            plays = [p for p in plays if p.get('quarter') == quarter]
        
        # Format plays for response
        formatted_plays = []
        for play in plays:
            formatted_plays.append({
                'play_id': play.get('play_id'),
                'quarter': play.get('quarter'),
                'clock': play.get('clock'),
                'play_type': play.get('play_type'),
                'play_text': play.get('play_text'),
                'team_name': play.get('team_name'),
                'is_scoring_play': bool(play.get('is_scoring_play')),
                'score_value': play.get('score_value'),
                'home_score': play.get('home_score'),
                'away_score': play.get('away_score'),
                'ai_commentary': play.get('ai_commentary'),
                'significance_score': play.get('significance_score'),
                'momentum_shift': play.get('momentum_shift'),
                'created_at': play.get('created_at')
            })
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'play_count': len(formatted_plays),
            'plays': formatted_plays
        })
        
    except Exception as e:
        logger.error(f"Error getting plays: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get plays', 'message': str(e)}), 500


@app.route('/api/games/live', methods=['GET'])
def get_live_games():
    """Get all currently live games."""
    try:
        live_games = game_manager.find_live_games()
        
        formatted_games = []
        for game in live_games:
            competition = game['competitions'][0]
            status = competition['status']
            competitors = competition['competitors']
            home_team = next((c for c in competitors if c['homeAway'] == 'home'), competitors[0])
            away_team = next((c for c in competitors if c['homeAway'] == 'away'), competitors[1])
            
            formatted_games.append({
                'event_id': game['id'],
                'name': game['name'],
                'short_name': game.get('shortName'),
                'home_team': home_team['team']['displayName'],
                'away_team': away_team['team']['displayName'],
                'home_score': int(home_team.get('score', 0)),
                'away_score': int(away_team.get('score', 0)),
                'quarter': status.get('period', 1),
                'clock': status.get('displayClock', '0:00'),
                'status': status['type']['detail']
            })
        
        return jsonify({
            'success': True,
            'count': len(formatted_games),
            'games': formatted_games
        })
        
    except Exception as e:
        logger.error(f"Error getting live games: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get live games', 'message': str(e)}), 500


@app.route('/api/games/tracked', methods=['GET'])
def get_tracked_games():
    """Get all games currently being tracked."""
    try:
        tracked_games = game_manager.get_tracked_games()
        
        formatted_games = []
        for game in tracked_games:
            formatted_games.append({
                'event_id': game['event_id'],
                'name': game['game_name'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'quarter': game['quarter'],
                'clock': game['clock'],
                'status': game['game_status'],
                'status_detail': game['game_status_detail'],
                'last_updated': game['last_updated']
            })
        
        return jsonify({
            'success': True,
            'count': len(formatted_games),
            'games': formatted_games
        })
        
    except Exception as e:
        logger.error(f"Error getting tracked games: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get tracked games', 'message': str(e)}), 500


@app.route('/api/game/analysis', methods=['GET'])
def get_game_analysis():
    """Get AI analysis for a game.
    
    Query parameters:
    - event_id: ESPN game ID (required)
    - type: Analysis type (optional: game_summary, game_final)
    
    Example: /api/game/analysis?event_id=401671746&type=game_summary
    """
    try:
        event_id = request.args.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'event_id parameter is required'}), 400
        
        analysis_type = request.args.get('type')
        
        analyses = game_manager.database.get_ai_analysis(event_id, analysis_type)
        
        formatted_analyses = []
        for analysis in analyses:
            formatted_analyses.append({
                'type': analysis['analysis_type'],
                'content': analysis['content'],
                'metadata': analysis.get('metadata'),
                'created_at': analysis['created_at']
            })
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'count': len(formatted_analyses),
            'analyses': formatted_analyses
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get analysis', 'message': str(e)}), 500


# API documentation endpoint
@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
def api_documentation():
    """API documentation."""
    return jsonify({
        'name': 'INPLAY Agent Backend API',
        'version': '1.0.0',
        'description': 'Real-time NFL game tracking and AI analysis',
        'endpoints': {
            'health': {
                'method': 'GET',
                'path': '/health',
                'description': 'Health check endpoint'
            },
            'configure_api': {
                'method': 'POST',
                'path': '/api/config/api',
                'description': 'Configure custom API endpoint',
                'body': {
                    'api_type': 'string (optional, default: custom)',
                    'endpoint_url': 'string (required)',
                    'auth_key': 'string (optional)'
                }
            },
            'get_api_config': {
                'method': 'GET',
                'path': '/api/config/api',
                'description': 'Get current API configuration'
            },
            'start_tracking': {
                'method': 'GET',
                'path': '/api/game/start',
                'description': 'Start tracking a game',
                'params': {
                    'event_id': 'string (required)',
                    'poll_interval': 'integer (optional, default: 15, range: 5-60)'
                }
            },
            'stop_tracking': {
                'method': 'GET',
                'path': '/api/game/stop',
                'description': 'Stop tracking a game',
                'params': {
                    'event_id': 'string (required)'
                }
            },
            'get_current_game': {
                'method': 'GET',
                'path': '/api/game/current',
                'description': 'Get current game state',
                'params': {
                    'event_id': 'string (required)'
                }
            },
            'get_plays': {
                'method': 'GET',
                'path': '/api/game/plays',
                'description': 'Get play-by-play list',
                'params': {
                    'event_id': 'string (required)',
                    'limit': 'integer (optional, default: 50)',
                    'quarter': 'integer (optional)'
                }
            },
            'get_live_games': {
                'method': 'GET',
                'path': '/api/games/live',
                'description': 'Get all currently live games'
            },
            'get_tracked_games': {
                'method': 'GET',
                'path': '/api/games/tracked',
                'description': 'Get all tracked games'
            },
            'get_analysis': {
                'method': 'GET',
                'path': '/api/game/analysis',
                'description': 'Get AI analysis for a game',
                'params': {
                    'event_id': 'string (required)',
                    'type': 'string (optional: game_summary, game_final)'
                }
            }
        }
    })


if __name__ == '__main__':
    logger.info("Starting INPLAY Agent Backend...")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")
    
    # Run Flask app
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
