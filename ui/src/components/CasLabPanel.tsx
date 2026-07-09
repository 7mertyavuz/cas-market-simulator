import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { getSimHistory } from '../api/client'
import type { TickResult } from '../types'

export default function CasLabPanel() {
  const [history, setHistory] = useState<TickResult[]>([])

  useEffect(() => {
    getSimHistory().then(setHistory)
  }, [])

  const refresh = () => getSimHistory().then(setHistory)

  const latest = history[history.length - 1]

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-accent-purple/10 to-accent-blue/10 border border-accent-purple/20 rounded-2xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-text">CAS Laboratuvarı</h2>
            <p className="text-sm text-text-muted mt-1">Simülasyon, şok enjeksiyonu ve crowd emergence gözlemi</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={refresh}
              className="px-4 py-2 bg-accent-blue/10 text-accent-blue border border-accent-blue/30 rounded-xl text-sm font-medium hover:bg-accent-blue/20 transition-colors"
            >
              🔄 Yenile
            </button>
            <button className="px-4 py-2 bg-accent-red/10 text-accent-red border border-accent-red/30 rounded-xl text-sm font-medium hover:bg-accent-red/20 transition-colors">
              💥 Panik Şoku
            </button>
            <button className="px-4 py-2 bg-accent-purple/10 text-accent-purple border border-accent-purple/30 rounded-xl text-sm font-medium hover:bg-accent-purple/20 transition-colors">
              🐋 Balina Emri
            </button>
          </div>
        </div>
      </div>

      {latest && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Metric label="Son Fiyat" value={latest.price.toLocaleString()} />
          <Metric label="Yön" value={latest.card_direction} />
          <Metric label="Crowd Score" value={latest.crowd_emergence_score.toFixed(2)} />
        </div>
      )}

      <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
        <h4 className="text-sm font-semibold text-text-muted mb-4">Fiyat Seyri</h4>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2e3a4a" />
              <XAxis dataKey="tick" stroke="#9ca3af" />
              <YAxis domain={['auto', 'auto']} stroke="#9ca3af" />
              <Tooltip contentStyle={{ backgroundColor: '#161b22', borderColor: '#2e3a4a' }} />
              <Line type="monotone" dataKey="price" stroke="#f59e0b" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-2xl p-6 shadow-sm">
        <h4 className="text-sm font-semibold text-text-muted mb-4">Crowd Emergence Score</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2e3a4a" />
              <XAxis dataKey="tick" stroke="#9ca3af" />
              <YAxis domain={[-1, 1]} stroke="#9ca3af" />
              <Tooltip contentStyle={{ backgroundColor: '#161b22', borderColor: '#2e3a4a' }} />
              <Line type="monotone" dataKey="crowd_emergence_score" stroke="#34d399" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-light p-4 rounded-xl border border-border text-center">
      <div className="text-xs text-text-muted uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-bold text-text mt-1">{value}</div>
    </div>
  )
}
