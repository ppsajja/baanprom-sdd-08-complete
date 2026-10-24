// หน้างานของฉัน (ลูกค้า) ตามแบบ UI-02-03 (CR-11, CR-12) รองรับ REQ-FN-052, REQ-FN-063, REQ-SEC-010
// เห็นเฉพาะงานของตัวเอง (GET /me/jobs) สถานะเป็นคำไทยตาม glossary งานที่ได้ช่างแทน (UC-05) มีปุ่ม "ไม่รับช่างแทน"
// ยอดคืนมาจากระบบ (BR-01 R4) หน้าจอไม่คำนวณเอง
// CR-15 (UC-11 UI-11-01): งานที่ระบบส่ง can_rate มีส่วน "ให้คะแนนช่าง" 1 ถึง 5 ดาวและความเห็นสั้น กฎทั้งหมดอยู่หลังบ้าน (BR-11)
import { useEffect, useState } from 'react'
import { statusTh, fmtDateTime } from '../statusNames.js'

function RateForm({ job, ratingApi, onDone }) {
  const [stars, setStars] = useState(0)
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')

  async function send() {
    setError('')
    const { status, body } = await ratingApi.rate({ jobId: job.job_id, stars, comment })
    if (status !== 201) return setError(body.message ?? 'ส่งคะแนนไม่สำเร็จ')
    onDone(body.message)
  }

  return (
    <div className="mt-3 rounded-lg bg-slate-50 p-3" aria-label={`ให้คะแนนงาน #${job.job_id}`}>
      <p className="text-sm text-slate-700">ให้คะแนนช่าง {job.technician_name}</p>
      <div className="mt-1 flex gap-1" role="group" aria-label="จำนวนดาว">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" onClick={() => setStars(n)} aria-pressed={stars === n}
            className={`rounded-md border px-3 py-1 text-sm ${stars >= n ? 'border-amber-500 bg-amber-100 text-amber-900' : 'border-slate-300 text-slate-600'}`}>
            {n} ดาว
          </button>
        ))}
      </div>
      <label className="mt-2 block text-sm text-slate-600">ความเห็น (ไม่บังคับ ไม่เกิน 300 ตัวอักษร)
        <textarea value={comment} maxLength={300} onChange={(e) => setComment(e.target.value)} rows={2}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900" />
      </label>
      <p className="text-xs text-slate-500">ความเห็นไม่แสดงต่อลูกค้าคนอื่นและไม่แสดงชื่อคุณ ลูกค้าคนอื่นเห็นเฉพาะคะแนนเฉลี่ย</p>
      <button type="button" disabled={!stars} onClick={send}
        className="mt-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300">ส่งคะแนน</button>
      {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  )
}

export default function MyJobs({ api, ratingApi }) {
  const [jobs, setJobs] = useState(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const { status, body } = await api.myJobs()
    if (status !== 200) return setError('โหลดงานไม่สำเร็จ')
    setJobs(body)
  }

  useEffect(() => { load() }, [])

  async function decline(job) {
    setError('')
    const { status, body } = await api.declineSubstitute({ jobId: job.job_id })
    if (status !== 200) return setError(body.message ?? 'เกิดข้อผิดพลาด กรุณาลองใหม่')
    setNotice(body.refund_message || `ยกเลิกงาน #${body.job_id} แล้ว คืนมัดจำ ${body.refund_amount} บาท`)
    load()
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">งานของฉัน</h2>
      {notice && <p className="mt-3 rounded-lg border border-teal-300 bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {jobs && jobs.length === 0 && <p className="mt-3 text-sm text-slate-600">ยังไม่มีงาน</p>}
      <ul className="mt-4 space-y-3">
        {(jobs ?? []).map((j) => (
          <li key={j.job_id} className="rounded-lg border border-slate-200 p-4" aria-label={`งาน #${j.job_id}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-slate-900">งาน #{j.job_id} <span className="font-normal text-slate-600">{j.category}</span></p>
                <p className="text-sm text-slate-600">นัดหมาย {fmtDateTime(j.scheduled_start)}</p>
                {j.technician_name && <p className="text-sm text-slate-600">ช่าง {j.technician_name}{j.substitute ? ' (ช่างแทน)' : ''}</p>}
              </div>
              <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800" data-testid={`my-status-${j.job_id}`}>
                {statusTh(j.status)}
              </span>
            </div>
            {j.my_rating != null && <p className="mt-2 text-sm text-slate-600">คุณให้คะแนน {j.my_rating} ดาว</p>}
            {j.can_rate && ratingApi && <RateForm job={j} ratingApi={ratingApi} onDone={(m) => { setNotice(m); load() }} />}
            {j.can_decline_substitute && (
              <div className="mt-3">
                <p className="text-sm text-slate-700">ช่างคนเดิมไม่สะดวก ระบบหาช่างแทนให้ในเวลาเดิม ถ้าไม่ต้องการช่างแทน ยกเลิกได้และได้มัดจำคืนเต็มจำนวน</p>
                <button type="button" onClick={() => decline(j)}
                  className="mt-2 rounded-lg border border-red-600 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50">
                  ไม่รับช่างแทน ขอคืนมัดจำ
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
