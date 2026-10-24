// DEF-01 (ตรวจรับ R1 รอบแรก EV-049, GAP-36): รายการต้องตรงของ UI-07-02 "ล็อกช่วงเวลานี้ไว้ให้คุณถึง HH:MM น." ต้องมีทุกทางที่เข้าหน้ายืนยัน
// รวมทางที่ลูกค้าแตะช่วงใกล้เคียงหลังช่วงเดิมถูกจองไป (AC-07-04) ซึ่งต้องล็อกช่วงใหม่ก่อนตาม REQ-FN-041 (ล็อกตั้งแต่ขั้น 3)
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../App.jsx'

// CR-11 (R2): App ต้องมีผู้เข้าสู่ระบบแล้ว (เลิกใช้ลูกค้าคงที่) test ส่ง session ของลูกค้า 1 คนที่มีที่อยู่ 1 แห่งเข้าไป
const SESSION = { role: 'customer', subjectId: 1, name: 'สมชาย', addresses: [{ address_id: 1, text: 'บ้านเลขที่ 12 ซอยสุขใจ' }] }

const alt = { slot_id: 2, technician_id: 1, technician_name: 'ประสิทธิ์', start: '2026-10-12T16:00:00', end: '2026-10-12T18:00:00' }

function fakeApi(holdAlt) {
  return {
    getTechnicians: vi.fn().mockResolvedValue({ status: 200, body: [{ technician_id: 1, name: 'ประสิทธิ์', slots: [{ slot_id: 1, start: '2026-10-12T14:00:00', end: '2026-10-12T16:00:00' }] }] }),
    holdSlot: vi.fn()
      .mockResolvedValueOnce({ status: 200, body: { slot_id: 1, hold_expires_at: '2026-10-11T10:10:00' } })
      .mockResolvedValueOnce(holdAlt),
    getDepositQuote: vi.fn().mockResolvedValue({ status: 200, body: { category: 'ประปา', deposit_amount: 350, estimate_amount: 700, estimate_note: 'ค่าบริการเบื้องต้น' } }),
    createBooking: vi.fn().mockResolvedValue({ status: 409, body: { reason: 'slot_taken', alternatives: [alt] } }),
  }
}

async function goToAlternative(api) {
  render(<App api={api} session={SESSION} />)
  fireEvent.click(screen.getByRole('button', { name: 'ค้นหาช่างที่ว่างใน 7 วัน' }))
  fireEvent.click(await screen.findByRole('button', { name: /14:00/ }))
  fireEvent.click(await screen.findByRole('button', { name: 'ยืนยันและชำระมัดจำ 350 บาท' }))
  fireEvent.click(await screen.findByRole('button', { name: /ช่าง ประสิทธิ์/ }))
}

test('UI-07-02 DEF-01 แตะช่วงใกล้เคียงแล้ว ระบบล็อกช่วงใหม่ และหน้ายืนยันบอกเวลาที่ล็อกไว้จากระบบ', async () => {
  const api = fakeApi({ status: 200, body: { slot_id: 2, hold_expires_at: '2026-10-11T10:25:00' } })
  await goToAlternative(api)
  await waitFor(() => expect(screen.getByText('ล็อกช่วงเวลานี้ไว้ให้คุณถึง 10:25 น.')).toBeInTheDocument())
  expect(api.holdSlot).toHaveBeenLastCalledWith({ slotId: 2, customerId: 1 })
  expect(screen.getByRole('button', { name: 'ยืนยันและชำระมัดจำ 350 บาท' })).toBeEnabled()
})

test('UI-07-02 DEF-01 ช่วงใกล้เคียงถูกล็อกไปก่อน แสดงข้อความและกดยืนยันไม่ได้', async () => {
  const api = fakeApi({ status: 409, body: { reason: 'slot_taken', alternatives: [] } })
  await goToAlternative(api)
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('ช่วงเวลานี้เพิ่งถูกจองไป'))
  expect(screen.getByRole('button', { name: 'ยืนยันและชำระมัดจำ 350 บาท' })).toBeDisabled()
})
