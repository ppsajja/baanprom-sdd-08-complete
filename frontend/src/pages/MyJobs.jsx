// หน้างานของฉัน (ลูกค้า) ตามแบบ UI-02-03 (CR-11, CR-12) รองรับ REQ-FN-052, REQ-FN-063, REQ-SEC-010
// เห็นเฉพาะงานของตัวเอง (GET /me/jobs) สถานะเป็นคำไทยตาม glossary งานที่ได้ช่างแทน (UC-05) มีปุ่ม "ไม่รับช่างแทน"
// ยอดคืนมาจากระบบ (BR-01 R4) หน้าจอไม่คำนวณเอง
import { useEffect, useState } from 'react'
import { statusTh, fmtDateTime } from '../statusNames.js'

export default function MyJobs({ api }) {
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
