import { useEffect, useState } from 'react'
import { getSentiment, getShocks } from '../api/client'
import LoadingSkeleton from './LoadingSkeleton'
import type { SentimentState, ShockEvent } from '../types'

interface Props {
  symbol: string
}

export default function SentimentPanel({ symbol }: Props) {
  const [sentiment, setSentiment] = useState<SentimentState | null>(null)
  const [shocks, setShocks] = useState<ShockEvent[]>([])

  useEffect(() => {
    const load = async () => {
      setSentiment(null)
      const [s, sh] = await Promise.all([getSentiment(symbol), getShocks()])
      setSentiment(s)
      setShocks(sh)
    }
    load()
    const id = setInterval(load, 5_000)
    return () => clearInterval(id)
  }, [symbol])

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-accent-red/10 to-accent-purple/10 border border-accent-red/20 rounded-2xl p-6">
        <h2 className="text-2xl font-bold text-text">Sentiment & Şoklar: {symbol}</h2>
        <p className="text-sm text-text-muted mt-1">Makro duygu durumu, duygu dağılımı ve aktif piyasa şokları</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-accent-blue flex items-center gap-2">
            <span>🧠</span> Sentiment State
          </h3>
          {sentiment ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-text-muted">Varlık</span>
                <span className="font-bold text-text text-lg">{sentiment.entity}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-text-muted">Polarite</span>
                <span className={`font-bold text-lg ${sentiment.polarity >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                  {sentiment.polarity.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-text-muted">Yoğunluk</span>
                <span className="font-bold text-text text-lg">{sentiment.intensity.toFixed(0)}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-text-muted">Confidence</span>
                <span className="font-bold text-text text-lg">{(sentiment.confidence * 100).toFixed(0)}%</span>
              </div>
              {sentiment.fed_tone !== null && (
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-text-muted">Fed Tonu</span>
                  <span className="font-bold text-accent text-lg">{sentiment.fed_tone.toFixed(2)}</span>
                </div>
              )}
              <div className="pt-2">
                <div className="text-sm text-text-muted mb-3">Duygu Dağılımı</div>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(sentiment.emotion).map(([k, v]) => (
                    <div key={k} className="bg-surface-light p-3 rounded-xl border border-border text-center">
                      <div className="text-xs text-text-muted uppercase">{k}</div>
                      <div className="font-bold text-text text-lg">{(v * 100).toFixed(0)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <LoadingSkeleton rows={5} />
          )}
        </div>

        <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-accent-red flex items-center gap-2">
            <span>⚡</span> Aktif Şoklar
          </h3>
          {shocks.length === 0 ? (
            <div className="text-text-muted">Aktif şok yok.</div>
          ) : (
            <div className="space-y-3">
              {shocks.map((s, i) => (
                <div key={i} className="bg-surface-light p-4 rounded-xl border-l-4 border-accent-red">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-text uppercase">{s.kind}</span>
                    <span className="text-sm text-text-muted">{s.entity}</span>
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-sm text-text-muted">Büyüklük</span>
                    <span className="font-bold text-accent">{(s.magnitude * 100).toFixed(0)}%</span>
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
