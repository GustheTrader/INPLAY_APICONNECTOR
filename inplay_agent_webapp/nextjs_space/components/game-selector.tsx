
'use client'

import { LiveGame } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Play, Clock, Users } from 'lucide-react'
import { ScrollArea } from './ui/scroll-area'

interface GameSelectorProps {
  games: LiveGame[]
  onSelectGame: (gameId: string) => void
  isLoading: boolean
}

export function GameSelector({ games, onSelectGame, isLoading }: GameSelectorProps) {
  const formatGameStatus = (status: string) => {
    if (status.includes('Final')) return { text: 'Final', variant: 'secondary' as const }
    if (status.includes('Half')) return { text: 'Halftime', variant: 'outline' as const }
    if (status.includes('In Progress')) return { text: 'Live', variant: 'destructive' as const }
    return { text: status, variant: 'outline' as const }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Live Games
          <Badge variant="outline" className="ml-auto">
            {games?.length || 0} available
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {games?.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Play className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No live games available</p>
            <p className="text-sm">Check back during NFL game times</p>
          </div>
        ) : (
          <ScrollArea className="max-h-[400px] custom-scrollbar">
            <div className="space-y-3">
              {games?.map((game) => {
                const status = formatGameStatus(game.status)
                const isLive = status.variant === 'destructive'
                
                return (
                  <Card key={game.event_id} className="relative overflow-hidden">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-medium text-sm mb-1">
                            {game.short_name || game.name}
                          </h3>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            <span>Q{game.quarter} {game.clock}</span>
                            <Badge variant={status.variant} className="text-xs">
                              {isLive && <div className="w-1 h-1 bg-current rounded-full mr-1 animate-pulse" />}
                              {status.text}
                            </Badge>
                          </div>
                        </div>
                        
                        <Button
                          size="sm"
                          onClick={() => onSelectGame(game.event_id)}
                          disabled={isLoading}
                          className="ml-4"
                        >
                          <Play className="w-3 h-3 mr-1" />
                          Track
                        </Button>
                      </div>

                      {/* Score Display */}
                      <div className="flex items-center justify-center space-x-6">
                        {/* Away Team */}
                        <div className="text-center flex-1">
                          <div className="text-xs text-muted-foreground mb-1 truncate">
                            {game.away_team}
                          </div>
                          <div className="text-lg font-bold">
                            {game.away_score}
                          </div>
                        </div>

                        <div className="text-xs text-muted-foreground font-medium">
                          vs
                        </div>

                        {/* Home Team */}
                        <div className="text-center flex-1">
                          <div className="text-xs text-muted-foreground mb-1 truncate">
                            {game.home_team}
                          </div>
                          <div className="text-lg font-bold">
                            {game.home_score}
                          </div>
                        </div>
                      </div>

                      {/* Live indicator overlay */}
                      {isLive && (
                        <div className="absolute top-2 right-2">
                          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
