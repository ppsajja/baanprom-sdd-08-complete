// ตรวจรายการ "ต้องตรง" ของ UI-02-04 ที่อยู่ของฉัน (specs/006-identity spec ส่วน 12 CR-18) และ AC-02-12 AC-02-13 ฝั่งหน้าจอ
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Addresses from '../pages/Addresses.jsx'

const rows = [{ address_id: 1, text: 'บ้านเลขที่ 12 ซอยสุขใจ', can_delete: false }, { address_id: 2, text: 'คอนโด เขตบางรัก', can_delete: true }]

test('UI-02-04 แสดงที่อยู่ ที่อยู่แรกเป็นค่าตั้งต้น ปุ่มลบเฉพาะที่ระบบอนุญาต ไม่มีพิกัดบนหน้าจอ', async () => {
  const api = { list: vi.fn().mockResolvedValue({ status: 200, body: rows }) }
  render(<Addresses api={api} />)
  expect(await screen.findByText('บ้านเลขที่ 12 ซอยสุขใจ (ค่าตั้งต้น)')).toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: 'ลบ' })).toHaveLength(1)
  expect(screen.getByText(/ใส่ชื่อเขตหรืออำเภอด้วย/)).toBeInTheDocument()
  expect(document.body.textContent).not.toMatch(/13\.7|100\.5/)
})

test('AC-02-13 เพิ่มที่อยู่ ส่งข้อความเท่านั้น ระบบหาตำแหน่งไม่พบ แสดงข้อความของระบบ', async () => {
  const api = {
    list: vi.fn().mockResolvedValue({ status: 200, body: rows }),
    add: vi.fn().mockResolvedValue({ status: 422, body: { reason: 'address_not_found', message: 'ไม่พบตำแหน่งของที่อยู่นี้ กรุณาใส่ชื่อเขตหรืออำเภอด้วย' } }),
  }
  render(<Addresses api={api} />)
  await screen.findByText('คอนโด เขตบางรัก')
  fireEvent.change(screen.getByLabelText('ที่อยู่ใหม่'), { target: { value: 'บ้านสวน' } })
  fireEvent.click(screen.getByRole('button', { name: 'เพิ่มที่อยู่' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ไม่พบตำแหน่งของที่อยู่นี้'))
  expect(api.add).toHaveBeenCalledWith({ text: 'บ้านสวน' })
})
