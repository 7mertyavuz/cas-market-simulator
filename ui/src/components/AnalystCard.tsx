import { useEffect, useState } from 'react'
import { getCard } from '../api/client'
import type { Card } from '../types'

const directionColor: Record<string, string> = {
  LONG: 'text-accent-green',
  SHORT: 'text-accent-red',
  NEUTRAL: 'text-text-muted',
}

const directionBg: Record<string, string> = {
  LONG: 'bg-accent-green/10 border-accent-green/30',
  SHORT: 'bg-accent-red/10 border-accent-red/30',
  NEUTRAL: 'bg-surface-light border-border',
}

export default function AnalystCard() {
  const [card, setCard] = useState<Card | null>(null)

  useEffect(() => {
    getCard('BTC').then(setCard)
    const id = setInterval(() => getCard('BTC').then(setCard), 5_000)
    return () => clearInterval(id)
  }, [])

  if (!card) return <div className="text-text-muted">Yükleniyor...</div>

  return (
    <div className="space-y-6">
      <div className={`p-6 rounded-xl border ${directionBg[card.direction]}`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-text">{card.symbol}</h2>
            <p className="text-sm text-text-muted mt-1">{new Date(card.ts).toLocaleString('tr-TR')}</p>
          </div>
          <div className="text-right">
            <div className={`text-4xl font-bold ${directionColor[card.direction]}`}>{card.direction}</div>
            <div className="text-lg text-text-muted">Güven: {(card.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 text-accent-blue">Faktör Oyları</h3>
          <div className="space-y-3">
            {card.votes.map((v) => (
              <div key={v.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-text">{v.name}</span>
                  <span className="text-text-muted">w={v.weight.toFixed(2)}</span>
                </div>
                <div className="h-2 bg-surface-light rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${v.vote >= 0 ? 'bg-accent-green' : 'bg-accent-red'}`}
                    style={{ width: `${Math.abs(v.vote) * 100}%`, marginLeft: v.vote < 0 ? 'auto' : 0, marginRight: v.vote < 0 ? 0 : 'auto' }}
                  />
                </div>
                <div className="text-right text-xs text-text-muted mt-0.5">{v.vote.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 text-accent-purple">Formasyonlar & Risk</h3>
          <div className="space-y-4">
            {card.patterns.map((p) => (
              <div key={p.name} className="flex items-center justify-between bg-surface-light p-3 rounded-lg">
                <div>
                  <div className="font-medium text-text">{p.name}</div>
                  <div className="text-xs text-text-muted">{p.direction}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-accent">{(p.strength * 100).toFixed(0)}%</div>
                  {p.invalidation && (
                    <div className="text-xs text-text-muted">inv: {p.invalidation.toLocaleString()}</div>
                  )}
                </div>
              </div>
            ))}
            {Object.entries(card.risk).map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm border-t border-border pt-2">
                <span className="text-text-muted">{k}</span>
                <span className="text-text">{typeof v === 'number' ? v.toLocaleString() : String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
