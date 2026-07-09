import { useState } from 'react'
import { getCard } from '../api/client'
import LoadingSkeleton from './LoadingSkeleton'
import type { Card } from '../types'

interface Props {
  symbol: string
}

export default function HitlPanel({ symbol }: Props) {
  const [card, setCard] = useState<Card | null>(null)
  const [override, setOverride] = useState<'LONG' | 'SHORT' | 'NEUTRAL' | null>(null)
  const [size, setSize] = useState(50)
  const [note, setNote] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const loadCard = async () => {
    setCard(null)
    const c = await getCard(symbol)
    setCard(c)
    setOverride(null)
    setSubmitted(false)
  }

  const submit = () => {
    setSubmitted(true)
    // TODO: POST /v1/hitl/override
    console.log({ override, size, note, card })
  }

  const dirColor = (d: string) =>
    d === 'LONG' ? 'text-accent-green' : d === 'SHORT' ? 'text-accent-red' : 'text-text-muted'

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-accent/10 to-accent-purple/10 border border-accent/20 rounded-2xl p-6">
        <h2 className="text-2xl font-bold text-text">HITL Onay: {symbol}</h2>
        <p className="text-sm text-text-muted mt-1">
          Model çıktısını gözden geçir, risk/override kararı ver ve operatör notunu kaydet.
        </p>
      </div>

      {!card && !submitted && (
        <div className="bg-surface border border-border rounded-2xl p-8 text-center">
          <div className="text-4xl mb-3">✋</div>
          <h3 className="text-lg font-semibold text-text mb-2">Kartı Yükle</h3>
          <p className="text-sm text-text-muted mb-4">
            {symbol} için üretilen analyst card'ı incelemek ve override vermek için yükleyin.
          </p>
          <button
            onClick={loadCard}
            className="px-6 py-2.5 bg-accent text-bg font-semibold rounded-xl hover:bg-accent/90 transition-colors"
          >
            Son Kartı Yükle
          </button>
        </div>
      )}

      {!card && submitted && <LoadingSkeleton rows={4} />}

      {card && (
        <div className="bg-surface border border-border rounded-2xl p-6 space-y-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-border">
            <div>
              <div className="text-sm text-text-muted">Model yönü</div>
              <div className={`text-3xl font-black ${dirColor(card.direction)}`}>{card.direction}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-text-muted">Confidence</div>
              <div className="text-3xl font-black text-text">{(card.confidence * 100).toFixed(0)}%</div>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-text block mb-3">Operatör Override</label>
            <div className="flex gap-3">
              {(['LONG', 'SHORT', 'NEUTRAL'] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => setOverride(d)}
                  className={`flex-1 py-3 rounded-xl border-2 text-sm font-bold transition-all ${
                    override === d
                      ? d === 'LONG'
                        ? 'bg-accent-green/20 border-accent-green text-accent-green shadow-md shadow-accent-green/10'
                        : d === 'SHORT'
                        ? 'bg-accent-red/20 border-accent-red text-accent-red shadow-md shadow-accent-red/10'
                        : 'bg-text-muted/20 border-text-muted text-text shadow-md'
                      : 'bg-surface-light border-border text-text-muted hover:text-text hover:border-accent/30'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-text block mb-3">Pozisyon büyüklüğü (%)</label>
            <input
              type="range"
              min={0}
              max={100}
              value={size}
              onChange={(e) => setSize(Number(e.target.value))}
              className="w-full accent-accent"
            />
            <div className="flex justify-between text-sm mt-2">
              <span className="text-text-muted">Kapalı</span>
              <span className="font-bold text-accent">{size}%</span>
              <span className="text-text-muted">Tam</span>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-text block mb-2">Operatör notu</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              className="w-full bg-surface-light border border-border rounded-xl p-4 text-sm text-text focus:outline-none focus:border-accent transition-colors resize-none"
              placeholder="Neden override edildi? Hangi risk senaryosu göz önünde bulunduruldu?"
            />
          </div>

          <button
            onClick={submit}
            disabled={!override}
            className="w-full py-3.5 bg-accent text-bg font-bold rounded-xl hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Kararı Onayla & Gönder
          </button>

          {submitted && (
            <div className="text-center text-sm text-accent-green bg-accent-green/10 border border-accent-green/30 rounded-xl py-2">
              Override kaydedildi (mock).
            </div>
          )}
        </div>
      )}
    </div>
  )
}
