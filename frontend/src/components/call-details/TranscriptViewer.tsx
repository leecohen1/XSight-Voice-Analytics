import { useState } from 'react'
import { parseTranscriptSegments } from '../../types'
import Waveform, { type WaveformBar } from '../visual/Waveform'
import styles from './TranscriptViewer.module.css'

export interface TranscriptViewerProps {
  transcript: string
}

/**
 * The transcript navigator — a real waveform derived from each turn's
 * length, not a decorative graphic. Agent turns render in a neutral
 * bright tone, customer turns in the evidence teal (the customer's
 * voice is literally the evidence being analyzed). Clicking a bar jumps
 * to and briefly highlights that turn — functional wayfinding, not a
 * hero moment; this is the one place waveform imagery appears inside
 * Call Details, per the approved 3D/waveform restraint rule.
 */
export default function TranscriptViewer({ transcript }: TranscriptViewerProps) {
  const segments = parseTranscriptSegments(transcript)
  const [activeIndex, setActiveIndex] = useState<number | null>(null)

  const maxLength = Math.max(1, ...segments.map((s) => s.text.length))
  const bars: WaveformBar[] = segments.map((s) => ({
    height: Math.max(0.18, s.text.length / maxLength),
    color: s.speaker === 'Customer' ? 'var(--color-evidence)' : undefined,
    active: s.index === activeIndex,
  }))

  const jumpTo = (index: number) => {
    setActiveIndex(index)
    document.getElementById(`transcript-turn-${index}`)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }

  return (
    <div>
      <div className={styles.navigator}>
        <Waveform bars={bars} tone="neutral" height={40} barWidth={2} gap={2} onBarClick={jumpTo} ariaLabel="Transcript navigator" />
        <div className={styles.legend}>
          <span className={styles.legendItem}>
            <span className={styles.legendSwatchAgent} /> Agent
          </span>
          <span className={styles.legendItem}>
            <span className={styles.legendSwatchCustomer} /> Customer
          </span>
        </div>
      </div>

      <div className={styles.list}>
        {segments.map((segment) => (
          <div
            className={[styles.turn, segment.index === activeIndex ? styles.turnActive : ''].join(' ')}
            key={segment.index}
            id={`transcript-turn-${segment.index}`}
          >
            <span className={[styles.speaker, segment.speaker === 'Agent' ? styles.speakerAgent : styles.speakerCustomer].join(' ')}>
              {segment.speaker}
            </span>
            <span className={styles.text}>{segment.text}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
