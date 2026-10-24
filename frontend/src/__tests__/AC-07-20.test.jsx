// test หน้าจอของ AC-07-20 ถึง AC-07-22 และ AC-07-24 (CR-08, UI-07-01 รายการ "ต้องตรง" ที่เพิ่ม) และ Q-29 เลือกที่อยู่
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TechnicianPicker from '../pages/TechnicianPicker.jsx'

function makeApi(over = {}) {
  return {
    getTechnicians: vi.fn().mockResolvedValue({ status: 200, body: [] }),
    holdSlot: vi.fn().mockResolvedValue({ status: 200, body: { slot_id: 5, hold_expires_at: '2026-10-11T10:10:00' } }),
    getDepositQuote: vi.fn().mockResolvedValue({ status: 200, body: { deposit_amount: 350, estimate_amount: 700, estimate_note: 'x' } }),
    getPastTechnicians: vi.fn().mockResolvedValue({ status: 200, body: [{ technician_id: 1, name: 'ประสิทธิ์', last_job_id: 3 }] }),
    getPastTechnicianSlots: vi.fn().mockResolvedValue({ status: 200, body: { technician_id: 1, name: 'ประสิทธิ์', available: true, slots: [{ slot_id: 5, start: '2026-10-12T14:00:00', end: '2026-10-12T16:00:00' }] } }),
    getContact: vi.fn().mockResolvedValue({ status: 200, body: { call_center_tel: '02-000-0000' } }),
    ...over,
  }
}

test('AC-07-20 ลูกค้าเห็นช่างที่เคยใช้ เลือกแล้วเห็นช่วงว่างของช่างคนนั้น และจองตามขั้นตอนเดิม', async () => {
  const api = makeApi()
  const onHeld = vi.fn()
  render(<TechnicianPicker api={api} customerId={1} addressId={1} onHeld={onHeld} />)
  fireEvent.click(await screen.findByRole('button', { name: 'จองช่าง ประสิทธิ์ อีกครั้ง' }))
  expect(await screen.findByText('ช่าง ประสิทธิ์')).toBeInTheDocument()
  expect(api.getPastTechnicianSlots).toHaveBeenCalledWith({ technicianId: 1, category: 'ประปา', addressId: 1 })
  fireEvent.click(screen.getAllByRole('button').find((b) => /14:00/.test(b.textContent)))
  await waitFor(() => expect(onHeld).toHaveBeenCalled())
  expect(api.holdSlot).toHaveBeenCalledWith({ slotId: 5, customerId: 1 })
})

test('AC-07-21 ช่างคนเดิมไม่ว่าง แสดงข้อความของระบบ ไม่มีปุ่มคิวรอ', async () => {
  const message = 'ช่าง ประสิทธิ์ ยังไม่มีช่วงเวลาว่างใน 7 วันข้างหน้า กรุณาค้นหาช่างคนอื่น'
  const api = makeApi({ getPastTechnicianSlots: vi.fn().mockResolvedValue({ status: 200, body: { available: false, reason: 'no_slots', message, slots: [] } }) })
  render(<TechnicianPicker api={api} customerId={1} addressId={1} onHeld={() => {}} />)
  fireEvent.click(await screen.findByRole('button', { name: 'จองช่าง ประสิทธิ์ อีกครั้ง' }))
  await waitFor(() => expect(screen.getByTestId('past-note')).toHaveTextContent(message))
  expect(screen.queryByText(/คิวรอ|waitlist/)).toBeNull()
})

test('AC-07-24 ไม่มีช่างว่างใน 7 วัน บอกเลขโทร call center ที่ระบบส่งมา', async () => {
  const api = makeApi()
  render(<TechnicianPicker api={api} customerId={1} addressId={1} onHeld={() => {}} />)
  fireEvent.click(screen.getByRole('button', { name: 'ค้นหาช่างที่ว่างใน 7 วัน' }))
  await waitFor(() => expect(screen.getByTestId('a1-contact')).toHaveTextContent('ให้เจ้าหน้าที่ช่วยหาช่าง โทร 02-000-0000'))
  expect(screen.getByText('ยังไม่มีช่างว่างใน 7 วันข้างหน้า')).toBeInTheDocument()
})

test('AC-02-10 ลูกค้าที่มีหลายที่อยู่ เลือกที่อยู่ก่อนค้นหา ระบบค้นด้วยที่อยู่ที่เลือก', async () => {
  const api = makeApi({ getPastTechnicians: undefined })
  const addresses = [{ address_id: 1, text: 'บ้าน' }, { address_id: 4, text: 'คอนโด' }]
  render(<TechnicianPicker api={api} customerId={1} addresses={addresses} onHeld={() => {}} />)
  fireEvent.change(screen.getByLabelText('ที่อยู่ให้บริการ'), { target: { value: '4' } })
  fireEvent.click(screen.getByRole('button', { name: 'ค้นหาช่างที่ว่างใน 7 วัน' }))
  await waitFor(() => expect(api.getTechnicians).toHaveBeenCalledWith({ category: 'ประปา', addressId: 4, customerId: 1 }))
})
