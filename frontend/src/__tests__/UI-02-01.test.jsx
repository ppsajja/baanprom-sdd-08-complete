// ตรวจรายการ "ต้องตรง" ของ UI-02-01 เข้าสู่ระบบของลูกค้า (specs/006-identity spec ส่วน 12, mockups/UI-02-01-login.html)
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Login from '../pages/Login.jsx'

function fakeAuth(verify) {
  return {
    requestOtp: vi.fn().mockResolvedValue({ status: 202, body: { challenge_id: 7, expires_at: '2026-10-04T10:05:00', resend_after_seconds: 60 } }),
    verifyOtp: vi.fn().mockResolvedValue(verify),
  }
}

async function enterPhoneAndCode(code = '123456') {
  fireEvent.change(screen.getByLabelText('เบอร์โทรศัพท์'), { target: { value: '089-111-2222' } })
  fireEvent.click(screen.getByRole('button', { name: 'ขอรหัส OTP' }))
  await screen.findByText(/ส่งรหัส 6 หลักไปที่ 089-111-2222 แล้ว รหัสใช้ได้ถึง 10:05 น\./)
  fireEvent.change(screen.getByLabelText('รหัส OTP'), { target: { value: code } })
  fireEvent.click(screen.getByRole('button', { name: 'เข้าสู่ระบบ' }))
}

test('UI-02-01 ขอรหัสด้วยเบอร์โทร กรอกรหัส 6 หลัก แล้วเข้าสู่ระบบ เวลาหมดอายุมาจากระบบ', async () => {
  const api = fakeAuth({ status: 200, body: { token: 't', role: 'customer', subject_id: 3, name: 'สมศรี' } })
  const onLoggedIn = vi.fn()
  render(<Login api={api} role="customer" onLoggedIn={onLoggedIn} />)
  expect(screen.getByRole('heading', { name: 'เข้าสู่ระบบด้วยเบอร์โทร' })).toBeInTheDocument()
  await enterPhoneAndCode()
  await waitFor(() => expect(onLoggedIn).toHaveBeenCalledWith(expect.objectContaining({ token: 't', subject_id: 3 })))
  expect(api.requestOtp).toHaveBeenCalledWith({ phone: '089-111-2222', role: 'customer' })
  expect(api.verifyOtp).toHaveBeenCalledWith({ challengeId: 7, code: '123456' })
})

test('UI-02-01 รหัสผิด แสดงข้อความและจำนวนครั้งที่เหลือจากระบบ ยังอยู่ที่ช่องรหัส', async () => {
  const api = fakeAuth({ status: 401, body: { reason: 'wrong_code', attempts_left: 3, message: 'รหัสไม่ถูกต้อง เหลืออีก 3 ครั้ง' } })
  render(<Login api={api} onLoggedIn={() => {}} />)
  await enterPhoneAndCode('000000')
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('รหัสไม่ถูกต้อง เหลืออีก 3 ครั้ง'))
  expect(screen.getByLabelText('รหัส OTP')).toBeInTheDocument()
})

test('UI-02-01 ลองผิดครบหรือรหัสหมดอายุ แสดงข้อความของระบบ แล้วกลับไปขอรหัสใหม่', async () => {
  const api = fakeAuth({ status: 410, body: { reason: 'locked', message: 'ใส่รหัสผิดครบ 5 ครั้ง กรุณาขอรหัสใหม่' } })
  render(<Login api={api} onLoggedIn={() => {}} />)
  await enterPhoneAndCode('000000')
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ใส่รหัสผิดครบ 5 ครั้ง กรุณาขอรหัสใหม่'))
  expect(screen.getByRole('button', { name: 'ขอรหัส OTP' })).toBeInTheDocument()
})

test('UI-02-01 ขอรหัสถี่เกิน แสดงข้อความของระบบ ลูกค้าใหม่ไปหน้าลงทะเบียน', async () => {
  const api = {
    requestOtp: vi.fn().mockResolvedValueOnce({ status: 429, body: { reason: 'too_soon', message: 'ขอรหัสใหม่ได้อีกครั้งใน 30 วินาที' } })
      .mockResolvedValue({ status: 202, body: { challenge_id: 8, expires_at: '2026-10-04T10:05:00' } }),
    verifyOtp: vi.fn().mockResolvedValue({ status: 200, body: { needs_registration: true, challenge_id: 8 } }),
  }
  const onNeedsRegistration = vi.fn()
  render(<Login api={api} onLoggedIn={() => {}} onNeedsRegistration={onNeedsRegistration} />)
  fireEvent.change(screen.getByLabelText('เบอร์โทรศัพท์'), { target: { value: '089-111-2222' } })
  fireEvent.click(screen.getByRole('button', { name: 'ขอรหัส OTP' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ขอรหัสใหม่ได้อีกครั้งใน 30 วินาที'))
  await enterPhoneAndCode()
  await waitFor(() => expect(onNeedsRegistration).toHaveBeenCalledWith({ challengeId: 8, phone: '089-111-2222' }))
})
