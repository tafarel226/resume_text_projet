import React from 'react'

export default function ResultPanel({result}){
  if(!result) return null
  return (
    <div className="mt-4 p-4 border rounded">
      <h2 className="font-semibold">Résumé</h2>
      <p className="mt-2">{result.summary}</p>
    </div>
  )
}
