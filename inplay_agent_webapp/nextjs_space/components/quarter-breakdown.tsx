
'use client'

import { QuarterScore } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { BarChart3, Trophy } from 'lucide-react'

interface QuarterBreakdownProps {
  quarterScores: QuarterScore[]
  homeTeam: string
  awayTeam: string
}

export function QuarterBreakdown({ quarterScores, homeTeam, awayTeam }: QuarterBreakdownProps) {
  const maxQuarterScore = Math.max(
    ...quarterScores.flatMap(q => [q.home_score, q.away_score])
  )

  const getTotalScore = (team: 'home' | 'away') => {
    return quarterScores.reduce((total, quarter) => {
      return total + (team === 'home' ? quarter.home_score : quarter.away_score)
    }, 0)
  }

  const getQuarterWinner = (quarter: QuarterScore) => {
    if (quarter.home_score > quarter.away_score) return 'home'
    if (quarter.away_score > quarter.home_score) return 'away'
    return 'tie'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Quarter Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {quarterScores?.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No quarter data available yet</p>
          </div>
        ) : (
          <>
            {/* Quarter by Quarter */}
            <div className="space-y-3">
              {quarterScores?.map((quarter) => {
                const winner = getQuarterWinner(quarter)
                return (
                  <div key={quarter.quarter} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline" className="text-xs">
                        Q{quarter.quarter}
                      </Badge>
                      {winner !== 'tie' && (
                        <Trophy className="w-3 h-3 text-yellow-500" />
                      )}
                    </div>
                    
                    <div className="space-y-1">
                      {/* Away Team */}
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground truncate max-w-[80px]">
                          {awayTeam}
                        </span>
                        <div className="flex items-center gap-2 flex-1 mx-2">
                          <div 
                            className={`h-2 bg-blue-500 rounded-full transition-all duration-500 ${
                              winner === 'away' ? 'bg-blue-400' : 'bg-blue-500/50'
                            }`}
                            style={{
                              width: maxQuarterScore > 0 
                                ? `${(quarter.away_score / maxQuarterScore) * 100}%` 
                                : '0%'
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-6 text-right">
                          {quarter.away_score}
                        </span>
                      </div>
                      
                      {/* Home Team */}
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground truncate max-w-[80px]">
                          {homeTeam}
                        </span>
                        <div className="flex items-center gap-2 flex-1 mx-2">
                          <div 
                            className={`h-2 bg-green-500 rounded-full transition-all duration-500 ${
                              winner === 'home' ? 'bg-green-400' : 'bg-green-500/50'
                            }`}
                            style={{
                              width: maxQuarterScore > 0 
                                ? `${(quarter.home_score / maxQuarterScore) * 100}%` 
                                : '0%'
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-6 text-right">
                          {quarter.home_score}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Total Scores */}
            <div className="border-t pt-4 space-y-2">
              <div className="text-sm font-medium text-center mb-2">Total Score</div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{awayTeam}</span>
                <Badge variant="secondary" className="text-lg font-bold px-3">
                  {getTotalScore('away')}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{homeTeam}</span>
                <Badge variant="secondary" className="text-lg font-bold px-3">
                  {getTotalScore('home')}
                </Badge>
              </div>
            </div>

            {/* Quarter Summary */}
            <div className="border-t pt-4">
              <div className="text-xs text-muted-foreground text-center">
                {quarterScores?.length > 0 && (
                  <>
                    Quarters played: {quarterScores.length}
                    {quarterScores.length >= 4 && (
                      <div className="mt-1">
                        {quarterScores.length > 4 ? 'Overtime' : 'Regulation'}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
