import { useEffect, useState } from 'react'
import { getSentiment, getShocks } from '../api/client'
import type { SentimentState, ShockEvent } from '../types'

export default function SentimentPanel() {
  const [sentiment, setSentiment] = useState<SentimentState | null>(null)
  const [shocks, setShocks] = useState<ShockEvent[]>([])

  useEffect(() => {
    const load = async () => {
      const [s, sh] = await Promise.all([getSentiment('BTC'), getShocks()])
      setSentiment(s)
      setShocks(sh)
    }
    load()
    const id = setInterval(load, 5_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 text-accent-blue">Sentiment State</h3>
          {sentiment ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Entity</span>
                <span className="font-semibold text-text">{sentiment.entity}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Polarity</span>
                <span className={`font-semibold ${sentiment.polarity >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                  {sentiment.polarity.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Intensity</span>
                <span className="font-semibold text-text">{sentiment.intensity.toFixed(0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Confidence</span>
                <span className="font-semibold text-text">{(sentiment.confidence * 100).toFixed(0)}%</span>
              </div>
              {sentiment.fed_tone !== null && (
                <div className="flex justify-between items-center">
                  <span className="text-text-muted">Fed Tone</span>
                  <span className="font-semibold text-accent">{sentiment.fed_tone.toFixed(2)}</span>
                </div>
              )}
              <div className="pt-4 border-t border-border">
                <div className="text-sm text-text-muted mb-2">Emotion</div>
                <div className="grid grid-cols-3 gap-2">
                  {Object.entries(sentiment.emotion).map(([k, v]) => (
                    <div key={k} className="bg-surface-light p-2 rounded text-center">
                      <div className="text-xs text-text-muted uppercase">{k}</div>
                      <div className="font-semibold text-text">{(v * 100).toFixed(0)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-text-muted">Yükleniyor...</div>
          )}
        </div>

        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 text-accent-red">Aktif Şoklar</h3>
          {shocks.length === 0 ? (
            <div className="text-text-muted">Aktif şok yok.</div>
          ) : (
            <div className="space-y-3">
              {shocks.map((s, i) => (
                <div key={i} className="bg-surface-light p-3 rounded-lg border-l-4 border-accent-red">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-text uppercase">{s.kind}</span>
                    <span className="text-sm text-text-muted">{s.entity}</span>
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-sm text-text-muted">Magnitude</span>
                    <span className="font-semibold text-accent">{(s.magnitude * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-xs text-text-muted mt-1">
                    Yarı ömür: {s.decay_halflife_s}s
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
