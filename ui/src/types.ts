export interface FactorVote {
  name: string
  vote: number
  weight: number
  market: string
}

export interface PatternHit {
  name: string
  direction: 'bull' | 'bear' | 'neutral'
  strength: number
  invalidation: number | null
}

export interface Card {
  symbol: string
  direction: 'LONG' | 'SHORT' | 'NEUTRAL'
  confidence: number
  votes: FactorVote[]
  patterns: PatternHit[]
  risk: Record<string, unknown>
  ts: string
}

export interface FlowState {
  token: string
  flow_imbalance: number
  vpin_toxicity: number
  whale_net_usd: number
  actor_mix: Record<string, number>
  direction_prob_up: number
  lead_lag_spread: number
  regime: 'normal' | 'toxic' | 'highvol'
  ts: string
}

export interface BookState {
  symbol: string
  spread_bps: number
  microprice: number
  depth_imbalance: number
  ofi: number
  queue_imbalance: number
  book_slope: number
  kyle_lambda: number
  iceberg_score: number
  spoof_score: number
  absorption: number
  liq_map_skew: number
  ts: string
}

export interface SentimentState {
  entity: string
  polarity: number
  intensity: number
  emotion: Record<string, number>
  confidence: number
  fed_tone: number | null
  source_breakdown: Record<string, number>
  ts: string
}

export interface ShockEvent {
  kind: 'panic' | 'euphoria' | 'fed_tone' | 'narrative_shift'
  entity: string
  magnitude: number
  decay_halflife_s: number
  ts: string
}

export interface TickResult {
  tick: number
  price: number
  card_direction: string
  card_confidence: number
  active_shock_magnitude: number
  crowd_emergence_score: number
}
