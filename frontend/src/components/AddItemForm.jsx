import { useState } from 'react'
import { addNote, addUrl } from '../api'

// Lets the user save either a text note or a URL.
export default function AddItemForm({ onAdded }) {
  const [type, setType] = useState('note')
  const [text, setText] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (type === 'note') {
        await addNote(text)
      } else {
        await addUrl(text)
      }
      setText('')
      onAdded() // tell the parent to refresh the list
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const tabStyle = (name) =>
    `px-3 py-1 rounded text-sm ${type === name ? 'bg-slate-800 text-white' : 'bg-slate-200'}`

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-4 space-y-3">
      <h2 className="font-semibold">Add to your inbox</h2>

      <div className="flex gap-2">
        <button type="button" className={tabStyle('note')} onClick={() => setType('note')}>
          Note
        </button>
        <button type="button" className={tabStyle('url')} onClick={() => setType('url')}>
          URL
        </button>
      </div>

      {type === 'note' ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Write a note..."
          rows={4}
          className="w-full border rounded p-2"
        />
      ) : (
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="https://example.com/article"
          className="w-full border rounded p-2"
        />
      )}

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <button
        type="submit"
        disabled={saving || !text.trim()}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {saving ? 'Saving...' : 'Save'}
      </button>
    </form>
  )
}
