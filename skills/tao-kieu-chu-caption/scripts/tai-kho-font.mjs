// TẢI KHO FONT cho skill: font Việt hoá, miễn phí cho cả mục đích thương mại,
// lấy từ Google Fonts. Tải xong tự kiểm dấu tiếng Việt và LOẠI THẲNG font thiếu dấu.
//
// Cách chọn: phủ đủ các DÁNG CHỮ, không gom nhiều font cùng dáng. Mười font dáng tròn
// không bằng sáu font sáu dáng khác nhau - khi dò font giống video mẫu, cái quyết định
// là có đúng dáng hay không.
//
// Chỉ lấy độ đậm dùng cho phụ đề (SemiBold trở lên). Chữ mảnh không ai làm phụ đề.
import { writeFileSync, mkdirSync, existsSync, unlinkSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { napFont, kiemDauViet } from './do-font.mjs';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..');
const KHO = join(GOC, 'fonts');
const NGUON = 'https://github.com/google/fonts/raw/main';

// Google Fonts đã bỏ hết file rời từng độ đậm, chỉ còn bản "co giãn được".
// Bản co giãn KHÔNG dùng cho phụ đề được: nạp vào ra độ đậm mặc định (Montserrat ra
// bản Thin - mảnh dính). Nên phải lấy file rời từ kho gốc của từng họ font.
// Mọi đường dẫn dưới đây ĐÃ THỬ TẢI THẬT, không đoán.
const NGUON_RIENG = [
  { dang: 'hinh-hoc-vuong', ten: 'Montserrat',
    goc: 'https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf',
    dam: ['SemiBold', 'Bold', 'ExtraBold', 'Black'] },
  { dang: 'humanist', ten: 'OpenSans',
    goc: 'https://github.com/googlefonts/opensans/raw/main/fonts/ttf',
    dam: ['SemiBold', 'Bold', 'ExtraBold'] },
  { dang: 'hinh-hoc-tron', ten: 'Mulish',
    goc: 'https://github.com/googlefonts/mulish/raw/main/fonts/ttf',
    dam: ['SemiBold', 'Bold', 'ExtraBold', 'Black'] },
];

// nhóm dáng -> các họ font, kèm thư mục giấy phép trên kho Google Fonts
const DANH_SACH = [
  { dang: 'hinh-hoc-tron', mo_ta: 'Tròn trịa, thân thiện - reel đời sống, mẹ và bé', ho: [
    ['ofl', 'nunitosans', 'NunitoSans'], ['ofl', 'quicksand', 'Quicksand'],
    ['ofl', 'mulish', 'Mulish'], ['ofl', 'baloo2', 'Baloo2'] ] },
  { dang: 'hinh-hoc-vuong', mo_ta: 'Vuông vức, chắc chắn - reel kinh doanh, chuyên gia', ho: [
    ['ofl', 'montserrat', 'Montserrat'], ['ofl', 'bevietnampro', 'BeVietnamPro'],
    ['ofl', 'outfit', 'Outfit'], ['ofl', 'sora', 'Sora'] ] },
  { dang: 'grotesk-hien-dai', mo_ta: 'Trung tính, hiện đại - công nghệ, giáo dục', ho: [
    ['ofl', 'inter', 'Inter'], ['ofl', 'manrope', 'Manrope'], ['ofl', 'lexend', 'Lexend'],
    ['ofl', 'plusjakartasans', 'PlusJakartaSans'], ['ofl', 'figtree', 'Figtree'],
    ['ofl', 'urbanist', 'Urbanist'] ] },
  { dang: 'hep', mo_ta: 'Hẹp ngang, nhét được nhiều chữ - tin tức, thể thao', ho: [
    ['ofl', 'barlowcondensed', 'BarlowCondensed'], ['ofl', 'archivonarrow', 'ArchivoNarrow'],
    ['ofl', 'oswald', 'Oswald'], ['ofl', 'saira', 'Saira'] ] },
  { dang: 'dam-ap-phich', mo_ta: 'Rất đậm, hô to - bán hàng, khẩu hiệu', ho: [
    ['ofl', 'anton', 'Anton'], ['ofl', 'archivo', 'Archivo'], ['ofl', 'rubik', 'Rubik'] ] },
  { dang: 'humanist', mo_ta: 'Mềm, dễ đọc lâu - tài liệu, phỏng vấn', ho: [
    ['ofl', 'opensans', 'OpenSans'], ['ofl', 'worksans', 'WorkSans'],
    ['ofl', 'publicsans', 'PublicSans'], ['ofl', 'firasans', 'FiraSans'] ] },
];

const DO_DAM = ['SemiBold', 'Bold', 'ExtraBold', 'Black'];

function tai(duongDanKho, raFile) {
  try {
    execFileSync('curl', ['-sL', '--fail', '-o', raFile, `${NGUON}/${duongDanKho}`], { stdio: 'pipe' });
    return existsSync(raFile);
  } catch { return false; }
}

if (!existsSync(KHO)) mkdirSync(KHO, { recursive: true });

const so = { tai: 0, thieuDau: 0, khongCo: 0 };
const so2 = [];

for (const nhom of DANH_SACH) {
  for (const [giayPhep, thuMuc, ten] of nhom.ho) {
    for (const dam of DO_DAM) {
      const tenFile = `${ten}-${dam}.ttf`;
      const dich = join(KHO, tenFile);
      if (existsSync(dich)) { so2.push({ tenFile, dang: nhom.dang, sanCo: true }); continue; }
      // họ font kiểu mới chỉ có bản "co giãn được", bản rời nằm trong thư mục static/
      const duong = [`${giayPhep}/${thuMuc}/${tenFile}`, `${giayPhep}/${thuMuc}/static/${tenFile}`];
      let duoc = false;
      for (const d of duong) if (tai(d, dich)) { duoc = true; break; }
      if (!duoc) { so.khongCo++; if (existsSync(dich)) unlinkSync(dich); continue; }

      // kiểm ngay: font thiếu dấu tiếng Việt thì XOÁ, giữ lại chỉ tổ hại về sau
      try {
        const f = napFont(dich);
        const k = kiemDauViet(f);
        if (!k.dat) {
          unlinkSync(dich); so.thieuDau++;
          console.log(`  loại  ${tenFile.padEnd(30)} thiếu ${k.thieu.length} dấu tiếng Việt`);
          continue;
        }
        so.tai++;
        so2.push({ tenFile, ten: f.tenDayDu, dang: nhom.dang });
        console.log(`  lấy   ${tenFile.padEnd(30)} ${f.tenDayDu}`);
      } catch (e) {
        unlinkSync(dich); so.khongCo++;
      }
    }
  }
}

// ---- các họ chỉ còn file rời ở kho gốc của chính họ font đó ----
for (const nh of NGUON_RIENG) {
  for (const dam of nh.dam) {
    const tenFile = `${nh.ten}-${dam}.ttf`;
    const dich = join(KHO, tenFile);
    if (existsSync(dich)) { so2.push({ tenFile, dang: nh.dang, sanCo: true }); continue; }
    try {
      execFileSync('curl', ['-sL', '--fail', '--max-time', '60', '-o', dich, `${nh.goc}/${tenFile}`], { stdio: 'pipe' });
    } catch { so.khongCo++; continue; }
    if (!existsSync(dich)) { so.khongCo++; continue; }
    try {
      const f = napFont(dich);
      const k = kiemDauViet(f);
      if (!k.dat) { unlinkSync(dich); so.thieuDau++; console.log(`  loại  ${tenFile.padEnd(30)} thiếu ${k.thieu.length} dấu tiếng Việt`); continue; }
      so.tai++; so2.push({ tenFile, ten: f.tenDayDu, dang: nh.dang });
      console.log(`  lấy   ${tenFile.padEnd(30)} ${f.tenDayDu}`);
    } catch { unlinkSync(dich); so.khongCo++; }
  }
}

// ghi sổ: font nào thuộc dáng nào, để lệnh dò font gợi ý được nhóm dáng
const soTay = {
  ghi_chu: 'Kho font miễn phí cho cả mục đích thương mại, lấy từ Google Fonts. Mọi font ở đây ĐÃ KIỂM đủ dấu tiếng Việt.',
  nhom_dang: Object.fromEntries(DANH_SACH.map((n) => [n.dang, n.mo_ta])),
  font: so2,
};
writeFileSync(join(KHO, 'so-tay-font.json'), JSON.stringify(soTay, null, 2) + '\n', 'utf8');

const conLai = readdirSync(KHO).filter((f) => /\.(ttf|otf)$/i.test(f)).length;
console.log(`\nĐã lấy ${so.tai} font mới · loại ${so.thieuDau} font thiếu dấu tiếng Việt · ${so.khongCo} font không tải được`);
console.log(`Kho hiện có ${conLai} file font, chia ${DANH_SACH.length} nhóm dáng.`);
