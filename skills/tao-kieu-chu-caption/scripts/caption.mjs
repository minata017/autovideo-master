#!/usr/bin/env node
// CÔNG CỤ DÒNG LỆNH cho kho kiểu chữ phụ đề.
// Mọi skill / agent / AI khác gọi được bằng lệnh, không cần biết gì bên trong.
//
//   node caption.mjs liet-ke
//   node caption.mjs xem <kiểu> [--che-do hoa|thuong|hoa_dau|nguyen]
//   node caption.mjs xuat <kiểu> --dich ass|css|drawtext [--che-do ...] [--phu-de a.srt]
//   node caption.mjs nuong <video> <phụ đề.srt> <kiểu> [--ra out.mp4] [--che-do ...]
//   node caption.mjs nhan-ban <kiểu gốc> --ten <tên mới> [--mau ... --vien ... --nen ...]
//   node caption.mjs chuan-co [<kiểu>]        (đo lại cỡ chữ chuẩn Netflix)
//   node caption.mjs kiem-font <file font>    (kiểm đủ dấu tiếng Việt)
import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname, basename, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { napKieuChu, raCSS, raCSSLopDuoi, raASS, raDrawtext, fileASS, doiHoaThuong,
         coChu, beNgangCau, theoKhung, CHE_DO_CHU, TEN_CHE_DO } from './kieu-chu.mjs';
import { napFont, kiemDauViet } from './do-font.mjs';
import { doBeNgangThat, beNgangDich, doHeSoASS } from './do-tren-anh.mjs';
import { timFont, moiFont } from './tim-font.mjs';
import { tachChuMau, dungChuCuaMinh, soHaiHinh, inBaoCao, khungBao } from './so-khop.mjs';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..');
const CAU_42 = 'Anh ấy đã về nhà lúc trời vừa sẩm tối rồi.';
const RONG = 1920, CAO = 1080, TI_LE_AN_TOAN = 0.8;

// ---------- kho kiểu chữ: kho riêng của người dùng đè lên kho mặc định đi kèm skill ----------
// Kho mặc định nằm trong skill (để chuyển giao trọn gói).
// Kho riêng nằm ngoài skill (để nâng cấp skill không xoá mất kiểu tự tạo).
const KHO_MAC_DINH = join(GOC, 'kieu-chu');
const KHO_RIENG = process.env.KHO_KIEU_CHU || join(process.env.USERPROFILE || process.env.HOME || GOC, '.kho-kieu-chu');

function dsKho() {
  const ra = new Map();
  for (const kho of [KHO_MAC_DINH, KHO_RIENG]) {
    if (!existsSync(kho)) continue;
    for (const f of readdirSync(kho).filter((x) => x.endsWith('.json'))) {
      ra.set(basename(f, '.json'), { duongDan: join(kho, f), rieng: kho === KHO_RIENG });
    }
  }
  return ra;
}

function docKieu(ten) {
  const kho = dsKho();
  if (!kho.has(ten)) {
    const co = [...kho.keys()].join(', ');
    throw new Error(`Không có kiểu chữ "${ten}". Kho đang có: ${co || '(trống)'}`);
  }
  return napKieuChu(JSON.parse(readFileSync(kho.get(ten).duongDan, 'utf8')));
}

// ---------- đọc tham số dòng lệnh ----------
function docThamSo(argv) {
  const t = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) t[argv[i].slice(2)] = (argv[i + 1] && !argv[i + 1].startsWith('--')) ? argv[++i] : true;
    else t._.push(argv[i]);
  }
  return t;
}

