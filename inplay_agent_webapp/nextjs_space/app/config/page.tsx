
import { ApiConfigForm } from '@/components/api-config-form'
import { Suspense } from 'react'

export const dynamic = 'force-dynamic'

export default function ConfigPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Configuration</h1>
          <p className="text-muted-foreground mt-2">
            Configure your custom API endpoint for game data
          </p>
        </div>
        <Suspense fallback={<div>Loading...</div>}>
          <ApiConfigForm />
        </Suspense>
      </div>
    </div>
  )
}
