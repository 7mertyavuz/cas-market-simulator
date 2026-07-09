import { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { getFlow, getBook } from '../api/client'
import LoadingSkeleton from './LoadingSkeleton'
import type { FlowState, BookState } from '../types'

const COLORS = ['#60a5fa', '#f87171', '#34d399', '#fbbf24', '#c084fc']

interface Props {
  symbol: string
}

export default function MicrostructurePanel({ symbol }: Props) {
  const [flow, setFlow] = useState<FlowState | null>(null)
  const [book, setBook] = useState<BookState | null>(null)

  useEffect(() => {
    const load = async () => {
      setFlow(null)
      setBook(null)
      const [f, b] = await Promise.all([getFlow(symbol), getBook(`${symbol}USDT`)])
      setFlow(f)
      setBook(b)
    }
    load()
    const id = setInterval(load, 5_000)
    return () => clearInterval(id)
  }, [symbol])

  const actorData = flow
    ? Object.entries(flow.actor_mix).map(([name, value]) => ({ name, value: Number((value * 100).toFixed(1)) }))
    : []

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-accent-blue/10 to-accent-purple/10 border border-accent-blue/20 rounded-2xl p-6">
        <h2 className="text-2xl font-bold text-text">Mikroyapı: {symbol}</h2>
        <p className="text-sm text-text-muted mt-1">Order flow, defter okuma ve katılımcı dağılımı</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-accent-blue flex items-center gap-2">
            <span>🌊</span> Flow State
          </h3>
          {flow ? (
            <div className="grid grid-cols-2 gap-4">
              <Metric label="Imbalance" value={flow.flow_imbalance.toFixed(2)} />
              <Metric label="VPIN Toksisite" value={(flow.vpin_toxicity * 100).toFixed(1) + '%'} />
              <Metric label="Yukarı İhtimal" value={(flow.direction_prob_up * 100).toFixed(1) + '%'} />
              <Metric label="Regime" value={flow.regime} />
              <Metric label="Whale Net" value={'$' + flow.whale_net_usd.toLocaleString()} />
              <Metric label="Lead-Lag" value={flow.lead_lag_spread.toFixed(4)} />
            </div>
          ) : (
            <LoadingSkeleton rows={4} />
          )}
        </div>

        <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-accent-purple flex items-center gap-2">
            <span>🥧</span> Actor Mix
          </h3>
          {flow ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={actorData} dataKey="value" nameKey="name" outerRadius={80} label={({ name, value }) => `${name}: ${value}%`}>
                    {actorData.map((_, i) => (
                      <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#161b22', borderColor: '#2e3a4a' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <LoadingSkeleton rows={4} />
          )}
        </div>
      </div>

      <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4 text-accent-green flex items-center gap-2">
          <span>📖</span> Book State
        </h3>
        {book ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Metric label="Spread bps" value={book.spread_bps.toFixed(2)} />
            <Metric label="Microprice" value={book.microprice.toLocaleString()} />
            <Metric label="Depth Imb" value={book.depth_imbalance.toFixed(2)} />
            <Metric label="OFI" value={book.ofi.toFixed(2)} />
            <Metric label="Book Slope" value={book.book_slope.toFixed(2)} />
            <Metric label="Kyle λ" value={book.kyle_lambda.toExponential(2)} />
            <Metric label="Iceberg Şüphesi" value={(book.iceberg_score * 100).toFixed(0) + '%'} />
            <Metric label="Spoof Şüphesi" value={(book.spoof_score * 100).toFixed(0) + '%'} />
            <Metric label="Absorption" value={book.absorption.toFixed(2)} />
            <Metric label="Liq Skew" value={book.liq_map_skew.toFixed(2)} />
          </div>
        ) : (
          <LoadingSkeleton rows={4} />
        )}
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-light p-4 rounded-xl border border-border hover:border-accent/30 transition-colors">
      <div className="text-xs text-text-muted uppercase tracking-wide">{label}</div>
      <div className="text-xl font-bold text-text mt-1">{value}</div>
    </div>
  )
}
