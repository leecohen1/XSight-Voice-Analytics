import type { AskXsightMessage } from '../../types'
import AskXsightCitationChip from './AskXsightCitationChip'
import AskXsightNotEnoughEvidence from './AskXsightNotEnoughEvidence'
import styles from './AskXsightMessageBubble.module.css'

export default function AskXsightMessageBubble({ message }: { message: AskXsightMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={[styles.row, isUser ? styles.rowUser : ''].join(' ')} role="listitem">
      {message.notEnoughEvidence ? (
        <AskXsightNotEnoughEvidence />
      ) : (
        <div className={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAssistant].join(' ')}>
          {message.text}
          {message.citations && message.citations.length > 0 && (
            <div className={styles.citations}>
              {message.citations.map((citation, i) => (
                <AskXsightCitationChip citation={citation} key={i} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
