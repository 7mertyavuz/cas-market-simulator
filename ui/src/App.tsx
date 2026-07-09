import { useState } from 'react'
import Sidebar from './components/Sidebar'
import AnalystCard from './components/AnalystCard'
import MicrostructurePanel from './components/MicrostructurePanel'
import SentimentPanel from './components/SentimentPanel'
import CasLabPanel from './components/CasLabPanel'
import HitlPanel from './components/HitlPanel'

export type View = 'card' | 'micro' | 'sentiment' | 'caslab' | 'hitl'

function App() {
  const [view, setView] = useState<View>('card')

  return (
    <div className="flex h-screen bg-bg text-text">
      <Sidebar active={view} onChange={setView} />
      <main className="flex-1 overflow-auto p-6">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-accent">CAS Market Dashboard</h1>
          <p className="text-sm text-text-muted">
            Karmaşık Uyarlanabilir Sistem tabanlı piyasa gözlem ve simülasyon ekranı
          </p>
        </header>
        {view === 'card' && <AnalystCard />}
        {view === 'micro' && <MicrostructurePanel />}
        {view === 'sentiment' && <SentimentPanel />}
        {view === 'caslab' && <CasLabPanel />}
        {view === 'hitl' && <HitlPanel />}
      </main>
    </div>
  )
}

export default App
