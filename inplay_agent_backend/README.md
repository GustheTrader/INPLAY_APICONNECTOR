# INPLAY Agent Backend

A real-time NFL game tracking and analysis system with AI-powered commentary. This backend provides comprehensive game tracking, play-by-play analysis, momentum detection, and betting insights.

## Features

✅ **Real-Time Game Tracking** - Poll live NFL games every 10-30 seconds for up-to-date information  
✅ **ESPN API Integration** - Built-in support for ESPN's unofficial API (no authentication required)  
✅ **Custom API Support** - Configure your own API endpoints with authentication  
✅ **SQLite Database** - Persistent storage for game state, plays, and analysis  
✅ **AI Commentary** - OpenAI-powered play analysis and game insights  
✅ **Quarter-by-Quarter Tracking** - Detailed scoring breakdown by quarter  
✅ **Momentum Detection** - Identify key momentum shifts and significant plays  
✅ **Betting Analysis** - Track spreads, totals, and betting implications  
✅ **REST API** - Clean HTTP endpoints for easy integration  
✅ **Comprehensive Logging** - Error handling and detailed logs

## Architecture

```
┌─────────────────────┐
│   Flask REST API    │ ← User Requests
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Game Manager      │ ← Orchestrates Components
└──────────┬──────────┘
           │
     ┌─────┴─────┬─────────────┬──────────────┐
     ▼           ▼             ▼              ▼
┌─────────┐ ┌─────────┐ ┌──────────┐  ┌──────────┐
│   API   │ │Database │ │  INPLAY  │  │   Game   │
│Connector│ │         │ │  Agent   │  │ Tracker  │
└─────────┘ └─────────┘ └──────────┘  └──────────┘
     │           │            │             │
     ▼           ▼            ▼             ▼
ESPN API     SQLite DB    OpenAI API    Polling Loop
```

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Clone or navigate to the project directory:**
```bash
cd /home/ubuntu/inplay_agent_backend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
nano .env
```

Edit `.env` and add your OpenAI API key (optional, for AI commentary):
```env
OPENAI_API_KEY=sk-your-key-here
FLASK_ENV=development
FLASK_PORT=5000
POLL_INTERVAL_SECONDS=15
```

4. **Run the server:**
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Health Check

**GET** `/health`

Check if the server is running.

```bash
curl http://localhost:5000/health
```

### Configuration

#### Configure Custom API

**POST** `/api/config/api`

Configure a custom API endpoint (alternative to ESPN API).

**Request Body:**
```json
{
  "api_type": "custom",
  "endpoint_url": "https://your-api.com/nfl",
  "auth_key": "your_api_key"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/config/api \
  -H "Content-Type: application/json" \
  -d '{
    "api_type": "custom",
    "endpoint_url": "https://api.mysportsfeeds.com/v2.1/pull/nfl",
    "auth_key": "YOUR_API_KEY"
  }'
```

#### Get API Configuration

**GET** `/api/config/api`

Get the current API configuration.

```bash
curl http://localhost:5000/api/config/api
```

### Game Tracking

#### Start Tracking a Game

**GET** `/api/game/start?event_id={EVENT_ID}&poll_interval={SECONDS}`

Start tracking a specific game by ESPN event ID.

**Parameters:**
- `event_id` (required): ESPN game ID (e.g., "401671746")
- `poll_interval` (optional): Polling interval in seconds (5-60, default: 15)

**Example:**
```bash
# Start tracking with default 15s interval
curl "http://localhost:5000/api/game/start?event_id=401671746"

# Start tracking with 20s interval
curl "http://localhost:5000/api/game/start?event_id=401671746&poll_interval=20"
```

#### Stop Tracking a Game

**GET** `/api/game/stop?event_id={EVENT_ID}`

Stop tracking a game.

```bash
curl "http://localhost:5000/api/game/stop?event_id=401671746"
```

### Game Data

#### Get Current Game State

**GET** `/api/game/current?event_id={EVENT_ID}`

Get the current state of a game including scores, quarter, clock, and situation.

**Example:**
```bash
curl "http://localhost:5000/api/game/current?event_id=401671746"
```

**Response:**
```json
{
  "success": true,
  "game": {
    "event_id": "401671746",
    "name": "Tampa Bay Buccaneers at Seattle Seahawks",
    "home_team": "Seattle Seahawks",
    "away_team": "Tampa Bay Buccaneers",
    "home_score": 27,
    "away_score": 17,
    "quarter": 4,
    "clock": "0:00",
    "status": "post",
    "status_detail": "Final",
    "venue": "Lumen Field",
    "spread": "SEA -3.5",
    "total_line": 44.5
  },
  "quarter_scores": [
    {"quarter": 1, "home_score": 7, "away_score": 0},
    {"quarter": 2, "home_score": 10, "away_score": 7},
    {"quarter": 3, "home_score": 7, "away_score": 7},
    {"quarter": 4, "home_score": 3, "away_score": 3}
  ],
  "situation": {
    "possession_team": "26",
    "down": 1,
    "distance": 10,
    "yard_line": 75
  },
  "ai_analysis": {
    "content": "Seattle covers the spread comfortably...",
    "created_at": "2025-10-18 20:15:30"
  }
}
```

