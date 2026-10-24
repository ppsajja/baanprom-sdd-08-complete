// หน้าเข้าสู่ระบบ (CR-11) ตามแบบ UI-02-01 (ลูกค้า UC-02) และ UI-01-01 (ช่าง UC-01) รองรับ REQ-FN-059, REQ-FN-060, REQ-SEC-013
// ข้อความผิดพลาดทุกข้อมาจากระบบ (message) หน้าจอไม่แต่งเอง เวลาหมดอายุของรหัสมาจากระบบ (expires_at)
// ลูกค้าใหม่ที่ยืนยันรหัสแล้ว ไปหน้าลงทะเบียน (UI-02-02) ช่างไม่มีทางลงทะเบียนเอง (บัญชีออกโดยบ้านพร้อม)
import { useState } from 'react'

function hhmm(iso) {
  return new Date(iso).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })
}

const TITLES = { customer: 'เข้าสู่ระบบด้วยเบอร์โทร', technician: 'เข้าสู่ระบบสำหรับช่าง' }

export default function Login({ api, role = 'customer', onLoggedIn, onNeedsRegistration }) {
  const [phone, setPhone] = useState('')
  const [challenge, setChallenge] = useState(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function askCode(e) {
    e?.preventDefault()
    setError('')
    setBusy(true)
    const { status, body } = await api.requestOtp({ phone, role })
    setBusy(false)
    if (status === 202) { setChallenge(body); setCode(''); return }
    setError(body.message ?? 'เกิดข้อผิดพลาด กรุณาลองใหม่')
  }

  async function submit(e) {
    e?.preventDefault()
    setError('')
    setBusy(true)
    const { status, body } = await api.verifyOtp({ challengeId: challenge.challenge_id, code })
    setBusy(false)
    if (status === 200 && body.needs_registration) return onNeedsRegistration?.({ challengeId: body.challenge_id, phone })
    if (status === 200) return onLoggedIn(body)
    setError(body.message ?? 'เกิดข้อผิดพลาด กรุณาลองใหม่')
    if (status === 410) setChallenge(null)  // หมดอายุ ลองผิดครบ หรือใช้แล้ว ต้องขอรหัสใหม่
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">{TITLES[role]}</h2>
      {role === 'technician' && <p className="mt-1 text-sm text-slate-600">ใช้เบอร์ที่ลงทะเบียนกับบ้านพร้อม ถ้ายังไม่มีบัญชี ติดต่อหัวหน้าช่าง</p>}
      {!challenge && (
        <form onSubmit={askCode} className="mt-4 space-y-3">
          <label className="block text-sm text-slate-600">
            เบอร์โทรศัพท์
            <input value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="tel" autoComplete="tel"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900" />
          </label>
          <button type="submit" disabled={busy || !phone.trim()}
            className="w-full rounded-lg bg-teal-700 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-800 disabled:bg-slate-300">
            ขอรหัส OTP
          </button>
        </form>
      )}
      {challenge && (
        <form onSubmit={submit} className="mt-4 space-y-3">
          <p className="text-sm text-slate-700">ส่งรหัส 6 หลักไปที่ {phone} แล้ว รหัสใช้ได้ถึง {hhmm(challenge.expires_at)} น.</p>
          {challenge.dev_code && <p className="text-xs text-slate-400" data-testid="dev-code">โหมดทดสอบ ระบบส่งข้อความเป็นของจำลอง รหัสคือ {challenge.dev_code}</p>}
          <label className="block text-sm text-slate-600">
            รหัส OTP
            <input value={code} onChange={(e) => setCode(e.target.value)} inputMode="numeric" autoComplete="one-time-code" maxLength={6}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 tracking-widest text-slate-900" />
          </label>
          <button type="submit" disabled={busy || code.length !== 6}
            className="w-full rounded-lg bg-teal-700 px-4 py-3 text-sm font-semibold text-white hover:bg-teal-800 disabled:bg-slate-300">
            เข้าสู่ระบบ
          </button>
          <button type="button" onClick={askCode} className="w-full text-sm text-teal-800 underline">ขอรหัสใหม่</button>
        </form>
      )}
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    </section>
  )
}
