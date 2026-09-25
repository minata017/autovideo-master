---
name: tao-kieu-chu-caption
description: |
  Kho kiểu chữ phụ đề cho video, và nhà máy đẻ ra kiểu chữ mới. Dùng skill này khi cần:
  gắn phụ đề vào video, chọn kiểu chữ phụ đề, đổi phụ đề sang IN HOA / chữ thường / Hoa Đầu Từ,
  tạo kiểu chữ phụ đề riêng theo màu thương hiệu, nhân bản một kiểu có sẵn thành biến thể mới,
  kiểm một file font có đủ dấu tiếng Việt không, hay hỏi "cỡ chữ phụ đề bao nhiêu là chuẩn".
  Kích hoạt khi người dùng nói: "gắn phụ đề", "làm phụ đề cho video", "đổi kiểu chữ phụ đề",
  "phụ đề chữ vàng/viền dày/nền đen", "phụ đề in hoa", "tạo kiểu chữ caption riêng",
  "font này có dấu tiếng Việt không", "chữ phụ đề to bao nhiêu", "caption giống CapCut".
  KHÔNG dùng để: bóc lời thoại ra file phụ đề (đó là việc của công cụ bóc băng),
  cắt/dựng video, hay làm hiệu ứng chữ động bay nhảy.
---

# Kiểu chữ phụ đề - kho dùng chung + nhà máy đẻ kiểu mới

Mọi skill, agent, hay AI khác đều gọi được skill này bằng lệnh. Không cần biết bên trong.

## Cần có trên máy

- **Node.js 18 trở lên** - chạy công cụ
- **ffmpeg** (có `libass`) - dựng phụ đề vào video
- Ít nhất một **file font đủ dấu tiếng Việt**

Kiểm nhanh: `node scripts/tu-kiem.mjs` - chạy hết bài kiểm, báo đạt/hỏng.

## Cách gọi

```bash
node scripts/caption.mjs liet-ke                       # xem kho có kiểu nào
node scripts/caption.mjs xem vien-day --che-do hoa     # dựng ảnh xem thử
node scripts/caption.mjs nuong phim.mp4 loi.srt vien-day --che-do hoa_dau
node scripts/caption.mjs xuat vien-day --dich css      # lấy CSS cho web/HTML
node scripts/caption.mjs xuat vien-day --dich ass --phu-de loi.srt --ra loi.ass
node scripts/caption.mjs nhan-ban vien-day --ten phu-de-vang --mau "#FFD84D"
node scripts/caption.mjs kiem-font duong/dan/font.ttf  # đủ dấu tiếng Việt không
node scripts/caption.mjs chuan-co                      # đo lại cỡ chữ chuẩn
```

## 4 chế độ chữ

Kiểu nào cũng dùng được cả 4, chọn bằng `--che-do`:

| Chế độ | Ra thế nào |
|---|---|
| `nguyen` | Anh ấy đã về nhà lúc trời vừa sẩm tối rồi. |
| `hoa` | ANH ẤY ĐÃ VỀ NHÀ LÚC TRỜI VỪA SẨM TỐI RỒI. |
| `thuong` | anh ấy đã về nhà lúc trời vừa sẩm tối rồi. |
| `hoa_dau` | Anh Ấy Đã Về Nhà Lúc Trời Vừa Sẩm Tối Rồi. |

**Mỗi chế độ mang cỡ chữ riêng đã đo sẵn.** Chữ in hoa chiếm chỗ rộng hơn chữ thường
khoảng 18%; dùng chung một cỡ thì bật IN HOA là phụ đề tràn xuống 2 dòng.

## Bắt chước kiểu chữ từ một video mẫu

Khi người dùng đưa video mẫu và muốn "làm giống caption của họ", làm theo đúng thứ tự:

**Bước 1 - Bóc khung ra nhìn.** `ffmpeg -ss <giây> -i mau.mp4 -frames:v 1 khung.png`.
Lấy 4-5 khung ở các đoạn khác nhau, đừng tin một khung.

**Bước 2 - Đo bằng máy, không ước lượng bằng mắt.** Lọc pixel sáng rồi tìm khung bao
quanh chữ: bề ngang, chiều cao, tâm dòng nằm ở bao nhiêu phần trăm chiều cao khung.

