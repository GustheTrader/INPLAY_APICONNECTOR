
'use client'

import { useState, useEffect } from 'react'
import { apiClient, ApiConfig } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Alert, AlertDescription } from './ui/alert'
import { Badge } from './ui/badge'
import { Settings, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import Link from 'next/link'

export function ApiConfigForm() {
  const [config, setConfig] = useState<ApiConfig | null>(null)
  const [formData, setFormData] = useState({
    api_type: 'custom',
    endpoint_url: '',
    auth_key: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    fetchCurrentConfig()
  }, [])

  const fetchCurrentConfig = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await apiClient.getApiConfig()
      if (response.success) {
        setConfig(response.config)
        if (response.config.api_type === 'custom') {
          setFormData({
            api_type: 'custom',
            endpoint_url: response.config.endpoint_url,
            auth_key: '' // Don't populate auth key for security
          })
        }
      }
    } catch (error) {
      console.error('Error fetching config:', error)
      setError('Failed to fetch current configuration')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.endpoint_url.trim()) {
      setError('Endpoint URL is required')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await apiClient.configureApi(
        formData.api_type,
        formData.endpoint_url,
        formData.auth_key || undefined
      )

      if (response.success) {
        toast({
          title: 'Success',
          description: 'API configuration saved successfully',
        })
        await fetchCurrentConfig()
      }
    } catch (error) {
      console.error('Error saving config:', error)
      setError('Failed to save configuration')
      toast({
        title: 'Error',
        description: 'Failed to save configuration',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetToDefault = () => {
    setFormData({
      api_type: 'espn',
      endpoint_url: 'https://site.api.espn.com/apis/site/v2/sports/football/nfl',
      auth_key: ''
    })
    setError(null)
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <div>
        <Link href="/">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </Link>
      </div>

      {/* Current Configuration */}
      {config && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Current Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">API Type:</span>
              <Badge variant={config.api_type === 'espn' ? 'default' : 'secondary'}>
                {config.api_type.toUpperCase()}
              </Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Endpoint:</span>
              <span className="text-sm font-mono bg-muted px-2 py-1 rounded truncate max-w-[300px]">
                {config.endpoint_url}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Auth Key:</span>
              <Badge variant={config.has_auth_key ? 'default' : 'outline'}>
                {config.has_auth_key ? 'Configured' : 'None'}
              </Badge>
            </div>

            {config.message && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{config.message}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Configuration Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Configure Custom API
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="endpoint_url">API Endpoint URL *</Label>
              <Input
                id="endpoint_url"
                type="url"
                placeholder="https://api.example.com/nfl"
                value={formData.endpoint_url}
                onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
                required
              />
              <p className="text-xs text-muted-foreground">
                Enter the base URL for your custom NFL data API
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="auth_key">Authentication Key (Optional)</Label>
              <Input
                id="auth_key"
                type="password"
                placeholder="Enter API key or leave blank"
                value={formData.auth_key}
                onChange={(e) => setFormData({ ...formData, auth_key: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">
                API key or token for authenticated requests (if required)
              </p>
            </div>

            <div className="flex items-center gap-4">
              <Button
                type="submit"
                disabled={isSubmitting || isLoading}
              >
                {isSubmitting ? 'Saving...' : 'Save Configuration'}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={resetToDefault}
                disabled={isSubmitting || isLoading}
              >
                Use ESPN Default
              </Button>
            </div>
          </form>

          {/* Configuration Notes */}
          <div className="mt-8 space-y-4 border-t pt-6">
            <h3 className="font-medium">Configuration Notes</h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>
                • The API endpoint should provide NFL game data in a compatible format
              </p>
              <p>
                • Leave the auth key blank if your API doesn't require authentication
              </p>
              <p>
                • The default ESPN API is free and doesn't require an API key
              </p>
              <p>
                • Changes take effect immediately for new game tracking sessions
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
