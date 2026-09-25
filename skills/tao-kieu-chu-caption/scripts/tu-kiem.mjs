// TỰ KIỂM: dựng thật từng kiểu chữ × từng chế độ rồi ĐO bề ngang trên ảnh đã dựng.
// Không tin phép tính - chỉ tin số đo trên hàng thật.
import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { napKieuChu, coChu, CHE_DO_CHU } from './kieu-chu.mjs';
import { doBeNgangThat, beNgangDich, doCaoChuHoaThat } from './do-tren-anh.mjs';
import { kiemDauViet } from './do-font.mjs';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..');
const TAM = join(GOC, 'out', '_tu-kiem');
const CAU_42 = 'Anh ấy đã về nhà lúc trời vừa sẩm tối rồi.';
const RONG = 1920, CAO = 1080;
const DICH = RONG * 0.8;      // bề ngang cần đạt
const DUNG_SAI = 0.03;        // lệch quá 3% là hỏng

if (existsSync(TAM)) rmSync(TAM, { recursive: true, force: true });
mkdirSync(TAM, { recursive: true });

// Đo bề ngang thật của chữ trên khung đã dựng: gom cả khung thành 1 hàng rồi
// tìm cột sáng đầu tiên và cuối cùng.
function doTrenAnh(tenAss) {
  execFileSync('ffmpeg', ['-y', '-f', 'lavfi', '-i', `color=c=black:s=${RONG}x${CAO}`,
    '-vf', `subtitles=${tenAss},crop=${RONG}:300:0:${CAO / 2 - 150},format=gray,scale=${RONG}:1:flags=area`,
    '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '_cot.raw'], { stdio: 'pipe', cwd: TAM });
  const b = readFileSync(join(TAM, '_cot.raw'));
  let dau = -1, cuoi = -1;
  for (let i = 0; i < b.length; i++) if (b[i] > 1) { if (dau < 0) dau = i; cuoi = i; }
  return dau < 0 ? 0 : cuoi - dau + 1;
}

const thuMucKieu = join(GOC, 'kieu-chu');
const dsKieu = readdirSync(thuMucKieu).filter((f) => f.endsWith('.json'))
  .map((f) => napKieuChu(JSON.parse(readFileSync(join(thuMucKieu, f), 'utf8'))));

let dat = 0, hong = 0;
const loi = [];

console.log('BÀI 1 - Font có đủ dấu tiếng Việt không\n');
for (const k of dsKieu) {
  const r = kiemDauViet(k._do);
  console.log(`  ${r.dat ? 'ĐẠT ' : 'HỎNG'} ${k.ten.padEnd(16)} ${k.font.ten_day_du}${r.dat ? '' : ` - thiếu ${r.thieu.length} ký tự`}`);
  r.dat ? dat++ : (hong++, loi.push(`${k.ten}: font thiếu dấu tiếng Việt`));
}

console.log('\nBÀI 2 - Cỡ chữ dựng ra có đúng mốc đã khai không\n');
for (const k of dsKieu) {
  // Mỗi cách chuẩn cỡ có mốc kiểm riêng - áp nhầm mốc là báo hỏng oan.
  if (k.chuan_co.kieu === 'cao-chu') {
    const dich = k.khung.cao * k.chuan_co.ti_le;
    const doDuoc = doCaoChuHoaThat(k);
    const lech = Math.abs(doDuoc - dich) / dich;
    const ok = lech <= 0.05;
    console.log(`  ${ok ? 'ĐẠT ' : 'HỎNG'} ${k.ten.padEnd(15)} chiều cao chữ hoa -> dựng ra ${doDuoc}px / cần ` +
      `${dich.toFixed(1)}px (lệch ${(lech * 100).toFixed(1)}%)`);
    ok ? dat++ : (hong++, loi.push(`${k.ten}: cao chữ hoa ${doDuoc}px, cần ${dich.toFixed(1)}px`));
    // thẻ ngắn kiểu reel: kiểm 5 từ không tràn vùng an toàn
    const the = 'CHUYỆN NÀY AI CŨNG GẶP';
    const rongThe = doBeNgangThat(k, the, k.hoa_thuong);
    const okThe = rongThe <= beNgangDich(k, 0.9);
    console.log(`  ${okThe ? 'ĐẠT ' : 'HỎNG'} ${k.ten.padEnd(15)} thẻ 5 từ       -> ${rongThe}px / được phép ${Math.round(beNgangDich(k, 0.9))}px`);
    okThe ? dat++ : (hong++, loi.push(`${k.ten}: thẻ 5 từ tràn (${rongThe}px)`));
    continue;
  }
  // kiểu có khối nền thì nét chữ được ít chỗ hơn, vì khối nền cũng ăn vào vùng an toàn
  const dich = beNgangDich(k, 0.8);
  for (const cheDo of CHE_DO_CHU) {
    const doDuoc = doBeNgangThat(k, CAU_42, cheDo);
    const lech = (dich - doDuoc) / dich;
    const ok = doDuoc <= dich && lech <= DUNG_SAI;
    console.log(`  ${ok ? 'ĐẠT ' : 'HỎNG'} ${k.ten.padEnd(15)} ${cheDo.padEnd(8)} cỡ ${String(coChu(k, cheDo)).padStart(3)}px` +
      ` -> dựng ra ${String(doDuoc).padStart(4)}px / được phép ${Math.round(dich)}px (${doDuoc > dich ? 'TRÀN' : 'hụt'} ${Math.abs(lech * 100).toFixed(1)}%)`);
    ok ? dat++ : (hong++, loi.push(`${k.ten}/${cheDo}: dựng ra ${doDuoc}px, mốc ${Math.round(dich)}px`));
  }
}

console.log(`\n${'='.repeat(60)}\nKẾT QUẢ: ${dat} đạt · ${hong} hỏng`);
if (hong) { console.log('\nCÁC LỖI:'); loi.forEach((l) => console.log(`  - ${l}`)); }
rmSync(TAM, { recursive: true, force: true });
process.exit(hong ? 1 : 0);
