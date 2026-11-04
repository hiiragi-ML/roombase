import { api, isDemo } from './api.js';
import { BOOKING_RULES } from './config.js';
import {
  addDays, esc, formatClock, formatDate, formatLong, formatShort,
  initials, isoAt, localDay, startOfWeek,
  slotById, overlaps, validateBooking,
} from './utils.js';

const root = document.getElementById('app');
const today = new Date();
const state = {
  user: null, rooms: [], reservations: [], loading: true, error: '',
  page: 'calendar', focus: today, calendarView: innerWidth < 740 ? 'day' : 'week',
  roomId: BOOKING_RULES.roomId, myFilter: 'upcoming', modal: null,
  toast: '', mobileMenu: false, authView: 'login', loginEmail: '',
};

const paths = {
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  door: '<path d="M4 21V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16M2 21h20"/><path d="M9 3v18M14 12h.01"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  chevronRight: '<path d="m9 18 6-6-6-6"/>',
  chevronDown: '<path d="m6 9 6 6 6-6"/>',
  close: '<path d="M18 6 6 18M6 6l12 12"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/>',
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  check: '<path d="m20 6-11 11-5-5"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 11v5M12 8h.01"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  spark: '<path d="m12 3 1.8 6.2L20 11l-6.2 1.8L12 19l-1.8-6.2L4 11l6.2-1.8L12 3ZM19 18l.7 1.3L21 20l-1.3.7L19 22l-.7-1.3L17 20l1.3-.7L19 18Z"/>',
  building: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 21v-5h6v5M8 7h2M14 7h2M8 11h2M14 11h2"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  alert: '<path d="m10.3 3.6-8.6 15a2 2 0 0 0 1.7 3h17.2a2 2 0 0 0 1.7-3l-8.6-15a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14.9-3M4 4v5h5M4 13a8 8 0 0 0 14.9 3M20 20v-5h-5"/>',
};
const ico = (name, size = 19) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.info}</svg>`;
const safeColor = (color) => /^#[0-9a-f]{6}$/i.test(color || '') ? color : '#6658df';
const roomById = (id) => state.rooms.find((r) => r.id === id);
const mine = (r) => r.user_id === state.user?.id;
const future = (r) => new Date(r.start_at) > new Date();
const bookingLabel = (r) => `${formatShort(r.start_at)} ${formatClock(r.start_at)}–${formatClock(r.end_at)}`;
const fullName = (r) => roomById(r.room_id)?.name || '部室';

async function refreshData() {
  const now = new Date(), earliest = addDays(now, -120), latest = addDays(now, 365);
  const center = state.focus;
  const from = new Date(Math.min(earliest.getTime(), addDays(center, -14).getTime())).toISOString();
  const to = new Date(Math.max(latest.getTime(), addDays(center, 15).getTime())).toISOString();
  const [rooms, reservations] = await Promise.all([api.rooms(), api.reservations(from, to)]);
  state.rooms = rooms;
  state.reservations = reservations;
  if (!rooms.some((r) => r.id === state.roomId)) state.roomId = rooms[0]?.id || '';
}
async function boot() {
  try {
    state.user = await api.me();
    if (state.user) await refreshData();
  } catch (e) { state.error = e.message; }
  state.loading = false;
  render();
}
function notify(message) {
  state.toast = message;
  render();
  const current = message;
  setTimeout(() => { if (state.toast === current) { state.toast = ''; root.querySelector('.toast')?.remove(); } }, 3700);
}
function showError(message) {
  const el = root.querySelector('[data-form-error]');
  if (el) { el.textContent = message; el.hidden = false; }
  else notify(message);
}
function rangeHeading() {
  if (state.calendarView === 'day') return formatLong(state.focus);
  const start = startOfWeek(state.focus), end = addDays(start, 6);
  return `${start.getFullYear()}年${start.getMonth() + 1}月${start.getDate()}日 – ${end.getMonth() + 1}月${end.getDate()}日`;
}
function navLink(page, label, iconName) {
  return `<button class="side-link ${state.page === page ? 'is-active' : ''}" data-action="nav" data-page="${page}" type="button">${ico(iconName, 19)}<span>${label}</span>${state.page === page ? '<span class="nav-active-mark"></span>' : ''}</button>`;
}
function sidebar() {
  return `<aside class="sidebar ${state.mobileMenu ? 'sidebar--show' : ''}">
    <div class="side-top"><a class="brand" href="#" data-action="home" aria-label="ROOMBASE ホーム"><span class="brand-mark">R<span class="brand-mark-dot"></span></span><span class="brand-word">room<span>base.</span></span></a><div class="brand-caption">部室予約システム</div></div>
    <div class="side-section-title">WORKSPACE</div>
    <nav class="side-nav" aria-label="メインメニュー">
      ${navLink('calendar', '予約カレンダー', 'calendar')}
      ${navLink('mine', '自分の予約', 'clock')}
      ${navLink('rooms', '部室について', 'door')}
    </nav>
    ${state.user.role === 'admin' ? `<div class="side-section-title side-section-title--second">MANAGEMENT</div><nav class="side-nav">${navLink('admin', '予約の管理', 'shield')}</nav>` : ''}
    <div class="side-spacer"></div>
    <div class="sidebar-footer"><div class="side-user-avatar">${esc(initials(state.user.name))}</div><div class="side-user-info"><strong>${esc(state.user.name)}</strong><span>${state.user.role === 'admin' ? '管理者' : 'サークルメンバー'}${isDemo ? ' · デモ' : ''}</span></div><button class="icon-button side-logout" title="ログアウト" aria-label="ログアウト" data-action="logout">${ico('logout', 18)}</button></div>
  </aside>`;
}
function topbar() {
  const labels = { calendar: '予約カレンダー', mine: '自分の予約', rooms: '部室について', admin: '予約の管理' };
  return `<header class="topbar"><div class="topbar-left"><button class="icon-button mobile-menu" data-action="toggle-menu" aria-label="メニューを開く">${ico('menu')}</button><span class="breadcrumb">WORKSPACE</span><span class="breadcrumb-slash">/</span><strong>${labels[state.page]}</strong></div><div class="topbar-right"><span class="topbar-today">${formatDate(new Date(), { year: 'numeric' })}</span><span class="topbar-avatar">${esc(initials(state.user.name))}</span></div></header>`;
}
function statCard(iconName, label, value, desc, accent = false) {
  return `<div class="stat-card"><div class="stat-icon ${accent ? 'stat-icon--purple' : ''}">${ico(iconName, 21)}</div><div><div class="stat-label">${esc(label)}</div><div class="stat-value">${esc(value)}</div><div class="stat-caption">${esc(desc)}</div></div></div>`;
}
function dashboardHeader() {
  const myUpcoming = state.reservations.filter((r) => mine(r) && future(r)).sort((a, b) => a.start_at.localeCompare(b.start_at));
  const weekStart = startOfWeek(new Date()), weekEnd = addDays(weekStart, 7);
  const weeklyTotal = state.reservations.filter((r) => new Date(r.start_at) >= weekStart && new Date(r.start_at) < weekEnd).length;
  const nextBooking = myUpcoming[0];
  return `<div class="page-heading page-heading--minimal"><h1>予約カレンダー</h1><button class="btn btn-primary page-create" data-action="new-booking">${ico('plus', 17)} 新しい予約</button></div>
    <div class="stats-grid">
      ${statCard('calendar', '今週の予約', String(weeklyTotal).padStart(2, '0'), '部室のすべての予約', true)}
      ${statCard('clock', '自分の予約', String(myUpcoming.length).padStart(2, '0'), 'これからの予約')}
      ${statCard('door', '利用できる部室', String(state.rooms.length).padStart(2, '0'), '共用の部室は1室')}
      ${statCard('spark', '次回の予約', nextBooking ? formatShort(nextBooking.start_at) : '未定', nextBooking ? `${formatClock(nextBooking.start_at)} · ${fullName(nextBooking)}` : '予約してみましょう')}
    </div>`;
}
function roomChips() {
  const room = state.rooms[0];
  return `<div class="room-filter"><span class="room-chip selected"><span class="room-dot" style="--room-color:${safeColor(room?.color)}"></span>${esc(room?.name || 'サークル部室')}・全7枠</span></div>`;
}
const slotStatus = (day, slot) => {
  const startAt = isoAt(day, slot.start), endAt = isoAt(day, slot.end);
  const booked = state.reservations.find((r) => r.room_id === BOOKING_RULES.roomId && overlaps(startAt, endAt, r.start_at, r.end_at));
  const past = new Date(startAt) <= new Date();
  return { booked, past };
};
function calendarGrid() {
  const days = state.calendarView === 'week'
    ? Array.from({ length: 7 }, (_, i) => addDays(startOfWeek(state.focus), i))
    : [new Date(state.focus)];
  const current = new Date();
  const header = days.map((d) => `<div class="cal-day-head ${localDay(d) === localDay(current) ? 'is-today' : ''}"><span class="cal-day-week">${new Intl.DateTimeFormat('ja-JP', { weekday: 'short' }).format(d)}</span><span class="cal-day-number">${d.getDate()}</span>${localDay(d) === localDay(current) ? '<span class="today-tick"></span>' : ''}</div>`).join('');
  const times = BOOKING_RULES.slots.map((slot, i) => `<div class="fixed-time-mark"><span class="fixed-time-index">${i + 1}限</span><strong>${slot.start}</strong><span class="fixed-time-divider">–</span><strong>${slot.end}</strong></div>`).join('');
  const lanes = days.map((date) => {
    const day = localDay(date);
    const slots = BOOKING_RULES.slots.map((slot) => {
      const { booked, past } = slotStatus(day, slot);
      if (booked) return `<button type="button" class="fixed-slot fixed-slot--booked ${mine(booked) ? 'fixed-slot--mine' : ''} ${past ? 'fixed-slot--past' : ''}" data-action="details" data-id="${esc(booked.id)}" title="${esc(booked.title)}の予約を見る"><span class="fixed-slot-state">${mine(booked) ? '自分の予約' : '予約済み'}</span><strong>${esc(booked.title)}</strong><span class="fixed-slot-owner">${esc(booked.user_name)}${mine(booked) ? ' · 自分' : ''}</span></button>`;
      return `<button type="button" class="fixed-slot ${past ? 'fixed-slot--past' : 'fixed-slot--free'}" data-action="slot" data-day="${day}" data-slot="${slot.id}" ${past ? 'disabled' : ''} aria-label="${esc(formatShort(date))} ${slot.start}〜${slot.end} ${past ? '終了' : '空き・予約する'}"><span class="fixed-slot-state">${past ? '終了' : '空き'}</span>${!past ? '<strong>＋ 予約する</strong>' : '<span class="fixed-slot-muted">予約不可</span>'}</button>`;
    }).join('');
    return `<div class="cal-lane fixed-lane">${slots}</div>`;
  }).join('');
  return `<div class="calendar-scroll"><div class="calendar-table ${state.calendarView === 'week' ? 'calendar-table--week' : 'calendar-table--day'}"><div class="cal-head"><div class="cal-corner">予約枠</div>${header}</div><div class="cal-body"><div class="fixed-time-rail">${times}</div><div class="cal-lanes">${lanes}</div></div></div></div>`;
}
function calendarPage() {
  return `${dashboardHeader()}<section class="panel calendar-panel"><div class="calendar-panel-top"><div><div class="section-kicker">SCHEDULE</div><h2>予約カレンダー</h2></div><div class="calendar-actions"><button class="btn btn-outline small" data-action="go-today">今日</button><div class="switcher" role="group" aria-label="表示切り替え"><button class="${state.calendarView === 'week' ? 'active' : ''}" data-action="calendar-view" data-value="week">週</button><button class="${state.calendarView === 'day' ? 'active' : ''}" data-action="calendar-view" data-value="day">日</button></div></div></div><div class="calendar-toprow"><div class="cal-current"><button class="icon-button nav-date" data-action="prev-date" aria-label="前の期間">${ico('chevronLeft')}</button><button class="icon-button nav-date" data-action="next-date" aria-label="次の期間">${ico('chevronRight')}</button><strong>${esc(rangeHeading())}</strong></div><div class="legend"><span><i class="legend-dot legend-dot--self"></i> 自分の予約</span><span><i class="legend-dot legend-dot--other"></i> ほかの予約</span></div></div>${roomChips()}${calendarGrid()}<div class="cal-footer">${ico('info', 16)} 1日7つの固定枠から1枠ずつ予約できます。空き枠をクリックすると予約画面が開きます。</div></section>`;
}
function reservationItem(r, admin = false) {
  const room = roomById(r.room_id);
  const canCancel = future(r) && (mine(r) || state.user.role === 'admin');
  return `<article class="booking-card"><div class="booking-color" style="background:${safeColor(room?.color)}"></div><div class="booking-date-box"><strong>${new Date(r.start_at).getDate()}</strong><span>${new Intl.DateTimeFormat('ja-JP', { month: 'short' }).format(new Date(r.start_at))}</span></div><div class="booking-info"><div class="booking-labels"><span class="tiny-pill" style="--pill-color:${safeColor(room?.color)}">${esc(room?.name || '部室')}</span>${mine(r) ? '<span class="tiny-pill tiny-pill--neutral">自分の予約</span>' : ''}</div><h3>${esc(r.title)}</h3><p>${ico('clock', 15)} ${esc(bookingLabel(r))}${admin ? ` <span class="separator-dot">·</span> ${esc(r.user_name)}` : ''}</p></div><div class="booking-actions"><button class="btn btn-outline small" data-action="details" data-id="${esc(r.id)}">詳細</button>${canCancel ? `<button class="btn btn-text-danger small" data-action="cancel" data-id="${esc(r.id)}">キャンセル</button>` : ''}</div></article>`;
}
function emptyState(title, description) {
  return `<div class="empty-state"><div class="empty-icon">${ico('calendar', 28)}</div><h3>${esc(title)}</h3><p>${esc(description)}</p><button class="btn btn-primary" data-action="new-booking">${ico('plus', 17)} 新しい予約</button></div>`;
}
function minePage() {
  const items = state.reservations.filter((r) => mine(r));
  const showUpcoming = state.myFilter === 'upcoming';
  const filtered = items.filter((r) => showUpcoming ? future(r) : !future(r)).sort((a, b) => showUpcoming ? a.start_at.localeCompare(b.start_at) : b.start_at.localeCompare(a.start_at));
  return `<div class="page-heading page-heading--sub"><div><div class="eyebrow">MY BOOKINGS</div><h1>自分の予約</h1><p>予約の詳細確認とキャンセルはこちらから。</p></div><button class="btn btn-primary" data-action="new-booking">${ico('plus', 17)} 新しい予約</button></div><section class="panel list-panel"><div class="list-panel-header"><div><div class="section-kicker">YOUR SCHEDULE</div><h2>予約一覧</h2></div><div class="switcher"><button class="${showUpcoming ? 'active' : ''}" data-action="my-filter" data-value="upcoming">これから</button><button class="${!showUpcoming ? 'active' : ''}" data-action="my-filter" data-value="past">過去</button></div></div><div class="booking-list">${filtered.length ? filtered.map((r) => reservationItem(r)).join('') : emptyState(showUpcoming ? '今後の予約はありません' : '過去の予約はありません', showUpcoming ? 'カレンダーから空き時間を選んで予約できます。' : '過去の予約がここに表示されます。')}</div></section>`;
}
function roomsPage() {
  return `<div class="page-heading page-heading--sub"><div><div class="eyebrow">OUR SPACES</div><h1>部室について</h1><p>予約できるのはサークル共用の部室1室です。予約は7つの時間枠から選びます。</p></div></div><div class="room-cards">${state.rooms.map((room, i) => `<article class="room-card"><div class="room-card-banner room-card-banner--${i % 3}" style="--room-accent:${safeColor(room.color)}"><span class="room-number">SPACE 0${i + 1}</span><span class="room-banner-icon">${ico(i === 1 ? 'spark' : i === 2 ? 'users' : 'door', 40)}</span><span class="room-decor-circle"></span></div><div class="room-card-body"><div class="room-card-heading"><h2>${esc(room.name)}</h2><span class="room-capacity">${ico('users', 16)} ${esc(room.capacity)}人</span></div><p>${esc(room.description)}</p><div class="room-amenities">${(room.amenities || []).map((a) => `<span>${ico('check', 13)} ${esc(a)}</span>`).join('')}</div><button class="btn btn-primary btn-full" data-action="book-room" data-room="${esc(room.id)}">この部室を予約 ${ico('arrow', 17)}</button></div></article>`).join('')}</div>`;
}
function adminPage() {
  if (state.user.role !== 'admin') return '';
  const upcoming = state.reservations.filter(future).sort((a, b) => a.start_at.localeCompare(b.start_at));
  const todayBookings = upcoming.filter((r) => localDay(r.start_at) === localDay(new Date())).length;
  return `<div class="page-heading page-heading--sub"><div><div class="eyebrow">ADMINISTRATION</div><h1>予約の管理</h1><p>部室の予約を確認・キャンセルできます。</p></div></div><div class="admin-stats">${statCard('calendar', '今後の予約', String(upcoming.length), '部室の全予約')}${statCard('clock', '本日の残り予約', String(todayBookings), '開始前の予約のみ')}${statCard('door', '管理中の部室', '01', '固定7枠')}</div><section class="panel list-panel"><div class="list-panel-header"><div><div class="section-kicker">RESERVATION MANAGEMENT</div><h2>予約一覧</h2></div></div><div class="booking-list">${upcoming.length ? upcoming.map((r) => reservationItem(r, true)).join('') : `<div class="empty-state"><div class="empty-icon">${ico('check', 28)}</div><h3>今後の予約はありません</h3><p>新しい予約が入るとここに表示されます。</p></div>`}</div></section><p class="admin-notice">${ico('shield', 17)} 管理者権限は必ずバックエンド側でもチェックしてください。</p>`;
}
function labelSelect(label, name, options, selected, extra = '') {
  return `<label class="field"><span>${label}</span><select name="${name}" ${extra}>${options.map((opt) => `<option value="${esc(opt.value)}" ${opt.disabled ? 'disabled' : ''} ${opt.value === selected ? 'selected' : ''}>${esc(opt.label)}</option>`).join('')}</select></label>`;
}
function bookingModal() {
  const m = state.modal;
  const options = BOOKING_RULES.slots.map((slot, i) => {
    const { booked, past } = slotStatus(m.day, slot);
    return { value: slot.id, label: `${i + 1}枠目　${slot.start}〜${slot.end}${booked ? '（予約済み）' : past ? '（終了）' : ''}`, disabled: Boolean(booked || past) };
  });
  if (!options.some((o) => o.value === m.slotId && !o.disabled)) m.slotId = options.find((o) => !o.disabled)?.value || '';
  const room = state.rooms[0];
  return `<div class="overlay" data-action="overlay"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="booking-modal-title"><div class="modal-head"><div class="modal-head-icon">${ico('calendar', 22)}</div><div><div class="section-kicker">NEW RESERVATION</div><h2 id="booking-modal-title">新しい予約</h2></div><button class="icon-button modal-x" data-action="close-modal" aria-label="閉じる">${ico('close')}</button></div><form id="booking-form" class="modal-form"><div class="field"><label for="booking-title">利用目的 <span class="required">必須</span></label><input id="booking-title" name="title" type="text" maxlength="80" required placeholder="例：バンド練習、運営会議" value="${esc(m.title || '')}" /></div><div class="form-two"><div class="field"><span>部室</span><div class="fixed-room-label">${ico('door', 17)} ${esc(room?.name || 'サークル部室')}</div></div><label class="field"><span>利用日</span><input name="day" data-change="booking-day" type="date" required min="${localDay(new Date())}" value="${esc(m.day)}" /></label></div>${labelSelect('予約枠（1枠ずつ）', 'slot', options, m.slotId, 'required data-change="booking-slot"')}<label class="field"><span>メモ <span class="optional">任意</span></span><textarea name="note" rows="3" maxlength="500" placeholder="利用内容や連絡事項など">${esc(m.note || '')}</textarea></label><div class="form-hint">${ico('info', 16)} 時間は固定です。開始・終了時刻の変更や複数枠をまとめて予約することはできません。</div>${!m.slotId ? '<div class="slot-unavailable-note">この日の予約可能な枠はありません。別の日を選択してください。</div>' : ''}<p class="form-error" data-form-error hidden></p><div class="modal-actions"><button type="button" class="btn btn-outline" data-action="close-modal">戻る</button><button type="submit" class="btn btn-primary" ${!m.slotId ? 'disabled' : ''}>${ico('check', 18)} 予約を確定する</button></div></form></section></div>`;
}
function detailModal() {
  const r = state.reservations.find((x) => x.id === state.modal.id);
  if (!r) return '';
  const room = roomById(r.room_id);
  const canCancel = future(r) && (mine(r) || state.user.role === 'admin');
  return `<div class="overlay" data-action="overlay"><section class="modal modal--detail" role="dialog" aria-modal="true" aria-labelledby="detail-modal-title"><div class="modal-head"><div class="modal-head-icon">${ico('calendar', 22)}</div><div><div class="section-kicker">RESERVATION DETAIL</div><h2 id="detail-modal-title">予約の詳細</h2></div><button class="icon-button modal-x" data-action="close-modal" aria-label="閉じる">${ico('close')}</button></div><div class="detail-body"><span class="tiny-pill" style="--pill-color:${safeColor(room?.color)}">${esc(room?.name || '部室')}</span><h3>${esc(r.title)}</h3><div class="detail-row">${ico('calendar', 18)} <span>${esc(formatLong(r.start_at))}</span></div><div class="detail-row">${ico('clock', 18)} <span>${formatClock(r.start_at)} – ${formatClock(r.end_at)}</span></div><div class="detail-row">${ico('users', 18)} <span>${esc(r.user_name)}${mine(r) ? '（あなた）' : ''}</span></div>${r.note ? `<div class="detail-note"><strong>メモ</strong><p>${esc(r.note)}</p></div>` : ''}<div class="modal-actions"><button class="btn btn-outline" data-action="close-modal">閉じる</button>${canCancel ? `<button class="btn btn-danger" data-action="cancel" data-id="${esc(r.id)}">予約をキャンセル</button>` : ''}</div></div></section></div>`;
}
function loginPage() {
  const registering = !isDemo && state.authView === 'register';
  const form = registering
    ? `<form id="register-form" class="login-form">
      <label class="field"><span>お名前</span><input name="name" type="text" maxlength="100" placeholder="表示名を入力" autocomplete="name" required /></label>
      <label class="field"><span>メールアドレス</span><input name="email" type="email" placeholder="you@example.com" autocomplete="email" required /></label>
      <label class="field"><span>パスワード</span><input name="password" type="password" placeholder="パスワードを設定" autocomplete="new-password" required /></label>
      <label class="field"><span>招待コード</span><input name="invite_code" type="text" placeholder="サークルから共有されたコード" autocomplete="off" required /></label>
      <p class="form-error" data-form-error hidden></p>
      <button class="btn btn-primary login-submit" type="submit">招待コードで登録する ${ico('arrow', 17)}</button>
    </form>`
    : `<form id="login-form" class="login-form">
      <label class="field"><span>メールアドレス</span><input name="email" type="email" placeholder="you@example.com" required autocomplete="username" value="${esc(state.loginEmail || (isDemo ? 'member@example.com' : ''))}" /></label>
      <label class="field"><span>パスワード</span><input name="password" type="password" placeholder="パスワードを入力" required autocomplete="current-password" value="${isDemo ? 'demo1234' : ''}" /></label>
      <p class="form-error" data-form-error hidden></p>
      <button class="btn btn-primary login-submit" type="submit">ログインする ${ico('arrow', 17)}</button>
    </form>`;
  const switcher = isDemo ? '' : `<div class="auth-switch">${registering
    ? '登録済みの方は <button type="button" data-action="show-login">ログイン</button>'
    : '初めて利用する方は <button type="button" data-action="show-register">招待コードで新規登録</button>'}</div>`;
  return `<main class="login-shell"><div class="login-visual"><div class="login-brand"><span class="brand-mark">R<span class="brand-mark-dot"></span></span><span class="brand-word">room<span>base.</span></span></div><div class="login-visual-content"><div class="login-system-line"></div><h1>部室予約システム</h1><p>予約・空き状況の確認</p></div><div class="login-visual-foot">共用部室 <span>·</span> 1日7枠</div></div><div class="login-main"><div class="login-card"><div class="login-toplabel">${registering ? 'アカウント登録' : 'アカウント'} <span class="toplabel-line"></span></div><h2>${registering ? '新規登録' : 'ログイン'}</h2><p class="login-lead">${registering ? 'サークルから共有された招待コードを入力してください。' : 'メールアドレスとパスワードを入力してください。'}</p>${form}${switcher}${isDemo ? `<div class="demo-divider"><span>デモアカウントで試す</span></div><div class="demo-buttons"><button class="btn btn-outline" data-action="demo-login" data-email="member@example.com">${ico('users', 17)} メンバー</button><button class="btn btn-outline" data-action="demo-login" data-email="admin@example.com">${ico('shield', 17)} 管理者</button></div><div class="demo-credentials">パスワード： <code>demo1234</code>　<span>※デモデータはこのブラウザに保存されます</span></div>` : ''}</div><div class="login-footer">© ${new Date().getFullYear()} ROOMBASE</div></div></main>`;
}
function errorPage() {
  return `<div class="error-screen"><div class="error-icon">${ico('alert', 32)}</div><h1>データを読み込めませんでした</h1><p>${esc(state.error)}</p><button class="btn btn-primary" data-action="retry">${ico('refresh', 17)} 再読み込み</button></div>`;
}
function render() {
  if (state.loading) { root.innerHTML = '<div class="boot-loading"><div class="boot-spinner"></div>ROOMBASEを読み込み中…</div>'; return; }
  if (state.error) { root.innerHTML = errorPage(); return; }
  if (!state.user) { root.innerHTML = `${loginPage()}${state.toast ? `<div class="toast">${ico('info', 18)} ${esc(state.toast)}</div>` : ''}`; return; }
  const pages = { calendar: calendarPage, mine: minePage, rooms: roomsPage, admin: adminPage };
  const page = pages[state.page] || calendarPage;
  root.innerHTML = `<div class="app-shell">${sidebar()}${state.mobileMenu ? '<button class="mobile-scrim" data-action="toggle-menu" aria-label="メニューを閉じる"></button>' : ''}<div class="main-shell">${topbar()}<main class="content">${page()}<div class="bottom-copyright">© ${new Date().getFullYear()} ROOMBASE</div></main></div></div>${state.modal ? state.modal.type === 'booking' ? bookingModal() : detailModal() : ''}${state.toast ? `<div class="toast">${ico('check', 18)} ${esc(state.toast)}</div>` : ''}`;
}
function nextAvailableSlot(day, preferredId = '') {
  if (preferredId) {
    const slot = slotById(preferredId);
    if (slot && !slotStatus(day, slot).past && !slotStatus(day, slot).booked) return preferredId;
  }
  return BOOKING_RULES.slots.find((slot) => !slotStatus(day, slot).past && !slotStatus(day, slot).booked)?.id || '';
}
function openBooking(day = localDay(new Date()), slotId = '') {
  let selectedDay = day < localDay(new Date()) ? localDay(new Date()) : day;
  let selectedSlot = nextAvailableSlot(selectedDay, slotId);
  // その日の枠がすべて終了している場合は、翌日を初期表示する。
  if (!selectedSlot && selectedDay === localDay(new Date())) {
    selectedDay = localDay(addDays(new Date(), 1));
    selectedSlot = nextAvailableSlot(selectedDay);
  }
  state.modal = { type: 'booking', roomId: BOOKING_RULES.roomId, day: selectedDay, slotId: selectedSlot, title: '', note: '' };
  render();
  root.querySelector('#booking-title')?.focus();
}
function captureModalInputs() {
  const form = root.querySelector('#booking-form');
  if (!form || !state.modal || state.modal.type !== 'booking') return;
  const data = new FormData(form);
  Object.assign(state.modal, { title: String(data.get('title') || ''), day: String(data.get('day') || ''), slotId: String(data.get('slot') || ''), note: String(data.get('note') || '') });
}
async function doLogin(email, password) {
  try {
    const user = await api.login(email, password);
    state.user = user;
    state.error = '';
    await refreshData();
    state.page = 'calendar';
    state.modal = null;
    notify('ログインしました。');
  } catch (e) { showError(e.message); }
}
async function doRegister(form) {
  const data = new FormData(form);
  const submit = form.querySelector('[type="submit"]');
  submit.disabled = true;
  try {
    const email = String(data.get('email') || '').trim();
    await api.register(
      String(data.get('name') || '').trim(),
      email,
      String(data.get('password') || ''),
      String(data.get('invite_code') || '').trim()
    );
    state.loginEmail = email;
    state.authView = 'login';
    notify('登録が完了しました。設定したパスワードでログインしてください。');
  } catch (e) {
    showError(e.message);
    submit.disabled = false;
  }
}
async function doCancel(id) {
  const r = state.reservations.find((x) => x.id === id);
  if (!r || !window.confirm(`「${r.title}」の予約をキャンセルしますか？`)) return;
  try {
    await api.cancel(id);
    state.modal = null;
    await refreshData();
    notify('予約をキャンセルしました。');
  } catch (e) { showError(e.message); }
}
async function doSubmit(form) {
  const data = new FormData(form);
  const day = String(data.get('day') || '');
  const slot = slotById(String(data.get('slot') || ''));
  if (!slot || !/^\d{4}-\d{2}-\d{2}$/.test(day)) return showError('予約日と時間枠を選択してください。');
  const payload = { room_id: BOOKING_RULES.roomId, title: String(data.get('title') || ''), note: String(data.get('note') || ''), start_at: isoAt(day, slot.start), end_at: isoAt(day, slot.end) };
  const error = validateBooking(payload, state.reservations);
  if (error) return showError(error);
  const submit = form.querySelector('[type="submit"]');
  submit.disabled = true;
  try {
    await api.create(payload);
    state.modal = null;
    state.focus = new Date(payload.start_at);
    state.roomId = payload.room_id;
    await refreshData();
    notify('予約を作成しました。');
  } catch (e) {
    showError(e.status === 409 ? '予約が重複しました。最新の空き状況をご確認ください。' : e.message);
    submit.disabled = false;
    if (e.status === 409) {
      try { await refreshData(); } catch { /* 再取得に失敗しても入力は維持 */ }
    }
  }
}
root.addEventListener('submit', async (event) => {
  if (event.target.id === 'login-form') {
    event.preventDefault();
    const data = new FormData(event.target);
    await doLogin(String(data.get('email')), String(data.get('password')));
  }
  if (event.target.id === 'register-form') { event.preventDefault(); await doRegister(event.target); }
  if (event.target.id === 'booking-form') { event.preventDefault(); await doSubmit(event.target); }
});
root.addEventListener('change', (event) => {
  const el = event.target;
  if (el.dataset.change === 'booking-day' || el.dataset.change === 'booking-slot') {
    captureModalInputs();
    if (el.dataset.change === 'booking-day') state.modal.slotId = nextAvailableSlot(state.modal.day, state.modal.slotId);
    render();
    root.querySelector('select[name="slot"]')?.focus();
  }
});
root.addEventListener('click', async (event) => {
  const target = event.target.closest('[data-action]');
  if (!target) return;
  const act = target.dataset.action;
  if (act === 'overlay' && event.target !== target) return;
  if (act === 'home') { event.preventDefault(); state.page = 'calendar'; state.mobileMenu = false; render(); }
  if (act === 'nav') { state.page = target.dataset.page; state.mobileMenu = false; render(); }
  if (act === 'toggle-menu') { state.mobileMenu = !state.mobileMenu; render(); }
  if (act === 'new-booking') openBooking(localDay(state.focus));
  if (act === 'book-room') openBooking(localDay(new Date()));
  if (act === 'slot') openBooking(target.dataset.day, target.dataset.slot);
  if (act === 'calendar-view') { state.calendarView = target.dataset.value; render(); }
  if (act === 'my-filter') { state.myFilter = target.dataset.value; render(); }
  if (act === 'prev-date' || act === 'next-date') {
    state.focus = addDays(state.focus, (act === 'next-date' ? 1 : -1) * (state.calendarView === 'week' ? 7 : 1));
    try { await refreshData(); render(); } catch (e) { notify(e.message); }
  }
  if (act === 'go-today') { state.focus = new Date(); try { await refreshData(); } catch (e) { notify(e.message); } render(); }
  if (act === 'details') { state.modal = { type: 'detail', id: target.dataset.id }; render(); }
  if (act === 'close-modal' || act === 'overlay') { state.modal = null; render(); }
  if (act === 'cancel') await doCancel(target.dataset.id);
  if (act === 'show-login') { state.authView = 'login'; render(); }
  if (act === 'show-register') { state.authView = 'register'; render(); }
  if (act === 'demo-login') await doLogin(target.dataset.email, 'demo1234');
  if (act === 'logout') {
    try { await api.logout(); state.user = null; state.modal = null; state.mobileMenu = false; notify('ログアウトしました。'); }
    catch (e) { notify(e.message); }
  }
  if (act === 'retry') { state.error = ''; state.loading = true; render(); await boot(); }
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && state.modal) { state.modal = null; render(); } });
boot();
