import { useEffect, useState } from 'react'
import './App.css'

const API = 'http://127.0.0.1:8000'

export default function App() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [db2Items, setDb2Items] = useState([])
  const [statusMessage, setStatusMessage] = useState('')

  const fetchDb2 = async () => {
    try {
      const res = await fetch(`${API}/db2`)
      if (!res.ok) throw new Error('Could not load DB2 data')
      setDb2Items(await res.json())
    } catch (error) {
      setStatusMessage(error.message)
    }
  }

  useEffect(() => {
    fetchDb2()
  }, [])

  const handleSearch = async (e) => {
    const value = e.target.value
    setQuery(value)

    if (value.length > 1) {
      try {
        const res = await fetch(`${API}/search-db1?q=${value}`)
        if (!res.ok) throw new Error('Search failed')
        setSearchResults(await res.json())
      } catch (error) {
        setStatusMessage(error.message)
      }
    } else {
      setSearchResults([])
    }
  }

  const addToDb2 = async (pokemon) => {
    try {
      const res = await fetch(`${API}/db2`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pokemon_id: pokemon.id }),
      })
      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(errorText || 'Could not add to DB2')
      }
      setStatusMessage(`Added ${pokemon.title}`)
      await fetchDb2()
    } catch (error) {
      setStatusMessage(error.message)
    }
  }

  const updateStatus = async (id, currentStatus) => {
    const newStatus = currentStatus === 'ready to fight' ? 'defeated' : 'ready to fight'

    try {
      const res = await fetch(`${API}/db2/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      if (!res.ok) throw new Error('Could not update status')
      setStatusMessage('Status updated')
      await fetchDb2()
    } catch (error) {
      setStatusMessage(error.message)
    }
  }

  const deleteFromDb2 = async (id) => {
    try {
      const res = await fetch(`${API}/db2/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Could not delete item')
      setStatusMessage('Entry removed')
      await fetchDb2()
    } catch (error) {
      setStatusMessage(error.message)
    }
  }

  const formatListValue = (value) => {
    if (!value) return 'none'
    return value.split(',').filter(Boolean).join(', ')
  }

  return (
    <div className="app-shell">
      <header className="hero-card">
        <p className="eyebrow">Pokemon Companion</p>
        <h1>Search DB1 and manage your team in DB2</h1>
        <p className="subtitle">Use the search bar to look up entries and move them into the editable list.</p>
      </header>

      {statusMessage && <p className="status">{statusMessage}</p>}

      <section className="panel">
        <div className="panel-heading">
          <h2>DB1 search</h2>
          <p>Search entries from the reference database.</p>
        </div>
        <input
          type="text"
          value={query}
          onChange={handleSearch}
          placeholder="Search in DB1..."
          className="search-input"
        />
        <ul className="list">
          {searchResults.length === 0 && query.length > 1 ? (
            <li className="empty">No results found.</li>
          ) : (
            searchResults.map((item) => (
              <li key={item.id} className="list-item">
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.type}</small>
                  <div className="details-grid">
                    <div className="detail-item"><span className="detail-label">Weak to</span><span>{formatListValue(item.double_damage_from)}</span></div>
                    <div className="detail-item"><span className="detail-label">Resistant to</span><span>{formatListValue(item.half_damage_from)}</span></div>
                    <div className="detail-item"><span className="detail-label">Immune to</span><span>{formatListValue(item.no_damage_from)}</span></div>
                    <div className="detail-item"><span className="detail-label">Strong against</span><span>{formatListValue(item.double_damage_to)}</span></div>
                    <div className="detail-item"><span className="detail-label">Not very effective against</span><span>{formatListValue(item.half_damage_to)}</span></div>
                    <div className="detail-item"><span className="detail-label">No effect against</span><span>{formatListValue(item.no_damage_to)}</span></div>
                  </div>
                </div>
                <button onClick={() => addToDb2(item)}>Copy to DB2</button>
              </li>
            ))
          )}
        </ul>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>DB2 entries</h2>
          <p>Manage the saved items from your second database.</p>
        </div>
        <ul className="list">
          {db2Items.length === 0 ? (
            <li className="empty">No items yet.</li>
          ) : (
            db2Items.map((item) => (
              <li key={item.id} className="list-item">
                <div>
                  <strong>{item.title}</strong>
                  <p className="meta">Type: {item.type || 'unknown'}</p>
                  <p className="meta">Status: {item.status}</p>
                  <div className="details-grid">
                    <div className="detail-item"><span className="detail-label">Weak to</span><span>{formatListValue(item.double_damage_from)}</span></div>
                    <div className="detail-item"><span className="detail-label">Resistant to</span><span>{formatListValue(item.half_damage_from)}</span></div>
                    <div className="detail-item"><span className="detail-label">Immune to</span><span>{formatListValue(item.no_damage_from)}</span></div>
                    <div className="detail-item"><span className="detail-label">Strong against</span><span>{formatListValue(item.double_damage_to)}</span></div>
                    <div className="detail-item"><span className="detail-label">Not very effective against</span><span>{formatListValue(item.half_damage_to)}</span></div>
                    <div className="detail-item"><span className="detail-label">No effect against</span><span>{formatListValue(item.no_damage_to)}</span></div>
                  </div>
                </div>
                <div className="actions">
                  <button onClick={() => updateStatus(item.id, item.status)}>
                    {item.status === 'ready to fight' ? 'Mark defeated' : 'Mark ready'}
                  </button>
                  <button onClick={() => deleteFromDb2(item.id)} className="danger">Delete</button>
                </div>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  )
}
