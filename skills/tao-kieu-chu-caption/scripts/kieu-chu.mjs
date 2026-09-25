// Bộ dịch KIỂU CHỮ: 1 file mô tả -> 3 nơi dùng (HTML/CSS · phụ đề ASS · ffmpeg drawtext)
// Mọi kích thước tính theo khung cao 1080px. Khung khác thì nhân theo tỉ lệ.
import { napFont } from './do-font.mjs';
import { timFont } from './tim-font.mjs';

// ---------- màu ----------
// "#RRGGBB" -> { r,g,b }
function docMau(hex) {
  const s = String(hex).replace('#', '').trim();
  const n = s.length === 3 ? s.split('').map((c) => c + c).join('') : s;
  return {
    r: parseInt(n.slice(0, 2), 16),
    g: parseInt(n.slice(2, 4), 16),
    b: parseInt(n.slice(4, 6), 16),
  };
}

function rgba(hex, doDam = 1) {
  const { r, g, b } = docMau(hex);
  return `rgba(${r},${g},${b},${doDam})`;
}

// ASS dùng &HAABBGGRR - AA: 00 = đặc, FF = trong suốt hoàn toàn
function mauASS(hex, doDam = 1) {
  const { r, g, b } = docMau(hex);
  const a = Math.round((1 - doDam) * 255);
  const hai = (v) => v.toString(16).toUpperCase().padStart(2, '0');
  return `&H${hai(a)}${hai(b)}${hai(g)}${hai(r)}`;
}

// ffmpeg drawtext: 0xRRGGBB@doDam
function mauFF(hex, doDam = 1) {
  const s = String(hex).replace('#', '');
  return doDam >= 1 ? `0x${s}` : `0x${s}@${doDam}`;
}

// ---------- giá trị mặc định ----------
const MAC_DINH = {
  ten: 'khong-ten',
  mo_ta: '',
  font: { ho: 'Fira Sans', file: 'FiraSans-Bold.ttf', dam: 700, nghieng: false },
  co_chu: 72,
  hoa_thuong: 'nguyen', // nguyen | hoa | thuong
  gian_chu: 0, // px
  // Bóp ngang chữ, tính theo phần trăm (100 = giữ nguyên, 80 = hẹp lại còn 4/5).
  // Dùng khi cần bắt chước một font hẹp mà trong tay chỉ có font rộng.
  // Bóp quá tay chữ sẽ méo - dưới 85 là đã thấy, dưới 75 thì hỏng hẳn.
  bop_ngang: 100,
  mau_chu: '#FFFFFF',
  gradient: null, // { tu, den, goc }
  vien: [], // [{ day, mau }] - xếp từ trong ra ngoài
  bong: null, // { x, y, nhoe, mau, do_dam }
  phat_sang: null, // { ban_kinh, mau, do_dam }
  nen: null, // { mau, do_dam, dem, bo_goc }
  // Khung video kiểu chữ này nhắm tới. Ngang 1920x1080 hay dọc 1080x1920 đều được.
  khung: { rong: 1920, cao: 1080 },
  // Cách ấn định cỡ chữ:
  //   netflix  - để câu 42 ký tự vừa khít vùng an toàn (phụ đề dịch chuẩn)
  //   cao-chu  - ấn định CHIỀU CAO CHỮ HOA theo phần của chiều cao khung
  //              (dùng khi bắt chước cỡ chữ của một video mẫu)
  chuan_co: { kieu: 'netflix' },
  // Chỗ đặt dòng chữ: tâm dòng nằm ở đâu tính từ đỉnh khung xuống (0,5 = giữa khung)
  vi_tri: { tam_doc: 0.88 },
};

// 4 chế độ chữ. Mỗi chế độ có CỠ CHỮ RIÊNG vì chữ in hoa chiếm chỗ rộng hơn
// chữ thường - dùng chung một cỡ thì đổi sang in hoa là tràn vùng an toàn.
export const CHE_DO_CHU = ['nguyen', 'hoa', 'thuong', 'hoa_dau'];
export const TEN_CHE_DO = {
  nguyen: 'giữ nguyên',
  hoa: 'IN HOA',
  thuong: 'chữ thường',
  hoa_dau: 'Hoa Đầu Từ',
};

const boNhoFont = new Map();
export function docFont(ten) {
  if (!boNhoFont.has(ten)) boNhoFont.set(ten, napFont(timFont(ten)));
  return boNhoFont.get(ten);
}

