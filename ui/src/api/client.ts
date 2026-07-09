import type { Card, FlowState, BookState, SentimentState, ShockEvent, TickResult } from '../types'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const API_BASE = '/v1'

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<T>
}

// ------------------------------------------------------------------
// Mock data (backend henuz bagli degilse)
// ------------------------------------------------------------------
const mockCard: Card = {
  symbol: 'BTC',
  direction: 'LONG',
  confidence: 0.62,
  votes: [
    { name: 'trend', vote: 0.4, weight: 1.0, market: 'crypto' },
    { name: 'momentum', vote: 0.5, weight: 0.9, market: 'crypto' },
    { name: 'volume', vote: 0.2, weight: 0.7, market: 'crypto' },
    { name: 'orderbook', vote: 0.3, weight: 0.6, market: 'crypto' },
    { name: 'sentiment', vote: 0.1, weight: 0.4, market: 'crypto' },
  ],
  patterns: [
    { name: 'engulfing', direction: 'bull', strength: 0.72, invalidation: 65000 },
  ],
  risk: { size_pct: 0.08, stop: 62500, take: 70500 },
  ts: new Date().toISOString(),
}

const mockFlow: FlowState = {
  token: 'UniswapV2',
  flow_imbalance: 0.25,
  vpin_toxicity: 0.18,
  whale_net_usd: 120_000,
  actor_mix: { WHALE: 0.15, MEV_BOT: 0.2, RETAIL: 0.65 },
  direction_prob_up: 0.58,
  lead_lag_spread: 0.003,
  regime: 'normal',
  ts: new Date().toISOString(),
}

const mockBook: BookState = {
  symbol: 'BTCUSDT',
  spread_bps: 8.5,
  microprice: 67_350.0,
  depth_imbalance: 0.12,
  ofi: 3.2,
  queue_imbalance: 0.08,
  book_slope: 2.1,
  kyle_lambda: 1.2e-6,
  iceberg_score: 0.22,
  spoof_score: 0.05,
  absorption: 0.18,
  liq_map_skew: -0.1,
  ts: new Date().toISOString(),
}

const mockSentiment: SentimentState = {
  entity: 'BTC',
  polarity: 0.15,
  intensity: 42,
  emotion: { fear: 0.25, greed: 0.35, uncertainty: 0.4 },
  confidence: 0.65,
  fed_tone: null,
  source_breakdown: { news: 0.1, social: 0.2, fed: 0.0 },
  ts: new Date().toISOString(),
}

const mockShocks: ShockEvent[] = [
  { kind: 'panic', entity: 'BTC', magnitude: 0.3, decay_halflife_s: 300, ts: new Date().toISOString() },
]

const mockHistory: TickResult[] = Array.from({ length: 30 }, (_, i) => ({
  tick: i,
  price: 67_000 + Math.sin(i / 3) * 500 + i * 10,
  card_direction: i % 5 === 0 ? 'SHORT' : 'LONG',
  card_confidence: 0.5 + Math.random() * 0.3,
  active_shock_magnitude: i === 10 ? 0.4 : 0,
  crowd_emergence_score: Math.sin(i / 4) * 0.3,
}))

// ------------------------------------------------------------------
// Client
// ------------------------------------------------------------------
export async function getCard(symbol: string): Promise<Card> {
  if (USE_MOCK) return { ...mockCard, symbol, ts: new Date().toISOString() }
  return fetchJson<Card>(`/card/${symbol}`)
}

export async function getFlow(token: string): Promise<FlowState> {
  if (USE_MOCK) return { ...mockFlow, token, ts: new Date().toISOString() }
  return fetchJson<FlowState>(`/flow/${token}`)
}

export async function getBook(symbol: string): Promise<BookState> {
  if (USE_MOCK) return { ...mockBook, symbol, ts: new Date().toISOString() }
  return fetchJson<BookState>(`/book/${symbol}`)
}

export async function getSentiment(entity: string): Promise<SentimentState> {
  if (USE_MOCK) return { ...mockSentiment, entity, ts: new Date().toISOString() }
  return fetchJson<SentimentState>(`/sentiment/${entity}`)
}

export async function getShocks(): Promise<ShockEvent[]> {
  if (USE_MOCK) return mockShocks.map((s) => ({ ...s, ts: new Date().toISOString() }))
  return fetchJson<ShockEvent[]>('/shocks')
}

export async function getSimHistory(): Promise<TickResult[]> {
  if (USE_MOCK) return mockHistory
  return fetchJson<TickResult[]>('/sim/history')
}
