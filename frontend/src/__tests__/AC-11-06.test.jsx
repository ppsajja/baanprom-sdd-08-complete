// AC-11-06 ฝั่งหน้าจอ (REQ-FN-069): หน้าเลือกช่างแสดงคะแนนเฉลี่ยจากระบบ ลำดับช่างตามที่ระบบส่ง ไม่เรียงตามคะแนน
import { render, screen, fireEvent } from '@testing-library/react'
import TechnicianPicker from '../pages/TechnicianPicker.jsx'

const technicians = [
  { technician_id: 1, name: 'ประสิทธิ์', rating: { average: null, count: 2 }, slots: [{ slot_id: 1, start: '2026-10-12T14:00:00', end: '2026-10-12T16:00:00' }] },
  { technician_id: 2, name: 'วิชัย', rating: { average: 4.7, count: 3 }, slots: [{ slot_id: 2, start: '2026-10-12T14:00:00', end: '2026-10-12T16:00:00' }] },
]

test('AC-11-06 คะแนนเฉลี่ยทศนิยม 1 ตำแหน่งและจำนวน คะแนนไม่พอแสดงว่ายังไม่พอ ลำดับเดิม', async () => {
  const api = { getTechnicians: vi.fn().mockResolvedValue({ status: 200, body: technicians }), holdSlot: vi.fn(), getDepositQuote: vi.fn() }
  render(<TechnicianPicker api={api} customerId={1} addressId={1} onHeld={() => {}} />)
  fireEvent.click(screen.getByRole('button', { name: 'ค้นหาช่างที่ว่างใน 7 วัน' }))
  expect(await screen.findByTestId('rating-2')).toHaveTextContent('คะแนนเฉลี่ย 4.7 จาก 5 (3 คะแนน)')
  expect(screen.getByTestId('rating-1')).toHaveTextContent('ยังมีคะแนนไม่พอแสดงค่าเฉลี่ย')
  const names = screen.getAllByText(/^ช่าง /).map((p) => p.textContent)
  expect(names).toEqual(['ช่าง ประสิทธิ์', 'ช่าง วิชัย'])
})
