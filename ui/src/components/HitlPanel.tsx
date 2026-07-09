import { useState } from 'react'
import { getCard } from '../api/client'
import type { Card } from '../types'

export default function HitlPanel() {
  const [card, setCard] = useState<Card | null>(null)
  const [override, setOverride] = useState<'LONG' | 'SHORT' | 'NEUTRAL' | null>(null)
  const [size, setSize] = useState(50)
  const [note, setNote] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const loadCard = async () => {
    const c = await getCard('BTC')
    setCard(c)
    setOverride(null)
    setSubmitted(false)
  }

  const submit = () => {
    setSubmitted(true)
    // TODO: POST /v1/hitl/override
    console.log({ override, size, note, card })
  }

  return (
    <div className="space-y-6">
      <div className="bg-surface border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-2 text-accent">İnsan-On-The-Loop (HITL)</h3>
        <p className="text-sm text-text-muted mb-4">
          Model çıktısını gözden geçir, risk/override kararı ver ve operatör notunu kaydet.
        </p>
        <button
          onClick={loadCard}
          className="px-4 py-2 bg-accent-blue/10 text-accent-blue border border-accent-blue/30 rounded-lg text-sm hover:bg-accent-blue/20"
        >
          Son Kartı Yükle
        </button>
      </div>

      {card && (
        <div className="bg-surface border border-border rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-text-muted">Model yönü</div>
              <div className={`text-2xl font-bold ${card.direction === 'LONG' ? 'text-accent-green' : card.direction === 'SHORT' ? 'text-accent-red' : 'text-text'}`}>
                {card.direction}
              </div>
            </div>
            <div>
              <div className="text-sm text-text-muted">Confidence</div>
              <div className="text-2xl font-bold text-text">{(card.confidence * 100).toFixed(0)}%</div>
            </div>
          </div>

          <div>
            <label className="text-sm text-text-muted block mb-2">Operatör Override</label>
            <div className="flex gap-3">
              {(['LONG', 'SHORT', 'NEUTRAL'] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => setOverride(d)}
                  className={`flex-1 py-2 rounded-lg border text-sm font-semibold transition-colors ${
                    override === d
                      ? d === 'LONG'
                        ? 'bg-accent-green/20 border-accent-green text-accent-green'
                        : d === 'SHORT'
                        ? 'bg-accent-red/20 border-accent-red text-accent-red'
                        : 'bg-text-muted/20 border-text-muted text-text'
                      : 'bg-surface-light border-border text-text-muted hover:text-text'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm text-text-muted block mb-2">Pozisyon büyüklüğü (%)</label>
            <input
              type="range"
              min={0}
              max={100}
              value={size}
              onChange={(e) => setSize(Number(e.target.value))}
              className="w-full accent-accent"
            />
            <div className="text-right text-sm text-text mt-1">{size}%</div>
          </div>

          <div>
            <label className="text-sm text-text-muted block mb-2">Operatör notu</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              className="w-full bg-surface-light border border-border rounded-lg p-3 text-sm text-text focus:outline-none focus:border-accent"
              placeholder="Neden override edildi?"
            />
          </div>

          <button
            onClick={submit}
            disabled={!override}
            className="w-full py-3 bg-accent text-bg font-semibold rounded-lg hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Kararı Onayla & Gönder
          </button>

          {submitted && (
            <div className="text-center text-sm text-accent-green">
              Override kaydedildi (mock).
            </div>
          )}
        </div>
      )}
    </div>
  )
}
