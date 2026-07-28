import { useLayoutEffect, useRef, useState } from 'react'
import styles from './Tabs.module.css'

export interface TabItem {
  id: string
  label: string
}

export interface TabsProps {
  items: TabItem[]
  activeId: string
  onChange: (id: string) => void
  label: string
}

/** Accessible tablist with a sliding active-tab indicator — arrow-key navigation per CLAUDE.md's accessible-tab-behavior requirement. */
export default function Tabs({ items, activeId, onChange, label }: TabsProps) {
  const refs = useRef<Record<string, HTMLButtonElement | null>>({})
  const listRef = useRef<HTMLDivElement>(null)
  const [indicator, setIndicator] = useState<{ left: number; width: number } | null>(null)

  useLayoutEffect(() => {
    const activeButton = refs.current[activeId]
    const list = listRef.current
    if (!activeButton || !list) return
    const buttonRect = activeButton.getBoundingClientRect()
    const listRect = list.getBoundingClientRect()
    setIndicator({ left: buttonRect.left - listRect.left, width: buttonRect.width })
  }, [activeId, items])

  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    event.preventDefault()
    const delta = event.key === 'ArrowRight' ? 1 : -1
    const nextIndex = (index + delta + items.length) % items.length
    const next = items[nextIndex]
    onChange(next.id)
    refs.current[next.id]?.focus()
  }

  return (
    <div className={styles.list} role="tablist" aria-label={label} ref={listRef}>
      {indicator && <span className={styles.indicator} style={{ left: indicator.left, width: indicator.width }} aria-hidden="true" />}
      {items.map((item, index) => (
        <button
          key={item.id}
          ref={(el) => {
            refs.current[item.id] = el
          }}
          role="tab"
          type="button"
          id={`tab-${item.id}`}
          aria-selected={item.id === activeId}
          aria-controls={`tabpanel-${item.id}`}
          tabIndex={item.id === activeId ? 0 : -1}
          className={[styles.tab, item.id === activeId ? styles.tabActive : ''].join(' ')}
          onClick={() => onChange(item.id)}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}
