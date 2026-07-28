import { useCallback, useState } from 'react'
import type { AskXsightError, AskXsightMessage, AskXsightQuestion, AskXsightState } from '../../types'
import { askCallQuestion, getConversationHistory, getSuggestedQuestions } from '../../services/askXsightApi'

export interface UseAskXsightResult {
  state: AskXsightState
  messages: AskXsightMessage[]
  suggestedQuestions: AskXsightQuestion[]
  error: AskXsightError | null
  open: () => void
  close: () => void
  ask: (question: string) => Promise<void>
}

/** Drives the Ask XSight panel's full state machine (CLAUDE.md §9.5). Never opens itself — the panel calls `open()` only in response to an explicit user action. */
export function useAskXsight(callId: string): UseAskXsightResult {
  const [state, setState] = useState<AskXsightState>('closed')
  const [messages, setMessages] = useState<AskXsightMessage[]>([])
  const [suggestedQuestions, setSuggestedQuestions] = useState<AskXsightQuestion[]>([])
  const [error, setError] = useState<AskXsightError | null>(null)
  const [loadedFor, setLoadedFor] = useState<string | null>(null)

  const open = useCallback(() => {
    setState('open')
    if (loadedFor !== callId) {
      getConversationHistory(callId).then(setMessages)
      getSuggestedQuestions(callId).then(setSuggestedQuestions)
      setLoadedFor(callId)
    }
  }, [callId, loadedFor])

  const close = useCallback(() => setState('closed'), [])

  const ask = useCallback(
    async (question: string) => {
      const trimmed = question.trim()
      if (!trimmed) return

      setState('loading')
      setError(null)
      setMessages((prev) => [
        ...prev,
        { id: `local-u-${Date.now()}`, role: 'user', text: trimmed, createdAt: new Date().toISOString() },
      ])

      const response = await askCallQuestion({ callId, question: trimmed })

      if (response.error) {
        setError(response.error)
        setState('error')
        return
      }

      if (!response.answer || response.answer.notEnoughEvidence) {
        setMessages((prev) => [
          ...prev,
          { id: `local-a-${Date.now()}`, role: 'assistant', text: '', notEnoughEvidence: true, createdAt: new Date().toISOString() },
        ])
        setState('not_enough_evidence')
        return
      }

      setMessages((prev) => [
        ...prev,
        {
          id: `local-a-${Date.now()}`,
          role: 'assistant',
          text: response.answer!.text,
          citations: response.answer!.citations,
          createdAt: new Date().toISOString(),
        },
      ])
      setState('answered')
    },
    [callId]
  )

  return { state, messages, suggestedQuestions, error, open, close, ask }
}
