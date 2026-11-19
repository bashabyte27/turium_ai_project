import { useState } from 'react'
import { askQuestion } from '../api'

// Handles asking a question: loading state, the result, and any error.
export function useAsk() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function ask(question) {
    setLoading(true)
    setError('')
    try {
      setResult(await askQuestion(question))
    } catch (err) {
      setResult(null)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return { result, loading, error, ask }
}