export function napKieuChu(tho) {
  const k = { ...MAC_DINH, ...tho };
  if (tho._he_so_ass) k._he_so_ass = tho._he_so_ass;
  k.font = { ...MAC_DINH.font, ...(tho.font || {}) };
  // Tên font lấy thẳng từ file font, không ghi tay -> không bao giờ lệch tên
  try {
    const f = docFont(k.font.file);
    k._do = f;
    k.font.ho = f.ho || k.font.ho;
    k.font.ten_day_du = f.tenDayDu || k.font.ho;
  } catch (e) {
    k._loiFont = e.message;
    k.font.ten_day_du = k.font.ho;
  }
  k.vien = (tho.vien || []).map((v) => ({ day: v.day, mau: v.mau }));
  k.khung = { ...MAC_DINH.khung, ...(tho.khung || {}) };
  k.chuan_co = { ...MAC_DINH.chuan_co, ...(tho.chuan_co || {}) };
  k.vi_tri = { ...MAC_DINH.vi_tri, ...(tho.vi_tri || {}) };
  // co_chu ghi 1 số -> hiểu là dùng chung cho cả 4 chế độ (sẽ được bộ chuẩn cỡ tách ra)
  if (typeof k.co_chu === 'number') {
    const n = k.co_chu;
    k.co_chu = Object.fromEntries(CHE_DO_CHU.map((c) => [c, n]));
  }
  return k;
}

// Quy kiểu chữ về ĐÚNG kích thước video thật.
// Kiểu chữ được thiết kế trên một khung mốc (vd 1080x1920). Video thật có thể nhỏ hơn
// (720x1280) hay lớn hơn (2160x3840). Cỡ chữ và mọi số đo phải co giãn theo, không thì
// cùng một kiểu chữ dựng lên video nhỏ sẽ ra chữ khổng lồ.
export function theoKhung(k, rong, cao) {
  const tiLe = cao / k.khung.cao;
  if (Math.abs(tiLe - 1) < 0.001) return k;
  const n = (x) => Math.round(x * tiLe);
  const m = { ...k, khung: { rong, cao } };
  m.co_chu = Object.fromEntries(Object.entries(k.co_chu).map(([c, v]) => [c, Math.max(6, n(v))]));
  m.gian_chu = k.gian_chu ? n(k.gian_chu) : 0;
  m.vien = k.vien.map((v) => ({ ...v, day: Math.max(1, n(v.day)) }));
  if (k.bong) m.bong = { ...k.bong, x: n(k.bong.x), y: n(k.bong.y), nhoe: n(k.bong.nhoe || 0) };
  if (k.phat_sang) m.phat_sang = { ...k.phat_sang, ban_kinh: n(k.phat_sang.ban_kinh) };
  if (k.nen) m.nen = { ...k.nen, dem: n(k.nen.dem || 0), bo_goc: n(k.nen.bo_goc || 0) };
  return m;
}

// Lấy cỡ chữ đúng chế độ đang dùng
export function coChu(k, cheDo) {
  const c = cheDo || k.hoa_thuong || 'nguyen';
  return k.co_chu[c] ?? k.co_chu.nguyen;
}

// Bề ngang thật của một câu khi dựng bằng kiểu chữ này (px), tính từ số đo trong file font.
// Có tính cả giãn chữ và đệm khối nền - hai thứ này là px cố định, không co theo cỡ chữ.
export function beNgangCau(k, cau, cheDo) {
  if (!k._do) throw new Error(`Không đọc được font: ${k._loiFont || k.font.file}`);
  const c = cheDo || k.hoa_thuong || 'nguyen';
  const chu = doiHoaThuong(cau, c);
  return k._do.beNgang(chu, coChu(k, c)) * ((k.bop_ngang ?? 100) / 100)
    + (k.gian_chu || 0) * [...chu].length
    + (k.nen ? (k.nen.dem || 0) * 2 : 0);
}

