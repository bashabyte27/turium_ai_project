// Colour and label for each processing status.
const STATUS = {
  pending: { label: 'Processing...', style: 'bg-yellow-100 text-yellow-800' },
  ready: { label: 'Ready', style: 'bg-green-100 text-green-800' },
  failed: { label: 'Failed', style: 'bg-red-100 text-red-800' },
}

function ItemRow({ item }) {
  const status = STATUS[item.status]
  return (
    <li className="border rounded p-3">
      <div className="flex justify-between gap-2">
        <span className="font-medium">{item.title}</span>
        <span className={`text-xs px-2 py-1 rounded h-fit ${status.style}`}>{status.label}</span>
      </div>

      <p className="text-xs text-slate-500">
        {item.source_type === 'url' ? 'URL' : 'Note'} · {new Date(item.created_at).toLocaleString()}
        {item.status === 'ready' && ` · ${item.chunk_count} chunks`}
      </p>

      {item.preview && <p className="text-sm text-slate-600 mt-1">{item.preview}</p>}
      {item.error && <p className="text-sm text-red-600 mt-1">{item.error}</p>}
    </li>
  )
}

export default function ItemList({ items, error }) {
  return (
    <section className="bg-white rounded-lg shadow p-4">
      <h2 className="font-semibold mb-3">Saved items ({items.length})</h2>

      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      {items.length === 0 && <p className="text-slate-500 text-sm">Nothing saved yet.</p>}

      <ul className="space-y-2">
        {items.map((item) => (
          <ItemRow key={item.id} item={item} />
        ))}
      </ul>
    </section>
  )
}
