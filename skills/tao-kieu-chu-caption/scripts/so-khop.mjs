// SO KHỚP CHI TIẾT với một khung video mẫu, rồi TỰ TỐI ƯU cho tới khi khớp.
//
// Vì sao cần: đo khung bao ngoài cùng (rộng bao nhiêu, cao bao nhiêu) là phép đo THÔ.
// Hai dòng chữ có thể trùng mép ngoài mà bên trong lệch hoàn toàn - sai font, sai khoảng
// cách chữ, sai độ dày nét. Bộ này so TỪNG ĐIỂM ẢNH: chồng hai hình chữ lên nhau rồi
// đếm phần trùng trên phần tổng (gọi là ĐỘ TRÙNG).
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { napKieuChu, raASS, fileASS, doiHoaThuong, theoKhung, coChu } from './kieu-chu.mjs';
import { chuanBiFont } from './font-cho-ffmpeg.mjs';

const TAM = join(tmpdir(), 'kieu-chu-so-khop');

// ---------- đọc ảnh thành mảng xám ----------
function docAnhXam(duongDan, rong, cao) {
  if (!existsSync(TAM)) mkdirSync(TAM, { recursive: true });
  const ra = join(TAM, '_anh.raw');
  execFileSync('ffmpeg', ['-y', '-i', duongDan, '-vf', `scale=${rong}:${cao},format=gray`,
    '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', ra], { stdio: 'pipe' });
  return readFileSync(ra);
}

// ---------- tách hình chữ khỏi khung mẫu ----------
// Chữ phụ đề luôn sáng hơn hẳn nền quanh nó. Lấy các điểm sáng trong dải hàng
// mà người dùng chỉ ra (hoặc tự tìm dải có nhiều điểm sáng nhất).
export function tachChuMau(duongDan, rong, cao, vung) {
  const xam = docAnhXam(duongDan, rong, cao);
  const nguong = 200;
  let y0 = 0, y1 = cao;
  if (vung) { y0 = vung.y; y1 = vung.y + vung.cao; }
  else {
    // tự tìm: chia khung thành các dải cao 40px, chọn dải nhiều điểm sáng nhất
    let tot = { dem: 0, y: 0 };
    for (let y = Math.round(cao * 0.35); y < cao - 40; y += 10) {
      let dem = 0;
      for (let yy = y; yy < y + 40; yy++) for (let x = 0; x < rong; x++) if (xam[yy * rong + x] > nguong) dem++;
      if (dem > tot.dem) tot = { dem, y };
    }
    y0 = Math.max(0, tot.y - 90); y1 = Math.min(cao, tot.y + 130);
  }
  const mat = new Uint8Array(rong * cao);
  for (let y = y0; y < y1; y++) for (let x = 0; x < rong; x++) {
    if (xam[y * rong + x] > nguong) mat[y * rong + x] = 1;
  }
  return mat;
}

// ---------- dựng chữ của mình thành hình ----------
export function dungChuCuaMinh(k, chu, cheDo, rong, cao) {
  if (!existsSync(TAM)) mkdirSync(TAM, { recursive: true });
  const r = raASS(k, cheDo);
  const cot = r.style.split(',');
  cot[15] = 1; cot[16] = 0; cot[17] = 0;    // bỏ viền, bóng, khối nền - chỉ lấy nét chữ
  const noiDung = fileASS([], [
    `Dialogue: 0,0:00:00.00,0:00:05.00,${k.ten},,0,0,0,,${doiHoaThuong(chu, cheDo)}`,
  ], rong, cao).replace('[Events]', cot.join(',') + '\n\n[Events]');
  writeFileSync(join(TAM, '_m.ass'), noiDung, 'utf8');
  execFileSync('ffmpeg', ['-y', '-f', 'lavfi', '-i', `color=c=black:s=${rong}x${cao}`,
    '-vf', 'subtitles=_m.ass' + chuanBiFont(k, TAM) + ',format=gray', '-frames:v', '1',
    '-f', 'rawvideo', '-pix_fmt', 'gray', '_m.raw'], { stdio: 'pipe', cwd: TAM });
  const b = readFileSync(join(TAM, '_m.raw'));
  const mat = new Uint8Array(rong * cao);
  for (let i = 0; i < mat.length; i++) if (b[i] > 128) mat[i] = 1;
  return mat;
}

// ---------- khung bao quanh hình chữ ----------
export function khungBao(mat, rong, cao) {
  let x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1, dem = 0;
  for (let y = 0; y < cao; y++) for (let x = 0; x < rong; x++) if (mat[y * rong + x]) {
    dem++; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
  }
  return dem ? { x0, x1, y0, y1, rong: x1 - x0 + 1, cao: y1 - y0 + 1, dem } : null;
}

