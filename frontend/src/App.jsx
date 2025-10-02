import React, { useState } from 'react'
import axios from 'axios'
import TextUploader from './components/TextUploader'
import SummaryOptions from './components/SummaryOptions'
import ResultPanel from './components/ResultPanel'

export default function App() {
  const [text, setText] = useState('')
  const [summary, setSummary] = useState(null)
  const [method, setMethod] = useState('abstractive') // par défaut
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSummarize = async (params = {}) => {
    if (!text.trim()) {
      setError("Veuillez entrer un texte avant de résumer")
      return
    }

    try {
      setLoading(true)
      setError(null)
      const res = await axios.post('/api/summarize', {
        text,
        method,   // ici la méthode choisie
        params,
        lang: "fr"
      })
      setSummary(res.data)
    } catch (err) {
      setError("Erreur lors du résumé")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Résumé & QA — Prototype</h1>
      <TextUploader value={text} onChange={setText} />
      <SummaryOptions 
        method={method} 
        setMethod={setMethod} 
        onSummarize={handleSummarize} 
        loading={loading}
        text={text}
      />
      <ResultPanel result={summary} loading={loading} error={error} />
    </div>
  )
}
