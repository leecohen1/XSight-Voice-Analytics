import { MenuIcon } from '../icons'
import styles from './TopNavigation.module.css'

export interface TopNavigationProps {
  onOpenMobileNav: () => void
}

export default function TopNavigation({ onOpenMobileNav }: TopNavigationProps) {
  return (
    <div className={styles.bar}>
      <button
        type="button"
        className={styles.menuButton}
        aria-label="Open navigation"
        aria-controls="primary-navigation"
        onClick={onOpenMobileNav}
      >
        <MenuIcon size={20} />
      </button>
      <span className={styles.mobileBrand}>XSight</span>
      <span className={styles.spacer} />
      <div className={styles.profile}>
        <div className={styles.profileText}>
          <span className={styles.profileName}>Sales Manager</span>
          <span className={styles.profileRole}>Demo workspace</span>
        </div>
        <span className={styles.avatar} aria-hidden="true">
          SM
        </span>
      </div>
    </div>
  )
}
