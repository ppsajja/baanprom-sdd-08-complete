// หน้ากระทบยอดของ Finance (UC-13, CR-16) ตามแบบ UI-13-01 รองรับ REQ-FN-070, REQ-FN-071
// Finance วางหรือเลือกไฟล์รายงานประจำวันของ gateway แล้วกดกระทบยอด ผลและรายการต่างมาจากระบบ ไม่มีข้อมูลส่วนบุคคล
// ระบบไม่ส่งคำขอคืนเงินซ้ำ รายการต่างทุกตัว Finance ปิดเองตามคู่มือเหตุการณ์ที่ 8
import { useState } from 'react'

export default function Reconciliation({ api }) {
  const [date, setDate] = useState('')
  const [csv, setCsv] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function readFile(e) {
    const f = e.target.files?.[0]
    if (f) setCsv(await f.text())
  }

  async function submit(e) {
    e.preventDefault()
    setError(''); setResult(null); setBusy(true)
    const { status, body } = await api.reconcile({ reportDate: date, csv })
    setBusy(false)
    if (status === 200 || status === 201) return setResult(body)
    setError(body.message ?? body.detail ?? 'กระทบยอดไม่สำเร็จ')
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">กระทบยอดกับรายงานของ gateway</h2>
      <form onSubmit={submit} className="mt-4 space-y-3">
        <label className="block text-sm text-slate-600">วันที่ของรายงาน
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="ml-2 rounded-lg border border-slate-300 px-2 py-1" />
        </label>
        <label className="block text-sm text-slate-600">ไฟล์รายงาน (CSV)
          <input type="file" accept=".csv,text/csv" onChange={readFile} className="ml-2 text-sm" />
        </label>
        <label className="block text-sm text-slate-600">หรือวางข้อความของรายงาน
          <textarea value={csv} onChange={(e) => setCsv(e.target.value)} rows={4}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs text-slate-900" />
        </label>
        <button type="submit" disabled={busy || !date || !csv.trim()} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300">กระทบยอด</button>
      </form>
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {result && (
        <div className="mt-4" data-testid="recon-result">
          {result.already_imported && <p className="mb-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">รายงานนี้นำเข้าไปแล้ว แสดงผลเดิม ระบบไม่ทำซ้ำ</p>}
          <p className="text-sm text-slate-800">รายการในรายงาน {result.rows_in_report} | ตรงกัน {result.matched} | รายการต่าง {result.differences}</p>
          {result.items.length > 0 && (
            <table className="mt-3 w-full text-left text-sm">
              <thead><tr className="text-slate-500"><th>รายการต่าง</th><th>งาน</th><th>ชนิด</th><th>ในระบบ</th><th>ในรายงาน</th></tr></thead>
              <tbody>
                {result.items.map((i) => (
                  <tr key={`${i.kind}-${i.type}-${i.reference}`} className="border-t border-slate-100">
                    <td>{i.kind_th}</td><td>{i.job_id ? `#${i.job_id}` : '-'}</td><td>{i.type === 'capture' ? 'ตัดมัดจำ' : 'คืนเงิน'}</td>
                    <td>{i.system_amount ?? '-'} {i.system_status ?? ''}</td><td>{i.report_amount ?? '-'} {i.report_status ?? ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  )
}
