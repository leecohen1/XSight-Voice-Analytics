import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeCall, isMockMode } from '../api/analyzeCall'

const initialForm = {
  agentName: '',
  callDate: '',
  customerName: '',
  notes: '',
}

export default function Upload() {
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [audioFile, setAudioFile] = useState(null)
  const [status, setStatus] = useState('idle') // idle | submitting | error
  const [errorMessage, setErrorMessage] = useState('')

  const updateField = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  const handleFileChange = (e) => {
    setAudioFile(e.target.files?.[0] ?? null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMessage('')

    if (!audioFile) {
      setStatus('error')
      setErrorMessage('Please choose an audio file to upload.')
      return
    }
    if (!form.agentName.trim() || !form.callDate) {
      setStatus('error')
      setErrorMessage('Agent name and call date are required.')
      return
    }

    setStatus('submitting')
    try {
      const result = await analyzeCall({
        audioFile,
        agentName: form.agentName,
        callDate: form.callDate,
        customerName: form.customerName,
        notes: form.notes,
      })
      navigate('/results', { state: { result } })
    } catch (err) {
      setStatus('error')
      setErrorMessage(err.message || 'Something went wrong while analyzing the call.')
    }
  }

  const isSubmitting = status === 'submitting'

  return (
    <div className="page page-upload">
      <h1>Sales Call Upload</h1>
      <p className="mode-indicator">
        Mode:{' '}
        <strong>{isMockMode() ? 'Mock (fixture data)' : 'Live (n8n webhook)'}</strong>
      </p>

      <form className="upload-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Audio file *</span>
          <input
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
            disabled={isSubmitting}
          />
        </label>

        <label className="field">
          <span>Agent name *</span>
          <input
            type="text"
            value={form.agentName}
            onChange={updateField('agentName')}
            placeholder="e.g. Sarah Levi"
            disabled={isSubmitting}
          />
        </label>

        <label className="field">
          <span>Call date *</span>
          <input
            type="date"
            value={form.callDate}
            onChange={updateField('callDate')}
            disabled={isSubmitting}
          />
        </label>

        <label className="field">
          <span>Customer / company name (optional)</span>
          <input
            type="text"
            value={form.customerName}
            onChange={updateField('customerName')}
            placeholder="e.g. Northwind Solutions"
            disabled={isSubmitting}
          />
        </label>

        <label className="field">
          <span>Notes (optional)</span>
          <textarea
            value={form.notes}
            onChange={updateField('notes')}
            rows={4}
            placeholder="Any extra context about this call"
            disabled={isSubmitting}
          />
        </label>

        {status === 'error' && (
          <div className="form-error" role="alert">
            {errorMessage}
          </div>
        )}

        <button className="button button-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <span className="spinner" aria-hidden="true" /> Analyzing call…
            </>
          ) : (
            'Submit for Analysis'
          )}
        </button>
      </form>
    </div>
  )
}
