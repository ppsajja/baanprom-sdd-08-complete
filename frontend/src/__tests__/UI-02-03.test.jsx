// ตรวจรายการ "ต้องตรง" ของ UI-02-03 งานของฉัน (specs/006-identity และ 007-accept-rematch spec ส่วน 12) และ AC-05-04 ฝั่งหน้าจอ
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import MyJobs from '../pages/MyJobs.jsx'

const jobs = [
  { job_id: 21, status: 'confirmed', category: 'ประปา', scheduled_start: '2026-10-05T14:00:00', technician_name: 'สมหมาย', substitute: true, can_decline_substitute: true },
  { job_id: 20, status: 'rematching', category: 'ไฟฟ้า', scheduled_start: '2026-10-06T09:00:00', technician_name: null, substitute: false, can_decline_substitute: false },
]

test('UI-02-03 งานของฉันแสดงสถานะคำไทย ช่างแทน และปุ่มไม่รับช่างแทนเฉพาะงานที่ระบบอนุญาต', async () => {
  const api = { myJobs: vi.fn().mockResolvedValue({ status: 200, body: jobs }), declineSubstitute: vi.fn() }
  render(<MyJobs api={api} />)
  expect(await screen.findByText(/ช่าง สมหมาย \(ช่างแทน\)/)).toBeInTheDocument()
  expect(screen.getByTestId('my-status-21')).toHaveTextContent('ยืนยันแล้ว')
  expect(screen.getByTestId('my-status-20')).toHaveTextContent('กำลังหาช่างใหม่')
  expect(screen.getAllByRole('button', { name: 'ไม่รับช่างแทน ขอคืนมัดจำ' })).toHaveLength(1)
})

test('AC-05-04 ลูกค้ากดไม่รับช่างแทน ระบบยกเลิกและบอกยอดคืนที่ระบบส่งมา', async () => {
  const api = {
    myJobs: vi.fn().mockResolvedValueOnce({ status: 200, body: jobs }).mockResolvedValue({ status: 200, body: [{ ...jobs[0], status: 'cancelled', can_decline_substitute: false }] }),
    declineSubstitute: vi.fn().mockResolvedValue({ status: 200, body: { job_id: 21, status: 'cancelled', rule: 'R4', refund_amount: 350, refund_message: '' } }),
  }
  render(<MyJobs api={api} />)
  fireEvent.click(await screen.findByRole('button', { name: 'ไม่รับช่างแทน ขอคืนมัดจำ' }))
  await waitFor(() => expect(screen.getByText('ยกเลิกงาน #21 แล้ว คืนมัดจำ 350 บาท')).toBeInTheDocument())
  expect(api.declineSubstitute).toHaveBeenCalledWith({ jobId: 21 })
  await waitFor(() => expect(screen.getByTestId('my-status-21')).toHaveTextContent('ยกเลิก'))
})
