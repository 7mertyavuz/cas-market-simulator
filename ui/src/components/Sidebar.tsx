import type { View } from '../App'

interface Props {
  active: View
  onChange: (view: View) => void
}

const items: { key: View; label: string; icon: string }[] = [
  { key: 'card', label: 'Analist Kartı', icon: '🃏' },
  { key: 'micro', label: 'Mikroyapı', icon: '🔬' },
  { key: 'sentiment', label: 'Sentiment & Şoklar', icon: '📰' },
  { key: 'caslab', label: 'CAS Laboratuvarı', icon: '🧪' },
  { key: 'hitl', label: 'HITL Onay', icon: '✋' },
]

export default function Sidebar({ active, onChange }: Props) {
  return (
    <aside className="w-64 bg-surface border-r border-border flex flex-col">
      <div className="p-6 border-b border-border">
        <h2 className="text-lg font-bold text-accent">CAS Market</h2>
        <p className="text-xs text-text-muted mt-1">Dashboard v0.1.0</p>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {items.map((item) => (
          <button
            key={item.key}
            onClick={() => onChange(item.key)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
              active === item.key
                ? 'bg-accent/10 text-accent border border-accent/30'
                : 'text-text-muted hover:bg-surface-light hover:text-text'
            }`}
          >
            <span>{item.icon}</span>
            <span className="text-sm font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="p-4 border-t border-border text-xs text-text-muted">
        Yatırım tavsiyesi değildir.
      </div>
    </aside>
  )
}
