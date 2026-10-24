// หน้าตารางเวลาของช่าง (UC-04, CR-14) ตามแบบ UI-04-01 รองรับ REQ-FN-066, REQ-FN-067
// ทุกกฎ (ช่วงละ 2 ชั่วโมง เวลาทำงาน ล่วงหน้า 30 วัน ซ้อนกัน วันหยุดที่มีงาน) ตรวจที่หลังบ้าน (BR-10) หน้าจอแสดงข้อความที่ระบบส่งมา
// ปุ่ม "ปิดช่วงนี้" มีเฉพาะช่วงที่ระบบส่ง can_close วันที่มีงานแสดงเลขงาน ไม่มีข้อมูลลูกค้า
import { useEffect, useState } from 'react'


function fmtDay(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('th-TH', { weekday: 'short', day: 'numeric', month: 'short' })
}
function fmtTime(iso) {
  return iso.slice(11, 16)
}

export default function TechnicianSchedule({ api }) {
  const [data, setData] = useState(null)
  const [day, setDay] = useState('')
  const [hour, setHour] = useState('09:00')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const { status, body } = await api.getSchedule()
    if (status !== 200) return setError('โหลดตารางเวลาไม่สำเร็จ')
    setData(body)
    if (!day && body.days.length > 1) setDay(body.days[1].date)
  }

  useEffect(() => { load() }, [])

  async function run(promise, ok) {
    setError(''); setNotice('')
    const { status, body } = await promise
    if (status >= 200 && status < 300) { setNotice(ok(body)); return load() }
    setError(body.message ?? 'เกิดข้อผิดพลาด กรุณาลองใหม่')
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">ตารางเวลาของฉัน</h2>
      {data && (
        <p className="mt-1 text-sm text-slate-600">
          ช่วงละ {data.rules.slot_hours} ชั่วโมง ระหว่าง {data.rules.from} ถึง {data.rules.to} เพิ่มล่วงหน้าได้ไม่เกิน {data.rules.days_ahead} วัน
        </p>
      )}
      <form className="mt-4 flex flex-wrap items-end gap-2" onSubmit={(e) => {
        e.preventDefault()
        run(api.addSlot({ start: `${day}T${hour}:00` }), (b) => `เพิ่มช่วง ${fmtTime(b.start)} ถึง ${fmtTime(b.end)} แล้ว`)
      }}>
        <label className="text-sm text-slate-600">วันที่
          <input type="date" value={day} onChange={(e) => setDay(e.target.value)} className="ml-2 rounded-lg border border-slate-300 px-2 py-1" />
        </label>
        <label className="text-sm text-slate-600">เวลาเริ่ม
          <select value={hour} onChange={(e) => setHour(e.target.value)} className="ml-2 rounded-lg border border-slate-300 px-2 py-1">
            {['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'].map((h) => <option key={h}>{h}</option>)}
          </select>
        </label>
        <button type="submit" disabled={!day} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300">เพิ่มช่วงเวลาว่าง</button>
      </form>
      {notice && <p className="mt-3 rounded-lg border border-teal-300 bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}
      {error && <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <ul className="mt-4 space-y-3">
        {(data?.days ?? []).map((d) => (
          <li key={d.date} className="rounded-lg border border-slate-200 p-3" aria-label={`วันที่ ${d.date}`}>
            <div className="flex items-center justify-between gap-2">
              <p className="font-medium text-slate-800">{fmtDay(d.date)} {d.day_off && <span className="ml-1 rounded-full bg-slate-200 px-2 text-xs">วันหยุด</span>}</p>
              {d.day_off
                ? <button type="button" onClick={() => run(api.removeDayOff({ day: d.date }), (b) => `ยกเลิกวันหยุดแล้ว เปิดช่วงเวลาคืน ${b.reopened_slots} ช่วง`)}
                    className="text-sm text-teal-800 underline">ยกเลิกวันหยุด</button>
                : <button type="button" onClick={() => run(api.addDayOff({ day: d.date }), (b) => `ประกาศวันหยุดแล้ว ปิดช่วงเวลาว่าง ${b.closed_slots} ช่วง`)}
                    className="text-sm text-teal-800 underline">ประกาศวันหยุด</button>}
            </div>
            {d.slots.length === 0 && <p className="mt-1 text-sm text-slate-500">ยังไม่มีช่วงเวลา</p>}
            <div className="mt-2 flex flex-wrap gap-2">
              {d.slots.map((s) => (
                <span key={s.slot_id} data-testid={`slot-${s.slot_id}`}
                  className={`rounded-md border px-2 py-1 text-sm ${s.state === 'free' ? 'border-teal-600 text-teal-800' : 'border-slate-300 text-slate-500'}`}>
                  {fmtTime(s.start)} {s.state_th}{s.job_id ? ` งาน #${s.job_id}` : ''}
                  {s.can_close && (
                    <button type="button" onClick={() => run(api.closeSlot({ slotId: s.slot_id }), () => `ปิดช่วง ${fmtTime(s.start)} แล้ว`)}
                      className="ml-2 text-xs text-red-700 underline">ปิดช่วงนี้</button>
                  )}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
