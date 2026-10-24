// ตรวจรายการ "ต้องตรง" ของ UI-04-01 ตารางเวลาของช่าง (specs/008-schedule spec ส่วน 12) และ AC-04-01 AC-04-06 ฝั่งหน้าจอ
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TechnicianSchedule from '../pages/TechnicianSchedule.jsx'

const schedule = {
  technician_id: 1,
  rules: { slot_hours: 2, from: '08:00', to: '20:00', days_ahead: 30 },
  days: [
    { date: '2026-10-04', day_off: false, slots: [] },
    { date: '2026-10-05', day_off: false, slots: [
      { slot_id: 1, start: '2026-10-05T14:00:00', end: '2026-10-05T16:00:00', state: 'booked', state_th: 'จองแล้ว', job_id: 7, can_close: false },
      { slot_id: 2, start: '2026-10-05T16:00:00', end: '2026-10-05T18:00:00', state: 'free', state_th: 'ว่าง', job_id: null, can_close: true },
    ] },
    { date: '2026-10-06', day_off: true, slots: [
      { slot_id: 3, start: '2026-10-06T14:00:00', end: '2026-10-06T16:00:00', state: 'closed', state_th: 'ปิด', job_id: null, can_close: false },
    ] },
  ],
}

function makeApi(over = {}) {
  return {
    getSchedule: vi.fn().mockResolvedValue({ status: 200, body: schedule }),
    addSlot: vi.fn().mockResolvedValue({ status: 201, body: { slot_id: 9, start: '2026-10-05T09:00:00', end: '2026-10-05T11:00:00', state: 'free' } }),
    closeSlot: vi.fn().mockResolvedValue({ status: 200, body: { slot_id: 2, state: 'closed' } }),
    addDayOff: vi.fn(), removeDayOff: vi.fn().mockResolvedValue({ status: 200, body: { reopened_slots: 1 } }),
    ...over,
  }
}

test('UI-04-01 แสดงกติกาจากระบบ สถานะช่วงเป็นคำไทย เลขงาน ปุ่มปิดเฉพาะช่วงที่ระบบอนุญาต และวันหยุด', async () => {
  render(<TechnicianSchedule api={makeApi()} />)
  expect(await screen.findByText(/ช่วงละ 2 ชั่วโมง ระหว่าง 08:00 ถึง 20:00/)).toBeInTheDocument()
  expect(screen.getByTestId('slot-1')).toHaveTextContent('14:00 จองแล้ว งาน #7')
  expect(screen.getByTestId('slot-2')).toHaveTextContent('16:00 ว่าง')
  expect(screen.getAllByRole('button', { name: 'ปิดช่วงนี้' })).toHaveLength(1)
  expect(screen.getByText('วันหยุด')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'ยกเลิกวันหยุด' })).toBeInTheDocument()
})

test('AC-04-01 เพิ่มช่วงเวลา ส่งเวลาเริ่มให้ระบบ ระบบปฏิเสธแสดงข้อความของระบบ', async () => {
  const api = makeApi({ addSlot: vi.fn().mockResolvedValue({ status: 409, body: { reason: 'overlap', message: 'ช่วงเวลานี้ซ้อนกับช่วงที่มีอยู่แล้ว' } }) })
  render(<TechnicianSchedule api={api} />)
  await screen.findByTestId('slot-1')
  fireEvent.click(screen.getByRole('button', { name: 'เพิ่มช่วงเวลาว่าง' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ช่วงเวลานี้ซ้อนกับช่วงที่มีอยู่แล้ว'))
  expect(api.addSlot).toHaveBeenCalledWith({ start: '2026-10-05T09:00:00' })
})

test('AC-04-06 ประกาศวันหยุดในวันที่มีงาน ระบบปฏิเสธ หน้าจอแสดงข้อความของระบบ ปิดช่วงว่างได้', async () => {
  const api = makeApi({ addDayOff: vi.fn().mockResolvedValue({ status: 409, body: { reason: 'has_jobs', job_ids: [7], message: 'วันนี้มีงานที่จองแล้วหรือกำลังจอง กรุณาปฏิเสธงานก่อนประกาศวันหยุด' } }) })
  render(<TechnicianSchedule api={api} />)
  await screen.findByTestId('slot-1')
  fireEvent.click(screen.getAllByRole('button', { name: 'ประกาศวันหยุด' })[1])
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('กรุณาปฏิเสธงานก่อนประกาศวันหยุด'))
  expect(api.addDayOff).toHaveBeenCalledWith({ day: '2026-10-05' })
  fireEvent.click(screen.getByRole('button', { name: 'ปิดช่วงนี้' }))
  await waitFor(() => expect(api.closeSlot).toHaveBeenCalledWith({ slotId: 2 }))
})
