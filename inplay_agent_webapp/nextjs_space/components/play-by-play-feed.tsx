
'use client'

import { Play } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { ScrollArea } from './ui/scroll-area'
import { Clock, TrendingUp, TrendingDown, Target, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PlayByPlayFeedProps {
  plays: Play[]
  isLoading: boolean
}

export function PlayByPlayFeed({ plays, isLoading }: PlayByPlayFeedProps) {
  const getMomentumIcon = (momentum: string | undefined) => {
    switch (momentum?.toLowerCase()) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-red-500" />
      default:
        return <Activity className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getPlayTypeColor = (playType: string | undefined) => {
    const type = playType?.toLowerCase() || ''
    if (type.includes('pass')) return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
    if (type.includes('rush') || type.includes('run')) return 'bg-green-500/10 text-green-400 border-green-500/20'
    if (type.includes('kick') || type.includes('punt')) return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
    if (type.includes('penalty')) return 'bg-red-500/10 text-red-400 border-red-500/20'
    return 'bg-muted/50 text-muted-foreground border-muted'
  }

  const formatPlayTime = (quarter: number | undefined, clock: string | undefined) => {
    if (!quarter || !clock) return ''
    return `Q${quarter} ${clock}`
  }

  return (
    <Card className="h-[600px]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Play-by-Play Feed
          {isLoading && (
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[520px] custom-scrollbar">
          <div className="p-6 space-y-4">
            {plays?.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No plays available yet</p>
                <p className="text-sm">Plays will appear as the game progresses</p>
              </div>
            ) : (
              plays?.map((play, index) => (
                <div
                  key={play.play_id || index}
                  className={cn(
                    "relative p-4 rounded-lg border transition-all duration-200 animate-slide-in",
                    play.is_scoring_play && "scoring-play",
                    play.momentum_shift === 'positive' && !play.is_scoring_play && "momentum-positive",
                    play.momentum_shift === 'negative' && !play.is_scoring_play && "momentum-negative"
                  )}
                  style={{ animationDelay: `${index * 0.05}s` }}
                >
                  {/* Play Header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant="outline" 
                        className={getPlayTypeColor(play.play_type)}
                      >
                        {play.play_type || 'Play'}
                      </Badge>
                      {play.is_scoring_play && (
                        <Badge variant="default" className="bg-yellow-500 text-black">
                          <Target className="w-3 h-3 mr-1" />
                          {play.score_value}pts
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {formatPlayTime(play.quarter, play.clock)}
                    </div>
                  </div>

                  {/* Play Description */}
                  <div className="mb-3">
                    <p className="font-medium text-sm mb-1">
                      {play.team_name}
                    </p>
                    <p className="text-sm leading-relaxed">
                      {play.play_text}
                    </p>
                  </div>

                  {/* AI Commentary */}
                  {play.ai_commentary && (
                    <div className="bg-muted/50 rounded-md p-3 mb-3">
                      <div className="flex items-start gap-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-500 rounded text-white text-xs flex items-center justify-center font-bold mt-0.5">
                          AI
                        </div>
                        <p className="text-sm leading-relaxed flex-1">
                          {play.ai_commentary}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Play Metrics */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-4">
                      {play.significance_score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span>Impact:</span>
                          <span className="font-medium">
                            {(play.significance_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                      {play.momentum_shift && (
                        <div className="flex items-center gap-1">
                          {getMomentumIcon(play.momentum_shift)}
                          <span className="capitalize">{play.momentum_shift}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="font-mono">
                      {play.away_score} - {play.home_score}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
