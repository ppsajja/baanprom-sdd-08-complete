// จุดเดียวที่หน้าจอใช้เรียก API หลังบ้าน (ตามสัญญา API ใน plan.md ข้อ 4)
// ตอน test ให้ส่ง client จำลองเข้าไปในหน้าจอแทน ไม่ต้องรันหลังบ้านจริง
// เรียกผ่าน /api (ดู proxy ใน vite.config.js) หลังบ้านต้องรันอยู่ที่ port 8000
// CR-11 (R2): ทุกคำขอแนบ token ของผู้ที่เข้าสู่ระบบ (Authorization: Bearer) ตัวตนมาจาก token เท่านั้น (REQ-SEC-014)
// customerId และ technicianId ที่หน้าจอยังส่งเข้ามาในฟังก์ชันไม่ถูกส่งไปหลังบ้านแล้ว token เก็บในหน่วยความจำของหน้าเท่านั้น
const BASE = import.meta.env.VITE_API_BASE ?? '/api'

let token = null
export function setToken(t) { token = t }
export function getToken() { return token }

function withAuth(init = {}) {
  const headers = { ...(init.headers ?? {}) }
  if (token) headers.Authorization = `Bearer ${token}`
  return { ...init, headers }
}

async function call(path, init) {
  return readJson(await fetch(`${BASE}${path}`, withAuth(init)))
}

function postJson(path, body) {
  return call(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) })
}

async function readJson(res) {
  return { status: res.status, body: await res.json() }
}

export const api = {
  // REQ-FN-008 ค้นช่างว่างใน 7 วัน
  async getTechnicians({ category, addressId }) {
    const q = new URLSearchParams({ category, address_id: addressId })
    return call(`/technicians?${q}`)
  },
  // REQ-FN-041 ล็อกช่วงเวลาชั่วคราว (ระยะล็อกอยู่ที่หลังบ้าน config HOLD_MINUTES หน้าจอรับเวลาสิ้นสุดจากคำตอบ)
  async holdSlot({ slotId }) {
    return postJson(`/slots/${slotId}/hold`)
  },
  // REQ-BR-002 ยอดมัดจำตามประเภทงาน (AC-07-11) หน้าจอห้ามคำนวณหรือพิมพ์ยอดเอง
  async getDepositQuote({ category }) {
    const q = new URLSearchParams({ category })
    return call(`/deposit-quote?${q}`)
  },
  // UC-07 ขั้น 5 ยืนยันและชำระมัดจำ ตอบ 201 / 409 slot_taken / 402 payment_failed
  async createBooking({ slotId, addressId, category }) {
    return postJson('/bookings', { slot_id: slotId, address_id: addressId, category })
  },
  // CR-08 REQ-FN-064 ช่างที่เคยใช้ (BR-08) และช่วงเวลาว่างของช่างคนนั้น
  async getPastTechnicians() {
    return call('/me/past-technicians')
  },
  async getPastTechnicianSlots({ technicianId, category, addressId }) {
    const q = new URLSearchParams({ category, address_id: addressId })
    return call(`/me/past-technicians/${technicianId}/slots?${q}`)
  },
  // CR-08 REQ-FN-065 (Q-28) เส้นทาง A1 เลขโทร call center มาจากระบบ
  async getContact() {
    return call('/contact')
  },
}

