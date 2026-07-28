import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopNavigation from './TopNavigation'
import styles from './AppShell.module.css'

export default function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  return (
    <div className={styles.shell}>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <Sidebar mobileOpen={mobileNavOpen} onCloseMobile={() => setMobileNavOpen(false)} />
      <div className={styles.contentColumn}>
        <TopNavigation onOpenMobileNav={() => setMobileNavOpen(true)} />
        <main id="main-content" className={styles.main} tabIndex={-1}>
          <div className={[styles.mainInner, 'animateFadeInUp'].join(' ')} key={location.pathname}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