// ---------- đọc phụ đề .srt ----------
function docSRT(duongDan) {
  const raw = readFileSync(duongDan, 'utf8').replace(/\r/g, '');
  const khoi = raw.split(/\n\n+/).map((b) => b.trim()).filter(Boolean);
  return khoi.map((b) => {
    const d = b.split('\n');
    const iGio = d.findIndex((x) => x.includes('-->'));
    if (iGio < 0) return null;
    const [dau, cuoi] = d[iGio].split('-->').map((s) => s.trim().replace(',', '.'));
    return { dau: gioASS(dau), cuoi: gioASS(cuoi), chu: d.slice(iGio + 1).join('\\N') };
  }).filter(Boolean);
}
const gioASS = (s) => {
  const m = s.match(/(\d+):(\d+):(\d+)[.,](\d+)/);
  if (!m) return '0:00:00.00';
  return `${+m[1]}:${m[2]}:${m[3]}.${m[4].slice(0, 2).padEnd(2, '0')}`;
};

// Hỏi ffprobe kích thước thật của video
function khungCuaVideo(duongDan) {
  const ra = execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x', resolve(duongDan)],
    { encoding: 'utf8' }).trim().split('\n')[0];
  const [rong, cao] = ra.split('x').map(Number);
  if (!rong || !cao) throw new Error(`Không đọc được kích thước video: ${duongDan}`);
  return { rong, cao };
}

// Đọc "1080x1920" từ tham số --khung
function docKhung(chuoi) {
  const m = String(chuoi).match(/(\d+)\s*[xX*]\s*(\d+)/);
  if (!m) throw new Error('Khung phải ghi kiểu --khung 1080x1920');
  return { rong: +m[1], cao: +m[2] };
}

// ================= các lệnh =================
const LENH = {};

LENH['liet-ke'] = () => {
  const kho = dsKho();
  if (!kho.size) return console.log('Kho kiểu chữ đang trống.');
  console.log(`Kho kiểu chữ (${kho.size} kiểu):\n`);
  for (const [ten, tt] of kho) {
    const k = docKieu(ten);
    const nguon = tt.rieng ? 'tự tạo' : 'đi kèm';
    console.log(`  ${ten.padEnd(18)} [${nguon}]  ${k.mo_ta || ''}`);
    console.log(`  ${' '.repeat(18)} cỡ chữ: ${CHE_DO_CHU.map((c) => `${c} ${coChu(k, c)}px`).join(' · ')}`);
  }
};

LENH['xem'] = (t) => {
  const k = docKieu(t._[0]);
  const cheDo = t['che-do'] || k.hoa_thuong || 'nguyen';
  const raDir = t.ra ? dirname(resolve(t.ra)) : join(GOC, 'out');
  if (!existsSync(raDir)) mkdirSync(raDir, { recursive: true });
  const anh = t.ra ? resolve(t.ra) : join(raDir, `xem-${k.ten}-${cheDo}.png`);
  dungAnhXemTruoc([k], cheDo, anh);
  console.log(`Đã dựng ảnh xem trước: ${anh}`);
};

LENH['xuat'] = (t) => {
  let k = docKieu(t._[0]);
  // quy về đúng kích thước video sẽ dùng, nếu không chữ sẽ sai cỡ
  if (t.khung) { const g = docKhung(t.khung); k = theoKhung(k, g.rong, g.cao); }
  else if (t.video) { const g = khungCuaVideo(t.video); k = theoKhung(k, g.rong, g.cao); }
  const cheDo = t['che-do'] || k.hoa_thuong || 'nguyen';
  const dich = t.dich || 'ass';
  if (dich === 'css') {
    const duoi = raCSSLopDuoi(k);
    console.log(`.phu-de {\n  ${raCSS(k, cheDo)}\n}` + (duoi ? `\n.phu-de::before {\n  ${duoi}\n}` : ''));
  } else if (dich === 'drawtext') {
    const r = raDrawtext(k, t.chu || CAU_42, '(w-text_w)/2', 'h-th-120', cheDo);
    r.canhBao.forEach((c) => console.error(`  ! ${c}`));
    console.log(r.loc);
  } else {
    const dong = t['phu-de']
      ? docSRT(t['phu-de']).map((p) => `Dialogue: 0,${p.dau},${p.cuoi},${k.ten},,0,0,0,,${doiHoaThuong(p.chu, cheDo)}`)
      : [`Dialogue: 0,0:00:00.00,0:00:05.00,${k.ten},,0,0,0,,${doiHoaThuong(t.chu || CAU_42, cheDo)}`];
    const r = raASS(k, cheDo);
    r.canhBao.forEach((c) => console.error(`  ! ${c}`));
    const noiDung = fileASS([{ ...k, hoa_thuong: cheDo }], dong, k.khung.rong, k.khung.cao);
    if (t.ra) { writeFileSync(resolve(t.ra), noiDung, 'utf8'); console.log(`Đã ghi: ${resolve(t.ra)}`); }
    else console.log(noiDung);
  }
};

