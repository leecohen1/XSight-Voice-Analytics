import PageHeader from '../components/ui/PageHeader'
import SectionCard from '../components/ui/SectionCard'
import EmptyState from '../components/ui/EmptyState'
import { SettingsIcon } from '../components/icons'

export default function Settings() {
  return (
    <>
      <PageHeader title="Settings" />
      <SectionCard>
        <EmptyState
          icon={<SettingsIcon size={18} />}
          title="Settings coming soon"
          description="Workspace, notification, and integration settings will live here in a later phase."
        />
      </SectionCard>
    </>
  )
}
