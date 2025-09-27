import React from 'react'

export default function TextUploader({value, onChange}){
  return (
    <div className="mb-4">
      <textarea className="w-full p-3 border rounded" rows={8} value={value} onChange={e=>onChange(e.target.value)} />
    </div>
  )
}
