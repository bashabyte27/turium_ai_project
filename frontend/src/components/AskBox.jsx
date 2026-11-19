import { useState } from 'react'
import { useAsk } from '../hooks/useAsk'

// Shows where a piece of the answer came from.
function SourceCard({ source }) {
  return (
    <li className="border rounded p-3 bg-slate-50">
      <p className="text-sm font-medium">
        [{source.number}] {source.source_url ? (
          <a href={source.source_url} target="_blank" rel="noreferrer" className="text-blue-600 underline">
            {source.title}
          </a>
        ) : (
          source.title
        )}
      </p>
      <p className="text-sm text-slate-600 mt-1">{source.snippet}</p>
      <p className="text-xs text-slate-400 mt-1">match score: {source.score.toFixed(2)}</p>
    </li>
  )
}

export default function AskBox() {
  const [question, setQuestion] = useState('')
  const { result, loading, error, ask } = useAsk()

  function handleSubmit(event) {
    event.preventDefault()
    ask(question)
  }

  return (
    <section className="bg-white rounded-lg shadow p-4 space-y-3">
      <h2 className="font-semibold">Ask a question</h2>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What do my notes say about...?"
          className="flex-1 border rounded p-2"
        />
        <button
          type="submit"
          disabled={loading || question.trim().length < 3}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {result && (
        <div className="space-y-3">
          <div>
            <h3 className="font-medium">Answer</h3>
            <p className="mt-1">{result.answer}</p>
            {result.mode === 'extractive' && (
              <p className="text-xs text-slate-400 mt-1">
                This answer is quoted directly from your saved text (the AI model was not used).
              </p>
            )}
          </div>

          {result.sources.length > 0 && (
            <div>
              <h3 className="font-medium mb-1">Sources</h3>
              <ul className="space-y-2">
                {result.sources.map((source) => (
                  <SourceCard key={source.number} source={source} />
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
