// หน้าตั้งค่าการแจ้งเตือน (UC-10, CR-17) ตามแบบ UI-10-01 รองรับ REQ-FN-072 ใช้ได้ทั้งลูกค้าและช่าง
// LINE เลือกได้หลังเชื่อมบัญชี (BR-12) รหัสเชื่อมและคำแนะนำมาจากระบบ OTP ส่ง SMS เสมอ (บอกบนหน้านี้)
import { useEffect, useState } from 'react'

const LABEL = { sms: 'SMS', line: 'LINE' }

export default function NotificationSettings({ api }) {
  const [s, setS] = useState(null)
  const [link, setLink] = useState(null)
  const [error, setError] = useState('')

  async function load() {
    const { status, body } = await api.get()
    if (status !== 200) return setError('โหลดการตั้งค่าไม่สำเร็จ')
    setS(body)
  }

  useEffect(() => { load() }, [])

  async function choose(channel) {
    setError('')
    const { status, body } = await api.setChannel({ channel })
    if (status !== 200) return setError(body.message ?? 'บันทึกไม่สำเร็จ')
    setS(body)
  }

  async function startLink() {
    setError('')
    const { status, body } = await api.startLineLink()
    if (status !== 200) return setError(body.message ?? 'เริ่มเชื่อม LINE ไม่สำเร็จ')
    setLink(body)
  }

  async function unlink() {
    const { body } = await api.unlinkLine()
    setLink(null)
    setS(body)
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">การแจ้งเตือน</h2>
      {s && (
        <>
          <p className="mt-1 text-sm text-slate-600">ตอนนี้รับข้อความทาง <b data-testid="channel">{LABEL[s.channel]}</b></p>
          <fieldset className="mt-4 space-y-2">
            <legend className="text-sm text-slate-600">เลือกช่องทาง</legend>
            {s.channels.map((c) => (
              <label key={c} className="flex items-center gap-2 text-sm text-slate-800">
                <input type="radio" name="channel" checked={s.channel === c} onChange={() => choose(c)} /> {LABEL[c]}
                {c === 'line' && !s.line_linked && <span className="text-xs text-slate-500">(ต้องเชื่อมบัญชีก่อน)</span>}
              </label>
            ))}
          </fieldset>
          <div className="mt-4">
            {s.line_linked
              ? <button type="button" onClick={unlink} className="text-sm text-teal-800 underline">ยกเลิกการเชื่อม LINE</button>
              : <button type="button" onClick={startLink} className="rounded-lg border border-teal-700 px-4 py-2 text-sm text-teal-800">เชื่อมบัญชี LINE</button>}
          </div>
          {link && <p className="mt-3 rounded-lg border border-teal-300 bg-teal-50 p-3 text-sm text-teal-800" data-testid="link-instruction">{link.instruction}</p>}
          <p className="mt-4 text-xs text-slate-500">รหัส OTP สำหรับเข้าสู่ระบบส่งทาง SMS เสมอ ถ้าส่งทาง LINE ไม่สำเร็จ ระบบส่ง SMS แทน</p>
        </>
      )}
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    </section>
  )
}
