import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AnalystCard from './AnalystCard'

describe('AnalystCard', () => {
  it('renders the card symbol and factor votes', async () => {
    render(<AnalystCard />)
    expect(await screen.findByText('BTC')).toBeInTheDocument()
    expect(screen.getByText('Faktör Oyları')).toBeInTheDocument()
  })
})