LENH['nuong'] = (t) => {
  const [video, phuDe, tenKieu] = t._;
  if (!video || !phuDe || !tenKieu) throw new Error('Cách dùng: nuong <video> <phụ đề.srt> <kiểu>');
  // quy kiểu chữ về đúng kích thước video này trước khi dựng
  const g = khungCuaVideo(video);
  const k = theoKhung(docKieu(tenKieu), g.rong, g.cao);
  const cheDo = t['che-do'] || k.hoa_thuong || 'nguyen';
  console.log(`Video ${g.rong}x${g.cao} · kiểu ${k.ten} · chế độ ${TEN_CHE_DO[cheDo]} · cỡ chữ ${coChu(k, cheDo)}px`);
  const ra = resolve(t.ra || video.replace(/\.(\w+)$/, '-phu-de.$1'));
  const tam = join(dirname(ra), `_${k.ten}-${cheDo}.ass`);
  const dong = docSRT(phuDe).map((p) => `Dialogue: 0,${p.dau},${p.cuoi},${k.ten},,0,0,0,,${doiHoaThuong(p.chu, cheDo)}`);
  writeFileSync(tam, fileASS([{ ...k, hoa_thuong: cheDo }], dong, g.rong, g.cao), 'utf8');
  execFileSync('ffmpeg', ['-y', '-i', resolve(video), '-vf', `subtitles=${basename(tam)}`,
    '-c:a', 'copy', ra], { stdio: 'inherit', cwd: dirname(tam) });
  console.log(`\nXong: ${ra}`);
};

LENH['nhan-ban'] = (t) => {
  const goc = docKieu(t._[0]);
  const tenMoi = t.ten;
  if (!tenMoi) throw new Error('Thiếu --ten <tên kiểu mới>');
  const moi = JSON.parse(JSON.stringify({ ...goc }));
  delete moi._do; delete moi._loiFont;
  moi.ten = tenMoi;
  moi.mo_ta = t['mo-ta'] || `Nhân bản từ ${goc.ten}. ${goc.mo_ta || ''}`.trim();
  if (t.mau) moi.mau_chu = t.mau;
  if (t.font) moi.font = { ...moi.font, file: t.font };
  if (t.vien) moi.vien = t.vien === 'khong' ? [] : [{ day: Number(t.vien), mau: t['mau-vien'] || '#000000' }];
  if (t.nen) moi.nen = t.nen === 'khong' ? null : { mau: t.nen, do_dam: Number(t['nen-mo'] || 0.72), dem: 28, bo_goc: 14 };
  if (t['gradient-tu']) moi.gradient = { tu: t['gradient-tu'], den: t['gradient-den'] || t['gradient-tu'], goc: 180 };
  if (t['bo-gradient']) moi.gradient = null;
  delete moi.font.ten_day_du;

  // kiểm trùng: kho đầy kiểu na ná nhau thì không ai tìm được gì
  const kho = dsKho();
  if (kho.has(tenMoi)) throw new Error(`Kho đã có kiểu tên "${tenMoi}". Đổi tên khác hoặc xoá cái cũ trước.`);
  const vanTay = (x) => JSON.stringify([x.font.file, x.mau_chu, x.gradient, x.vien, x.nen, x.hoa_thuong, x.gian_chu]);
  for (const [ten] of kho) {
    if (vanTay(docKieu(ten)) === vanTay(napKieuChu(moi))) {
      throw new Error(`Kiểu này giống hệt "${ten}" đã có trong kho. Dùng lại kiểu đó, đừng tạo bản sao.`);
    }
  }

  if (!existsSync(KHO_RIENG)) mkdirSync(KHO_RIENG, { recursive: true });
  const duongDan = join(KHO_RIENG, `${tenMoi}.json`);
  writeFileSync(duongDan, JSON.stringify(moi, null, 2) + '\n', 'utf8');
  chuanCo([tenMoi]);
  console.log(`Đã tạo kiểu "${tenMoi}" và cất vào kho: ${duongDan}`);
};

