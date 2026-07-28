import styles from './CitationChip.module.css'

export interface CitationChipProps {
  label: string
  title?: string
  onClick?: () => void
}

/** An annotation-mark citation — a footnote reference in the evidence teal, not a chat-style pill. Used for similar-call references and Ask XSight citations. */
export default function CitationChip({ label, title, onClick }: CitationChipProps) {
  if (onClick) {
    return (
      <button type="button" className={styles.mark} onClick={onClick} title={title}>
        {label}
      </button>
    )
  }
  return (
    <span className={styles.mark} title={title}>
      {label}
    </span>
  )
}
