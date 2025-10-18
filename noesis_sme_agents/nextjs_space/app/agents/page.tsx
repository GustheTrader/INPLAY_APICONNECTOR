
import { getServerSession } from 'next-auth'
import { redirect } from 'next/navigation'
import { authOptions } from '@/lib/auth'
import { AgentsDashboard } from '@/components/agents/agents-dashboard'

export default async function AgentsPage() {
  const session = await getServerSession(authOptions)

  if (!session) {
    redirect('/auth/signin')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <AgentsDashboard />
    </div>
  )
}
