import { NavLink } from 'react-router-dom'
import {
  AiOperationsIcon,
  AnalyzeIcon,
  CallsIcon,
  OverviewIcon,
  SettingsIcon,
  TeamIcon,
  UploadIcon,
} from '../icons'
import { buttonClassName } from '../ui/buttonClassName'
import styles from './Sidebar.module.css'

const PRIMARY_NAV = [
  { to: '/overview', label: 'Overview', icon: OverviewIcon },
  { to: '/analyze', label: 'Analyze Call', icon: AnalyzeIcon },
  { to: '/calls', label: 'Calls', icon: CallsIcon },
  { to: '/team', label: 'Team Intelligence', icon: TeamIcon },
  { to: '/ai-operations', label: 'AI Operations', icon: AiOperationsIcon },
]

export interface SidebarProps {
  mobileOpen: boolean
  onCloseMobile: () => void
}

export default function Sidebar({ mobileOpen, onCloseMobile }: SidebarProps) {
  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          className={styles.overlay}
          aria-label="Close navigation"
          onClick={onCloseMobile}
        />
      )}
      <nav
        id="primary-navigation"
        aria-label="Primary"
        className={[styles.sidebar, mobileOpen ? styles.sidebarOpen : ''].join(' ')}
      >
        <div className={styles.brand}>
          <span className={styles.brandMark} aria-hidden="true" />
          <span className={styles.brandName}>XSight</span>
        </div>

        <div className={styles.primaryAction}>
          <NavLink to="/analyze" className={buttonClassName('primary', 'sm')} style={{ width: '100%' }} onClick={onCloseMobile}>
            <UploadIcon size={15} />
            <span className={styles.primaryActionLabel}>Analyze New Call</span>
          </NavLink>
        </div>

        <div className={styles.nav}>
          {PRIMARY_NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onCloseMobile}
              className={({ isActive }) => [styles.navLink, isActive ? styles.navLinkActive : ''].join(' ')}
            >
              <Icon size={18} />
              <span className={styles.navLabel}>{label}</span>
            </NavLink>
          ))}
        </div>

        <div className={styles.secondary}>
          <NavLink
            to="/settings"
            onClick={onCloseMobile}
            className={({ isActive }) => [styles.navLink, isActive ? styles.navLinkActive : ''].join(' ')}
          >
            <SettingsIcon size={18} />
            <span className={styles.navLabel}>Settings</span>
          </NavLink>
        </div>
      </nav>
    </>
  )
}