LENH['chuan-co'] = (t) => chuanCo(t._.length ? t._ : [...dsKho().keys()]);

// So kiểu chữ của mình với chữ trong một khung video mẫu, từng điểm ảnh.
// Thêm --toi-uu thì máy tự dò cỡ chữ / bóp ngang / giãn chữ cho tới khi khớp nhất.
LENH['so-khop'] = (t) => {
  const [tenKieu, anhMau] = t._;
  if (!tenKieu || !anhMau) throw new Error('Cách dùng: so-khop <kiểu> <ảnh khung mẫu> --chu "..." [--toi-uu]');
  if (!t.chu) throw new Error('Thiếu --chu "<câu chữ đang hiện trong khung mẫu>"');
  const g = khungCuaVideo(anhMau);
  const goc = docKieu(tenKieu);
  const cheDo = t['che-do'] || goc.hoa_thuong || 'nguyen';
  const vung = t.vung ? (([x, y, w, h]) => ({ x: +x, y: +y, rong: +w, cao: +h }))(String(t.vung).split(',')) : null;

  const matMau = tachChuMau(resolve(anhMau), g.rong, g.cao, vung);
  const soVoi = (k) => {
    const kk = theoKhung(k, g.rong, g.cao);
    return soHaiHinh(matMau, dungChuCuaMinh(kk, t.chu, cheDo, g.rong, g.cao), g.rong, g.cao);
  };

  console.log(`Khung mẫu ${g.rong}x${g.cao} · kiểu "${tenKieu}" · chữ: "${t.chu}"`);
  let kq = soVoi(goc);
  if (!kq) throw new Error('Không tách được chữ trong khung mẫu. Chỉ vùng chữ bằng --vung x,y,rộng,cao');
  inBaoCao(kq, tenKieu);

  if (!t['toi-uu']) return;

  // ---- tự tối ưu: dò từ thô tới mịn, mỗi vòng thu hẹp khoảng dò ----
  console.log('\nTỰ TỐI ƯU (dựng thử rồi so, lặp tới khi hết cải thiện)\n');
  const tt = dsKho().get(tenKieu);
  const tho = JSON.parse(readFileSync(tt.duongDan, 'utf8'));
  const nen = napKieuChu(tho);
  let tot = { doTrung: kq.doTrung, co: coChu(nen, cheDo), bop: nen.bop_ngang ?? 100, gian: nen.gian_chu || 0 };

  const thu = (co, bop, gian) => {
    const k = napKieuChu({ ...tho, co_chu: Object.fromEntries(CHE_DO_CHU.map((c) => [c, co])), bop_ngang: bop, gian_chu: gian });
    const r = soVoi(k);
    return r ? r.doTrung : 0;
  };

  // Vòng 1 - DÒ THÔ trên lưới. Ba thông số ăn nhau (đổi cỡ thì bóp ngang và giãn chữ
  // phải đổi theo), nên dò từng cái một sẽ kẹt ở một điểm không phải tốt nhất.
  const goc0 = tot.co;
  for (let co = Math.round(goc0 * 0.85); co <= Math.round(goc0 * 1.2); co += Math.max(1, Math.round(goc0 * 0.05))) {
    for (let bop = 75; bop <= 110; bop += 5) {
      for (let gian = 0; gian <= 6; gian += 2) {
        const d = thu(co, bop, gian);
        if (d > tot.doTrung + 0.002) {
          tot = { doTrung: d, co, bop, gian };
          console.log(`  [thô] cỡ ${co}px · bóp ${bop}% · giãn ${gian}px -> ${(d * 100).toFixed(1)}%`);
        }
      }
    }
  }
  // Vòng 2 - TINH CHỈNH quanh điểm tốt nhất vừa tìm được
  for (const buoc of [[2, 2, 1], [1, 1, 1]]) {
    let caiThien = true;
    while (caiThien) {
      caiThien = false;
      for (const [dCo, dBop, dGian] of [[buoc[0], 0, 0], [-buoc[0], 0, 0], [0, buoc[1], 0], [0, -buoc[1], 0], [0, 0, buoc[2]], [0, 0, -buoc[2]]]) {
        const co = tot.co + dCo, bop = tot.bop + dBop, gian = tot.gian + dGian;
        if (co < 10 || bop < 60 || bop > 140 || gian < 0 || gian > 20) continue;
        const d = thu(co, bop, gian);
        if (d > tot.doTrung + 0.0015) {
          tot = { doTrung: d, co, bop, gian };
          caiThien = true;
          console.log(`  [tinh] cỡ ${co}px · bóp ${bop}% · giãn ${gian}px -> ${(d * 100).toFixed(1)}%`);
        }
      }
    }
  }

  // Ghi lại kết quả tốt nhất. tot.co đã là cỡ ở KHUNG MỐC của kiểu chữ
  // (hàm thử tự quy về khung video khi so), nên KHÔNG nhân tỉ lệ lần nữa.
  tho.co_chu = Object.fromEntries(CHE_DO_CHU.map((c) => [c, tot.co]));
  tho.bop_ngang = tot.bop;
  tho.gian_chu = tot.gian;
  if (tho.chuan_co?.kieu === 'cao-chu') {
    tho.chuan_co.ti_le = Math.round(tot.co * nen._do.tiLeCaoChuHoa / nen.khung.cao * 10000) / 10000;
  }
  // chỉnh luôn chỗ đặt dòng chữ theo độ lệch dọc đo được
  const cuoi = soVoi(napKieuChu(tho));
  // lechTamDoc = tâm mẫu trừ tâm của mình. Số ÂM nghĩa là chữ mình đang nằm THẤP hơn
  // -> phải kéo LÊN, tức GIẢM tam_doc. Cộng thẳng, đừng đảo dấu.
  if (cuoi && Math.abs(cuoi.lechTamDoc) > 2) {
    tho.vi_tri = { ...(tho.vi_tri || {}),
      tam_doc: Math.round(((tho.vi_tri?.tam_doc ?? 0.88) + cuoi.lechTamDoc / g.cao) * 10000) / 10000 };
  }
  writeFileSync(tt.duongDan, JSON.stringify(tho, null, 2) + '\n', 'utf8');
  console.log(`\nĐã ghi vào kiểu chữ: cỡ ${tho.co_chu.hoa}px · bóp ngang ${tot.bop}% · giãn chữ ${tho.gian_chu}px · vị trí ${tho.vi_tri.tam_doc}`);
  inBaoCao(soVoi(napKieuChu(tho)), tenKieu);
};

