// Đọc SỐ ĐO thẳng từ file font (.ttf/.otf) - không cần trình duyệt, không cần cài gì thêm.
// Dùng để: (1) tính bề ngang một câu ở cỡ chữ bất kỳ, (2) kiểm font có đủ dấu tiếng Việt.
//
// Vì sao không đo bằng trình duyệt: trình duyệt và ffmpeg dựng chữ theo hai đường khác nhau,
// cùng một cỡ chữ ra hai bề ngang lệch nhau hơn 10%. Số đo trong file font là gốc chung
// của cả hai -> đo từ đây thì phụ đề đúng cỡ ở mọi nơi.
import { readFileSync } from 'node:fs';

function docBang(buf) {
  const soBang = buf.readUInt16BE(4);
  const bang = {};
  for (let i = 0; i < soBang; i++) {
    const o = 12 + i * 16;
    bang[buf.toString('ascii', o, o + 4).trim()] = {
      vt: buf.readUInt32BE(o + 8),
      dai: buf.readUInt32BE(o + 12),
    };
  }
  return bang;
}

// cmap format 4 (ký tự trong vùng cơ bản) + format 12 (ngoài vùng cơ bản)
function docCmap(buf, vtCmap) {
  const soBang = buf.readUInt16BE(vtCmap + 2);
  let tot = null;
  for (let i = 0; i < soBang; i++) {
    const o = vtCmap + 4 + i * 8;
    const nenTang = buf.readUInt16BE(o);
    const maHoa = buf.readUInt16BE(o + 2);
    const vt = vtCmap + buf.readUInt32BE(o + 4);
    const dinhDang = buf.readUInt16BE(vt);
    const diem = (nenTang === 3 && maHoa === 10 && dinhDang === 12) ? 3
      : (nenTang === 3 && maHoa === 1 && dinhDang === 4) ? 2
      : (dinhDang === 4 || dinhDang === 12) ? 1 : 0;
    if (diem && (!tot || diem > tot.diem)) tot = { vt, dinhDang, diem };
  }
  if (!tot) throw new Error('Font không có bảng ánh xạ ký tự đọc được (cmap)');

  const map = new Map();
  if (tot.dinhDang === 4) {
    const soDoi = buf.readUInt16BE(tot.vt + 6) / 2;
    const vtCuoi = tot.vt + 14;
    const vtDau = vtCuoi + soDoi * 2 + 2;
    const vtDelta = vtDau + soDoi * 2;
    const vtRange = vtDelta + soDoi * 2;
    for (let i = 0; i < soDoi; i++) {
      const cuoi = buf.readUInt16BE(vtCuoi + i * 2);
      const dau = buf.readUInt16BE(vtDau + i * 2);
      if (dau === 0xFFFF) continue;
      const delta = buf.readInt16BE(vtDelta + i * 2);
      const range = buf.readUInt16BE(vtRange + i * 2);
      for (let c = dau; c <= cuoi && c !== 0x10000; c++) {
        let g;
        if (range === 0) g = (c + delta) & 0xFFFF;
        else {
          const vtG = vtRange + i * 2 + range + (c - dau) * 2;
          if (vtG + 1 >= buf.length) continue;
          g = buf.readUInt16BE(vtG);
          if (g) g = (g + delta) & 0xFFFF;
        }
        if (g) map.set(c, g);
      }
    }
  } else {
    const soNhom = buf.readUInt32BE(tot.vt + 12);
    for (let i = 0; i < soNhom; i++) {
      const o = tot.vt + 16 + i * 12;
      const dau = buf.readUInt32BE(o), cuoi = buf.readUInt32BE(o + 4), gDau = buf.readUInt32BE(o + 8);
      for (let c = dau; c <= cuoi; c++) map.set(c, gDau + (c - dau));
    }
  }
  return map;
}

