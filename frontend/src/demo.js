import { addDays, isoAt, localDay, startOfWeek, validateBooking, slotById } from './utils.js';
import { BOOKING_RULES } from './config.js';

const USERS = [
  { id: 'u-001', name: '田中 はるか', email: 'member@example.com', role: 'member' },
  { id: 'u-002', name: '佐藤 ゆうき', email: 'admin@example.com', role: 'admin' },
  { id: 'u-003', name: '鈴木 りお', email: 'rio@example.com', role: 'member' },
  { id: 'u-004', name: '山本 そら', email: 'sora@example.com', role: 'member' },
];
export const DEMO_ROOMS = [
  { id: BOOKING_RULES.roomId, name: 'サークル部室', description: 'サークルの活動や練習、ミーティングに利用できる共用の部室です。', capacity: 12, color: '#6658df', amenities: ['共用スペース'] },
];
const SKEY = 'roombase-demo-session-v1';
const RKEY = 'roombase-demo-reservations-v2';
const pause = (ms = 100) => new Promise((r) => setTimeout(r, ms));
const fail = (message, status = 400) => { const e = new Error(message); e.status = status; throw e; };
const read = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; } catch { return fallback; } };

function seed() {
  if (localStorage.getItem(RKEY) !== null) return;
  const monday = startOfWeek(new Date());
  // すべて正式な時間枠・同じ部室。以前のデモ予約は別の保存キーで残します。
  const fixtures = [
    [0, '2', '定例ミーティング', 'u-003'],
    [1, '4', '企画会議', 'u-001'],
    [2, '3', '新歓打ち合わせ', 'u-004'],
    [3, '5', '自主練習', 'u-001'],
    [4, '6', '全体練習', 'u-003'],
    [5, '4', '運営ミーティング', 'u-002'],
    [7, '6', '次週の活動', 'u-001'],
    [8, '2', 'パート練習', 'u-003'],
  ];
  const reservations = fixtures.map(([dayOffset, slotId, title, user_id], n) => {
    const day = localDay(addDays(monday, dayOffset));
    const slot = slotById(slotId);
    return { id: `demo-${n + 1}`, room_id: BOOKING_RULES.roomId, user_id, user_name: USERS.find((u) => u.id === user_id).name, title, note: '', start_at: isoAt(day, slot.start), end_at: isoAt(day, slot.end), created_at: new Date().toISOString() };
  });
  localStorage.setItem(RKEY, JSON.stringify(reservations));
}
const allReservations = () => { seed(); return read(RKEY, []); };
const loggedIn = () => {
  const user = USERS.find((u) => u.id === read(SKEY, null));
  if (!user) fail('ログインが必要です。', 401);
  return user;
};
export const demoApi = {
  async me() { await pause(); return USERS.find((u) => u.id === read(SKEY, null)) || null; },
  async login(email, password) {
    await pause(200);
    const user = USERS.find((u) => u.email === email.trim().toLowerCase());
    if (!user || password !== 'demo1234' || user.id === 'u-003' || user.id === 'u-004') fail('メールアドレスまたはパスワードが違います。', 401);
    localStorage.setItem(SKEY, JSON.stringify(user.id));
    return user;
  },
  async logout() { localStorage.removeItem(SKEY); await pause(); },
  async rooms() { loggedIn(); await pause(); return structuredClone(DEMO_ROOMS); },
  async reservations(from, to) {
    loggedIn(); await pause();
    return allReservations().filter((r) => r.start_at < to && r.end_at > from).sort((a, b) => a.start_at.localeCompare(b.start_at));
  },
  async create(data) {
    const user = loggedIn(); await pause(160);
    if (!DEMO_ROOMS.some((r) => r.id === data.room_id)) fail('指定された部室がありません。', 404);
    const old = allReservations();
    const error = validateBooking(data, old);
    if (error) fail(error, error.includes('すでに予約') ? 409 : 400);
    const reservation = { ...data, id: `demo-${crypto.randomUUID()}`, user_id: user.id, user_name: user.name, title: data.title.trim(), note: (data.note || '').trim(), created_at: new Date().toISOString() };
    localStorage.setItem(RKEY, JSON.stringify([...old, reservation]));
    return reservation;
  },
  async cancel(id) {
    const user = loggedIn(); await pause(130);
    const all = allReservations(), reservation = all.find((r) => r.id === id);
    if (!reservation) fail('予約が見つかりません。', 404);
    if (reservation.user_id !== user.id && user.role !== 'admin') fail('この予約をキャンセルする権限がありません。', 403);
    if (new Date(reservation.start_at) <= new Date()) fail('開始済みの予約はキャンセルできません。', 400);
    localStorage.setItem(RKEY, JSON.stringify(all.filter((r) => r.id !== id)));
  },
};