// ---- UC-09 ช่างอัปเดตสถานะงาน (specs/003-job-status, CR-05) ----
export const jobStatusApi = {
  // REQ-FN-050 รายการงานของช่างคนนี้ (เบอร์ลูกค้ามาเฉพาะช่วงที่ REQ-SEC-004 อนุญาต หน้าจอไม่คำนวณเอง)
  async getTechnicianJobs({ technicianId }) {
    return call(`/technicians/${technicianId}/jobs`)
  },
  // REQ-FN-051 เปลี่ยนสถานะตามลูกศรของ MD-STM-01 ตอบ 200 หรือ 409 transition_not_allowed
  async updateJobStatus({ jobId, toStatus }) {
    return postJson(`/jobs/${jobId}/status`, { to_status: toStatus })
  },
  // CR-12 REQ-FN-061 (UC-12) รับงาน หรือปฏิเสธงาน
  async acceptJob({ jobId }) {
    return postJson(`/jobs/${jobId}/accept`)
  },
  async rejectJob({ jobId, reason }) {
    return postJson(`/jobs/${jobId}/reject`, { reason })
  },
  // REQ-FN-052 มุมมองลูกค้าและ call center อ่านสถานะจากที่เดียวกับช่าง
  async getJob({ jobId }) {
    return call(`/jobs/${jobId}`)
  },
  // REQ-DAT-002 ประวัติการเปลี่ยนสถานะ
  async getJobHistory({ jobId }) {
    return call(`/jobs/${jobId}/history`)
  },
}

// ---- UC-08 ลูกค้ายกเลิกการจองและรับเงินคืน (specs/004-cancel-refund, CR-06) ----
export const cancelApi = {
  // REQ-FN-054 / REQ-BR-001 ยอดคืนตาม BR-01 จากระบบ หน้าจอห้ามคำนวณเอง (D-00-05)
  async getRefundQuote({ jobId }) {
    return call(`/jobs/${jobId}/refund-quote`)
  },
  // REQ-FN-054 ยกเลิกจริง ตอบ 200 หรือ 409 (R6, ยกเลิกไปแล้ว)
  async cancelByCustomer({ jobId }) {
    return postJson(`/jobs/${jobId}/customer-cancel`)
  },
}

// ---- UC-14 ผู้ช่วยตอบคำถามและเลื่อนนัด (specs/005-ai-assistant, CR-09) ----
const post = postJson

export const assistantApi = {
  // REQ-AI-022 ผู้ช่วยเปิดอยู่ไหม (ปิดอยู่ แสดงข้อความและปุ่มโทร)
  async getStatus() {
    return call('/assistant/status')
  },
  // REQ-AI-020 ข้อความแรกมาจากระบบ
  async start() {
    return post('/assistant/conversations')
  },
  async send({ conversationId, text }) {
    return post('/assistant/messages', { conversation_id: conversationId, text })
  },
  // REQ-AI-011 ระดับ 2: เรียกเฉพาะเมื่อลูกค้ากด "ยืนยันเลื่อนนัด"
  async confirm({ proposalId }) {
    return post(`/assistant/proposals/${proposalId}/confirm`)
  },
  async decline({ proposalId }) {
    return post(`/assistant/proposals/${proposalId}/decline`)
  },
  async handoff({ conversationId }) {
    return post(`/assistant/conversations/${conversationId}/handoff`)
  },
  // REQ-AI-022 ปุ่ม "คำตอบนี้ไม่ถูกต้อง"
  async report({ turnId }) {
    return post(`/assistant/turns/${turnId}/report`)
  },
}

// ---- CR-11 UC-01 ช่างเข้าสู่ระบบ และ UC-02 ลูกค้าลงทะเบียนและเข้าสู่ระบบ (specs/006-identity) ----
export const authApi = {
  // REQ-SEC-013 ขอรหัส OTP (ระบบส่งทาง IF-02) ตอบ 202 หรือ 429 too_soon / too_many
  async requestOtp({ phone, role }) {
    return postJson('/auth/otp', { phone, role })
  },
  // ตอบ token (มีบัญชีแล้ว) หรือ needs_registration (ลูกค้าใหม่) หรือ 401 wrong_code / 410 expired locked
  async verifyOtp({ challengeId, code }) {
    return postJson('/auth/verify', { challenge_id: challengeId, code })
  },
  // REQ-FN-058 ลูกค้าใหม่กรอกชื่อและที่อยู่ให้บริการ
  async register({ challengeId, name, addressText, lat, lng }) {
    return postJson('/auth/register', { challenge_id: challengeId, name, address_text: addressText, lat, lng })
  },
  async logout() {
    return postJson('/auth/logout')
  },
  async me() {
    return call('/me')
  },
  async addAddress({ text, lat, lng }) {
    return postJson('/me/addresses', { text, lat, lng })
  },
  // REQ-FN-052 งานของฉัน และ REQ-FN-063 ไม่รับช่างแทน
  async myJobs() {
    return call('/me/jobs')
  },
  async declineSubstitute({ jobId }) {
    return postJson(`/jobs/${jobId}/decline-substitute`)
  },
}

