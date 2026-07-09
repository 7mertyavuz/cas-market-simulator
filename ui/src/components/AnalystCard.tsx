import { useEffect, useState } from 'react'
import { getCard } from '../api/client'
import LoadingSkeleton from './LoadingSkeleton'
import type { Card } from '../types'

const directionColor: Record<string, string> = {
  LONG: 'text-accent-green',
  SHORT: 'text-accent-red',
  NEUTRAL: 'text-text-muted',
}

const directionBg: Record<string, string> = {
  LONG: 'from-accent-green/10 to-accent-green/5 border-accent-green/30',
  SHORT: 'from-accent-red/10 to-accent-red/5 border-accent-red/30',
  NEUTRAL: 'from-surface-light to-surface border-border',
}

const directionGlow: Record<string, string> = {
  LONG: 'shadow-accent-green/10',
  SHORT: 'shadow-accent-red/10',
  NEUTRAL: 'shadow-transparent',
}

interface Props {
  symbol: string
}

export default function AnalystCard({ symbol }: Props) {
  const [card, setCard] = useState<Card | null>(null)

  useEffect(() => {
    setCard(null)
    getCard(symbol).then(setCard)
    const id = setInterval(() => getCard(symbol).then(setCard), 5_000)
    return () => clearInterval(id)
  }, [symbol])

  if (!card) return <LoadingSkeleton rows={6} />

  return (
    <div className="space-y-6">
      <div className={`rounded-2xl border bg-gradient-to-br p-6 shadow-lg ${directionBg[card.direction]} ${directionGlow[card.direction]}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-4xl font-black tracking-tight text-text">{card.symbol}</h2>
              <span className="px-2.5 py-1 rounded-md bg-surface/60 border border-border text-xs font-semibold text-text-muted uppercase tracking-wide">
                Analyst Card
              </span>
            </div>
            <p className="text-sm text-text-muted mt-1">{new Date(card.ts).toLocaleString('tr-TR')}</p>
          </div>
          <div className="text-left sm:text-right">
            <div className={`text-5xl font-black ${directionColor[card.direction]}`}>{card.direction}</div>
            <div className="text-lg text-text-muted">Güven: {(card.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-accent-blue flex items-center gap-2">
            <span>📊</span> Faktör Oyları
          </h3>
          <div className="space-y-4">
            {card.votes.map((v) => (
              <div key={v.name}>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="text-text font-medium capitalize">{v.name}</span>
                  <span className="text-text-muted">ağırlık {v.weight.toFixed(2)}</span>
                </div>
                <div className="h-2.5 bg-surface-light rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${v.vote >= 0 ? 'bg-accent-green' : 'bg-accent-red'}`}
                    style={{ width: `${Math.abs(v.vote) * 100}%`, marginLeft: v.vote < 0 ? 'auto' : 0, marginRight: v.vote < 0 ? 0 : 'auto' }}
                  />
                </div>
                <div className="flex justify-between text-xs text-text-muted mt-1">
                  <span>{v.market}</span>
                  <span>{v.vote.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-accent-purple flex items-center gap-2">
            <span>🎯</span> Formasyonlar & Risk
          </h3>
          <div className="space-y-4">
            {card.patterns.length === 0 && (
              <div className="text-sm text-text-muted">Aktif formasyon tespiti yok.</div>
            )}
            {card.patterns.map((p) => (
              <div key={p.name} className="flex items-center justify-between bg-surface-light p-3 rounded-xl border border-border">
                <div>
                  <div className="font-medium text-text capitalize">{p.name}</div>
                  <div className="text-xs text-text-muted uppercase">{p.direction}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-accent">{(p.strength * 100).toFixed(0)}%</div>
                  {p.invalidation && (
                    <div className="text-xs text-text-muted">inv: {p.invalidation.toLocaleString()}</div>
                  )}
                </div>
              </div>
            ))}
            <div className="pt-2 border-t border-border">
              <div className="text-sm font-medium text-text-muted mb-2">Risk Parametreleri</div>
              {Object.entries(card.risk).length === 0 && (
                <div className="text-sm text-text-muted">Risk parametresi yok.</div>
              )}
              {Object.entries(card.risk).map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm py-1">
                  <span className="text-text-muted capitalize">{k}</span>
                  <span className="text-text font-medium">{typeof v === 'number' ? v.toLocaleString() : String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
