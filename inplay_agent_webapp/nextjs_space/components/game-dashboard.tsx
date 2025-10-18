
'use client'

import { useState, useEffect } from 'react'
import { apiClient, GameState, QuarterScore, Play, LiveGame } from '@/lib/api'
import { GameHeader } from './game-header'
import { PlayByPlayFeed } from './play-by-play-feed'
import { QuarterBreakdown } from './quarter-breakdown'
import { GameSelector } from './game-selector'
import { Button } from './ui/button'
import { RefreshCw, Settings, AlertCircle } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import Link from 'next/link'
import { Alert, AlertDescription } from './ui/alert'

export function GameDashboard() {
  const [currentGame, setCurrentGame] = useState<GameState | null>(null)
  const [quarterScores, setQuarterScores] = useState<QuarterScore[]>([])
  const [plays, setPlays] = useState<Play[]>([])
  const [liveGames, setLiveGames] = useState<LiveGame[]>([])
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isTracking, setIsTracking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const { toast } = useToast()

  // Auto-refresh interval
  useEffect(() => {
    let interval: NodeJS.Timeout

    if (selectedGameId && isTracking) {
      interval = setInterval(() => {
        fetchGameData(selectedGameId, false)
      }, 20000) // Refresh every 20 seconds
    }

    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [selectedGameId, isTracking])

  // Load live games on mount
  useEffect(() => {
    fetchLiveGames()
  }, [])

  const fetchLiveGames = async () => {
    try {
      const response = await apiClient.getLiveGames()
      if (response.success) {
        setLiveGames(response.games)
        setError(null)
      }
    } catch (error) {
      console.error('Error fetching live games:', error)
      setError('Failed to fetch live games. Please check if the backend is running.')
    }
  }

  const fetchGameData = async (gameId: string, showLoading = true) => {
    if (showLoading) setIsLoading(true)
    setError(null)

    try {
      // Fetch current game state
      const gameResponse = await apiClient.getCurrentGame(gameId)
      if (gameResponse.success) {
        setCurrentGame(gameResponse.game)
        setQuarterScores(gameResponse.quarter_scores)
      }

      // Fetch recent plays
      const playsResponse = await apiClient.getGamePlays(gameId, 25)
      if (playsResponse.success) {
        setPlays(playsResponse.plays)
      }

      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching game data:', error)
      setError('Failed to fetch game data')
      toast({
        title: 'Error',
        description: 'Failed to fetch game data',
        variant: 'destructive',
      })
    } finally {
      if (showLoading) setIsLoading(false)
    }
  }

  const startTracking = async (gameId: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await apiClient.startTracking(gameId, 15)
      if (response.success) {
        setIsTracking(true)
        setSelectedGameId(gameId)
        await fetchGameData(gameId, false)
        toast({
          title: 'Success',
          description: `Started tracking game ${gameId}`,
        })
      }
    } catch (error) {
      console.error('Error starting tracking:', error)
      setError('Failed to start tracking game')
      toast({
        title: 'Error',
        description: 'Failed to start tracking game',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const stopTracking = async () => {
    if (!selectedGameId) return

    try {
      await apiClient.stopTracking(selectedGameId)
      setIsTracking(false)
      setSelectedGameId(null)
      setCurrentGame(null)
      setQuarterScores([])
      setPlays([])
      toast({
        title: 'Success',
        description: 'Stopped tracking game',
      })
    } catch (error) {
      console.error('Error stopping tracking:', error)
      toast({
        title: 'Error',
        description: 'Failed to stop tracking',
        variant: 'destructive',
      })
    }
  }

  const refreshData = () => {
    if (selectedGameId) {
      fetchGameData(selectedGameId)
    } else {
      fetchLiveGames()
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">INPLAY Agent</h1>
          <p className="text-muted-foreground">
            Real-time NFL game tracking with AI analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refreshData}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Link href="/config">
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Config
            </Button>
          </Link>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Game Selector */}
      {!isTracking && (
        <div className="mb-6">
          <GameSelector
            games={liveGames}
            onSelectGame={startTracking}
            isLoading={isLoading}
          />
        </div>
      )}

      {/* Main Dashboard */}
      {currentGame && isTracking ? (
        <div className="space-y-6">
          {/* Game Header */}
          <GameHeader
            game={currentGame}
            isLive={isTracking}
            onStopTracking={stopTracking}
            lastUpdated={lastUpdated}
          />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Play-by-Play Feed */}
            <div className="lg:col-span-2">
              <PlayByPlayFeed
                plays={plays}
                isLoading={isLoading}
              />
            </div>

            {/* Quarter Breakdown */}
            <div>
              <QuarterBreakdown
                quarterScores={quarterScores}
                homeTeam={currentGame.home_team}
                awayTeam={currentGame.away_team}
              />
            </div>
          </div>
        </div>
      ) : (
        !isTracking && (
          <div className="text-center py-12">
            <h2 className="text-2xl font-semibold mb-4">
              Select a live game to start tracking
            </h2>
            <p className="text-muted-foreground">
              Choose from the available live games above to begin real-time tracking and AI analysis.
            </p>
          </div>
        )
      )}
    </div>
  )
}