function doiHoaThuong(chu, che_do) {
  if (che_do === 'hoa') return chu.toLocaleUpperCase('vi-VN');
  if (che_do === 'thuong') return chu.toLocaleLowerCase('vi-VN');
  if (che_do === 'hoa_dau') {
    return chu.toLocaleLowerCase('vi-VN').replace(/(^|[\s"'(\[«-])(\p{L})/gu,
      (_, truoc, chuCai) => truoc + chuCai.toLocaleUpperCase('vi-VN'));
  }
  return chu;
}

// Gom mọi thứ vẽ theo hình chữ (viền, phát sáng, bóng) thành danh sách text-shadow
function vongBongDo(k) {
  const bongDo = [];
  if (k.vien.length) {
    // cộng dồn độ dày, vẽ lớp ngoài trước để lớp trong đè lên
    let dayCong = 0;
    const lop = k.vien.map((v) => ({ mau: v.mau, day: (dayCong += v.day) }));
    for (const l of [...lop].reverse()) {
      // vòng càng dày càng cần nhiều điểm, không thì mép viền lởm chởm
      const buoc = Math.max(16, Math.ceil(l.day * 4));
      for (let i = 0; i < buoc; i++) {
        const goc = (Math.PI * 2 * i) / buoc;
        bongDo.push(`${+(Math.cos(goc) * l.day).toFixed(2)}px ${+(Math.sin(goc) * l.day).toFixed(2)}px 0 ${l.mau}`);
      }
    }
  }
  if (k.phat_sang) {
    const p = k.phat_sang;
    bongDo.push(`0 0 ${p.ban_kinh}px ${rgba(p.mau, p.do_dam ?? 0.7)}`);
    bongDo.push(`0 0 ${p.ban_kinh * 2.4}px ${rgba(p.mau, (p.do_dam ?? 0.7) * 0.5)}`);
  }
  if (k.bong) {
    const b = k.bong;
    bongDo.push(`${b.x}px ${b.y}px ${b.nhoe || 0}px ${rgba(b.mau, b.do_dam ?? 1)}`);
  }
  return bongDo;
}

// Chữ đổ màu (gradient) phải để trong suốt mới lộ được màu nền -> viền/bóng vẽ theo
// hình chữ sẽ phủ kín và ra một mảng đen. Bởi vậy khi có gradient thì viền/bóng
// phải nằm ở MỘT LỚP CHỮ RIÊNG ĐẶT DƯỚI (::before), lớp gradient nằm trên.
export function canLopDuoi(k) {
  return Boolean(k.gradient) && vongBongDo(k).length > 0;
}

// CSS cho lớp nằm dưới. Trả null nếu không cần.
export function raCSSLopDuoi(k) {
  if (!canLopDuoi(k)) return null;
  const mauDac = k.vien.length ? k.mau_chu : k.mau_chu;
  return [
    'content: attr(data-chu)',
    'position: absolute',
    'left: 0',
    'top: 0',
    'z-index: -1',
    'background: none',
    '-webkit-background-clip: border-box',
    'background-clip: border-box',
    `color: ${mauDac}`,
    `text-shadow: ${vongBongDo(k).join(', ')}`,
  ].join(';\n  ') + ';';
}

// ================= ĐÍCH 1: HTML / CSS =================
// Trung thực nhất - làm được mọi hiệu ứng.
export function raCSS(k, cheDo) {
  const c = cheDo || k.hoa_thuong || 'nguyen';
  const d = [];
  d.push(`font-family: '${k.font.ho}', sans-serif`);
  d.push(`font-weight: ${k.font.dam}`);
  if (k.font.nghieng) d.push('font-style: italic');
  d.push(`font-size: ${coChu(k, c)}px`);
  d.push(`line-height: 1.15`);
  if (k.gian_chu) d.push(`letter-spacing: ${k.gian_chu}px`);
  if ((k.bop_ngang ?? 100) !== 100) {
    d.push(`transform: scaleX(${(k.bop_ngang / 100).toFixed(3)})`);
    d.push('transform-origin: center');
    d.push('display: inline-block');
  }
  if (c === 'hoa') d.push('text-transform: uppercase');
  if (c === 'thuong') d.push('text-transform: lowercase');
  if (c === 'hoa_dau') d.push('text-transform: capitalize');

  // Viền: nhiều lớp -> vẽ bằng vòng text-shadow (paint-order không đủ cho >1 lớp)
  // Có gradient thì viền/bóng chuyển xuống lớp ::before (xem raCSSLopDuoi).
  const bongDo = canLopDuoi(k) ? [] : vongBongDo(k);
  if (bongDo.length) d.push(`text-shadow: ${bongDo.join(', ')}`);
  if (canLopDuoi(k)) {
    // Lớp viền nằm dưới (::before) canh theo hộp của thẻ này. Thẻ phải là inline-block
    // thì hộp mới ôm sát chữ; để inline thì hộp là cả DÒNG -> lớp viền lệch vài px,
    // lộ ra viền sai màu quanh mép chữ.
    d.push('position: relative');
    d.push('display: inline-block');
  }

  if (k.gradient) {
    const g = k.gradient;
    d.push(`background-image: linear-gradient(${g.goc ?? 180}deg, ${g.tu}, ${g.den})`);
    d.push('-webkit-background-clip: text');
    d.push('background-clip: text');
    d.push('color: transparent');
  } else {
    d.push(`color: ${k.mau_chu}`);
  }

  if (k.nen) {
    const n = k.nen;
    d.push(`background-color: ${rgba(n.mau, n.do_dam ?? 1)}`);
    d.push(`padding: ${Math.round((n.dem || 0) * 0.6)}px ${n.dem || 0}px`);
    d.push(`border-radius: ${n.bo_goc || 0}px`);
    if (k.gradient) d.push('/* CẢNH BÁO: nền + gradient chữ phải tách 2 thẻ lồng nhau */');
  }
  return d.join(';\n  ') + ';';
}

// ================= ĐÍCH 2: phụ đề ASS =================
// libass: 1 lớp viền, 1 bóng, không gradient, không glow thật.
export function raASS(k, cheDo) {
  const c = cheDo || k.hoa_thuong || 'nguyen';
  const canhBao = [];
  if (k.vien.length > 1) canhBao.push(`viền ${k.vien.length} lớp -> ASS gộp còn 1 lớp (cộng độ dày)`);
  if (k.gradient) canhBao.push('gradient chữ -> ASS không có, thay bằng màu giữa của gradient');
  if (k.phat_sang) canhBao.push('phát sáng -> ASS dựng gần đúng bằng 1 lớp chữ nhoè màu sáng nằm dưới (không mượt bằng bản HTML)');

  const dayVien = k.vien.reduce((s, v) => s + v.day, 0);
  let mauVien = k.vien.length ? k.vien[k.vien.length - 1].mau : '#000000';
  let mauChinh = k.mau_chu;
  if (k.gradient) {
    const a = docMau(k.gradient.tu), b = docMau(k.gradient.den);
    const tron = (x, y) => Math.round((x + y) / 2).toString(16).padStart(2, '0');
    mauChinh = `#${tron(a.r, b.r)}${tron(a.g, b.g)}${tron(a.b, b.b)}`;
  }

  // BorderStyle 3 = vẽ khối nền đặc sau chữ (dùng khi kiểu chữ có "nen")
  // Lưu ý libass: ở BorderStyle 3, màu khối nền lấy từ OutlineColour, KHÔNG phải BackColour.
  const kieuVien = k.nen ? 3 : 1;
  if (k.nen) {
    mauVien = k.nen.mau;
    if (k.nen.bo_goc) canhBao.push('bo góc khối nền -> ASS không có, khối nền sẽ vuông góc');
  }
  const mauNen = k.bong ? mauASS(k.bong.mau, k.bong.do_dam ?? 1) : mauASS('#000000', 0);

  const style = [
    `Style: ${k.ten}`,
    // Tên ĐẦY ĐỦ (vd "Segoe UI Black"), không phải tên họ + cờ đậm.
    // File ASS chỉ có cờ đậm/không-đậm, ghi tên họ thì ffmpeg lấy bản Bold,
    // trong khi thiết kế dùng bản Black -> chữ sai nét và hụt bề ngang.
    k.font.ten_day_du || k.font.ho,
    // nhân hệ số quy đổi: ASS đo theo chiều cao cả dòng, thiết kế đo theo thân chữ
    // hệ số quy đổi ĐÃ ĐO của font này; chưa đo thì tạm dùng số suy từ bảng font
    Math.round(coChu(k, c) * (k._he_so_ass ?? (k._do ? k._do.heSoASS : 1))),
    mauASS(mauChinh),           // PrimaryColour
    mauASS(mauChinh),           // SecondaryColour
    mauASS(mauVien),            // OutlineColour
    mauNen,                     // BackColour
    0,                          // Bold: độ đậm đã nằm trong tên font ở trên
    k.font.nghieng ? -1 : 0,    // Italic
    0, 0,                       // Underline, StrikeOut
    Math.round(k.bop_ngang ?? 100), 100,   // ScaleX, ScaleY
    k.gian_chu,                 // Spacing
    0,                          // Angle
    kieuVien,                   // BorderStyle
    kieuVien === 3 ? Math.max(2, Math.round((k.nen.dem || 20) / 4)) : dayVien, // Outline
    k.bong ? Math.max(Math.abs(k.bong.x), Math.abs(k.bong.y)) : 0,             // Shadow
    2,                          // Alignment (2 = giữa dưới)
    // Lề dọc: khoảng cách từ đáy khung lên đáy dòng chữ. Tính ngược từ chỗ muốn
    // đặt tâm dòng, để dòng chữ nằm đúng vị trí đã khai trong kiểu chữ.
    Math.round(k.khung.rong * 0.06), Math.round(k.khung.rong * 0.06),
    Math.max(0, Math.round(k.khung.cao * (1 - (k.vi_tri?.tam_doc ?? 0.88))
      - coChu(k, c) * (k._do ? k._do.heSoASS : 1.2) / 2)),
    1,                          // Encoding
  ].join(',');

  // Phát sáng: libass không có glow. Dựng gần đúng bằng MỘT LỚP CHỮ PHỤ nằm dưới,
  // tô màu sáng và làm nhoè; lớp chữ chính vẫn nét nằm trên.
  let styleSang = null;
  if (k.phat_sang) {
    const p = k.phat_sang;
    const o = style.split(',');
    o[0] = `Style: ${k.ten}__sang`;
    o[3] = o[4] = mauASS(p.mau);   // Primary + Secondary = màu sáng
    o[5] = mauASS(p.mau);          // viền cùng màu để quầng sáng dày hơn
    o[15] = 1;                     // BorderStyle thường
    o[16] = Math.max(2, Math.round(p.ban_kinh / 5)); // Outline: nới quầng sáng
    o[17] = 0;                     // bỏ bóng ở lớp sáng
    styleSang = {
      ten: `${k.ten}__sang`,
      style: o.join(','),
      the: `{\\blur${Math.max(3, Math.round(p.ban_kinh / 3))}}`,
    };
  }

  return { style, the: '', styleSang, canhBao };
}

export function fileASS(dsKieu, dsDong, rong = 1920, cao = 1080) {
  const styles = dsKieu.map((k) => raASS(k).style);
  return [
    '[Script Info]',
    'ScriptType: v4.00+',
    `PlayResX: ${rong}`,
    `PlayResY: ${cao}`,
    'WrapStyle: 2',
    'ScaledBorderAndShadow: yes',
    '',
    '[V4+ Styles]',
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
    ...styles,
    '',
    '[Events]',
    'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    ...dsDong,
  ].join('\n');
}

// ================= ĐÍCH 3: ffmpeg drawtext =================
// Yếu nhất: 1 lớp viền, 1 bóng, khối nền. Không gradient, không glow.
export function raDrawtext(k, chu, x = '(w-text_w)/2', y = '(h-text_h)/2', cheDo) {
  const c = cheDo || k.hoa_thuong || 'nguyen';
  const canhBao = [];
  if (k.vien.length > 1) canhBao.push(`viền ${k.vien.length} lớp -> drawtext gộp còn 1 lớp`);
  if (k.gradient) canhBao.push('gradient chữ -> drawtext không có, dùng màu đặc');
  if (k.phat_sang) canhBao.push('phát sáng -> drawtext không có, bỏ qua');
  if (k.gian_chu) canhBao.push('giãn chữ -> drawtext không chỉnh được');

  const dayVien = k.vien.reduce((s, v) => s + v.day, 0);
  const mauVien = k.vien.length ? k.vien[k.vien.length - 1].mau : '#000000';
  const noiDung = doiHoaThuong(chu, c).replace(/([:'\\%])/g, '\\$1');

  const p = [
    `fontfile='${k.font.file.replace(/\\/g, '/').replace(':', '\\:')}'`,
    `text='${noiDung}'`,
    `fontsize=${coChu(k, c)}`,
    `fontcolor=${mauFF(k.gradient ? k.gradient.tu : k.mau_chu)}`,
    `x=${x}`,
    `y=${y}`,
  ];
  if (dayVien) p.push(`borderw=${dayVien}`, `bordercolor=${mauFF(mauVien)}`);
  if (k.bong) p.push(`shadowx=${k.bong.x}`, `shadowy=${k.bong.y}`, `shadowcolor=${mauFF(k.bong.mau, k.bong.do_dam ?? 1)}`);
  if (k.nen) p.push('box=1', `boxcolor=${mauFF(k.nen.mau, k.nen.do_dam ?? 1)}`, `boxborderw=${k.nen.dem || 20}`);

  return { loc: `drawtext=${p.join(':')}`, canhBao };
}

export { doiHoaThuong, rgba, mauASS, mauFF };
