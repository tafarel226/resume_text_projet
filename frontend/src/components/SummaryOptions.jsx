import React from 'react'

export default function SummaryOptions({method, setMethod, onSummarize}){
  return (
    <div className="mb-4 flex items-center gap-4">
      <select value={method} onChange={e=>setMethod(e.target.value)} className="p-2 border rounded">
        <option value="abstractive">Abstractive</option>
        <option value="extractive">Extractive</option>
      </select>
      <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={()=>onSummarize({})}>Résumer</button>
    </div>
  )
}
