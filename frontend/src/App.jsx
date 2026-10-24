// หน้าหลักของบ้านพร้อม: UC-07 จองงาน (เลือกช่าง ยืนยัน ผล), UC-08 ยกเลิกการจอง, UC-09 สถานะงานและงานของช่าง, UC-14 ผู้ช่วย (CR-09)
// R1 ใช้ลูกค้า ที่อยู่ และช่างคงที่ CR-11 (R2): เลิกใช้ค่าคงที่ ผู้ใช้ต้องเข้าสู่ระบบก่อน (UC-02 ลูกค้า, UC-01 ช่าง)
// ลูกค้า ที่อยู่ และช่างมาจาก session ของการเข้าสู่ระบบ token ส่งไปทุกคำขอผ่าน api/client.js (REQ-SEC-014)
// แถบเมนูด้านบนและปุ่มออกจากระบบเป็นปุ่มนำทาง ไม่ต้องมี REQ รองรับ เมนูแยกตามบทบาท (ช่างเห็นเฉพาะงานของช่าง)
// R2 ส่วน B: ช่างมีตารางเวลา (UC-04) ทุกคนตั้งค่าการแจ้งเตือนได้ (UC-10) ลูกค้ามีหน้าที่อยู่ (F-17)
// เจ้าหน้าที่ (Finance กระทบยอด UC-13 และ call center) ใช้กุญแจของบทบาทตัวเอง (GAP-32) กุญแจอยู่ในหน่วยความจำของหน้าเท่านั้น
import { useEffect, useState } from 'react'
import {
  api as realApi, jobStatusApi as realJobStatusApi, cancelApi as realCancelApi, assistantApi as realAssistantApi,
  authApi as realAuthApi, setToken, scheduleApi as realScheduleApi, ratingApi as realRatingApi,
  addressApi as realAddressApi, notifyApi as realNotifyApi, financeApi as realFinanceApi, callCenterApi as realCallCenterApi,
  setStaffKey, STAFF_HEADERS,
} from './api/client.js'
import TechnicianPicker from './pages/TechnicianPicker.jsx'
import ConfirmBooking from './pages/ConfirmBooking.jsx'
import BookingResult from './pages/BookingResult.jsx'
import TechnicianJobs from './pages/TechnicianJobs.jsx'
import JobStatus from './pages/JobStatus.jsx'
import CancelBooking from './pages/CancelBooking.jsx'
import CancelResult from './pages/CancelResult.jsx'
import AssistantChat from './pages/AssistantChat.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import MyJobs from './pages/MyJobs.jsx'
import TechnicianSchedule from './pages/TechnicianSchedule.jsx'
import Addresses from './pages/Addresses.jsx'
import NotificationSettings from './pages/NotificationSettings.jsx'
import Reconciliation from './pages/Reconciliation.jsx'
import CallCenterTools from './pages/CallCenterTools.jsx'

const VIEWS = {
  customer: [['book', 'จองงาน'], ['myjobs', 'งานของฉัน'], ['status', 'สถานะงาน'], ['cancel', 'ยกเลิกการจอง'], ['assistant', 'ผู้ช่วย'],
    ['addresses', 'ที่อยู่ของฉัน'], ['notify', 'การแจ้งเตือน']],
  technician: [['technician', 'งานของช่าง'], ['schedule', 'ตารางเวลา'], ['notify', 'การแจ้งเตือน']],
  finance: [['reconcile', 'กระทบยอด']],
  call_center: [['callcenter', 'เครื่องมือ call center']],
}
const FIRST_VIEW = { customer: 'book', technician: 'technician', finance: 'reconcile', call_center: 'callcenter' }
const STAFF_ROLES = [['finance', 'Finance'], ['call_center', 'call center']]

function StaffLogin({ onLoggedIn }) {
  const [role, setRole] = useState('finance')
  const [key, setKey] = useState('')
  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800">เข้าใช้งานของเจ้าหน้าที่</h2>
      <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); onLoggedIn(role, key) }}>
        <label className="block text-sm text-slate-600">บทบาท
          <select value={role} onChange={(e) => setRole(e.target.value)} className="ml-2 rounded-lg border border-slate-300 px-2 py-1">
            {STAFF_ROLES.map(([k, label]) => <option key={k} value={k}>{label}</option>)}
          </select>
        </label>
        <label className="block text-sm text-slate-600">กุญแจของบทบาท
          <input type="password" value={key} onChange={(e) => setKey(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
        </label>
        <button type="submit" disabled={!key} className="w-full rounded-lg bg-teal-700 px-4 py-3 text-sm font-semibold text-white disabled:bg-slate-300">เข้าใช้งาน</button>
      </form>
    </section>
  )
}
const STORE_KEY = 'baanprom.session'

