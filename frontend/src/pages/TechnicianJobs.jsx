// หน้างานของช่าง (UC-09) ตามแบบ UI-09-01 (CR-05) รองรับ REQ-FN-050, REQ-FN-051, REQ-SEC-004
// ปุ่มเปลี่ยนสถานะมีเฉพาะที่ระบบส่งมาใน next_statuses (ตาราง MD-STM-01 อยู่หลังบ้านที่เดียว D-00-05)
// เบอร์โทรลูกค้าแสดงเฉพาะเมื่อระบบส่ง customer_phone มา หน้าจอไม่คำนวณเวลาเอง (REQ-SEC-004)
// กล่อง "รอ Q-30" (ย้อนสถานะ) และ "รอ Q-32" (ซ่อนงานที่ปิดแล้ว) ใน mockup ไม่สร้าง
// CR-12 (UC-12, REQ-FN-061): ปุ่ม "รับงาน" "ปฏิเสธงาน" มีเฉพาะที่ระบบส่งมาใน responses เวลาที่ต้องตอบมาจาก assignment.respond_by
// ปฏิเสธแล้วงานออกจากรายการ (ระบบหาช่างใหม่ให้ลูกค้า UC-05) CR-11: ช่างมาจาก token ของการเข้าสู่ระบบ (UC-01)
import { useEffect, useState } from 'react'
import { statusTh, fmtDateTime } from '../statusNames.js'

function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })
}

export default function TechnicianJobs({ api, technicianId }) {
  const [jobs, setJobs] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(null)

  async function load() {
    const { status, body } = await api.getTechnicianJobs({ technicianId })
    if (status !== 200) return setError('โหลดรายการงานไม่สำเร็จ')
    setJobs(body)
  }

  useEffect(() => { load() }, [technicianId])

  async function respond(job, action) {
    setError('')
    setBusy(job.job_id)
    const call = action === 'accept' ? api.acceptJob : api.rejectJob
    const { status, body } = await call({ jobId: job.job_id })
    setBusy(null)
    if (status === 200 && action === 'reject') return setJobs((list) => list.filter((j) => j.job_id !== job.job_id))
    if (status === 200) return setJobs((list) => list.map((j) => (j.job_id === body.job_id ? body : j)))
    setError(body.message ?? 'เกิดข้อผิดพลาด กรุณาลองใหม่')
  }

  async function change(job, toStatus) {
    setError('')
    setBusy(job.job_id)
    const { status, body } = await api.updateJobStatus({ jobId: job.job_id, technicianId, toStatus })
    setBusy(null)
    if (status === 200) return setJobs((list) => list.map((j) => (j.job_id === body.job_id ? body : j)))
    if (status === 409) return setError('เปลี่ยนสถานะนี้ไม่ได้')
    setError('เกิดข้อผิดพลาด กรุณาลองใหม่')
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">งานของฉัน</h2>
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {jobs && jobs.length === 0 && <p className="mt-3 text-sm text-slate-600">ยังไม่มีงานที่มอบหมายให้คุณ</p>}
      <ul className="mt-4 space-y-3">
        {(jobs ?? []).map((job) => (
          <li key={job.job_id} className="rounded-lg border border-slate-200 p-4" aria-label={`งาน #${job.job_id}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-slate-900">งาน #{job.job_id} <span className="font-normal text-slate-600">{job.category}</span></p>
                <p className="text-sm text-slate-600">นัดหมาย {fmtDateTime(job.scheduled_start)}</p>
                <p className="text-sm text-slate-600">ลูกค้า {job.customer_name}</p>
                <p className="text-sm text-slate-600">
                  {job.customer_phone ? <>โทร {job.customer_phone}</> : <span className="text-slate-400">เบอร์โทรจะแสดง 2 ชั่วโมงก่อนนัด</span>}
                </p>
              </div>
              <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800" data-testid={`status-${job.job_id}`}>
                {statusTh(job.status)}
              </span>
            </div>
            {job.assignment?.response === 'pending' && (
              <p className="mt-2 text-sm font-medium text-orange-700" data-testid={`respond-by-${job.job_id}`}>
                {job.assignment.via_rematch ? 'งานแทนช่างคนเดิม ' : ''}กรุณารับหรือปฏิเสธภายใน {fmtTime(job.assignment.respond_by)} น.
              </p>
            )}
            {(job.responses ?? []).length > 0 && (
              <div className="mt-3 flex gap-2">
                {job.responses.map((r) => (
                  <button key={r.action} type="button" disabled={busy === job.job_id} onClick={() => respond(job, r.action)}
                    className={r.action === 'accept'
                      ? 'rounded-lg bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600 disabled:bg-slate-300'
                      : 'rounded-lg border border-slate-400 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:text-slate-300'}>
                    {r.label}
                  </button>
                ))}
              </div>
            )}
            {job.next_statuses.length > 0 && (
              <div className="mt-3 flex gap-2">
                {job.next_statuses.map((n) => (
                  <button key={n.status} type="button" disabled={busy === job.job_id} onClick={() => change(job, n.status)}
                    className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:bg-slate-300">
                    {n.label}
                  </button>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
