import { useEffect, useRef, useState } from 'react'
import { useAskXsight } from '../../features/ask-xsight/useAskXsight'
import { CloseIcon, MessageIcon, SendIcon } from '../icons'
import AskXsightMessageBubble from './AskXsightMessageBubble'
import AskXsightSuggestedQuestions from './AskXsightSuggestedQuestions'
import styles from './AskXsightPanel.module.css'

export interface AskXsightPanelProps {
  callId: string
  /** Whether this call has an analysis to ask questions about — disables the trigger otherwise. */
  disabled?: boolean
}

/**
 * Floating "Ask XSight" action + contained side panel (bottom sheet on
 * mobile). Never opens itself (CLAUDE.md §9) — only in response to the
 * trigger button. Fully self-contained: owns its own state via
 * useAskXsight, so Call Details just renders <AskXsightPanel callId={...} />.
 */
export default function AskXsightPanel({ callId, disabled }: AskXsightPanelProps) {
  const { state, messages, suggestedQuestions, error, open, close, ask } = useAskXsight(callId)
  const [draft, setDraft] = useState('')
  const triggerRef = useRef<HTMLButtonElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const bodyRef = useRef<HTMLDivElement>(null)
  const isOpen = state !== 'closed'
  const isLoading = state === 'loading'

  useEffect(() => {
    if (isOpen) inputRef.current?.focus()
  }, [isOpen])

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight
  }, [messages, state])

  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close()
        triggerRef.current?.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, close])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft.trim() || isLoading) return
    void ask(draft)
    setDraft('')
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className={styles.trigger}
        onClick={open}
        disabled={disabled}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-controls="ask-xsight-panel"
      >
        <MessageIcon size={16} />
        Ask XSight
      </button>

      {isOpen && (
        <>
          <button type="button" className={styles.overlay} aria-label="Close Ask XSight" onClick={close} />
          <div id="ask-xsight-panel" className={styles.panel} role="dialog" aria-modal="true" aria-label="Ask XSight">
            <div className={styles.header}>
              <div className={styles.headerTitleGroup}>
                <span className={styles.headerTitle}>Ask XSight</span>
                <span className={styles.headerCaption}>Evidence-grounded explanations about this call</span>
              </div>
              <button type="button" className={styles.closeButton} onClick={close} aria-label="Close Ask XSight">
                <CloseIcon size={18} />
              </button>
            </div>

            <div className={styles.body} ref={bodyRef}>
              {messages.length === 0 && (
                <p className={styles.emptyIntro}>
                  Ask a question about this call's transcript, evidence, scores, or routing decision. XSight answers
                  only from this call's evidence and always cites its sources.
                </p>
              )}

              {messages.length > 0 && (
                <div className={styles.messages} role="list" aria-label="Conversation">
                  {messages.map((message) => (
                    <AskXsightMessageBubble message={message} key={message.id} />
                  ))}
                </div>
              )}

              {isLoading && (
                <div className={styles.loadingRow} role="status" aria-label="XSight is thinking">
                  <span className={styles.dot} />
                  <span className={styles.dot} />
                  <span className={styles.dot} />
                </div>
              )}

              {state === 'error' && error && (
                <div className={styles.errorBox} role="alert">
                  <strong>Couldn't get an answer</strong>
                  <span>{error.message}</span>
                </div>
              )}

              {suggestedQuestions.length > 0 && !isLoading && (
                <div>
                  <div className={styles.suggestedLabel}>Suggested questions</div>
                  <AskXsightSuggestedQuestions
                    questions={suggestedQuestions}
                    onSelect={(q) => void ask(q.text)}
                  />
                </div>
              )}
            </div>

            <form className={styles.form} onSubmit={handleSubmit}>
              <input
                ref={inputRef}
                className={styles.input}
                type="text"
                placeholder="Ask a question about this call…"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                disabled={isLoading}
                aria-label="Ask a question about this call"
              />
              <button type="submit" className={styles.sendButton} disabled={isLoading || !draft.trim()} aria-label="Send question">
                <SendIcon size={16} />
              </button>
            </form>
          </div>
        </>
      )}
    </>
  )
}