// Dò xem font nào trên máy giống chữ trong khung mẫu nhất.
// Chữ trong video mẫu thường dùng font mình không có; lệnh này tìm bản gần nhất.
LENH['tim-font-giong'] = (t) => {
  const anhMau = t._[0];
  if (!anhMau || !t.chu) throw new Error('Cách dùng: tim-font-giong <ảnh khung mẫu> --chu "..." [--kieu <kiểu làm nền>]');
  const g = khungCuaVideo(anhMau);
  const vung = t.vung ? (([x, y, w, h]) => ({ x: +x, y: +y, rong: +w, cao: +h }))(String(t.vung).split(',')) : null;
  const matMau = tachChuMau(resolve(anhMau), g.rong, g.cao, vung);
  const bao = khungBao(matMau, g.rong, g.cao);
  if (!bao) throw new Error('Không tách được chữ trong khung mẫu');

  const nen = docKieu(t.kieu || [...dsKho().keys()][0]);
  const cheDo = t['che-do'] || nen.hoa_thuong || 'hoa';
  const dsFont = [...new Set(moiFont())];
  console.log(`Dò ${dsFont.length} font trên máy · khung mẫu ${g.rong}x${g.cao} · chữ "${t.chu}"\n`);

  const ketQua = [];
  for (const duongDan of dsFont) {
    let f;
    try { f = napFont(duongDan); } catch { continue; }
    if (!kiemDauViet(f).dat) continue;   // thiếu dấu tiếng Việt thì loại thẳng
    try {
      // Chấm CÔNG BẰNG về hình dáng: với mỗi font, tự chỉnh cỡ cho khớp chiều cao
      // rồi chỉnh bóp ngang cho khớp bề ngang. Không làm vậy thì font rộng bị trừ
      // điểm oan chỉ vì rộng, trong khi bóp ngang là chỉnh được.
      const dung = (co, bop) => {
        const k = theoKhung(napKieuChu({ ...nen, ten: 'thu', font: { ...nen.font, file: duongDan },
          co_chu: co, bop_ngang: bop, _he_so_ass: null }), g.rong, g.cao);
        return dungChuCuaMinh(k, t.chu, cheDo, g.rong, g.cao);
      };
      let co = Math.round(bao.cao / 1.6 / f.tiLeCaoChuHoa), bop = 100, b = null;
      for (let vong = 0; vong < 5; vong++) {         // khớp chiều cao trước
        b = khungBao(dung(co, 100), g.rong, g.cao);
        if (!b) break;
        if (Math.abs(b.cao - bao.cao) / bao.cao < 0.02) break;
        co = Math.max(8, Math.round(co * bao.cao / b.cao));
      }
      if (!b) continue;
      bop = Math.max(50, Math.min(150, Math.round(100 * bao.rong / b.rong)));  // rồi khớp bề ngang
      const mat = dung(co, bop);
      const r = soHaiHinh(matMau, mat, g.rong, g.cao);
      if (r) ketQua.push({ ten: f.tenDayDu, duongDan, co, bop, ...r });
    } catch { /* font hỏng thì bỏ qua */ }
  }

  ketQua.sort((a, b) => b.doTrung - a.doTrung);
  console.log('Font giống nhất (xếp theo độ trùng):\n');
  for (const r of ketQua.slice(0, 10)) {
    console.log(`  ${(r.doTrung * 100).toFixed(1).padStart(5)}%  ${r.ten.padEnd(30)} cỡ ${String(r.co).padStart(3)}px` +
      ` · ngang lệch ${(r.lechNgang * 100).toFixed(1)}% · nét lệch ${(r.lechNetDay * 100).toFixed(1)}%`);
  }
  if (!ketQua.length) console.log('  Không font nào trên máy đủ dấu tiếng Việt để so.');
};

