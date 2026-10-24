// ตรวจรายการ "ต้องตรง" ของ UI-13-01 กระทบยอด (specs/010-reconciliation spec ส่วน 12) และ AC-13-07 ฝั่งหน้าจอ (กุญแจของ Finance)
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Reconciliation from '../pages/Reconciliation.jsx'
import App from '../App.jsx'
import { financeApi, setStaffKey, setToken } from '../api/client.js'

const result = {
  run_id: 1, report_date: '2026-12-10', rows_in_report: 4, matched: 3, differences: 2, already_imported: false,
  items: [
    { kind: 'refund_unknown_resolved', kind_th: 'คืนเงินที่ไม่รู้ผล ได้ผลจากรายงานแล้ว', type: 'refund', reference: 'BP-3-a', job_id: 3, system_amount: 350, report_amount: 350, system_status: 'unknown', report_status: 'success' },
    { kind: 'missing_in_report', kind_th: 'มีในระบบ ไม่มีในรายงาน', type: 'capture', reference: 'BP-1-b', job_id: 1, system_amount: 400, report_amount: null, system_status: 'success', report_status: null },
  ],
}

test('UI-13-01 ส่งวันที่และข้อความรายงานให้ระบบ แสดงสรุปและรายการต่างเป็นคำไทยจากระบบ ไม่มีข้อมูลลูกค้า', async () => {
  const api = { reconcile: vi.fn().mockResolvedValue({ status: 201, body: result }) }
  render(<Reconciliation api={api} />)
  const btn = screen.getByRole('button', { name: 'กระทบยอด' })
  expect(btn).toBeDisabled()
  fireEvent.change(screen.getByLabelText('วันที่ของรายงาน'), { target: { value: '2026-12-10' } })
  fireEvent.change(screen.getByLabelText('หรือวางข้อความของรายงาน'), { target: { value: 'date,type,reference,amount,status\n' } })
  fireEvent.click(btn)
  expect(await screen.findByTestId('recon-result')).toHaveTextContent('รายการในรายงาน 4 | ตรงกัน 3 | รายการต่าง 2')
  expect(screen.getByText('คืนเงินที่ไม่รู้ผล ได้ผลจากรายงานแล้ว')).toBeInTheDocument()
  expect(screen.getByText('มีในระบบ ไม่มีในรายงาน')).toBeInTheDocument()
  expect(api.reconcile).toHaveBeenCalledWith({ reportDate: '2026-12-10', csv: 'date,type,reference,amount,status\n' })
})

test('AC-13-08 ไฟล์ผิด ระบบบอกเลขบรรทัด หน้าจอแสดงข้อความของระบบ', async () => {
  const api = { reconcile: vi.fn().mockResolvedValue({ status: 422, body: { reason: 'bad_report', line: 2, message: 'บรรทัด 2: ยอดเงินต้องเป็นจำนวนเต็มบาท' } }) }
  render(<Reconciliation api={api} />)
  fireEvent.change(screen.getByLabelText('วันที่ของรายงาน'), { target: { value: '2026-12-10' } })
  fireEvent.change(screen.getByLabelText('หรือวางข้อความของรายงาน'), { target: { value: 'x' } })
  fireEvent.click(screen.getByRole('button', { name: 'กระทบยอด' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('บรรทัด 2: ยอดเงินต้องเป็นจำนวนเต็มบาท'))
})

test('AC-13-07 เจ้าหน้าที่ Finance เข้าใช้ด้วยกุญแจ เห็นเฉพาะเมนูกระทบยอด คำขอส่ง X-Finance-Token ไม่ส่ง token ของลูกค้า', async () => {
  render(<App />)
  fireEvent.click(screen.getByRole('button', { name: 'เจ้าหน้าที่' }))
  fireEvent.change(screen.getByLabelText('กุญแจของบทบาท'), { target: { value: 'fin-key' } })
  fireEvent.click(screen.getByRole('button', { name: 'เข้าใช้งาน' }))
  const menu = await screen.findByRole('navigation', { name: 'เมนู' })
  expect(menu).toHaveTextContent('กระทบยอด')
  expect(screen.getByText('เจ้าหน้าที่ Finance')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'จองงาน' })).toBeNull()
  const fetchMock = vi.fn().mockResolvedValue({ status: 200, json: async () => [] })
  vi.stubGlobal('fetch', fetchMock)
  setToken('tok-customer')
  await financeApi.followUp()
  const [, init] = fetchMock.mock.calls[0]
  expect(init.headers['X-Finance-Token']).toBe('fin-key')
  expect(init.headers.Authorization).toBeUndefined()
  setToken(null); setStaffKey(null)
  vi.unstubAllGlobals()
})