#### Get Play-by-Play

**GET** `/api/game/plays?event_id={EVENT_ID}&limit={NUM}&quarter={Q}`

Get play-by-play events with AI commentary.

**Parameters:**
- `event_id` (required): ESPN game ID
- `limit` (optional): Number of plays to return (default: 50)
- `quarter` (optional): Filter by specific quarter

**Example:**
```bash
# Get last 20 plays
curl "http://localhost:5000/api/game/plays?event_id=401671746&limit=20"

# Get all Q4 plays
curl "http://localhost:5000/api/game/plays?event_id=401671746&quarter=4"
```

**Response:**
```json
{
  "success": true,
  "event_id": "401671746",
  "play_count": 20,
  "plays": [
    {
      "play_id": "4016717461234",
      "quarter": 4,
      "clock": "8:42",
      "play_type": "touchdown",
      "play_text": "Kenneth Walker III 15 yd run (Jason Myers kick)",
      "team_name": "Seattle Seahawks",
      "is_scoring_play": true,
      "score_value": 7,
      "home_score": 27,
      "away_score": 17,
      "ai_commentary": "Crucial touchdown for Seattle extends their lead...",
      "significance_score": 8.5,
      "momentum_shift": "Major shift to Seattle Seahawks"
    }
  ]
}
```

#### Get Live Games

**GET** `/api/games/live`

Get all currently live NFL games.

```bash
curl http://localhost:5000/api/games/live
```

#### Get Tracked Games

**GET** `/api/games/tracked`

Get all games currently being tracked by the system.

```bash
curl http://localhost:5000/api/games/tracked
```

#### Get AI Analysis

**GET** `/api/game/analysis?event_id={EVENT_ID}&type={TYPE}`

Get AI-generated analysis for a game.

**Parameters:**
- `event_id` (required): ESPN game ID
- `type` (optional): Analysis type (game_summary, game_final)

```bash
curl "http://localhost:5000/api/game/analysis?event_id=401671746&type=game_summary"
```

## Usage Examples

### Python Client Example

```python
import requests
import time

BASE_URL = "http://localhost:5000"

# 1. Find live games
response = requests.get(f"{BASE_URL}/api/games/live")
live_games = response.json()

print(f"Found {live_games['count']} live games:")
for game in live_games['games']:
    print(f"  {game['event_id']}: {game['name']} - Q{game['quarter']} {game['clock']}")

# 2. Start tracking a game
if live_games['games']:
    event_id = live_games['games'][0]['event_id']
    
    response = requests.get(
        f"{BASE_URL}/api/game/start",
        params={'event_id': event_id, 'poll_interval': 15}
    )
    
    print(f"Started tracking: {response.json()}")
    
    # 3. Monitor game state
    for _ in range(10):  # Check 10 times
        time.sleep(20)
        
        response = requests.get(
            f"{BASE_URL}/api/game/current",
            params={'event_id': event_id}
        )
        
        game = response.json()['game']
        print(f"\nQ{game['quarter']} {game['clock']}: "
              f"{game['away_team']} {game['away_score']} - "
              f"{game['home_team']} {game['home_score']}")
        
        # Get latest plays
        response = requests.get(
            f"{BASE_URL}/api/game/plays",
            params={'event_id': event_id, 'limit': 5}
        )
        
        plays = response.json()['plays']
        for play in plays[:3]:  # Show top 3 plays
            if play['ai_commentary']:
                print(f"  → {play['play_text'][:60]}")
                print(f"    AI: {play['ai_commentary'][:80]}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:5000';

async function trackGame() {
  try {
    // Find live games
    const liveGames = await axios.get(`${BASE_URL}/api/games/live`);
    console.log(`Found ${liveGames.data.count} live games`);
    
    if (liveGames.data.games.length > 0) {
      const eventId = liveGames.data.games[0].event_id;
      
      // Start tracking
      await axios.get(`${BASE_URL}/api/game/start`, {
        params: { event_id: eventId, poll_interval: 15 }
      });
      
      console.log(`Started tracking game: ${eventId}`);
      
      // Monitor game
      setInterval(async () => {
        const gameState = await axios.get(`${BASE_URL}/api/game/current`, {
          params: { event_id: eventId }
        });
        
        const game = gameState.data.game;
        console.log(`Q${game.quarter} ${game.clock}: ${game.away_team} ${game.away_score} - ${game.home_team} ${game.home_score}`);
      }, 20000);
    }
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

trackGame();
```

### cURL Examples