// Bảng 'name': lấy TÊN THẬT của font. Cần cho file phụ đề ASS - ở đó chỉ ghi được tên,
// và chỉ có cờ đậm/không-đậm. Ghi "Segoe UI" + cờ đậm thì ffmpeg lấy bản Bold, trong khi
// thiết kế có thể đang dùng bản Black -> chữ ra sai nét và sai bề ngang.
// Ghi thẳng "Segoe UI Black" thì ffmpeg tìm đúng file.
function docTen(buf, bangName) {
  const vt = bangName.vt;
  const soBanGhi = buf.readUInt16BE(vt + 2);
  const vtChuoi = vt + buf.readUInt16BE(vt + 4);
  const lay = {};
  for (let i = 0; i < soBanGhi; i++) {
    const o = vt + 6 + i * 12;
    const nenTang = buf.readUInt16BE(o);
    const maID = buf.readUInt16BE(o + 6);
    const dai = buf.readUInt16BE(o + 8);
    const lech = buf.readUInt16BE(o + 10);
    if (![1, 2, 4, 16, 17].includes(maID)) continue;
    const b = buf.subarray(vtChuoi + lech, vtChuoi + lech + dai);
    // nền tảng 0 (Unicode) và 3 (Windows) đều ghi UTF-16 kiểu byte-lớn-trước;
    // chỉ nền tảng 1 (Mac) mới là 1 byte/ký tự. Copy ra trước khi đảo byte,
    // không thì đảo trúng vào bộ nhớ của chính file font.
    const chu = (nenTang === 0 || nenTang === 3)
      ? Buffer.from(b).swap16().toString('utf16le')
      : b.toString('latin1');
    if (chu && !lay[maID]) lay[maID] = chu.replace(/\0/g, '').trim();
  }
  // 16/17 = tên theo cách xếp kiểu chữ hiện đại, đúng hơn 1/2 khi họ font có nhiều độ đậm
  const ho = lay[16] || lay[1] || '';
  const kieu = lay[17] || lay[2] || '';
  const day = lay[4] || `${ho} ${kieu}`.trim();
  return { ho, kieu, tenDayDu: day };
}

export function napFont(duongDan) {
  const buf = readFileSync(duongDan);
  const nhan = buf.readUInt32BE(0);
  if (nhan === 0x74746366) throw new Error('File .ttc (nhiều font gộp) chưa hỗ trợ - hãy dùng file .ttf/.otf rời');
  const bang = docBang(buf);
  for (const can of ['head', 'hhea', 'hmtx', 'cmap']) {
    if (!bang[can]) throw new Error(`Font thiếu bảng ${can}, không đọc được số đo`);
  }
  const donViEm = buf.readUInt16BE(bang.head.vt + 18);
  const soMetric = buf.readUInt16BE(bang.hhea.vt + 34);
  // File phụ đề ASS hiểu "cỡ chữ" là CHIỀU CAO CẢ DÒNG (đỉnh chữ tới đuôi chữ),
  // còn CSS hiểu là chiều cao thân chữ (em). Hai bên lệch nhau một hệ số cố định
  // của từng font. Không nhân hệ số này thì phụ đề ra nhỏ hơn thiết kế khoảng 25%.
  const dinh = buf.readInt16BE(bang.hhea.vt + 4);
  const duoi = buf.readInt16BE(bang.hhea.vt + 6);
  const heSoASS = (dinh - duoi) / donViEm;

  // CHIỀU CAO CHỮ HOA: cần khi bắt chước cỡ chữ theo một video mẫu.
  // Trên video ta đo được chiều cao chữ hoa (đo được bằng mắt/bằng máy), còn cỡ chữ
  // là con số bên trong font -> phải có tỉ lệ này mới quy đổi qua lại được.
  let caoChuHoa = 0;
  if (bang['OS/2'] && buf.readUInt16BE(bang['OS/2'].vt) >= 2) {
    caoChuHoa = buf.readInt16BE(bang['OS/2'].vt + 88);
  }
  if (!caoChuHoa || caoChuHoa <= 0) caoChuHoa = Math.round(donViEm * 0.7); // font không khai thì ước lượng
  const tiLeCaoChuHoa = caoChuHoa / donViEm;
  const map = docCmap(buf, bang.cmap.vt);

  const beNgangGlyph = (g) => {
    const i = Math.min(g, soMetric - 1);
    const o = bang.hmtx.vt + i * 4;
    return o + 1 < buf.length ? buf.readUInt16BE(o) : 0;
  };

  const ten = bang.name ? docTen(buf, bang.name) : { ho: '', kieu: '', tenDayDu: '' };

  return {
    duongDan,
    donViEm,
    heSoASS,
    tiLeCaoChuHoa,
    ...ten,
    coKyTu: (ch) => map.has(ch.codePointAt(0)),
    // bề ngang một câu, tính theo đơn vị em (chưa nhân cỡ chữ)
    beNgangEm(cau) {
      let tong = 0;
      for (const ch of cau) {
        const g = map.get(ch.codePointAt(0));
        tong += beNgangGlyph(g ?? 0);
      }
      return tong / donViEm;
    },
    beNgang(cau, coChu) { return this.beNgangEm(cau) * coChu; },
  };
}

// ---------- kiểm font có đủ dấu tiếng Việt ----------
// 134 ký tự riêng của tiếng Việt (có dấu), viết hoa và viết thường.
export const CHU_VIET = (() => {
  const t = 'àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ';
  return [...t, ...t.toLocaleUpperCase('vi-VN')];
})();

export function kiemDauViet(font) {
  const thieu = CHU_VIET.filter((c) => !font.coKyTu(c));
  return { dat: thieu.length === 0, thieu, tong: CHU_VIET.length };
}
