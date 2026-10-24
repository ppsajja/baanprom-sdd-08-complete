// ตรวจรายการ "ต้องตรง" ของ UI-14-02 เครื่องมือ call center (specs/005-ai-assistant spec ส่วน 12 CR-18) และ AC-14-19 AC-00-15 ฝั่งหน้าจอ
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CallCenterTools from '../pages/CallCenterTools.jsx'

function makeApi(over = {}) {
  return {
    assistantStatus: vi.fn().mockResolvedValue({ status: 200, body: { enabled: true } }),
    tickets: vi.fn().mockResolvedValue({ status: 200, body: [{ status: 'open' }, { status: 'closed' }] }),
    switchAssistant: vi.fn().mockResolvedValue({ status: 200, body: { enabled: false } }),
    getJob: vi.fn().mockResolvedValue({ status: 200, body: { job_id: 5, status: 'confirmed', scheduled_start: '2026-10-06T14:00:00' } }),
    revertReschedule: vi.fn().mockResolvedValue({ status: 200, body: { job_id: 5, scheduled_start: '2026-10-05T14:00:00', slot_id: 1 } }),
    ...over,
  }
}

test('UI-14-02 หัวหน้า call center เห็นสถานะผู้ช่วยและตั๋วที่รอ ปิดผู้ช่วยได้ทันทีด้วยกุญแจของตัวเอง', async () => {
  const api = makeApi()
  render(<CallCenterTools api={api} />)
  expect(await screen.findByTestId('assistant-state')).toHaveTextContent('เปิด')
  expect(screen.getByText(/ตั๋วรอเจ้าหน้าที่ 1 ใบ/)).toBeInTheDocument()
  api.assistantStatus.mockResolvedValue({ status: 200, body: { enabled: false } })
  fireEvent.click(screen.getByRole('button', { name: 'ปิดผู้ช่วยทันที' }))
  await waitFor(() => expect(screen.getByText(/ปิดผู้ช่วยแล้ว/)).toBeInTheDocument())
  expect(api.switchAssistant).toHaveBeenCalledWith({ enabled: false })
})

test('AC-14-19 เปิดงานแล้วเลื่อนนัดกลับเวลาเดิม ระบบปฏิเสธแสดงข้อความของระบบ', async () => {
  const api = makeApi({ revertReschedule: vi.fn().mockResolvedValue({ status: 409, body: { reason: 'slot_taken', message: 'ช่วงเวลาเดิมไม่ว่างแล้ว กรุณาหาเวลาใหม่กับลูกค้า' } }) })
  render(<CallCenterTools api={api} />)
  fireEvent.change(await screen.findByLabelText('เลขงาน'), { target: { value: '5' } })
  fireEvent.click(screen.getByRole('button', { name: 'เปิดงาน' }))
  fireEvent.click(await screen.findByRole('button', { name: 'เลื่อนนัดกลับเวลาเดิม' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ช่วงเวลาเดิมไม่ว่างแล้ว'))
  expect(api.revertReschedule).toHaveBeenCalledWith({ jobId: 5 })
})
