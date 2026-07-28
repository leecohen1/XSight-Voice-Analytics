import type { WaveformBar } from './Waveform'

/** Deterministic, pleasant-looking ambient bar pattern (no true randomness — stays stable across renders). */
export function generateAmbientBars(count: number): WaveformBar[] {
  return Array.from({ length: count }).map((_, i) => {
    const t = i / count
    const wave = Math.sin(t * Math.PI * 3.1) * 0.35 + Math.sin(t * Math.PI * 7.7 + 1.2) * 0.2
    return { height: Math.max(0.12, Math.min(1, 0.55 + wave)) }
  })
}
