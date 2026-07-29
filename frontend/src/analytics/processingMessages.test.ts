/**
 * Pure escalation logic for Analyze Call's processing message. Tested
 * directly against elapsed seconds rather than through fake component
 * timers, which is both faster and avoids the well-known fragility of
 * mixing vitest fake timers with React's own scheduling.
 */
import { describe, expect, it } from 'vitest'
import { elapsedMessage, formatElapsed } from './processingMessages'

describe('elapsedMessage', () => {
  it('starts with the upload/validation message', () => {
    expect(elapsedMessage(0)).toMatch(/Uploading and validating/i)
    expect(elapsedMessage(19)).toMatch(/Uploading and validating/i)
  })

  it('escalates to the AI-analysis message at 20s', () => {
    expect(elapsedMessage(20)).toMatch(/AI analysis is running/i)
    expect(elapsedMessage(59)).toMatch(/AI analysis is running/i)
  })

  it('escalates to the still-processing message at 60s', () => {
    expect(elapsedMessage(60)).toMatch(/Still processing/i)
    expect(elapsedMessage(119)).toMatch(/Still processing/i)
  })

  it('escalates to the taking-longer message at 120s', () => {
    expect(elapsedMessage(120)).toMatch(/Taking longer than usual/i)
    expect(elapsedMessage(500)).toMatch(/Taking longer than usual/i)
  })

  it('never claims a specific backend pipeline stage has finished', () => {
    // The messages may describe the process in aggregate ("transcription,
    // extraction... happen in this step") -- the thing that must never
    // appear is a specific stage marked done, which is what the old
    // four-step tracker got wrong by sitting frozen on "Uploaded".
    for (const seconds of [0, 10, 25, 61, 130, 300]) {
      const text = elapsedMessage(seconds)
      expect(text).not.toMatch(/transcription (complete|done|finished)/i)
      expect(text).not.toMatch(/guardrails? (passed|complete|done)/i)
      expect(text).not.toMatch(/extraction (complete|done|finished)/i)
    }
  })
})

describe('formatElapsed', () => {
  it('renders under a minute as seconds', () => {
    expect(formatElapsed(0)).toBe('0s')
    expect(formatElapsed(45)).toBe('45s')
  })

  it('renders a minute or more as m:ss', () => {
    expect(formatElapsed(60)).toBe('1:00')
    expect(formatElapsed(65)).toBe('1:05')
    expect(formatElapsed(150)).toBe('2:30')
  })
})
