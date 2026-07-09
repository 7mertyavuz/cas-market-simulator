import { useState } from 'react'
import Sidebar from './components/Sidebar'
import SearchBar from './components/SearchBar'
import AnalystCard from './components/AnalystCard'
import MicrostructurePanel from './components/MicrostructurePanel'
import SentimentPanel from './components/SentimentPanel'
import CasLabPanel from './components/CasLabPanel'
import HitlPanel from './components/HitlPanel'
import GuidePanel from './components/GuidePanel'

export type View = 'card' | 'micro' | 'sentiment' | 'caslab' | 'hitl' | 'guide'

function App() {
  const [view, setView] = useState<View>('card')
  const [symbol, setSymbol] = useState('BTC')

  return (
    <div className="flex h-screen bg-bg text-text">
      <Sidebar active={view} onChange={setView} />
      <main className="flex-1 overflow-auto p-6">
        <header className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 mb-4">
            <div>
              <h1 className="text-3xl font-black tracking-tight text-accent">CAS Market Dashboard</h1>
              <p className="text-sm text-text-muted mt-1">
                Karmaşık Uyarlanabilir Sistem tabanlı piyasa gözlem ve simülasyon ekranı
              </p>
            </div>
            <div className="text-xs text-text-muted">
              v0.1.0 · mock/real toggle: <code className="text-accent">VITE_USE_MOCK=false</code>
            </div>
          </div>
          <SearchBar value={symbol} onChange={setSymbol} />
        </header>

        {view === 'card' && <AnalystCard symbol={symbol} />}
        {view === 'micro' && <MicrostructurePanel symbol={symbol} />}
        {view === 'sentiment' && <SentimentPanel symbol={symbol} />}
        {view === 'caslab' && <CasLabPanel />}
        {view === 'hitl' && <HitlPanel symbol={symbol} />}
        {view === 'guide' && <GuidePanel />}
      </main>
    </div>
  )
}

export default App
