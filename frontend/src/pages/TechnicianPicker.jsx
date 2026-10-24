// CR-15 (UC-11 REQ-FN-069): คะแนนเฉลี่ยมาจากระบบ แสดงประกอบเท่านั้น ลำดับช่างตามที่ระบบส่งมา (ไม่เรียงตามคะแนน)
// หน้าเลือกช่าง (UC-07 ขั้น 1 ถึง 3) รองรับ REQ-FN-008 และ REQ-FN-041 ตามแบบ UI-07-01 (CR-03)
// ที่อยู่ให้บริการ: ยังรอ Q-29 จึงใช้ที่อยู่หลักที่ส่งเข้ามา (addressId) และยังไม่แสดงบนหน้าจอ
// CR-11 (Q-29 ปิดใน EV-051): ลูกค้าที่มีหลายที่อยู่เลือกที่อยู่บนหน้านี้ (รายการ addresses มาจาก GET /me) ไม่ส่ง addresses มา = ใช้ addressId
// CR-08 (REQ-FN-064, BR-08): ส่วน "ช่างที่เคยใช้" ช่วงเวลาและข้อความเมื่อจองไม่ได้มาจากระบบ ไม่มีปุ่มคิวรอ (Q-33 Won't)
// CR-08 (REQ-FN-065, Q-28): ไม่มีช่างว่างใน 7 วัน บอกเลขโทร call center ที่ได้จากระบบ (GET /contact)
import { useEffect, useState } from 'react'
import Steps from '../components/Steps.jsx'

const CATEGORIES = ['ประปา', 'ไฟฟ้า', 'แอร์']

