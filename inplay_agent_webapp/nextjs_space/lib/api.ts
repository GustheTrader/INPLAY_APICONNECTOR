
/**
 * API utilities for communicating with the INPLAY Agent backend
 */

const API_BASE_URL = 'http://localhost:5000';

export interface GameState {
  event_id: string;
  name: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  quarter: number;
  clock: string;
  status: string;
  status_detail: string;
  venue?: string;
  spread?: string;
  total_line?: string;
  last_updated: string;
}

export interface GameSituation {
  possession_team?: string;
  down?: number;
  distance?: number;
  yard_line?: string;
}

export interface Play {
  play_id?: string;
  quarter?: number;
  clock?: string;
  play_type?: string;
  play_text?: string;
  team_name?: string;
  is_scoring_play?: boolean;
  score_value?: number;
  home_score?: number;
  away_score?: number;
  ai_commentary?: string;
  significance_score?: number;
  momentum_shift?: string;
  created_at?: string;
}

export interface QuarterScore {
  quarter: number;
  home_score: number;
  away_score: number;
}

export interface LiveGame {
  event_id: string;
  name: string;
  short_name?: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  quarter: number;
  clock: string;
  status: string;
}

export interface ApiConfig {
  api_type: string;
  endpoint_url: string;
  has_auth_key: boolean;
  created_at?: string;
  message?: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string; version: string }> {
    return this.request('/health');
  }

  // Game tracking
  async startTracking(eventId: string, pollInterval: number = 15): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/game/start?event_id=${eventId}&poll_interval=${pollInterval}`);
  }

  async stopTracking(eventId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/game/stop?event_id=${eventId}`);
  }

  async getCurrentGame(eventId: string): Promise<{
    success: boolean;
    game: GameState;
    quarter_scores: QuarterScore[];
    situation: GameSituation;
    ai_analysis?: { content: string; created_at: string };
  }> {
    return this.request(`/api/game/current?event_id=${eventId}`);
  }

  async getGamePlays(eventId: string, limit: number = 50, quarter?: number): Promise<{
    success: boolean;
    event_id: string;
    play_count: number;
    plays: Play[];
  }> {
    let endpoint = `/api/game/plays?event_id=${eventId}&limit=${limit}`;
    if (quarter) {
      endpoint += `&quarter=${quarter}`;
    }
    return this.request(endpoint);
  }

  async getLiveGames(): Promise<{
    success: boolean;
    count: number;
    games: LiveGame[];
  }> {
    return this.request('/api/games/live');
  }

  async getTrackedGames(): Promise<{
    success: boolean;
    count: number;
    games: GameState[];
  }> {
    return this.request('/api/games/tracked');
  }

  async getGameAnalysis(eventId: string, type?: string): Promise<{
    success: boolean;
    event_id: string;
    count: number;
    analyses: Array<{
      type: string;
      content: string;
      metadata?: any;
      created_at: string;
    }>;
  }> {
    let endpoint = `/api/game/analysis?event_id=${eventId}`;
    if (type) {
      endpoint += `&type=${type}`;
    }
    return this.request(endpoint);
  }

  // API Configuration
  async configureApi(apiType: string, endpointUrl: string, authKey?: string): Promise<{
    success: boolean;
    config_id: string;
    message: string;
  }> {
    return this.request('/api/config/api', {
      method: 'POST',
      body: JSON.stringify({
        api_type: apiType,
        endpoint_url: endpointUrl,
        auth_key: authKey,
      }),
    });
  }

  async getApiConfig(): Promise<{
    success: boolean;
    config: ApiConfig;
  }> {
    return this.request('/api/config/api');
  }
}

export const apiClient = new ApiClient();