// ---------- so hai hình chữ, sau khi đã kéo về trùng tâm ----------
export function soHaiHinh(matA, matB, rong, cao) {
  const a = khungBao(matA, rong, cao), b = khungBao(matB, rong, cao);
  if (!a || !b) return null;
  // kéo hình của mình về trùng tâm hình mẫu, để chỉ còn so HÌNH DÁNG
  const dx = Math.round((a.x0 + a.x1) / 2 - (b.x0 + b.x1) / 2);
  const dy = Math.round((a.y0 + a.y1) / 2 - (b.y0 + b.y1) / 2);
  let trung = 0, tong = 0;
  for (let y = 0; y < cao; y++) for (let x = 0; x < rong; x++) {
    const va = matA[y * rong + x];
    const xb = x - dx, yb = y - dy;
    const vb = (xb >= 0 && xb < rong && yb >= 0 && yb < cao) ? matB[yb * rong + xb] : 0;
    if (va || vb) tong++;
    if (va && vb) trung++;
  }
  return {
    doTrung: tong ? trung / tong : 0,
    mau: a, minh: b,
    lechNgang: (b.rong - a.rong) / a.rong,
    lechCao: (b.cao - a.cao) / a.cao,
    lechNetDay: (b.dem / (b.rong * b.cao)) / (a.dem / (a.rong * a.cao)) - 1,
    lechTamNgang: dx, lechTamDoc: dy,
  };
}

// ---------- lưu ảnh để NHÌN máy đang so cái gì ----------
// Đỏ = chữ mẫu · Xanh lá = chữ của mình · Vàng = phần trùng nhau.
export function luuAnhSoSanh(matMau, matMinh, rong, cao, duongDan, keoVeTrungTam = true) {
  const a = khungBao(matMau, rong, cao), b = khungBao(matMinh, rong, cao);
  let dx = 0, dy = 0;
  if (keoVeTrungTam && a && b) {
    dx = Math.round((a.x0 + a.x1) / 2 - (b.x0 + b.x1) / 2);
    dy = Math.round((a.y0 + a.y1) / 2 - (b.y0 + b.y1) / 2);
  }
  const anh = Buffer.alloc(rong * cao * 3);
  for (let y = 0; y < cao; y++) for (let x = 0; x < rong; x++) {
    const i = (y * rong + x) * 3;
    const va = matMau[y * rong + x];
    const xb = x - dx, yb = y - dy;
    const vb = (xb >= 0 && xb < rong && yb >= 0 && yb < cao) ? matMinh[yb * rong + xb] : 0;
    if (va && vb) { anh[i] = 255; anh[i + 1] = 220; anh[i + 2] = 0; }
    else if (va) { anh[i] = 255; anh[i + 1] = 40; anh[i + 2] = 40; }
    else if (vb) { anh[i] = 40; anh[i + 1] = 230; anh[i + 2] = 80; }
  }
  const raw = join(TAM, '_ss.raw');
  writeFileSync(raw, anh);
  execFileSync('ffmpeg', ['-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', `${rong}x${cao}`,
    '-i', raw, duongDan], { stdio: 'pipe' });
}

// ---------- báo cáo dễ đọc ----------
export function inBaoCao(kq, ten) {
  const pt = (x) => (x * 100).toFixed(1) + '%';
  console.log(`\n  ĐỘ TRÙNG: ${pt(kq.doTrung)}   ${kq.doTrung > 0.85 ? '(khớp tốt)' : kq.doTrung > 0.7 ? '(tạm được)' : '(CHƯA KHỚP)'}`);
  console.log(`  Bề ngang : mẫu ${kq.mau.rong}px · của mình ${kq.minh.rong}px · lệch ${pt(kq.lechNgang)}`);
  console.log(`  Chiều cao: mẫu ${kq.mau.cao}px · của mình ${kq.minh.cao}px · lệch ${pt(kq.lechCao)}`);
  console.log(`  Độ dày nét: lệch ${pt(kq.lechNetDay)} ${Math.abs(kq.lechNetDay) > 0.12 ? '<- font sai độ đậm' : ''}`);
  console.log(`  Lệch tâm : ngang ${kq.lechTamNgang}px · dọc ${kq.lechTamDoc}px`);
  if (kq.doTrung < 0.85) {
    console.log('\n  Chỗ cần sửa:');
    if (Math.abs(kq.lechCao) > 0.03) console.log(`   - cỡ chữ ${kq.lechCao > 0 ? 'to' : 'nhỏ'} quá ${pt(Math.abs(kq.lechCao))}`);
    if (Math.abs(kq.lechNgang - kq.lechCao) > 0.05) console.log(`   - bề ngang lệch riêng ${pt(kq.lechNgang - kq.lechCao)} -> sai font hoặc cần chỉnh bóp ngang`);
    if (Math.abs(kq.lechNetDay) > 0.12) console.log(`   - nét chữ ${kq.lechNetDay > 0 ? 'dày' : 'mảnh'} hơn mẫu -> đổi sang bản font ${kq.lechNetDay > 0 ? 'nhẹ' : 'đậm'} hơn`);
    if (Math.abs(kq.lechTamDoc) > 6) console.log(`   - đặt lệch dọc ${kq.lechTamDoc}px -> chỉnh vi_tri.tam_doc`);
  }
}
