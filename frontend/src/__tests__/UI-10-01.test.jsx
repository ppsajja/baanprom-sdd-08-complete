// ตรวจรายการ "ต้องตรง" ของ UI-10-01 การแจ้งเตือน (specs/011-notifications spec ส่วน 12) และ AC-10-02 AC-10-03 ฝั่งหน้าจอ
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import NotificationSettings from '../pages/NotificationSettings.jsx'

test('UI-10-01 ค่าตั้งต้น SMS LINE ต้องเชื่อมก่อน ระบบปฏิเสธแสดงข้อความของระบบ บอกว่า OTP ส่ง SMS เสมอ', async () => {
  const api = {
    get: vi.fn().mockResolvedValue({ status: 200, body: { channel: 'sms', line_linked: false, channels: ['sms', 'line'] } }),
    setChannel: vi.fn().mockResolvedValue({ status: 409, body: { reason: 'line_not_linked', message: 'กรุณาเชื่อมบัญชี LINE ก่อนเลือกรับข้อความทาง LINE' } }),
    startLineLink: vi.fn().mockResolvedValue({ status: 200, body: { instruction: 'เพิ่มเพื่อนบัญชี LINE ของบ้านพร้อม แล้วพิมพ์รหัส 123456 ภายใน 10 นาที', link_code: '123456' } }),
  }
  render(<NotificationSettings api={api} />)
  expect(await screen.findByTestId('channel')).toHaveTextContent('SMS')
  expect(screen.getByText('(ต้องเชื่อมบัญชีก่อน)')).toBeInTheDocument()
  expect(screen.getByText(/รหัส OTP สำหรับเข้าสู่ระบบส่งทาง SMS เสมอ/)).toBeInTheDocument()
  fireEvent.click(screen.getByLabelText(/LINE/))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('กรุณาเชื่อมบัญชี LINE ก่อน'))
  fireEvent.click(screen.getByRole('button', { name: 'เชื่อมบัญชี LINE' }))
  expect(await screen.findByTestId('link-instruction')).toHaveTextContent('พิมพ์รหัส 123456 ภายใน 10 นาที')
})

test('AC-10-02 เชื่อมแล้วเลือก LINE ได้ แสดงช่องทางที่ระบบบันทึก', async () => {
  const api = {
    get: vi.fn().mockResolvedValue({ status: 200, body: { channel: 'sms', line_linked: true, channels: ['sms', 'line'] } }),
    setChannel: vi.fn().mockResolvedValue({ status: 200, body: { channel: 'line', line_linked: true, channels: ['sms', 'line'] } }),
  }
  render(<NotificationSettings api={api} />)
  await screen.findByTestId('channel')
  fireEvent.click(screen.getByLabelText(/LINE/))
  await waitFor(() => expect(screen.getByTestId('channel')).toHaveTextContent('LINE'))
  expect(api.setChannel).toHaveBeenCalledWith({ channel: 'line' })
  expect(screen.getByRole('button', { name: 'ยกเลิกการเชื่อม LINE' })).toBeInTheDocument()
})
