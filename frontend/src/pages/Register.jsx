// หน้าลงทะเบียนลูกค้าใหม่ (UC-02, CR-11) ตามแบบ UI-02-02 รองรับ REQ-FN-058, REQ-PRV-011
// ตำแหน่งที่อยู่: บริการแผนที่ (IF-03) ยังเป็นของจำลอง หน้าจอส่งพิกัดกลางพื้นที่ให้บริการไปก่อน (GAP-40) ห้ามเดาพิกัดเอง
import { useState } from 'react'

// พิกัดกลางพื้นที่ให้บริการทดสอบ (ค่าเดียวกับ uat_seed.py) ใช้จนกว่าแผนที่จริง (IF-03) มาแทน
export const DEFAULT_PIN = { lat: 13.74, lng: 100.53 }

export default function Register({ api, challengeId, phone, onRegistered, onBack }) {
  const [name, setName] = useState('')
  const [addressText, setAddressText] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e?.preventDefault()
    setError('')
    setBusy(true)
    const { status, body } = await api.register({ challengeId, name, addressText, ...DEFAULT_PIN })
    setBusy(false)
    if (status === 201) return onRegistered(body)
    setError(body.message ?? 'กรุณากรอกชื่อและที่อยู่ให้ครบ')
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">ลงทะเบียนลูกค้าใหม่</h2>
      <p className="mt-1 text-sm text-slate-600">ยืนยันเบอร์ {phone} แล้ว กรอกชื่อและที่อยู่ที่ต้องการให้ช่างไป</p>
      <form onSubmit={submit} className="mt-4 space-y-3">
        <label className="block text-sm text-slate-600">
          ชื่อ
          <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900" />
        </label>
        <label className="block text-sm text-slate-600">
          ที่อยู่ให้บริการ
          <textarea value={addressText} onChange={(e) => setAddressText(e.target.value)} rows={2}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900" />
        </label>
        <p className="text-xs text-slate-500">พิกัดใช้คำนวณระยะทางถึงช่างเท่านั้น ไม่แสดงให้ใครเห็น</p>
        <button type="submit" disabled={busy || !name.trim() || !addressText.trim()}
          className="w-full rounded-lg bg-teal-700 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-800 disabled:bg-slate-300">
          ลงทะเบียนและเข้าสู่ระบบ
        </button>
        <button type="button" onClick={onBack} className="w-full text-sm text-teal-800 underline">กลับ</button>
      </form>
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    </section>
  )
}
