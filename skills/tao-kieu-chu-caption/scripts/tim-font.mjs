// TÌM FILE FONT theo tên - để kiểu chữ không phải ghi cứng đường dẫn kiểu "C:/Windows/Fonts/...".
// Ghi cứng thì chuyển máy khác là gãy: Mac, Linux, hay Windows cài font ở thư mục người dùng.
//
// Thứ tự tìm: kho font đi kèm skill -> kho font riêng -> thư mục font của hệ điều hành.
// Nhờ vậy chuyển giao chỉ cần chép thư mục skill, người nhận thả font vào fonts/ là chạy.
import { existsSync, readdirSync, statSync } from 'node:fs';
import { join, dirname, isAbsolute, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir, platform } from 'node:os';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..');
const DUOI = ['.ttf', '.otf', '.TTF', '.OTF'];

export function thuMucFont() {
  // Chế độ thử "máy sạch": chỉ cho dùng kho font đi kèm skill, chặn hết font hệ thống.
  // Dùng để chứng minh skill chạy được trên máy chưa cài font gì thêm.
  if (process.env.CHI_KHO_SKILL) return [join(GOC, 'fonts')];
  const nha = homedir();
  const ds = [
    join(GOC, 'fonts'),                                   // kho font đi kèm skill
    process.env.KHO_FONT,                                 // kho font riêng, tự đặt
  ];
  // Font của các phần mềm dựng video: CapCut tải font về máy khi người dùng chọn font đó.
  // Đọc thẳng từ đây để dùng lại, KHÔNG chép đi nơi khác - font đó có bản quyền riêng.
  ds.push(join(nha, 'AppData/Local/CapCut/User Data/Resources/Font'));
  ds.push(join(nha, 'AppData/Local/CapCut/User Data/Cache/font'));
  ds.push(join(nha, 'Library/Containers/com.lemon.lvoverseas/Data/Documents/Resources/Font'));

  if (platform() === 'win32') {
    ds.push('C:/Windows/Fonts', join(nha, 'AppData/Local/Microsoft/Windows/Fonts'));
  } else if (platform() === 'darwin') {
    ds.push('/System/Library/Fonts', '/System/Library/Fonts/Supplemental', '/Library/Fonts', join(nha, 'Library/Fonts'));
  } else {
    ds.push('/usr/share/fonts', '/usr/local/share/fonts', join(nha, '.fonts'), join(nha, '.local/share/fonts'));
  }
  return ds.filter((d) => d && existsSync(d));
}

function quet(thuMuc, sau = 0) {
  const ra = [];
  if (sau > 3) return ra;
  let ds; try { ds = readdirSync(thuMuc); } catch { return ra; }
  for (const t of ds) {
    const d = join(thuMuc, t);
    let st; try { st = statSync(d); } catch { continue; }
    if (st.isDirectory()) ra.push(...quet(d, sau + 1));
    else if (DUOI.some((x) => t.endsWith(x))) ra.push(d);
  }
  return ra;
}

let boNho = null;
export function moiFont() {
  if (!boNho) boNho = thuMucFont().flatMap((d) => quet(d));
  return boNho;
}

// Nhận: đường dẫn đầy đủ, hoặc tên file ("seguibl.ttf"), hoặc tên font ("Segoe UI Black").
export function timFont(ten) {
  if (!ten) throw new Error('Chưa nói dùng font nào');
  if (isAbsolute(ten) && existsSync(ten)) return ten;

  const ds = moiFont();
  const goi = basename(ten).toLowerCase();
  const khop = ds.find((d) => basename(d).toLowerCase() === goi);
  if (khop) return khop;

  // so theo tên font ghi bên trong file (chậm hơn, chỉ dùng khi không khớp tên file)
  const goiGon = ten.toLowerCase().replace(/[\s_-]/g, '');
  const theoTen = ds.find((d) => basename(d).toLowerCase().replace(/[\s_-]/g, '').replace(/\.(ttf|otf)$/, '') === goiGon);
  if (theoTen) return theoTen;

  throw new Error(
    `Không tìm thấy font "${ten}".\n` +
    `  Đã tìm trong: ${thuMucFont().join(' · ')}\n` +
    `  Cách chữa: chép file font vào thư mục fonts/ của skill, hoặc cài font đó vào máy.`
  );
}