**Bước 3 - Ba bẫy phải tránh khi đo:**

1. **Dấu tiếng Việt làm chữ cao thêm ~1,6 lần.** Đo "VÀ CÁC BẠN CỨ ÁP DỤNG" ra 55px
   thì đó KHÔNG phải chiều cao thân chữ - `Ứ` có dấu trên, `Ạ Ụ` có dấu dưới. Chiều cao
   thân chữ thật chỉ khoảng 34px. Lấy nhầm là chữ to gấp rưỡi.
   Muốn đo thân chữ thì đo trên chữ KHÔNG DẤU, hoặc so bằng cùng một câu.
2. **Cùng chiều cao mà khác bề ngang nghĩa là khác font.** Đừng chỉnh cỡ chữ để chữa,
   phải đổi font hoặc bóp ngang bằng `bop_ngang`.
3. **Kích thước video mẫu thường không phải 1080x1920.** Mọi số đo phải quy về phần trăm
   khung rồi mới đem dùng.

**Bước 4 - So khớp từng điểm ảnh, KHÔNG đo mép ngoài.**

```bash
node scripts/caption.mjs so-khop <kiểu> khung-mau.png --chu "câu đang hiện" --toi-uu
```

Đo mép ngoài (rộng bao nhiêu, cao bao nhiêu) là phép đo THÔ và **rất dễ đánh lừa**:
hai dòng chữ trùng khít mép ngoài mà bên trong lệch hoàn toàn - sai font, sai khoảng
cách chữ, sai độ dày nét. Lệnh này chồng hai hình chữ lên nhau rồi đếm phần trùng
trên phần tổng, gọi là **độ trùng**.

Đọc kết quả:

| Độ trùng | Nghĩa |
|---|---|
| trên 85% | khớp tốt, dùng được |
| 70-85% | font gần giống, chưa đúng bản |
| dưới 70% | sai font, phải đổi |

Máy còn chỉ thẳng chỗ sai: cỡ chữ to/nhỏ bao nhiêu · bề ngang lệch riêng (dấu hiệu
sai font) · nét chữ dày/mảnh bao nhiêu (dấu hiệu sai độ đậm) · lệch dọc bao nhiêu px.

Thêm `--toi-uu` thì máy tự dò cỡ chữ, bóp ngang, giãn chữ và vị trí cho tới khi hết
cải thiện: dò thô trên lưới trước rồi tinh chỉnh, tránh kẹt ở điểm chưa phải tốt nhất.

**Bước 5 - Nếu độ trùng vẫn thấp, vấn đề nằm ở FONT.** Dò xem font nào trên máy giống nhất:

```bash
node scripts/caption.mjs tim-font-giong khung-mau.png --chu "câu đang hiện"
```

Lệnh này thử mọi font đủ dấu tiếng Việt trên máy; với mỗi font tự chỉnh cỡ và bóp ngang
cho khớp kích thước rồi mới chấm hình dáng, nên font rộng không bị trừ điểm oan.
Điểm cao nhất vẫn dưới 80% nghĩa là **font của mẫu không có trên máy** - phải nói thẳng
với người dùng và đề xuất tải font, đừng cố ép bằng bóp ngang.

**Bước 6 - Nhìn tận mắt.** Bộ so khớp xuất được ảnh chồng: đỏ = chữ mẫu, xanh lá = chữ
của mình, vàng = phần trùng. Nhiều vàng là khớp. Nhiều đỏ/xanh tách rời là chưa khớp.
Luôn xuất ảnh này cho người dùng xem, đừng chỉ đưa con số.

## Cỡ chữ lấy theo chuẩn Netflix

Netflix quy định **42 ký tự một dòng, tối đa 2 dòng**, và ghi cỡ chữ theo phần trăm
chứ không theo pixel. Nên "cỡ chuẩn" ở đây = cỡ để một câu 42 ký tự vừa khít
**vùng an toàn 80% bề ngang khung**. Máy tự đo trên chính font đang dùng, không đoán.

Đó là cách chuẩn cỡ mặc định (`chuan_co.kieu = "netflix"`). Kiểu chữ bắt chước video mẫu
thì dùng `chuan_co.kieu = "cao-chu"`: ấn định chiều cao thân chữ hoa theo phần trăm chiều
cao khung, cả 4 chế độ chữ dùng chung một cỡ.