LENH['kiem-font'] = (t) => {
  // nhận cả đường dẫn đầy đủ lẫn tên font, giống mọi lệnh khác
  const f = napFont(timFont(t._[0]));
  const k = kiemDauViet(f);
  console.log(`Font: ${f.tenDayDu}  (họ: ${f.ho})`);
  console.log(`Dấu tiếng Việt: ${k.dat ? 'ĐỦ - dùng được' : `THIẾU ${k.thieu.length}/${k.tong} ký tự - KHÔNG dùng cho phụ đề tiếng Việt`}`);
  if (!k.dat) console.log(`Thiếu: ${k.thieu.join(' ')}`);
  console.log(`Cỡ chữ chuẩn Netflix (42 ký tự vừa vùng an toàn): ${Math.floor(RONG * TI_LE_AN_TOAN / f.beNgangEm(CAU_42))}px`);
};

// ---------- chuẩn cỡ chữ ----------
// Hai bước: (1) tính nhanh từ số đo trong file font, (2) DỰNG THỬ rồi tự chỉnh.
// Bước 2 cần vì phép tính không tính được khoảng ghép giữa các cặp chữ (kerning),
// bỏ qua thì phụ đề hụt 2-3% so với chuẩn.
function chuanCo(dsTen, imLang = false) {
  const kho = dsKho();
  for (const ten of dsTen) {
    const tt = kho.get(ten);
    const tho = JSON.parse(readFileSync(tt.duongDan, 'utf8'));
    let k = napKieuChu(tho);

    // BƯỚC 0 (bắt buộc, làm trước mọi thứ): đo hệ số quy đổi cỡ chữ sang file phụ đề.
    // Mỗi font khai số đo một kiểu; suy từ bảng font thì có font đúng có font lệch 25%.
    tho._he_so_ass = doHeSoASS(k, (heSo) => napKieuChu({ ...tho, _he_so_ass: heSo }));
    k = napKieuChu(tho);

    // Cách 2: ấn định CHIỀU CAO CHỮ HOA theo phần của chiều cao khung.
    // Chiều cao chữ hoa không đổi giữa 4 chế độ chữ, nên cả 4 dùng chung một cỡ.
    if (k.chuan_co.kieu === 'cao-chu') {
      const caoChuPx = k.khung.cao * k.chuan_co.ti_le;
      const co = Math.round(caoChuPx / k._do.tiLeCaoChuHoa);
      tho.co_chu = Object.fromEntries(CHE_DO_CHU.map((c) => [c, co]));
      writeFileSync(tt.duongDan, JSON.stringify(tho, null, 2) + '\n', 'utf8');
      if (!imLang) {
        console.log(`${ten.padEnd(16)} cỡ ${co}px cho cả 4 chế độ ` +
          `(cao chữ hoa ${caoChuPx.toFixed(1)}px = ${(k.chuan_co.ti_le * 100).toFixed(2)}% khung cao ${k.khung.cao}px)`);
      }
      continue;
    }

    const dich = beNgangDich(k, TI_LE_AN_TOAN);
    tho.co_chu = {};
    for (const c of CHE_DO_CHU) {
      const chu = doiHoaThuong(CAU_42, c);
      const demGianChu = (k.gian_chu || 0) * [...chu].length;
      tho.co_chu[c] = Math.floor((dich - demGianChu) / k._do.beNgangEm(chu));
    }

    // dựng thử rồi chỉnh, tối đa 4 vòng - thường 2 vòng là khít
    for (let vong = 0; vong < 4; vong++) {
      k = napKieuChu(tho);
      let conLech = false;
      for (const c of CHE_DO_CHU) {
        const thuc = doBeNgangThat(k, CAU_42, c);
        if (!thuc) continue;
        const lech = (dich - thuc) / dich;
        if (Math.abs(lech) <= 0.005) continue;      // trong 0,5% thì thôi
        const moi = Math.max(8, Math.round(tho.co_chu[c] * (dich / thuc)));
        if (moi !== tho.co_chu[c]) { tho.co_chu[c] = moi; conLech = true; }
      }
      if (!conLech) break;
    }
    // vòng cuối: thà hụt vài px còn hơn tràn ra ngoài vùng an toàn
    k = napKieuChu(tho);
    for (const c of CHE_DO_CHU) {
      let dem = 0;
      while (doBeNgangThat(k, CAU_42, c) > dich && dem++ < 5) {
        tho.co_chu[c] -= 1;
        k = napKieuChu(tho);
      }
    }

    writeFileSync(tt.duongDan, JSON.stringify(tho, null, 2) + '\n', 'utf8');
    if (imLang) continue;
    const k2 = napKieuChu(tho);
    console.log(`${ten.padEnd(16)} ` + CHE_DO_CHU.map((c) =>
      `${c} ${String(coChu(k2, c)).padStart(3)}px (${Math.round(doBeNgangThat(k2, CAU_42, c))}/${Math.round(dich)})`).join(' · '));
  }
}

