
'use client'

import { GameState } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Clock, MapPin, StopCircle, Wifi } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface GameHeaderProps {
  game: GameState
  isLive: boolean
  onStopTracking: () => void
  lastUpdated: Date | null
}

export function GameHeader({ game, isLive, onStopTracking, lastUpdated }: GameHeaderProps) {
  const formatGameStatus = (status: string, statusDetail: string) => {
    if (status.includes('Final')) return 'Final'
    if (status.includes('Half')) return 'Halftime'
    return statusDetail || status
  }

  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold">
            {game.name}
          </CardTitle>
          <div className="flex items-center gap-2">
            {isLive && (
              <Badge variant="destructive" className="live-indicator">
                LIVE
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={onStopTracking}
              className="text-destructive hover:text-destructive"
            >
              <StopCircle className="w-4 h-4 mr-2" />
              Stop Tracking
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Score Display */}
        <div className="flex items-center justify-center space-x-8">
          {/* Away Team */}
          <div className="text-center">
            <div className="text-2xl font-bold text-muted-foreground mb-1">
              {game.away_team}
            </div>
            <div className="text-4xl font-bold">
              {game.away_score}
            </div>
          </div>

          {/* VS and Game Info */}
          <div className="text-center">
            <div className="text-lg font-semibold text-muted-foreground mb-2">
              VS
            </div>
            <div className="space-y-1">
              <Badge variant="secondary" className="text-sm">
                Q{game.quarter}
              </Badge>
              <div className="text-sm text-muted-foreground">
                {game.clock}
              </div>
            </div>
          </div>

          {/* Home Team */}
          <div className="text-center">
            <div className="text-2xl font-bold text-muted-foreground mb-1">
              {game.home_team}
            </div>
            <div className="text-4xl font-bold">
              {game.home_score}
            </div>
          </div>
        </div>

        {/* Game Status */}
        <div className="flex items-center justify-center">
          <Badge 
            variant={game.status.includes('Final') ? 'secondary' : 'default'}
            className="text-sm"
          >
            <Clock className="w-3 h-3 mr-1" />
            {formatGameStatus(game.status, game.status_detail)}
          </Badge>
        </div>

        {/* Additional Info */}
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-4">
            {game.venue && (
              <div className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                <span>{game.venue}</span>
              </div>
            )}
            {game.spread && (
              <div>
                <span className="font-medium">Spread:</span> {game.spread}
              </div>
            )}
            {game.total_line && (
              <div>
                <span className="font-medium">O/U:</span> {game.total_line}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <Wifi className="w-3 h-3" />
            {lastUpdated ? (
              <span>
                Updated {formatDistanceToNow(lastUpdated, { addSuffix: true })}
              </span>
            ) : (
              <span>Connecting...</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
