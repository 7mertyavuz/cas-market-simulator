import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('switches views via sidebar and searches a symbol', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByText('Faktör Oyları')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Mikroyapı'))
    await waitFor(() => expect(screen.getByText('Flow State')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Sentiment & Şoklar'))
    await waitFor(() => expect(screen.getByText('Sentiment State')).toBeInTheDocument())

    fireEvent.click(screen.getByText('CAS Laboratuvarı'))
    expect(screen.getByText('Fiyat Seyri')).toBeInTheDocument()

    fireEvent.click(screen.getByText('HITL Onay'))
    expect(screen.getByText('HITL Onay: BTC')).toBeInTheDocument()
    expect(screen.getByText('Kartı Yükle')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Kılavuz'))
    expect(screen.getByText('CAS Market Kılavuzu')).toBeInTheDocument()

    const input = screen.getByPlaceholderText('Sembol girin (örn: BTC, ETH, TSLA)...')
    fireEvent.change(input, { target: { value: 'ETH' } })
    fireEvent.click(screen.getByText('Analiz Et'))
    await waitFor(() => expect(screen.getByText('ETH')).toBeInTheDocument())
  })
})
