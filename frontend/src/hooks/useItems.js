import { useCallback, useEffect, useState } from 'react'
import { getItems } from '../api'

// Loads the saved items. While any item is still "pending" (being fetched and
// embedded in the background), it re-checks every 2 seconds until they finish.
export function useItems() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    try {
      const data = await getItems()
      setItems(data.items)
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  const hasPending = items.some((item) => item.status === 'pending')

  useEffect(() => {
    if (!hasPending) return
    const timer = setInterval(reload, 2000)
    return () => clearInterval(timer)
  }, [hasPending, reload])

  return { items, error, reload }
}
