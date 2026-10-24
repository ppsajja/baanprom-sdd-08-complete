// test หน้าจอของ AC-12-01 ถึง AC-12-02 และ AC-05-01 (CR-12, UI-09-01 รายการ "ต้องตรง" ที่เพิ่ม) ปุ่มรับงานและปฏิเสธงานมาจากระบบ
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TechnicianJobs from '../pages/TechnicianJobs.jsx'

const pending = {
  job_id: 31, status: 'confirmed', category: 'ประปา', scheduled_start: '2026-10-05T14:00:00', customer_name: 'สมชาย',
  next_statuses: [{ status: 'en_route', label: 'ออกเดินทาง' }],
  responses: [{ action: 'accept', label: 'รับงาน' }, { action: 'reject', label: 'ปฏิเสธงาน' }],
  assignment: { response: 'pending', respond_by: '2026-10-04T10:30:00', via_rematch: false },
}

test('AC-12-01 งานใหม่มีปุ่มรับงานและปฏิเสธงาน พร้อมเวลาที่ต้องตอบจากระบบ', async () => {
  const api = { getTechnicianJobs: vi.fn().mockResolvedValue({ status: 200, body: [pending] }) }
  render(<TechnicianJobs api={api} technicianId={1} />)
  expect(await screen.findByRole('button', { name: 'รับงาน' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'ปฏิเสธงาน' })).toBeInTheDocument()
  expect(screen.getByTestId('respond-by-31')).toHaveTextContent('กรุณารับหรือปฏิเสธภายใน 10:30 น.')
})

test('AC-12-02 กดรับงาน ปุ่มรับงานหายตามที่ระบบส่งกลับ สถานะยังเป็นยืนยันแล้ว', async () => {
  const accepted = { ...pending, responses: [{ action: 'reject', label: 'ปฏิเสธงาน' }], assignment: { ...pending.assignment, response: 'accepted' } }
  const api = {
    getTechnicianJobs: vi.fn().mockResolvedValue({ status: 200, body: [pending] }),
    acceptJob: vi.fn().mockResolvedValue({ status: 200, body: accepted }),
  }
  render(<TechnicianJobs api={api} technicianId={1} />)
  fireEvent.click(await screen.findByRole('button', { name: 'รับงาน' }))
  await waitFor(() => expect(screen.queryByRole('button', { name: 'รับงาน' })).toBeNull())
  expect(api.acceptJob).toHaveBeenCalledWith({ jobId: 31 })
  expect(screen.getByTestId('status-31')).toHaveTextContent('ยืนยันแล้ว')
  expect(screen.queryByTestId('respond-by-31')).toBeNull()
})

test('AC-05-01 ช่างกดปฏิเสธงาน งานออกจากรายการของช่าง', async () => {
  const api = {
    getTechnicianJobs: vi.fn().mockResolvedValue({ status: 200, body: [pending] }),
    rejectJob: vi.fn().mockResolvedValue({ status: 200, body: { job_id: 31, released: true } }),
  }
  render(<TechnicianJobs api={api} technicianId={1} />)
  fireEvent.click(await screen.findByRole('button', { name: 'ปฏิเสธงาน' }))
  await waitFor(() => expect(screen.getByText('ยังไม่มีงานที่มอบหมายให้คุณ')).toBeInTheDocument())
})

test('AC-12-05 ระบบปฏิเสธ (ออกเดินทางแล้ว) แสดงข้อความของระบบ', async () => {
  const api = {
    getTechnicianJobs: vi.fn().mockResolvedValue({ status: 200, body: [pending] }),
    rejectJob: vi.fn().mockResolvedValue({ status: 409, body: { reason: 'not_confirmed', message: 'รับหรือปฏิเสธได้เฉพาะงานที่สถานะ ยืนยันแล้ว' } }),
  }
  render(<TechnicianJobs api={api} technicianId={1} />)
  fireEvent.click(await screen.findByRole('button', { name: 'ปฏิเสธงาน' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('รับหรือปฏิเสธได้เฉพาะงานที่สถานะ ยืนยันแล้ว'))
})
