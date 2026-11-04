import { BOOKING_RULES } from './config.js';

export const pad = (n) => String(n).padStart(2, '0');
export const localDay = (value) => {
  const d = value instanceof Date ? value : new Date(value);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};
export const addDays = (value, days) => {
  const d = new Date(value);
  d.setDate(d.getDate() + days);
  return d;
};
export const startOfWeek = (value) => {
  const d = new Date(value);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d;
};
export const toLocalDateTime = (day, time) => {
  const [y, m, d] = day.split('-').map(Number);
  const [h, min] = time.split(':').map(Number);
  return new Date(y, m - 1, d, h, min, 0, 0);
};
export const isoAt = (day, time) => toLocalDateTime(day, time).toISOString();
export const formatDate = (value, options = {}) => new Intl.DateTimeFormat('ja-JP', { month: 'long', day: 'numeric', weekday: 'short', ...options }).format(new Date(value));
export const formatClock = (value) => new Intl.DateTimeFormat('ja-JP', { hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value));
export const formatShort = (value) => new Intl.DateTimeFormat('ja-JP', { month: 'numeric', day: 'numeric', weekday: 'short' }).format(new Date(value));
export const formatLong = (value) => new Intl.DateTimeFormat('ja-JP', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }).format(new Date(value));
export const timeFromMinutes = (m) => `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;
export const minutesFromTime = (time) => { const [h, m] = time.split(':').map(Number); return h * 60 + m; };
export const slotById = (id) => BOOKING_RULES.slots.find((s) => s.id === String(id));
export const slotByStart = (time) => BOOKING_RULES.slots.find((s) => s.start === time);
export const slotForReservation = (r) => {
  const start = new Date(r.start_at), end = new Date(r.end_at);
  return BOOKING_RULES.slots.find((s) =>
    start.getHours() * 60 + start.getMinutes() === minutesFromTime(s.start) &&
    end.getHours() * 60 + end.getMinutes() === minutesFromTime(s.end) &&
    localDay(start) === localDay(end));
};
export const overlaps = (aStart, aEnd, bStart, bEnd) => new Date(aStart).getTime() < new Date(bEnd).getTime() && new Date(aEnd).getTime() > new Date(bStart).getTime();
export const validateBooking = ({ title, room_id, start_at, end_at }, reservations, now = new Date()) => {
  if (!title || !title.trim()) return '利用目的を入力してください。';
  if (title.trim().length > 80) return '利用目的は80文字以内で入力してください。';
  if (room_id !== BOOKING_RULES.roomId) return '予約できる部室は1室のみです。';
  const start = new Date(start_at), end = new Date(end_at);
  if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime())) return '日時が正しくありません。';
  if (start <= now) return '過去の日時は予約できません。';
  if (localDay(start) !== localDay(end)) return '日付をまたぐ予約はできません。';
  if (!slotForReservation({ start_at, end_at })) return '指定の7つの予約枠から1枠を選択してください。';
  if (reservations.some((r) => r.room_id === room_id && overlaps(start_at, end_at, r.start_at, r.end_at))) return 'この時間帯にはすでに予約があります。';
  return null;
};
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
export const initials = (name) => [...String(name || 'U')].slice(0, 2).join('');