```bash
# Find live games
curl http://localhost:5000/api/games/live

# Start tracking
curl "http://localhost:5000/api/game/start?event_id=401671746"

# Get current game state
curl "http://localhost:5000/api/game/current?event_id=401671746"

# Get recent plays
curl "http://localhost:5000/api/game/plays?event_id=401671746&limit=10"

# Get Q4 plays only
curl "http://localhost:5000/api/game/plays?event_id=401671746&quarter=4"

# Stop tracking
curl "http://localhost:5000/api/game/stop?event_id=401671746"
```

## Database Schema

### Tables

- **api_config** - API endpoint configurations
- **game_state** - Current game states
- **quarter_scores** - Quarter-by-quarter scoring
- **plays** - Play-by-play events with AI commentary
- **ai_analysis** - AI-generated game analysis

### Example Queries

```sql
-- Get game state
SELECT * FROM game_state WHERE event_id = '401671746';

-- Get quarter scores
SELECT * FROM quarter_scores WHERE event_id = '401671746' ORDER BY quarter;

-- Get scoring plays
SELECT * FROM plays WHERE event_id = '401671746' AND is_scoring_play = 1;

-- Get plays with high significance
SELECT * FROM plays WHERE event_id = '401671746' AND significance_score >= 8.0;
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI commentary | None (AI disabled) |
| `FLASK_ENV` | Flask environment (development/production) | development |
| `FLASK_PORT` | Server port | 5000 |
| `FLASK_HOST` | Server host | 0.0.0.0 |
| `POLL_INTERVAL_SECONDS` | Default polling interval | 15 |
| `DATABASE_PATH` | SQLite database file path | inplay_agent.db |

### Polling Intervals

- **Live Games**: 10-15 seconds (recommended)
- **Pre-Game**: 5-10 minutes
- **Completed Games**: Stop polling

## AI Commentary

The INPLAY Agent uses OpenAI's GPT-4 to generate intelligent commentary on plays and game state.

### Features:
- **Play Significance**: Rates plays 0-10 based on impact
- **Momentum Detection**: Identifies momentum shifts
- **Context-Aware**: Considers game situation, score, time remaining
- **Betting Insights**: Analyzes spread and total implications

### Without OpenAI API Key:
If no API key is provided, the system uses rule-based commentary that still provides valuable insights but without AI-generated text.

## Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `inplay_agent.log`

Log levels:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Failures and exceptions
- DEBUG: Detailed debugging info

## Error Handling

The system includes comprehensive error handling:
- API request retries with exponential backoff
- Database transaction rollbacks on errors
- Graceful degradation when AI is unavailable
- Detailed error messages in responses

## Limitations

1. **ESPN API**: Unofficial API, may change without notice
2. **Rate Limits**: Unknown limits on ESPN API
3. **Single-Game Focus**: Optimized for tracking one game at a time
4. **AI Costs**: OpenAI API usage incurs costs
5. **Real-Time Delay**: ESPN data may lag 5-10 seconds behind live action

## Production Considerations

For production deployment:

1. **Use Official API**: Switch to MySportsFeeds or SportsDataIO
2. **Add Authentication**: Secure API endpoints
3. **Use Production Database**: PostgreSQL instead of SQLite
4. **Add Caching**: Redis for API responses
5. **Load Balancing**: For multiple concurrent games
6. **Monitoring**: Set up application monitoring
7. **Rate Limiting**: Implement request throttling

## Troubleshooting

### Game Not Found
- Verify event ID is correct
- Check if game exists in today's schedule
- Try using date parameter in scoreboard query

### No AI Commentary
- Check OPENAI_API_KEY is set correctly
- Verify API key has sufficient credits
- Check logs for OpenAI API errors

### Stale Data
- Verify polling is active with `/api/games/tracked`
- Check poll interval is reasonable (10-30s)
- Look for errors in logs

### Database Locked
- SQLite has limited concurrent write support
- Consider PostgreSQL for production

## Development

### Project Structure
```
inplay_agent_backend/
├── app.py                 # Flask REST API
├── database.py            # Database operations
├── api_connector.py       # API client and polling
├── inplay_agent.py        # AI analysis logic
├── game_tracker.py        # Game tracking orchestration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── inplay_agent.db       # SQLite database (created at runtime)
```

### Adding Custom APIs

To integrate a custom API:

1. Use the `/api/config/api` endpoint to configure your endpoint
2. Ensure your API returns data in a similar structure to ESPN
3. Modify `api_connector.py` if custom parsing is needed

### Extending AI Analysis

To customize AI commentary:

1. Edit `inplay_agent.py`
2. Modify `_generate_ai_commentary()` method
3. Adjust prompts for different analysis styles
4. Add new analysis types in `_calculate_significance()`

## License

MIT License - Free to use and modify

## Support

For issues and questions:
- Check logs: `inplay_agent.log`
- Review API documentation: `GET /api`
- Verify configuration: `GET /api/config/api`

## Credits

- ESPN API data (unofficial)
- OpenAI GPT-4 for AI commentary
- Flask web framework
- SQLite database

---

**Built for real-time NFL game tracking and analysis** 🏈
