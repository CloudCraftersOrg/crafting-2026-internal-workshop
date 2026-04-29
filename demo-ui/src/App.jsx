import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

// Example queries for quick testing
const EXAMPLE_QUERIES = [
  {
    tier: "Tier 1 - Basic",
    text: "What did Harry use to sneak around Hogwarts at night?"
  },
  {
    tier: "Tier 2 - Intermediate",
    text: "What are all of Voldemort's Horcruxes, in which book is each one discovered, and how was each destroyed?"
  },
  {
    tier: "Tier 3 - Complex",
    text: "Compare the evolution of Snape and Draco Malfoy throughout the saga. At what key moments do their paths diverge from Voldemort's?"
  },
  {
    tier: "Tier 4 - Structured",
    text: "Show me all Slytherin characters from the structured data and their allegiances"
  }
]

function App() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!query.trim()) {
      setError('Please enter a query')
      return
    }

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: query }),
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Failed to query agent')
      }

      const data = await res.json()
      setResponse(data.answer)
      setSessionId(data.session_id)
    } catch (err) {
      setError(err.message)
      console.error('Query error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setQuery('')
    setResponse(null)
    setError(null)
    setSessionId(null)
  }

  const handleExampleClick = (exampleText) => {
    setQuery(exampleText)
    setResponse(null)
    setError(null)
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1 className="title">HORROCRUXES</h1>
        <p className="subtitle">Multi-Agent Intelligence System</p>
        <div className="team-badge">🐍 Team Slytherin</div>
      </header>

      {/* Quick Examples */}
      <div className="examples-section">
        <div className="examples-title">⚡ Quick Examples</div>
        <div className="examples-grid">
          {EXAMPLE_QUERIES.map((example, idx) => (
            <div
              key={idx}
              className="example-card"
              onClick={() => handleExampleClick(example.text)}
            >
              <div className="example-tier">{example.tier}</div>
              <div className="example-text">{example.text}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Query Input */}
      <div className="query-section">
        <label className="query-label">Ask CRAFTY</label>
        <form onSubmit={handleSubmit}>
          <textarea
            className="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask any question about the Harry Potter saga..."
            rows={4}
          />
          <div className="button-group">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !query.trim()}
            >
              {loading ? 'Casting Spell...' : 'Ask CRAFTY'}
            </button>
            {(query || response) && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClear}
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {error && (
          <div className="error">
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <div className="loading-text">Consulting the 7 books...</div>
        </div>
      )}

      {/* Response */}
      {response && !loading && (
        <div className="response-section">
          <div className="response-header">
            <div className="response-title">🔮 CRAFTY's Response</div>
            {sessionId && (
              <div className="session-id">Session: {sessionId.slice(0, 8)}</div>
            )}
          </div>
          <div className="response-content">
            <ReactMarkdown>{response}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        <p>HORROCRUXES — Built by Team Slytherin</p>
        <p>CloudCrafters × Business Analysis LATAM Workshop 2026</p>
      </footer>
    </div>
  )
}

export default App
