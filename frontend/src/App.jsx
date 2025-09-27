import React, {useState} from 'react'
import axios from 'axios'
import TextUploader from './components/TextUploader'
import SummaryOptions from './components/SummaryOptions'
import ResultPanel from './components/ResultPanel'

export default function App(){
  const [text, setText] = useState('')
  const [summary, setSummary] = useState(null)
  const [method, setMethod] = useState('abstractive')

  const handleSummarize = async (params={}) =>{
    const res = await axios.post('/api/summarize', {text, method, params})
    setSummary(res.data)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Résumé & QA — Prototype</h1>
      <TextUploader value={text} onChange={setText} />
      <SummaryOptions method={method} setMethod={setMethod} onSummarize={handleSummarize} />
      <ResultPanel result={summary} />
    </div>
  )
}
