import styles from './Button.module.css'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost'
export type ButtonSize = 'sm' | 'md'

/** Shared class-name builder so Link-as-button (e.g. Overview's CTA, Sidebar's primary action) matches Button exactly. */
export function buttonClassName(variant: ButtonVariant = 'primary', size: ButtonSize = 'md', extra?: string): string {
  return [styles.button, styles[variant], styles[size], extra].filter(Boolean).join(' ')
}
