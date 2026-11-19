// All calls to the backend live here, so components never deal with fetch directly.

async function request(path, options) {
  const response = await fetch(path, options)
  const data = await response.json()

  if (!response.ok) {
    // The backend always sends errors as { error: { code, message } }
    throw new Error(data.error?.message || 'Something went wrong.')
  }
  return data
}

function postJson(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function getItems() {
  return request('/items')
}

export function addNote(content) {
  return postJson('/ingest', { type: 'note', content })
}

export function addUrl(url) {
  return postJson('/ingest', { type: 'url', url })
}

export function askQuestion(question) {
  return postJson('/query', { question })
}
