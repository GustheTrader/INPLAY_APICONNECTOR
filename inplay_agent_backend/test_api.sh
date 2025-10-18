
#!/bin/bash

# Test script for INPLAY Agent Backend API

BASE_URL="http://localhost:5000"

echo "================================================"
echo "  INPLAY Agent Backend - API Tests"
echo "================================================"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: API documentation
echo "Test 2: API Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/api" | python3 -m json.tool | head -30
echo "... (truncated)"
echo ""
echo ""

# Test 3: Get API config
echo "Test 3: Get API Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/api/config/api" | python3 -m json.tool
echo ""
echo ""

# Test 4: Find live games
echo "Test 4: Find Live Games"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/api/games/live" | python3 -m json.tool
echo ""
echo ""

# Test 5: Get tracked games
echo "Test 5: Get Tracked Games"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$BASE_URL/api/games/tracked" | python3 -m json.tool
echo ""
echo ""

echo "================================================"
echo "  All tests completed!"
echo "================================================"
echo ""
echo "To start tracking a game:"
echo "  curl \"$BASE_URL/api/game/start?event_id=YOUR_EVENT_ID\""
echo ""
echo "To get game state:"
echo "  curl \"$BASE_URL/api/game/current?event_id=YOUR_EVENT_ID\""
echo ""
