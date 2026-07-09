import { describe, it, expect } from 'vitest'
import { getCard, getFlow, getBook, getSentiment, getShocks, getSimHistory } from './client'

describe('API client (mock mode)', () => {
  it('returns a card for the requested symbol', async () => {
    const card = await getCard('ETH')
    expect(card.symbol).toBe('ETH')
    expect(['LONG', 'SHORT', 'NEUTRAL']).toContain(card.direction)
    expect(card.confidence).toBeGreaterThanOrEqual(0)
    expect(card.votes.length).toBeGreaterThan(0)
  })

  it('returns flow state for the requested token', async () => {
    const flow = await getFlow('Sushi')
    expect(flow.token).toBe('Sushi')
    expect(flow.actor_mix).toBeDefined()
  })

  it('returns book state for the requested symbol', async () => {
    const book = await getBook('ETHUSDT')
    expect(book.symbol).toBe('ETHUSDT')
    expect(book.spread_bps).toBeGreaterThanOrEqual(0)
  })

  it('returns sentiment for the requested entity', async () => {
    const s = await getSentiment('ETH')
    expect(s.entity).toBe('ETH')
    expect(s.polarity).toBeGreaterThanOrEqual(-1)
    expect(s.polarity).toBeLessThanOrEqual(1)
  })

  it('returns shocks and history arrays', async () => {
    const shocks = await getShocks()
    expect(Array.isArray(shocks)).toBe(true)
    const history = await getSimHistory()
    expect(history.length).toBeGreaterThan(0)
    expect(history[0]).toHaveProperty('tick')
    expect(history[0]).toHaveProperty('price')
  })
})
