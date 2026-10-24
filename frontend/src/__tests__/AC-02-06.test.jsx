// test หน้าจอของ AC-02-06 (REQ-SEC-014, CR-11): ต้องเข้าสู่ระบบก่อน เมนูตามบทบาท และทุกคำขอส่ง token ไม่ส่ง customer_id
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../App.jsx'
import { api, setToken } from '../api/client.js'

function fakeAuth(login) {
  return {
    requestOtp: vi.fn().mockResolvedValue({ status: 202, body: { challenge_id: 1, expires_at: '2026-10-04T10:05:00' } }),
    verifyOtp: vi.fn().mockResolvedValue({ status: 200, body: login }),
    me: vi.fn().mockResolvedValue({ status: 200, body: { addresses: [{ address_id: 3, text: 'บ้าน' }] } }),
    logout: vi.fn().mockResolvedValue({ status: 200, body: { ok: true } }),
  }
}

async function login(authApi) {
  render(<App authApi={authApi} api={{ getTechnicians: vi.fn() }} jobStatusApi={{ getTechnicianJobs: vi.fn().mockResolvedValue({ status: 200, body: [] }) }} />)
  fireEvent.change(screen.getByLabelText('เบอร์โทรศัพท์'), { target: { value: '0891112222' } })
  fireEvent.click(screen.getByRole('button', { name: 'ขอรหัส OTP' }))
  fireEvent.change(await screen.findByLabelText('รหัส OTP'), { target: { value: '123456' } })
  fireEvent.click(screen.getByRole('button', { name: 'เข้าสู่ระบบ' }))
}

test('AC-02-06 ยังไม่เข้าสู่ระบบ เห็นหน้าเข้าสู่ระบบเท่านั้น ไม่มีเมนูจองงาน', () => {
  render(<App authApi={fakeAuth({})} />)
  expect(screen.getByRole('heading', { name: 'เข้าสู่ระบบด้วยเบอร์โทร' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'จองงาน' })).toBeNull()
})

test('AC-02-06 ลูกค้าเข้าสู่ระบบแล้วเห็นเมนูของลูกค้าและชื่อของตัวเอง ออกจากระบบแล้วกลับหน้าเข้าสู่ระบบ', async () => {
  const authApi = fakeAuth({ token: 'tok-c', role: 'customer', subject_id: 3, name: 'สมศรี' })
  await login(authApi)
  expect(await screen.findByRole('button', { name: 'งานของฉัน' })).toBeInTheDocument()
  expect(screen.getByText('คุณ สมศรี')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'งานของช่าง' })).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'ออกจากระบบ' }))
  await waitFor(() => expect(screen.getByRole('button', { name: 'ขอรหัส OTP' })).toBeInTheDocument())
  expect(authApi.logout).toHaveBeenCalled()
})

test('AC-01-03 ช่างเข้าสู่ระบบแล้วเห็นเฉพาะเมนูงานของช่าง', async () => {
  const authApi = fakeAuth({ token: 'tok-t', role: 'technician', subject_id: 1, name: 'ประสิทธิ์' })
  render(<App authApi={authApi} jobStatusApi={{ getTechnicianJobs: vi.fn().mockResolvedValue({ status: 200, body: [] }) }} />)
  fireEvent.click(screen.getByRole('button', { name: 'ช่าง' }))
  fireEvent.change(screen.getByLabelText('เบอร์โทรศัพท์'), { target: { value: '0865550101' } })
  fireEvent.click(screen.getByRole('button', { name: 'ขอรหัส OTP' }))
  fireEvent.change(await screen.findByLabelText('รหัส OTP'), { target: { value: '123456' } })
  fireEvent.click(screen.getByRole('button', { name: 'เข้าสู่ระบบ' }))
  expect(await screen.findByRole('heading', { name: 'งานของฉัน' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'จองงาน' })).toBeNull()
  expect(authApi.requestOtp).toHaveBeenCalledWith({ phone: '0865550101', role: 'technician' })
})

test('AC-02-06 client ส่ง Authorization ทุกคำขอ และไม่ส่ง customer_id ในคำขอ', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ status: 200, json: async () => ({}) })
  vi.stubGlobal('fetch', fetchMock)
  setToken('tok-xyz')
  await api.holdSlot({ slotId: 9, customerId: 1 })
  await api.getTechnicians({ category: 'ประปา', addressId: 3, customerId: 1 })
  for (const [url, init] of fetchMock.mock.calls) {
    expect(init.headers.Authorization).toBe('Bearer tok-xyz')
    expect(url).not.toMatch(/customer_id/)
    expect(String(init.body ?? '')).not.toMatch(/customer_id/)
  }
  setToken(null)
  vi.unstubAllGlobals()
})