function fmt(iso) {
  const d = new Date(iso)
  return d.toLocaleString('th-TH', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function TechnicianPicker({ api, customerId, addressId: defaultAddressId, addresses, onHeld }) {
  const [category, setCategory] = useState('ประปา')
  const [addressId, setAddressId] = useState(addresses?.[0]?.address_id ?? defaultAddressId)
  const [technicians, setTechnicians] = useState(null)
  const [error, setError] = useState('')
  const [past, setPast] = useState([])
  const [pastNote, setPastNote] = useState('')
  const [tel, setTel] = useState('')

  useEffect(() => {
    if (!api.getPastTechnicians) return
    api.getPastTechnicians().then(({ status, body }) => { if (status === 200) setPast(body) })
  }, [api])

  async function search() {
    setError('')
    setPastNote('')
    const { status, body } = await api.getTechnicians({ category, addressId, customerId })
    if (status !== 200) return setError('ค้นหาไม่สำเร็จ')
    setTechnicians(body)
    if (body.length === 0 && api.getContact) {
      const c = await api.getContact()
      if (c.status === 200) setTel(c.body.call_center_tel)
    }
  }

  async function pickPast(t) {
    // CR-08: กฎเดิมทุกข้อใช้กับช่างคนเดิม (ทักษะ ระยะ 15 กม. ช่วงว่างใน 7 วัน) ระบบตัดสิน หน้าจอแสดงผล
    setError('')
    const { status, body } = await api.getPastTechnicianSlots({ technicianId: t.technician_id, category, addressId })
    if (status !== 200) return setError('ค้นหาไม่สำเร็จ')
    if (!body.available) { setTechnicians(null); return setPastNote(body.message) }
    setPastNote('')
    setTechnicians([{ technician_id: body.technician_id, name: body.name, slots: body.slots }])
  }

  async function pick(tech, slot) {
    // REQ-FN-041: เลือกช่วงเวลาแล้วล็อกทันที ถ้าคนอื่นล็อกไปก่อน (BR-02) ให้แจ้งและเลือกใหม่
    const hold = await api.holdSlot({ slotId: slot.slot_id, customerId })
    // CR-07 REQ-SEC-011 (AC-07-14): ถือล็อกช่วงอื่นอยู่ ระบบตอบ 409 hold_limit แสดงข้อความที่ระบบส่งมา
    if (hold.status === 409 && hold.body.reason === 'hold_limit') return setError(hold.body.message)
    if (hold.status === 409) return setError('ช่วงเวลานี้เพิ่งถูกจองไป')
    // REQ-BR-002: ขอยอดมัดจำจากระบบ ไม่คำนวณหรือพิมพ์ยอดเองในหน้าจอ (D-00-05)
    const quote = await api.getDepositQuote({ category })
    if (quote.status !== 200) return setError('ยังแสดงยอดมัดจำไม่ได้ กรุณาลองใหม่')
    // CR-10 REQ-FN-057 (Q-26): ราคาประเมินและข้อความกำกับมาจากคำตอบเดียวกัน
    onHeld({ slot, technician: tech, category, addressId, holdExpiresAt: hold.body.hold_expires_at, depositAmount: quote.body.deposit_amount,
      estimateAmount: quote.body.estimate_amount, estimateNote: quote.body.estimate_note })
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <Steps current={1} />
      <h2 className="text-lg font-semibold text-slate-800">เลือกประเภทงานและช่างที่ว่าง</h2>
      <p className="mt-3 text-sm text-slate-500">ประเภทงาน</p>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        {CATEGORIES.map((c) => (
          <button key={c} type="button" onClick={() => setCategory(c)} aria-pressed={category === c}
            className={`rounded-full border px-4 py-1 text-sm ${category === c ? 'border-teal-700 bg-teal-700 text-white' : 'border-slate-300 bg-white text-slate-700'}`}>
            {c}
          </button>
        ))}
      </div>
      {addresses && addresses.length > 0 && (
        <label className="mt-3 block text-sm text-slate-500">
          ที่อยู่ให้บริการ
          <select value={addressId} onChange={(e) => { setAddressId(Number(e.target.value)); setTechnicians(null) }}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900">
            {addresses.map((a) => <option key={a.address_id} value={a.address_id}>{a.text}</option>)}
          </select>
        </label>
      )}
      {past.length > 0 && (
        <div className="mt-3" aria-label="ช่างที่เคยใช้">
          <p className="text-sm text-slate-500">ช่างที่เคยใช้</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {past.map((t) => (
              <button key={t.technician_id} type="button" onClick={() => pickPast(t)}
                className="rounded-full border border-teal-700 px-4 py-1 text-sm text-teal-800 hover:bg-teal-50">
                จองช่าง {t.name} อีกครั้ง
              </button>
            ))}
          </div>
        </div>
      )}
      {pastNote && <p className="mt-3 rounded-lg border border-orange-300 bg-orange-50 p-3 text-sm text-orange-800" data-testid="past-note">{pastNote}</p>}
      <button type="button" onClick={search} className="mt-4 w-full rounded-lg bg-orange-500 px-4 py-3 text-sm font-semibold text-white hover:bg-orange-600">
        ค้นหาช่างที่ว่างใน 7 วัน
      </button>
      {error && (
        <div role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          <p className="font-semibold">{error}</p>
          {error === 'ช่วงเวลานี้เพิ่งถูกจองไป' && <p>กรุณาเลือกช่วงเวลาใหม่</p>}
        </div>
      )}
      {technicians && technicians.length === 0 && (
        <div className="mt-3 text-sm text-slate-600">
          <p>ยังไม่มีช่างว่างใน 7 วันข้างหน้า</p>
          {tel && <p data-testid="a1-contact">ให้เจ้าหน้าที่ช่วยหาช่าง โทร {tel}</p>}
        </div>
      )}
      <ul className="mt-4 space-y-3">
        {technicians?.map((t) => (
          <li key={t.technician_id} className="rounded-lg border border-slate-200 p-3">
            <p className="font-medium text-slate-800">ช่าง {t.name}</p>
            {t.rating && (
              <p className="text-xs text-slate-600" data-testid={`rating-${t.technician_id}`}>
                {t.rating.average != null ? `คะแนนเฉลี่ย ${t.rating.average.toFixed(1)} จาก 5 (${t.rating.count} คะแนน)` : 'ยังมีคะแนนไม่พอแสดงค่าเฉลี่ย'}
              </p>
            )}
            <div className="mt-2 flex flex-wrap gap-2">
              {t.slots.map((s) => (
                <button key={s.slot_id} type="button" onClick={() => pick(t, s)}
                  className="rounded-md border border-teal-600 px-3 py-1 text-sm text-teal-800 hover:bg-teal-50">
                  {fmt(s.start)}
                </button>
              ))}
            </div>
          </li>
        ))}
      </ul>
      {technicians && technicians.length > 0 && (
        <p className="mt-3 text-sm text-slate-600">แตะช่วงเวลาเพื่อเลือก ระบบจะล็อกช่วงเวลานั้นไว้ให้ระหว่างที่คุณยืนยัน</p>
      )}
    </section>
  )
}
