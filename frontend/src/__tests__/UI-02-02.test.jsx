// ตรวจรายการ "ต้องตรง" ของ UI-02-02 ลงทะเบียนลูกค้าใหม่ (specs/006-identity spec ส่วน 12)
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Register from '../pages/Register.jsx'

test('UI-02-02 ต้องกรอกชื่อและที่อยู่ก่อน แล้วส่งชื่อ ที่อยู่ และ challenge เดิมให้ระบบ', async () => {
  const api = { register: vi.fn().mockResolvedValue({ status: 201, body: { token: 't', role: 'customer', subject_id: 9, name: 'สมศรี' } }) }
  const onRegistered = vi.fn()
  render(<Register api={api} challengeId={8} phone="089-111-2222" onRegistered={onRegistered} onBack={() => {}} />)
  expect(screen.getByRole('heading', { name: 'ลงทะเบียนลูกค้าใหม่' })).toBeInTheDocument()
  expect(screen.getByText(/ยืนยันเบอร์ 089-111-2222 แล้ว/)).toBeInTheDocument()
  const submit = screen.getByRole('button', { name: 'ลงทะเบียนและเข้าสู่ระบบ' })
  expect(submit).toBeDisabled()
  fireEvent.change(screen.getByLabelText('ชื่อ'), { target: { value: 'สมศรี' } })
  fireEvent.change(screen.getByLabelText('ที่อยู่ให้บริการ'), { target: { value: 'บ้านเลขที่ 9' } })
  fireEvent.click(submit)
  await waitFor(() => expect(onRegistered).toHaveBeenCalled())
  expect(api.register).toHaveBeenCalledWith(expect.objectContaining({ challengeId: 8, name: 'สมศรี', addressText: 'บ้านเลขที่ 9' }))
  expect(screen.getByText('พิกัดใช้คำนวณระยะทางถึงช่างเท่านั้น ไม่แสดงให้ใครเห็น')).toBeInTheDocument()
})

test('UI-02-02 ระบบปฏิเสธ (เช่น หมดเวลาลงทะเบียน) แสดงข้อความของระบบ', async () => {
  const api = { register: vi.fn().mockResolvedValue({ status: 410, body: { reason: 'expired', message: 'รหัสหมดอายุแล้ว กรุณาขอรหัสใหม่' } }) }
  render(<Register api={api} challengeId={8} phone="089" onRegistered={() => {}} onBack={() => {}} />)
  fireEvent.change(screen.getByLabelText('ชื่อ'), { target: { value: 'ก' } })
  fireEvent.change(screen.getByLabelText('ที่อยู่ให้บริการ'), { target: { value: 'ข' } })
  fireEvent.click(screen.getByRole('button', { name: 'ลงทะเบียนและเข้าสู่ระบบ' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('รหัสหมดอายุแล้ว กรุณาขอรหัสใหม่'))
})
