import { API_BASE_URL, API_MODE } from './config.js';
import { demoApi } from './demo.js';

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api${path}`, {
      ...options,
      credentials: 'include', // 本番では HttpOnly + Secure + SameSite Cookie のセッションを推奨
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new Error('サーバーに接続できません。APIの起動と接続先URLを確認してください。');
  }
  if (!response.ok) {
    let payload = {};
    try { payload = await response.json(); } catch { /* 非JSONエラーを許容 */ }
    const detail = payload.detail;
    const msg = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((issue) => `${(issue.loc || []).slice(1).join('.') || '入力値'}: ${issue.msg || '入力内容を確認してください'}`).join(' / ')
        : (payload.message || `エラーが発生しました (${response.status})`);
    const error = new Error(msg);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}
const serverApi = {
  async me() {
    try { return (await request('/auth/me')).user; }
    catch (e) { if (e.status === 401) return null; throw e; }
  },
  async login(email, password) { return (await request('/auth/login', { method: 'POST', body: { email, password } })).user; },
  async register(name, email, password, inviteCode) { return (await request('/auth/register', { method: 'POST', body: { name, email, password, invite_code: inviteCode } })).user; },
  async logout() { await request('/auth/logout', { method: 'POST' }); },
  async rooms() { return (await request('/rooms')).rooms; },
  async reservations(from, to) { return (await request(`/reservations?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`)).reservations; },
  async create(data) { return (await request('/reservations', { method: 'POST', body: data })).reservation; },
  async cancel(id) { await request(`/reservations/${encodeURIComponent(id)}`, { method: 'DELETE' }); },
};
export const api = API_MODE === 'server' ? serverApi : demoApi;
export const isDemo = API_MODE === 'demo';
