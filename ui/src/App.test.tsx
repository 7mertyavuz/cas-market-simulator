import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('switches views via sidebar', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByText('Faktör Oyları')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Mikroyapı'))
    await waitFor(() => expect(screen.getByText('Flow State')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Sentiment & Şoklar'))
    await waitFor(() => expect(screen.getByText('Sentiment State')).toBeInTheDocument())

    fireEvent.click(screen.getByText('CAS Laboratuvarı'))
    expect(screen.getByText('Fiyat Seyri')).toBeInTheDocument()

    fireEvent.click(screen.getByText('HITL Onay'))
    expect(screen.getByText('İnsan-On-The-Loop (HITL)')).toBeInTheDocument()
    expect(screen.getByText('Son Kartı Yükle')).toBeInTheDocument()
  })
})
