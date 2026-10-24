// หน้าที่อยู่ของฉัน (ลูกค้า CR-18) ตามแบบ UI-02-04 รองรับ REQ-FN-058, REQ-FN-074 ปิด F-17
// พิกัดหาจากข้อความที่อยู่ที่หลังบ้าน (IF-03) หน้าจอไม่เห็นพิกัด ปุ่มลบมีเฉพาะที่อยู่ที่ระบบส่ง can_delete
import { useEffect, useState } from 'react'

export default function Addresses({ api, onChanged }) {
  const [rows, setRows] = useState(null)
  const [text, setText] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const { status, body } = await api.list()
    if (status !== 200) return setError('โหลดที่อยู่ไม่สำเร็จ')
    setRows(body)
    onChanged?.(body)
  }

  useEffect(() => { load() }, [])

  async function add(e) {
    e.preventDefault()
    setError(''); setNotice('')
    const { status, body } = await api.add({ text })
    if (status !== 201) return setError(body.message ?? 'เพิ่มที่อยู่ไม่สำเร็จ')
    setText('')
    setNotice(`เพิ่มที่อยู่ ${body.text} แล้ว`)
    load()
  }

  async function remove(a) {
    setError(''); setNotice('')
    const { status, body } = await api.remove({ addressId: a.address_id })
    if (status !== 200) return setError(body.message ?? 'ลบที่อยู่ไม่สำเร็จ')
    setNotice('ลบที่อยู่แล้ว')
    load()
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">ที่อยู่ของฉัน</h2>
      <p className="mt-1 text-sm text-slate-600">ที่อยู่แรกเป็นค่าตั้งต้นตอนค้นหาช่าง เลือกที่อยู่อื่นได้ที่หน้าจองงาน</p>
      <ul className="mt-4 space-y-2">
        {(rows ?? []).map((a, i) => (
          <li key={a.address_id} className="flex items-center justify-between rounded-lg border border-slate-200 p-3">
            <span className="text-sm text-slate-800">{a.text}{i === 0 ? ' (ค่าตั้งต้น)' : ''}</span>
            {a.can_delete && <button type="button" onClick={() => remove(a)} className="text-sm text-red-700 underline">ลบ</button>}
          </li>
        ))}
      </ul>
      <form onSubmit={add} className="mt-4 space-y-2">
        <label className="block text-sm text-slate-600">
          ที่อยู่ใหม่
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900" />
        </label>
        <p className="text-xs text-slate-500">ใส่ชื่อเขตหรืออำเภอด้วย ระบบใช้หาตำแหน่งบนแผนที่ พิกัดไม่แสดงให้ใครเห็น</p>
        <button type="submit" disabled={!text.trim()} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300">เพิ่มที่อยู่</button>
      </form>
      {notice && <p className="mt-3 rounded-lg border border-teal-300 bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    </section>
  )
}
