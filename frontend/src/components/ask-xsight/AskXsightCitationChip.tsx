import type { AskXsightCitation } from '../../types'
import CitationChip from '../ui/CitationChip'

export default function AskXsightCitationChip({ citation }: { citation: AskXsightCitation }) {
  return <CitationChip label={citation.label} title={citation.detail} />
}