**Cỡ chữ tự co theo kích thước video.** Kiểu chữ khai một khung mốc (`khung`), lúc nướng
máy đọc kích thước video thật rồi quy đổi. Không có bước này thì kiểu thiết kế ở 1080x1920
dựng lên video 720x1280 sẽ ra chữ to gấp rưỡi.

## Quy trình khi người dùng nhờ làm phụ đề

**Bước 1 - Hỏi cho đủ, đừng đoán.** Cần biết: video nào · file phụ đề nào ·
muốn kiểu chữ nào (đọc `liet-ke` ra cho họ chọn) · chế độ chữ nào.

**Bước 2 - Chọn kiểu theo nội dung**, gợi ý rồi để người dùng chốt:
- Video bán hàng, TikTok, Reels -> `vien-day` (viền dày, đọc được trên nền rối)
- Bài giảng, phỏng vấn, nội dung nghiêm túc -> `vien-mong`
- Nền video rối hoặc nhiều chữ sẵn -> `nen-khoi`
- Nhấn từ khoá, con số, lời hứa -> `gradient-vang`

**Bước 3 - Dựng ảnh xem thử TRƯỚC khi nướng cả video.**
`node scripts/caption.mjs xem <kiểu> --che-do <chế độ>` rồi cho người dùng nhìn.
Nướng cả video mất vài phút, xem trước mất vài giây.

**Bước 4 - Nướng vào video** bằng lệnh `nuong`.

**Bước 5 - Mở khung thành phẩm ra nhìn.** Không báo "xong" khi chưa nhìn thấy chữ
nằm đúng chỗ, đủ dấu tiếng Việt.

## Khi người dùng muốn kiểu chữ riêng

Dùng `nhan-ban`: lấy một kiểu gần giống nhất làm gốc rồi đổi phần khác.

```bash
node scripts/caption.mjs nhan-ban vien-day --ten phu-de-thuong-hieu \
  --mau "#FFD84D" --vien 8 --mau-vien "#1A1A1A" --mo-ta "Phụ đề màu thương hiệu"
```

Máy sẽ: tạo kiểu mới -> tự đo đủ 4 cỡ chữ -> **kiểm trùng với kho** -> cất vào kho riêng.

Kiểm trùng là bắt buộc: kho đầy kiểu na ná nhau thì vài tháng sau không ai tìm được gì.
Máy báo trùng thì dùng lại kiểu cũ, đừng ép tạo bản sao.

## Kho kiểu chữ nằm ở đâu

- **Kho đi kèm**: `kieu-chu/` trong skill - 4 kiểu mẫu, chuyển giao trọn gói.
- **Kho riêng**: `~/.kho-kieu-chu/` - kiểu người dùng tự tạo. Đổi chỗ bằng biến `KHO_KIEU_CHU`.

Tách hai kho để **nâng cấp skill không xoá mất kiểu người dùng tự tạo**.
Trùng tên thì kho riêng thắng.

## Font

Kiểu chữ ghi **tên font**, không ghi đường dẫn. Máy tự tìm trong: thư mục `fonts/` của
skill -> biến `KHO_FONT` -> thư mục font của hệ điều hành (Windows, macOS, Linux đều biết).

Chuyển giao cho người khác: chép cả thư mục skill, thả font vào `fonts/`, chạy được ngay.

**Font phải đủ dấu tiếng Việt.** Rất nhiều font đẹp thiếu `ắ ệ ỡ ữ` - dựng xong mới thấy
chữ vỡ. Luôn chạy `kiem-font` trước khi dùng font mới.

## Mấy điều máy không làm được, phải nói thẳng

Phụ đề nướng vào video đi qua đường ASS, đường này **không có** chữ đổ màu gradient,
không có chữ phát sáng, chỉ vẽ được một lớp viền, khối nền không bo góc được.
Khi dùng kiểu có mấy thứ đó, máy tự in ra dòng cảnh báo bắt đầu bằng `!` - **đọc nó
và nói lại cho người dùng**, đừng lờ đi rồi để họ tự phát hiện.

Muốn đủ hiệu ứng thì đi đường HTML (`--dich css`), dùng cho web hoặc công cụ dựng video
chạy nền trình duyệt.
