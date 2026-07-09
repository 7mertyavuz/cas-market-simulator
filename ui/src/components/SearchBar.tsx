import { useState } from 'react'

interface Props {
  value: string
  onChange: (symbol: string) => void
}

const PRESETS = ['BTC', 'ETH', 'SOL', 'AVAX', 'BIST', 'TSLA', 'GOLD', 'EURUSD']

export default function SearchBar({ value, onChange }: Props) {
  const [input, setInput] = useState(value)

  const submit = (s: string) => {
    const clean = s.trim().toUpperCase()
    if (!clean) return
    setInput(clean)
    onChange(clean)
  }

  return (
    <div className="space-y-3">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit(input)
        }}
        className="flex gap-3"
      >
        <div className="relative flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">🔎</span>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase())}
            placeholder="Sembol girin (örn: BTC, ETH, TSLA)..."
            className="w-full bg-surface border border-border rounded-xl pl-10 pr-4 py-3 text-text placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
          />
        </div>
        <button
          type="submit"
          className="px-6 py-3 bg-accent text-bg font-semibold rounded-xl hover:bg-accent/90 transition-colors"
        >
          Analiz Et
        </button>
      </form>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((s) => (
          <button
            key={s}
            onClick={() => submit(s)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              value === s
                ? 'bg-accent/20 border-accent text-accent'
                : 'bg-surface border-border text-text-muted hover:border-accent/50 hover:text-text'
            }`}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