// ---------- ảnh xem trước (dùng ffmpeg, không cần trình duyệt) ----------
function dungAnhXemTruoc(dsKieu, cheDo, duongDanAnh) {
  const le = Math.round(RONG * (1 - TI_LE_AN_TOAN) / 2);
  const vach = [
    `drawbox=x=${le}:y=0:w=2:h=${CAO}:color=0xFF3B30@0.85:t=fill`,
    `drawbox=x=${RONG - le}:y=0:w=2:h=${CAO}:color=0xFF3B30@0.85:t=fill`,
  ].join(',');
  const dong = [], styleThem = [];
  dsKieu.forEach((k, i) => {
    const r = raASS(k, cheDo);
    const y = Math.round(CAO / (dsKieu.length + 1)) * (i + 1);
    const chu = doiHoaThuong(CAU_42, cheDo);
    if (r.styleSang) {
      styleThem.push(r.styleSang.style);
      dong.push(`Dialogue: 0,0:00:00.00,0:00:05.00,${r.styleSang.ten},,0,0,0,,{\\an5\\pos(${RONG / 2},${y})}${r.styleSang.the}${chu}`);
    }
    dong.push(`Dialogue: 1,0:00:00.00,0:00:05.00,${k.ten},,0,0,0,,{\\an5\\pos(${RONG / 2},${y})}${r.the}${chu}`);
    dong.push(`Dialogue: 2,0:00:00.00,0:00:05.00,nhan,,0,0,0,,{\\an1\\pos(${le},${y - 80})}${k.ten} · ${TEN_CHE_DO[cheDo]} · ${coChu(k, cheDo)}px`);
  });
  const kieuNhan = napKieuChu({ ten: 'nhan', co_chu: 24, mau_chu: '#FFD84D',
    font: { ho: 'Open Sans', file: 'OpenSans-SemiBold.ttf', dam: 600 }, vien: [{ day: 2, mau: '#000000' }] });
  const thuMuc = dirname(duongDanAnh);
  const tam = join(thuMuc, '_xem.ass');
  writeFileSync(tam, fileASS([...dsKieu.map((k) => ({ ...k, hoa_thuong: cheDo })), kieuNhan], dong, RONG, CAO)
    .replace('[Events]', styleThem.join('\n') + '\n\n[Events]'), 'utf8');
  execFileSync('ffmpeg', ['-y', '-f', 'lavfi',
    '-i', `gradients=s=${RONG}x${CAO}:c0=0xE8ECF2:c1=0x080C16:x0=0:y0=0:x1=${RONG}:y1=${CAO}:nb_colors=2`,
    '-vf', `${vach},subtitles=_xem.ass`, '-frames:v', '1', basename(duongDanAnh)],
    { stdio: 'pipe', cwd: thuMuc });
}

// ================= chạy =================
const [, , lenh, ...con] = process.argv;
if (!lenh || !LENH[lenh]) {
  console.log(readFileSync(fileURLToPath(import.meta.url), 'utf8')
    .split('\n').filter((l) => l.startsWith('//')).slice(0, 12).map((l) => l.slice(3)).join('\n'));
  process.exit(lenh ? 1 : 0);
}
try {
  LENH[lenh](docThamSo(con));
} catch (e) {
  console.error(`Lỗi: ${e.message}`);
  process.exit(1);
}