function loadStored() {
  try { return JSON.parse(window.localStorage.getItem(STORE_KEY) ?? 'null') } catch { return null }
}
function store(s) {
  try {
    if (s) window.localStorage.setItem(STORE_KEY, JSON.stringify({ token: s.token, role: s.role, subjectId: s.subjectId, name: s.name }))
    else window.localStorage.removeItem(STORE_KEY)
  } catch { /* ไม่มีที่เก็บ ใช้ได้เฉพาะหน้านี้ */ }
}

export default function App({ api = realApi, jobStatusApi = realJobStatusApi, cancelApi = realCancelApi, assistantApi = realAssistantApi,
  authApi = realAuthApi, scheduleApi = realScheduleApi, ratingApi = realRatingApi, addressApi = realAddressApi,
  notifyApi = realNotifyApi, financeApi = realFinanceApi, callCenterApi = realCallCenterApi,
  session: initialSession = null, initialView }) {
  const [session, setSession] = useState(initialSession)
  const [loginRole, setLoginRole] = useState('customer')
  const [registering, setRegistering] = useState(null)
  const [view, setView] = useState(initialView ?? FIRST_VIEW[initialSession?.role ?? 'customer'])
  const [held, setHeld] = useState(null)
  const [job, setJob] = useState(null)
  const [cancelled, setCancelled] = useState(null)

  useEffect(() => {
    if (initialSession) { if (initialSession.token) setToken(initialSession.token); return }
    const saved = loadStored()
    if (!saved?.token) return
    setToken(saved.token)
    authApi.me().then(({ status, body }) => {
      if (status !== 200) { setToken(null); store(null); return }
      begin({ ...saved, addresses: body.addresses ?? [] })
    })
  }, [])

  function begin(s) {
    setSession(s)
    setView(FIRST_VIEW[s.role])
    setHeld(null); setJob(null); setCancelled(null)
  }

  async function loggedIn(body) {
    setToken(body.token)
    const me = await authApi.me()
    const s = { token: body.token, role: body.role, subjectId: body.subject_id, name: body.name, addresses: me.body?.addresses ?? [] }
    store(s)
    setRegistering(null)
    begin(s)
  }

  async function logout() {
    if (session?.staff) setStaffKey(null)
    else await authApi.logout()
    setToken(null); store(null)
    setSession(null)
  }

  function staffLogin(role, key) {
    setStaffKey({ header: STAFF_HEADERS[role], key })
    begin({ role, staff: true, name: STAFF_ROLES.find(([k]) => k === role)[1] })
  }

  if (!session) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <header className="mb-4">
          <h1 className="text-2xl font-bold text-teal-800">บ้านพร้อม</h1>
          <p className="text-slate-600">จองช่างซ่อมบ้านที่ว่างจริง ไม่ต้องโทรถาม</p>
        </header>
        {!registering && (
          <nav aria-label="ประเภทผู้ใช้" className="mb-4 flex gap-2">
            {[['customer', 'ลูกค้า'], ['technician', 'ช่าง'], ['staff', 'เจ้าหน้าที่']].map(([key, label]) => (
              <button key={key} type="button" onClick={() => setLoginRole(key)} aria-current={loginRole === key ? 'page' : undefined}
                className={`rounded-full px-3 py-1 text-sm ${loginRole === key ? 'bg-teal-700 text-white' : 'bg-white text-teal-800 ring-1 ring-teal-700'}`}>
                {label}
              </button>
            ))}
          </nav>
        )}
        {registering
          ? <Register api={authApi} challengeId={registering.challengeId} phone={registering.phone} onRegistered={loggedIn} onBack={() => setRegistering(null)} />
          : loginRole === 'staff'
            ? <StaffLogin onLoggedIn={staffLogin} />
            : <Login key={loginRole} api={authApi} role={loginRole} onLoggedIn={loggedIn} onNeedsRegistration={setRegistering} />}
      </main>
    )
  }

  const customerId = session.subjectId
  const addresses = session.addresses ?? []
  const addressId = held?.addressId ?? addresses[0]?.address_id

  return (
    <main className="mx-auto max-w-2xl p-6">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-teal-800">บ้านพร้อม</h1>
          <p className="text-slate-600">จองช่างซ่อมบ้านที่ว่างจริง ไม่ต้องโทรถาม</p>
        </div>
        <div className="text-right text-sm text-slate-600">
          <p>{session.staff ? 'เจ้าหน้าที่' : session.role === 'technician' ? 'ช่าง' : 'คุณ'} {session.name}</p>
          <button type="button" onClick={logout} className="text-teal-800 underline">ออกจากระบบ</button>
        </div>
      </header>
      <nav aria-label="เมนู" className="mb-4 flex flex-wrap gap-2">
        {VIEWS[session.role].map(([key, label]) => (
          <button key={key} type="button" onClick={() => { setView(key); setCancelled(null) }} aria-current={view === key ? 'page' : undefined}
            className={`rounded-full px-3 py-1 text-sm ${view === key ? 'bg-teal-700 text-white' : 'bg-white text-teal-800 ring-1 ring-teal-700'}`}>
            {label}
          </button>
        ))}
      </nav>

      {view === 'book' && !held && !job && (
        <TechnicianPicker api={api} customerId={customerId} addressId={addressId} addresses={addresses.length > 1 ? addresses : undefined} onHeld={setHeld} />
      )}
      {view === 'book' && held && !job && (
        <ConfirmBooking key={held.slot.slot_id} api={api} customerId={customerId} addressId={addressId} held={held}
          onConfirmed={setJob}
          onBack={() => setHeld(null)}
          onPickAlternative={async (a) => {
            // DEF-01 (ตรวจรับ R1 EV-049, GAP-36): เดิมตั้ง holdExpiresAt เป็น null และไม่ล็อกช่วงใหม่ หน้ายืนยันจึงไม่บอกเวลาที่ต้องชำระให้เสร็จ
            // REQ-FN-041: ล็อกช่วงที่เลือกตั้งแต่ขั้น 3 เวลาสิ้นสุดมาจากระบบ (D-00-05) ล็อกไม่ได้ แสดงข้อความและห้ามกดยืนยัน
            const technician = { technician_id: a.technician_id, name: a.technician_name }
            const hold = await api.holdSlot({ slotId: a.slot_id, customerId })
            if (hold.status === 200) return setHeld({ ...held, slot: a, technician, holdExpiresAt: hold.body.hold_expires_at, holdError: null })
            const holdError = hold.body?.reason === 'hold_limit' ? hold.body.message : 'ช่วงเวลานี้เพิ่งถูกจองไป'
            setHeld({ ...held, slot: a, technician, holdExpiresAt: null, holdError })
          }} />
      )}
      {view === 'book' && job && <BookingResult job={job} technicianName={held?.technician?.name} onRestart={() => { setHeld(null); setJob(null) }} />}

      {view === 'myjobs' && <MyJobs api={authApi} ratingApi={ratingApi} />}
      {view === 'addresses' && <Addresses api={addressApi} onChanged={(rows) => setSession((s) => ({ ...s, addresses: rows.map(({ address_id, text }) => ({ address_id, text })) }))} />}
      {view === 'notify' && <NotificationSettings api={notifyApi} />}
      {view === 'schedule' && <TechnicianSchedule api={scheduleApi} />}
      {view === 'reconcile' && <Reconciliation api={financeApi} />}
      {view === 'callcenter' && <CallCenterTools api={callCenterApi} />}
      {view === 'status' && <JobStatus api={jobStatusApi} />}
      {view === 'cancel' && !cancelled && <CancelBooking api={cancelApi} customerId={customerId} onCancelled={setCancelled} />}
      {view === 'cancel' && cancelled && <CancelResult result={cancelled} onHome={() => { setCancelled(null); setView('book') }} />}
      {view === 'technician' && <TechnicianJobs api={jobStatusApi} technicianId={session.subjectId} />}
      {view === 'assistant' && <AssistantChat api={assistantApi} customerId={customerId} />}
    </main>
  )
}
