// Đo bề ngang THẬT của chữ bằng cách dựng ra ảnh rồi đếm cột sáng.
// Dùng chung cho bộ chuẩn cỡ chữ và bài tự kiểm - một cách đo duy nhất, không lệch nhau.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { raASS, fileASS, doiHoaThuong } from './kieu-chu.mjs';
import { chuanBiFont } from './font-cho-ffmpeg.mjs';

const RONG = 1920, CAO = 1080;
const TAM = join(tmpdir(), 'kieu-chu-caption-do');

// Dựng một câu bằng kiểu chữ đã cho rồi trả về bề ngang phần NÉT CHỮ (px).
// Bỏ viền và khối nền khi đo, vì hai thứ đó lan ra ngoài nét chữ.
export function doBeNgangThat(k, cau, cheDo) {
  if (!existsSync(TAM)) mkdirSync(TAM, { recursive: true });
  const rong = k.khung?.rong ?? RONG, cao = k.khung?.cao ?? CAO;
  const r = raASS(k, cheDo);
  const cot = r.style.split(',');
  cot[15] = 1;  // kiểu viền thường (bỏ khối nền)
  cot[16] = 0;  // bỏ viền
  cot[17] = 0;  // bỏ bóng
  const chu = doiHoaThuong(cau, cheDo);
  const noiDung = fileASS([], [
    `Dialogue: 0,0:00:00.00,0:00:05.00,${k.ten},,0,0,0,,{\\an5\\pos(${rong / 2},${cao / 2})}${chu}`,
  ], rong, cao).replace('[Events]', cot.join(',') + '\n\n[Events]');

  const tenAss = '_do.ass';
  writeFileSync(join(TAM, tenAss), noiDung, 'utf8');
  execFileSync('ffmpeg', ['-y', '-f', 'lavfi', '-i', `color=c=black:s=${rong}x${cao}`,
    '-vf', `subtitles=${tenAss}${chuanBiFont(k, TAM)},crop=${rong}:340:0:${cao / 2 - 170},format=gray,scale=${rong}:1:flags=area`,
    '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '_cot.raw'], { stdio: 'pipe', cwd: TAM });

  const b = readFileSync(join(TAM, '_cot.raw'));
  let dau = -1, cuoi = -1;
  for (let i = 0; i < b.length; i++) if (b[i] > 1) { if (dau < 0) dau = i; cuoi = i; }
  return dau < 0 ? 0 : cuoi - dau + 1;
}

// Bề ngang mà phần NÉT CHỮ được phép chiếm (đã trừ đệm khối nền)
export function beNgangDich(k, tiLeAnToan = 0.8) {
  return (k.khung?.rong ?? RONG) * tiLeAnToan - (k.nen ? (k.nen.dem || 0) * 2 : 0);
}

// Đo CHIỀU CAO CHỮ HOA thật khi dựng ra (px, theo khung của kiểu chữ).
export function doCaoChuHoaThat(k) {
  if (!existsSync(TAM)) mkdirSync(TAM, { recursive: true });
  const rong = k.khung?.rong ?? RONG, cao = k.khung?.cao ?? CAO;
  const r = raASS(k, 'hoa');
  const cot = r.style.split(',');
  cot[15] = 1; cot[16] = 0; cot[17] = 0;   // bỏ viền, bỏ bóng, bỏ khối nền
  cot[19] = cot[20] = cot[21] = 0;         // bỏ lề để chữ nằm giữa khung
  cot[18] = 5;                             // canh giữa khung
  const noiDung = fileASS([], [
    `Dialogue: 0,0:00:00.00,0:00:05.00,${k.ten},,0,0,0,,{\\an5\\pos(${rong / 2},${cao / 2})}HEX`,
  ], rong, cao).replace('[Events]', cot.join(',') + '\n\n[Events]');

  writeFileSync(join(TAM, '_cao.ass'), noiDung, 'utf8');
  execFileSync('ffmpeg', ['-y', '-f', 'lavfi', '-i', `color=c=black:s=${rong}x${cao}`,
    '-vf', `subtitles=_cao.ass${chuanBiFont(k, TAM)},format=gray,scale=1:${cao}:flags=area`,
    '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '_hang.raw'], { stdio: 'pipe', cwd: TAM });

  const b = readFileSync(join(TAM, '_hang.raw'));
  let dau = -1, cuoi = -1;
  for (let i = 0; i < b.length; i++) if (b[i] > 1) { if (dau < 0) dau = i; cuoi = i; }
  return dau < 0 ? 0 : cuoi - dau + 1;
}

// Hệ số quy đổi cỡ chữ thiết kế -> cỡ chữ ghi trong file ASS.
// PHẢI ĐO, không suy từ bảng số đo trong font: mỗi font khai một kiểu, có font
// khớp có font lệch tới 25%. Đo một lần rồi ghi lại vào kiểu chữ.
export function doHeSoASS(k, napLai) {
  const dich = coChuThietKe(k) * k._do.tiLeCaoChuHoa;
  let heSo = k._he_so_ass ?? k._do.heSoASS;
  for (let vong = 0; vong < 6; vong++) {
    const thu = napLai(heSo);
    const caoThat = doCaoChuHoaThat(thu);
    if (!caoThat) break;
    const lech = Math.abs(caoThat - dich) / dich;
    if (lech <= 0.004) break;
    heSo = heSo * (dich / caoThat);
  }
  return Math.round(heSo * 10000) / 10000;
}

function coChuThietKe(k) {
  return k.co_chu?.hoa ?? k.co_chu?.nguyen ?? 72;
}
