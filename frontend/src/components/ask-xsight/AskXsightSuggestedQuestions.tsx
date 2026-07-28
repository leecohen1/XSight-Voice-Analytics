import type { AskXsightQuestion } from '../../types'
import styles from './AskXsightSuggestedQuestions.module.css'

export interface AskXsightSuggestedQuestionsProps {
  questions: AskXsightQuestion[]
  onSelect: (question: AskXsightQuestion) => void
}

export default function AskXsightSuggestedQuestions({ questions, onSelect }: AskXsightSuggestedQuestionsProps) {
  if (questions.length === 0) return null
  return (
    <div className={styles.list} role="list" aria-label="Suggested questions">
      {questions.map((q) => (
        <button key={q.id} type="button" className={styles.item} onClick={() => onSelect(q)}>
          {q.text}
        </button>
      ))}
    </div>
  )
}
