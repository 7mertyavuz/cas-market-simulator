import { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { getFlow, getBook } from '../api/client'
import type { FlowState, BookState } from '../types'

const COLORS = ['#60a5fa', '#f87171', '#34d399']

export default function MicrostructurePanel() {
  const [flow, setFlow] = useState<FlowState | null>(null)
  const [book, setBook] = useState<BookState | null>(null)

  useEffect(() => {
    const load = async () => {
      const [f, b] = await Promise.all([getFlow('UniswapV2'), getBook('BTCUSDT')])
      setFlow(f)
      setBook(b)
    }
    load()
    const id = setInterval(load, 5_000)
    return () => clearInterval(id)
  }, [])

  const actorData = flow
    ? Object.entries(flow.actor_mix).map(([name, value]) => ({ name, value: Number((value * 100).toFixed(1)) }))
    : []

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 text-accent-blue">Flow State</h3>
          {flow ? (
            <div className="grid grid-cols-2 gap-4">
              <Metric label="Imbalance" value={flow.flow_imbalance.toFixed(2)} />
              <Metric label="VPIN" value={(flow.vpin_toxicity * 100).toFixed(1) + '%'} />
              <Metric label="Prob Up" value={(flow.direction_prob_up * 100).toFixed(1) + '%'} />
              <Metric label="Regime" value={flow.regime} />
              <Metric label="Whale Net" value={'$' + flow.whale_net_usd.toLocaleString()} />
              <Metric label="Lead-Lag" value={flow.lead_lag_spread.toFixed(4)} />
            </div>
          ) : (
            <div className="text-text-muted">Yükleniyor...</div>
          )}
        </div>

        <div className="bg-surface border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 text-accent-purple">Actor Mix</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={actorData} dataKey="value" nameKey="name" outerRadius={70}>
                  {actorData.map((_, i) => (
                    <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#161b22', borderColor: '#2e3a4a' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4 text-accent-green">Book State</h3>
        {book ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Metric label="Spread bps" value={book.spread_bps.toFixed(2)} />
            <Metric label="Microprice" value={book.microprice.toLocaleString()} />
            <Metric label="Depth Imb" value={book.depth_imbalance.toFixed(2)} />
            <Metric label="OFI" value={book.ofi.toFixed(2)} />
            <Metric label="Book Slope" value={book.book_slope.toFixed(2)} />
            <Metric label="Kyle λ" value={book.kyle_lambda.toExponential(2)} />
            <Metric label="Iceberg" value={(book.iceberg_score * 100).toFixed(0) + '%'} />
            <Metric label="Spoof" value={(book.spoof_score * 100).toFixed(0) + '%'} />
            <Metric label="Absorption" value={book.absorption.toFixed(2)} />
            <Metric label="Liq Skew" value={book.liq_map_skew.toFixed(2)} />
          </div>
        ) : (
          <div className="text-text-muted">Yükleniyor...</div>
        )}
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-light p-3 rounded-lg">
      <div className="text-xs text-text-muted uppercase tracking-wide">{label}</div>
      <div className="text-lg font-semibold text-text mt-1">{value}</div>
    </div>
  )
}
