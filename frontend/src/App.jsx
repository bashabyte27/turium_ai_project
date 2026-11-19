import AddItemForm from './components/AddItemForm'
import AskBox from './components/AskBox'
import ItemList from './components/ItemList'
import { useItems } from './hooks/useItems'

export default function App() {
  const { items, error, reload } = useItems()

  return (
    <div className="min-h-screen bg-slate-100">
      <main className="max-w-3xl mx-auto p-4 space-y-4">
        <h1 className="text-2xl font-bold">AI Knowledge Inbox</h1>

        <AddItemForm onAdded={reload} />
        <AskBox />
        <ItemList items={items} error={error} />
      </main>
    </div>
  )
}
