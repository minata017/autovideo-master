// ffmpeg chỉ nhìn thấy font ĐÃ CÀI vào hệ điều hành. File font để trong thư mục
// fonts/ của skill thì nó KHÔNG thấy - dựng ra sẽ lặng lẽ thay bằng font khác,
// không báo lỗi, người dùng chỉ thấy "chữ trông lạ lạ".
//
// Cách chữa: chép file font sang chỗ ffmpeg sắp chạy rồi bảo nó tìm font ở ngay đó.
// Nhờ vậy chuyển giao chỉ cần thả font vào fonts/, không phải cài vào máy.
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, basename } from 'node:path';

export function chuanBiFont(dsKieu, thuMucChay) {
  if (!existsSync(thuMucChay)) mkdirSync(thuMucChay, { recursive: true });
  let coFont = false;
  for (const k of [].concat(dsKieu)) {
    const nguon = k?._do?.duongDan;
    if (!nguon || !existsSync(nguon)) continue;
    const dich = join(thuMucChay, basename(nguon));
    try { if (!existsSync(dich)) copyFileSync(nguon, dich); coFont = true; } catch { /* bỏ qua */ }
  }
  // "fontsdir=." = tìm font ngay trong thư mục đang chạy ffmpeg
  return coFont ? ':fontsdir=.' : '';
}
