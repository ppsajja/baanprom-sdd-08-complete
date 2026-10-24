// ตรวจรายการ "ต้องตรง" ของ UI-01-01 เข้าสู่ระบบของช่าง (specs/006-identity spec ส่วน 12)
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Login from '../pages/Login.jsx'

test('UI-01-01 หัวเรื่องของช่าง บอกว่าบัญชีออกโดยบ้านพร้อม และขอรหัสในบทบาทช่าง', async () => {
  const api = {
    requestOtp: vi.fn().mockResolvedValue({ status: 202, body: { challenge_id: 2, expires_at: '2026-10-04T10:05:00' } }),
    verifyOtp: vi.fn().mockResolvedValue({ status: 200, body: { token: 'x', role: 'technician', subject_id: 1, name: 'ประสิทธิ์' } }),
  }
  const onLoggedIn = vi.fn()
  render(<Login api={api} role="technician" onLoggedIn={onLoggedIn} />)
  expect(screen.getByRole('heading', { name: 'เข้าสู่ระบบสำหรับช่าง' })).toBeInTheDocument()
  expect(screen.getByText(/ถ้ายังไม่มีบัญชี ติดต่อหัวหน้าช่าง/)).toBeInTheDocument()
  fireEvent.change(screen.getByLabelText('เบอร์โทรศัพท์'), { target: { value: '086-555-0101' } })
  fireEvent.click(screen.getByRole('button', { name: 'ขอรหัส OTP' }))
  fireEvent.change(await screen.findByLabelText('รหัส OTP'), { target: { value: '654321' } })
  fireEvent.click(screen.getByRole('button', { name: 'เข้าสู่ระบบ' }))
  await waitFor(() => expect(onLoggedIn).toHaveBeenCalled())
  expect(api.requestOtp).toHaveBeenCalledWith({ phone: '086-555-0101', role: 'technician' })
  expect(screen.queryByRole('button', { name: /ลงทะเบียน/ })).toBeNull()  // ช่างไม่มีทางลงทะเบียนเอง
})
