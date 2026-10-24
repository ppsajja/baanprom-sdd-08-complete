// เครื่องมือของ call center (CR-18) ตามแบบ UI-14-02 รองรับ REQ-AI-022, REQ-FN-075, REQ-SEC-015 ปิด GAP-31 GAP-32
// หัวหน้า call center ปิดหรือเปิดผู้ช่วยเองด้วยกุญแจของ call center และเลื่อนนัดกลับเมื่อผู้ช่วยเลื่อนผิด (ไม่นับครั้งของ BR-06)
import { useEffect, useState } from 'react'
import { statusTh, fmtDateTime } from '../statusNames.js'

export default function CallCenterTools({ api }) {
  const [assistant, setAssistant] = useState(null)
  const [tickets, setTickets] = useState([])
  const [jobId, setJobId] = useState('')
  const [job, setJob] = useState(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const st = await api.assistantStatus()
    if (st.status === 200) setAssistant(st.body)
    const t = await api.tickets()
    if (t.status === 200) setTickets(t.body)
    if (t.status === 403) setError('กุญแจของ call center ไม่ถูกต้อง')
  }

  useEffect(() => { load() }, [])

  async function toggle() {
    setError(''); setNotice('')
    const { status, body } = await api.switchAssistant({ enabled: !assistant.enabled })
    if (status !== 200) return setError(body.detail ?? 'สั่งไม่สำเร็จ')
    setNotice(body.enabled ? 'เปิดผู้ช่วยแล้ว' : 'ปิดผู้ช่วยแล้ว ลูกค้าเห็นข้อความปิดชั่วคราวและเลขโทร')
    load()
  }

  async function find(e) {
    e.preventDefault()
    setError(''); setNotice(''); setJob(null)
    const { status, body } = await api.getJob({ jobId })
    if (status !== 200) return setError(body.detail ?? 'ไม่พบงาน')
    setJob(body)
  }

  async function revert() {
    setError(''); setNotice('')
    const { status, body } = await api.revertReschedule({ jobId: job.job_id })
    if (status !== 200) return setError(body.message ?? 'เลื่อนกลับไม่สำเร็จ')
    setNotice(`เลื่อนนัดกลับเป็น ${fmtDateTime(body.scheduled_start)} แล้ว ระบบแจ้งลูกค้าและช่างภายใน 60 วินาที`)
    setJob({ ...job, scheduled_start: body.scheduled_start })
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">เครื่องมือ call center</h2>
      {assistant && (
        <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-200 p-3">
          <p className="text-sm text-slate-800">ผู้ช่วยตอนนี้ <b data-testid="assistant-state">{assistant.enabled ? 'เปิด' : 'ปิด'}</b> | ตั๋วรอเจ้าหน้าที่ {tickets.filter((t) => t.status === 'open').length} ใบ</p>
          <button type="button" onClick={toggle} className={`rounded-lg px-4 py-2 text-sm font-semibold text-white ${assistant.enabled ? 'bg-red-600' : 'bg-teal-700'}`}>
            {assistant.enabled ? 'ปิดผู้ช่วยทันที' : 'เปิดผู้ช่วย'}
          </button>
        </div>
      )}
      <form onSubmit={find} className="mt-4 flex gap-2">
        <label className="text-sm text-slate-600">เลขงาน
          <input value={jobId} onChange={(e) => setJobId(e.target.value)} className="ml-2 w-24 rounded-lg border border-slate-300 px-2 py-1" />
        </label>
        <button type="submit" disabled={!jobId} className="rounded-lg border border-teal-700 px-3 py-1 text-sm text-teal-800">เปิดงาน</button>
      </form>
      {job && (
        <div className="mt-3 rounded-lg border border-slate-200 p-3 text-sm">
          <p>งาน #{job.job_id} {statusTh(job.status)} นัด {fmtDateTime(job.scheduled_start)}</p>
          <button type="button" onClick={revert} className="mt-2 rounded-lg border border-red-600 px-3 py-1 text-red-700">เลื่อนนัดกลับเวลาเดิม</button>
          <p className="mt-1 text-xs text-slate-500">ใช้เมื่อผู้ช่วยหรือลูกค้าเลื่อนนัดผิด ไม่นับเป็นครั้งของการเลื่อนนัด</p>
        </div>
      )}
      {notice && <p className="mt-3 rounded-lg border border-teal-300 bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    </section>
  )
}
