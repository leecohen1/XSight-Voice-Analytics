import type { ButtonHTMLAttributes } from 'react'
import styles from './Button.module.css'
import { buttonClassName, type ButtonSize, type ButtonVariant } from './buttonClassName'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}

export default function Button({ variant = 'primary', size = 'md', loading, disabled, children, className, ...rest }: ButtonProps) {
  return (
    <button className={buttonClassName(variant, size, className)} disabled={disabled || loading} {...rest}>
      {loading && <span className={styles.spinner} aria-hidden="true" />}
      {children}
    </button>
  )
}
