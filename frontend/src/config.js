// FastAPI接続版。デモに戻す場合は 'demo' に変更。
export const API_MODE = 'server'; // 'demo' | 'server'
// ローカルのフロントエンド用HTTPサーバーでは、FastAPI(8000)に接続。
// 本番ではフロントエンドとAPIを同一Originで配信するため、そのOriginを利用する。
// Node.jsでフロントエンドの単体テストを実行する場合はローカル設定を使用。
const currentOrigin = typeof window !== 'undefined' ? window.location.origin : null;
export const API_BASE_URL =
  currentOrigin === 'http://localhost:5173'
    ? 'http://localhost:8000'
    : (currentOrigin ?? 'http://localhost:8000');

// 部室は1室・予約は下記の7枠のみ。複数枠をまとめた予約は不可。
// バックエンド側にも同じルールを必ず実装してください。
export const BOOKING_RULES = Object.freeze({
  roomId: 'main',
  timeZone: 'Asia/Tokyo',
  slots: Object.freeze([
    Object.freeze({ id: '1', start: '08:50', end: '10:30' }),
    Object.freeze({ id: '2', start: '10:40', end: '12:20' }),
    Object.freeze({ id: '3', start: '12:20', end: '13:10' }),
    Object.freeze({ id: '4', start: '13:10', end: '14:50' }),
    Object.freeze({ id: '5', start: '15:05', end: '16:45' }),
    Object.freeze({ id: '6', start: '17:00', end: '18:40' }),
    Object.freeze({ id: '7', start: '18:55', end: '20:35' }),
  ]),
});