// ---- R2 ส่วน B ----
// CR-18 (GAP-32): เจ้าหน้าที่ใช้กุญแจของบทบาทตัวเอง (Finance หรือ call center) เก็บในหน่วยความจำของหน้าเท่านั้น ไม่เก็บลงเครื่อง
let staff = null
export function setStaffKey(s) { staff = s }
function staffCall(path, init = {}) {
  const headers = { ...(init.headers ?? {}) }
  if (staff) headers[staff.header] = staff.key
  return fetch(`${BASE}${path}`, { ...init, headers }).then(readJson)
}
function staffPost(path, body) {
  return staffCall(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) })
}
export const STAFF_HEADERS = { finance: 'X-Finance-Token', call_center: 'X-Call-Center-Token' }

// CR-14 UC-04 ช่างจัดตารางเวลา (specs/008-schedule) กฎทั้งหมดอยู่หลังบ้าน (BR-10) หน้าจอแสดงข้อความที่ระบบส่งมา
export const scheduleApi = {
  async getSchedule() { return call('/me/schedule') },
  async addSlot({ start }) { return postJson('/me/slots', { start }) },
  async closeSlot({ slotId }) { return postJson(`/me/slots/${slotId}/close`) },
  async addDayOff({ day }) { return postJson('/me/days-off', { day }) },
  async removeDayOff({ day }) { return call(`/me/days-off/${day}`, { method: 'DELETE' }) },
}

// CR-15 UC-11 ให้คะแนนช่าง (specs/009-rating) ให้ได้หรือไม่มาจาก can_rate ของระบบ
export const ratingApi = {
  async rate({ jobId, stars, comment }) { return postJson(`/jobs/${jobId}/rating`, { stars, comment }) },
  async myRating() { return call('/me/rating') },
}

// CR-18 REQ-FN-074 หน้าจัดการที่อยู่ (UI-02-04) พิกัดหาจากข้อความที่อยู่ที่หลังบ้าน (IF-03) หน้าจอไม่ส่งพิกัด
export const addressApi = {
  async list() { return call('/me/addresses') },
  async add({ text }) { return postJson('/me/addresses', { text }) },
  async remove({ addressId }) { return call(`/me/addresses/${addressId}`, { method: 'DELETE' }) },
}

// CR-17 UC-10 ตั้งค่าการแจ้งเตือน (specs/011-notifications)
export const notifyApi = {
  async get() { return call('/me/notifications') },
  async setChannel({ channel }) {
    return call('/me/notifications', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ channel }) })
  },
  async startLineLink() { return postJson('/me/notifications/line-link') },
  async unlinkLine() { return postJson('/me/notifications/line-unlink') },
}

// CR-16 UC-13 กระทบยอดของ Finance (specs/010-reconciliation) ใช้กุญแจของ Finance
export const financeApi = {
  async reconcile({ reportDate, csv }) { return staffPost('/finance/reconciliations', { report_date: reportDate, csv }) },
  async followUp() { return staffCall('/finance/refunds/follow-up') },
}

// CR-18 เครื่องมือของ call center (GAP-31 GAP-32) ใช้กุญแจของ call center
export const callCenterApi = {
  async getJob({ jobId }) { return staffCall(`/jobs/${jobId}`) },
  async switchAssistant({ enabled }) { return staffPost('/call-center/assistant/switch', { enabled }) },
  async tickets() { return staffCall('/call-center/assistant/tickets') },
  async revertReschedule({ jobId }) { return staffPost(`/call-center/jobs/${jobId}/revert-reschedule`) },
  async assistantStatus() { return staffCall('/assistant/status') },
}
