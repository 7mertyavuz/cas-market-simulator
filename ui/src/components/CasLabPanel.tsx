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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-accent">CAS Laboratuvarı</h3>
        <div className="flex gap-2">
          <button
            onClick={refresh}
            className="px-4 py-2 bg-accent-blue/10 text-accent-blue border border-accent-blue/30 rounded-lg text-sm hover:bg-accent-blue/20"
          >
            Yenile
          </button>
          <button className="px-4 py-2 bg-accent-red/10 text-accent-red border border-accent-red/30 rounded-lg text-sm hover:bg-accent-red/20">
            Panik Şoku
          </button>
          <button className="px-4 py-2 bg-accent-purple/10 text-accent-purple border border-accent-purple/30 rounded-lg text-sm hover:bg-accent-purple/20">
            Balina Emri
          </button>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-xl p-6">
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

      <div className="bg-surface border border-border rounded-xl p-6">
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
