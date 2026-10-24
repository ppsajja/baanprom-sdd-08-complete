// ตรวจรายการ "ต้องตรง" ของ UI-11-01 ให้คะแนนช่าง (specs/009-rating spec ส่วน 12) และ AC-11-01 AC-11-03 ฝั่งหน้าจอ
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import MyJobs from '../pages/MyJobs.jsx'

const done = { job_id: 30, status: 'done', category: 'ประปา', scheduled_start: '2026-10-05T14:00:00', technician_name: 'ประสิทธิ์', substitute: false, can_decline_substitute: false, can_rate: true, my_rating: null }

test('UI-11-01 งานที่ระบบให้คะแนนได้มีส่วนให้คะแนน ต้องเลือกดาวก่อนส่ง ส่งแล้วแสดงข้อความของระบบและคะแนนของฉัน', async () => {
  const api = { myJobs: vi.fn().mockResolvedValueOnce({ status: 200, body: [done] }).mockResolvedValue({ status: 200, body: [{ ...done, can_rate: false, my_rating: 4 }] }) }
  const ratingApi = { rate: vi.fn().mockResolvedValue({ status: 201, body: { job_id: 30, stars: 4, message: 'ขอบคุณสำหรับคะแนน' } }) }
  render(<MyJobs api={api} ratingApi={ratingApi} />)
  expect(await screen.findByText('ให้คะแนนช่าง ประสิทธิ์')).toBeInTheDocument()
  expect(screen.getByText(/ลูกค้าคนอื่นเห็นเฉพาะคะแนนเฉลี่ย/)).toBeInTheDocument()
  const send = screen.getByRole('button', { name: 'ส่งคะแนน' })
  expect(send).toBeDisabled()
  fireEvent.click(screen.getByRole('button', { name: '4 ดาว' }))
  fireEvent.change(screen.getByLabelText(/ความเห็น/), { target: { value: 'ตรงเวลา' } })
  fireEvent.click(send)
  await waitFor(() => expect(screen.getByText('ขอบคุณสำหรับคะแนน')).toBeInTheDocument())
  expect(ratingApi.rate).toHaveBeenCalledWith({ jobId: 30, stars: 4, comment: 'ตรงเวลา' })
  expect(await screen.findByText('คุณให้คะแนน 4 ดาว')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'ส่งคะแนน' })).toBeNull()
})

test('AC-11-03 ระบบปฏิเสธ (ให้ซ้ำ) แสดงข้อความของระบบ งานที่ระบบไม่อนุญาตไม่มีส่วนให้คะแนน', async () => {
  const api = { myJobs: vi.fn().mockResolvedValue({ status: 200, body: [done, { ...done, job_id: 31, can_rate: false }] }) }
  const ratingApi = { rate: vi.fn().mockResolvedValue({ status: 409, body: { reason: 'already_rated', message: 'งานนี้ให้คะแนนแล้ว' } }) }
  render(<MyJobs api={api} ratingApi={ratingApi} />)
  await screen.findByText('ให้คะแนนช่าง ประสิทธิ์')
  expect(screen.getAllByRole('button', { name: 'ส่งคะแนน' })).toHaveLength(1)
  fireEvent.click(screen.getByRole('button', { name: '5 ดาว' }))
  fireEvent.click(screen.getByRole('button', { name: 'ส่งคะแนน' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('งานนี้ให้คะแนนแล้ว'))
})
