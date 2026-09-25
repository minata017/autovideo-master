---
name: dung-broll-collage
description: "CÔNG CỤ SINH CẢNH TRÁM B-ROLL phong cách cắt dán giấy (paper-collage stop-motion) để chèn vào video chính. Nhận câu thoại + độ dài + tỉ lệ khung → trả về file mp4 câm khớp ĐÚNG TỪNG KHUNG HÌNH; skill/agent biên tập tự ghép vào. Dựng hình ngay trên máy nên 0 đồng mỗi cảnh, không cài thêm gì, không tốn phí dịch vụ bên ngoài, và chạy được cả khi máy không có mạng. Dùng skill này khi: skill hay agent biên tập video cần cảnh trám mà kho cảnh quay không có gì hợp (câu nói trừu tượng: quy trình, tiền bạc, thời gian, AI, sai lầm); hoặc người dùng nói 'làm b-roll cho đoạn này', 'trám cảnh vào giây X', 'cần cảnh minh hoạ cho câu này', 'sinh b-roll collage', 'làm cảnh chèn kiểu cắt dán'. Việc nối tiếp: 'đổi màu cảnh trám', 'làm lại dài hơn', 'đổi sang khung ngang' - đều dùng skill này. KHÔNG dùng để: tìm chỗ nào trong video cần chèn b-roll (việc của trợ lý biên tập), ghép cảnh vào video, thay cảnh xấu đã quay, dựng cả một video hoàn chỉnh có lời dẫn, hay đắp chữ và hiệu ứng lên video quay người thật."
---

# Công cụ sinh cảnh trám B-roll cắt dán giấy

## Nói với người dùng thế nào (đọc trước tiên)

Người dùng skill này là **học viên đang học làm video**, không phải người viết phần mềm. Mọi câu bạn nói ra màn hình phải theo đúng những điều sau:

1. **Nói kết quả, đừng nói ruột máy.** Nói "đã dựng xong cảnh 3 giây, mở xem thử nhé" - **đừng** nói tên file, số dòng, tên thư viện, tên hàm, mã lỗi. Họ không cần và cũng không muốn biết.
2. **Hỏng thì nói phải làm gì**, đừng chỉ mô tả chỗ hỏng. "Máy chưa có ffmpeg, cài tại ffmpeg.org rồi mở lại Claude Code" - chứ không phải "ffprobe returned exit code 127".
3. **Đừng nhắc chuyện nội bộ của lớp**: không nói "báo thầy", "chờ vá ở kho gốc", "lỗi số 3 trong tài liệu", "kho upstream". Với học viên, công cụ này là thứ hoàn chỉnh - nhắc mấy chuyện đó chỉ làm họ thấy sản phẩm còn dở.
4. **Nếu bạn phát hiện lỗi thật trong chính công cụ**: cứ tự sửa nếu sửa được, rồi nói gọn "chỗ này tôi vừa chỉnh cho chạy đúng". Còn nếu cần người làm skill xử lý, nói một câu: *"chỗ này nên báo lại nhóm lớp"* - không phân tích dài dòng ra màn hình.
5. **Tiếng Việt có dấu, câu ngắn, không chen tiếng Anh** khi có từ tiếng Việt tương đương.

## Vai của skill này trong dây chuyền

Đây là **công cụ hậu kỳ nhỏ, được gọi** - không phải skill tự chạy một mình.

```
Skill/agent biên tập chính            dung-broll-collage (skill này)
─────────────────────────            ──────────────────────────────
1. Biên tập, quyết định đoạn
   nào cần b-roll
2. Ra lệnh: câu thoại + độ dài  ───►  3. Sinh cảnh trám đúng độ dài
   + tỉ lệ + fps + tông màu           (tự chọn ẩn dụ + màu theo câu nói)
5. Ghép cảnh vào video chính    ◄───  4. Trả file mp4 + bảng kê
```

**Skill này KHÔNG:** tự xem video để tìm chỗ trám · tự quyết định có nên chèn hay không · tự ghép vào video chính. Ba việc đó thuộc skill biên tập chính, vì chỉ nó nắm ý đồ tổng thể của video.

**Skill này CHỈ:** nhận yêu cầu → trả cảnh trám đạt chuẩn ghép.

## Chạy bằng gì

**HyperFrames** - đúng cỗ máy dựng hình đã cài ở bài 01 của nhóm này. **Không cài thêm thư viện nào.** Composition là một file HTML: hình vẽ bằng SVG, làm động bằng GSAP, render bằng `npx hyperframes render`.

Cần có: `node` · `ffmpeg` + `ffprobe` · HyperFrames CLI (`npx hyperframes`).

## Ba luật cứng (sai là hỏng khi ghép)

1. **Số khung = làm tròn(số giây × fps).** Skill chính cần 3,7 giây thì trả đúng 3,7 giây - không làm tròn lên 4, không mặc định 5 giây. Ghép lệch là hỏng tiếng.
2. **fps phải bằng fps video chính.** Lệch fps thì ghép vào giật. Skill chính không nói fps → hỏi, đừng đoán.
3. **Cảnh trám luôn CÂM.** Tiếng của video chính chạy đè lên. Không bao giờ sinh tiếng.

## Hợp đồng giao nhận

**Skill chính đưa vào** (mỗi cảnh trám một dòng):

| Trường | Bắt buộc | Nghĩa |
|---|---|---|
| `loi` | Có | Câu thoại tại chỗ trám - dùng để chọn ẩn dụ hình + màu |
| `bat_dau` + `ket_thuc` | Một trong hai | Mốc trên video chính (giây) → độ dài = hiệu hai số |
| `giay` | Một trong hai | Hoặc đưa thẳng độ dài |
| `khung` | Không | `9:16` (mặc định) · `16:9` · `1:1` · `4:5` |
| `fps` | Nên có | Mặc định 30 - phải khớp video chính |
| `mau_nen` / `mau_nhan` / `mau_chot` | Không | Ép màu; bỏ trống thì tự chọn theo nghĩa câu nói |
| `canh` | Không | Ép ẩn dụ (xem `--list-canh`); bỏ trống thì tự chọn |
| `ra` | Không | Đường dẫn file ra |

**Skill này trả về** - JSON in ra màn hình, skill chính đọc để ghép:

```json
{"so_canh": 2, "dat_chuan_het": true, "canh": [
  {"stt":1, "file":"...\\broll-01.mp4", "giay":3.2, "so_khung":80,
   "fps":25, "khung":"16:9", "canh":"thoi-gian-troi", "dat_chuan":true,
   "mau_nen":"#1b7d70", "bat_dau":10, "ket_thuc":13.2}
]}
```

## Thư viện ẩn dụ hình (5 cảnh)

Đây là thứ quyết định chất lượng: **mỗi câu thoại ra một hình khác nhau**. Không có nó thì chèn 5 chỗ b-roll là 5 lần giống hệt - nhìn phát chán ngay.

| Tên cảnh | Kể chuyện gì | Hợp câu nói về |
|---|---|---|
| `quay-cat-xuat-ban` | máy quay nhả phim → kéo cắt đứt → tay đặt nút play | làm video, quy trình, các bước |
| `thoi-gian-troi` | đồng hồ kim quay loạn → lịch rơi → cát chảy → dấu X | mất thời gian, thủ công, chậm trễ |
| `hon-loan-ngan-nap` | giấy bay lung tung → tủ hồ sơ → giấy xếp vào ngăn → tick | kiến thức rải rác, hệ thống hoá, bộ não thứ 2 |
| `tang-truong` | 4 cột mọc lên → mũi tên leo → đồng xu nảy | doanh thu, tăng gấp đôi, kết quả |
| `may-lam-thay` | 4 bánh răng ăn khớp quay → tay buông ra → nút nguồn | AI, tự động hoá, máy làm thay |

Xem danh sách bằng `--list-canh`. Không ép thì công cụ **tự chọn theo nghĩa câu nói** và **tự tránh lặp cảnh liền trước**.

## Cách gọi

```bash
# Cả loạt - KHUYẾN DÙNG: tự tránh trùng cảnh và màu giữa các đoạn
python scripts/lam_broll.py --bang yeucau.json --thu-muc "<thư-mục>/broll" --fps 30

# Một cảnh lẻ
python scripts/lam_broll.py --loi "AI cắt ghép thay bạn" --bat-dau 12.4 --ket-thuc 15.6 \
    --khung 16:9 --fps 30 --ra "<thư-mục>/broll/b1.mp4"

# Duyệt RẺ trước khi render: chỉ ra 1 ảnh tĩnh (~15 giây)
python scripts/lam_broll.py --loi "..." --giay 3 --ra out/a.mp4 --xem-truoc

# Xem có ẩn dụ nào / ép dùng một ẩn dụ cụ thể
python scripts/lam_broll.py --list-canh
python scripts/lam_broll.py --loi "..." --giay 3 --canh tang-truong --ra out/a.mp4

# Bám tông màu video chính (trích khung tại mốc lấy màu)
python scripts/lam_broll.py --bang yeucau.json --thu-muc out --tu-video "video-chinh.mp4"
```

File `yeucau.json`:
```json
[
  {"loi": "mỗi ngày bạn mất 2 tiếng dựng video thủ công", "bat_dau": 12.4, "ket_thuc": 15.6},
  {"loi": "AI làm thay bạn trong 5 phút", "giay": 3.5, "mau_nen": "#b3402e"}
]
```

## Tự bảo vệ (khỏi phải nhớ)

1. **Tự kiểm mọi file** bằng ffprobe ngay sau render: đúng số khung chưa · đúng fps chưa · đúng kích thước chưa · có lẫn tiếng không. Lệch thì ghi vào `canh_bao`, đặt `dat_chuan: false`, và **thoát với mã lỗi 2** - skill chính biết mà không ghép bừa vào video.
2. **Tự gỡ luồng tiếng** nếu lọt vào (chép luồng hình, không mã hoá lại).
3. **Không để lại rác**: mỗi lần chạy dựng một dự án HyperFrames trong thư mục tạm rồi xoá sạch.
4. **Báo lỗi rõ**: thiếu Node/ffmpeg, tên cảnh sai, thiếu độ dài - đều nói thẳng phải làm gì.
5. **Chịu được tiếng Việt có dấu** trong đường dẫn và lời thoại (đã ép UTF-8; trước đây lỗi này làm chết script *sau khi* đã render xong).

## Luật phong cách (giữ chất collage)

1. **3-6 vật chính**, mỗi vật một vai trong mạch - không nhồi.
2. **Ghép từ khung trống**: mảnh trượt/rơi/bật vào. Không fade, không zoom trôi.
3. **Nhịp stop-motion**: mọi tween dùng `ease:"steps(n)"` - giật nấc như chụp từng tấm giấy, không mượt kiểu máy tính. Mỗi mảnh còn có nhịp rung tay (`js_rung`).
4. **Mọi mảnh là giấy**: bóng đổ mềm, mép rách (`torn`), vật "ảnh" dùng hoạ tiết `ht` (halftone).
5. **Kể một mạch** theo thứ tự ghép, mảnh chốt vào cuối cùng có nhấn.
6. **Không chữ, không logo** trong hình - chữ là việc của phụ đề, đắp sau.
7. **Cuối cảnh vẫn động nhẹ**: bob, nháy, lấp lánh. Không đứng hình chết.

## Bố cục thích ứng theo khung

Hình gốc vẽ trên hệ toạ độ dọc 1080×1920. **Không được cắt xén** để ra khung ngang - cắt là mất vật chính. Mỗi cảnh có **bộ toạ độ riêng** cho dọc / ngang / vuông, tự xếp lại các cụm:

- **Dọc 9:16** - xếp trên → dưới.
- **Ngang 16:9** - xếp trái → phải; cảnh `quay-cat-xuat-ban` có đường phim chảy ngang riêng để không đứt mạch.
- **Vuông 1:1** - dồn gọn vào giữa.

## Hai bẫy kỹ thuật khi sửa cảnh

1. **GSAP ghi đè `transform` của SVG.** Nếu để GSAP làm động thẳng vào thẻ đã có `transform="translate(...)"`, nó xoá translate đó và mảnh văng khỏi vị trí. **Luôn bọc hai lớp** bằng hàm `mieng()`: lớp ngoài giữ vị trí, lớp trong mang `id` để GSAP đụng vào.
2. **Một thẻ không thể vừa `filter=` vừa `style="filter:"`** - cái sau nuốt cái trước (mất mép giấy rách). Tách hai lớp: ngoài đổ bóng, trong làm rách.

Ngoài ra: mảnh nào `mieng()` đặt `opacity="0"` thì animation **phải bật lại `opacity:1`**, và tâm xoay dùng `transformOrigin:"center"` (đừng dùng `svgOrigin` cho mảnh nằm trong nhóm đã dịch - tính sai).

## Thêm ẩn dụ mới (3 bước)

1. Viết một hàm trong `scripts/canh.py` theo đúng khuôn: nhận `(L, M)` → trả `(svg, js)`. Dùng lại `tam_giay()`, `mieng()`, `ban_tay()`, `js_rung()`, `defs()` - **đừng chép lại**.
2. Đăng ký vào `DS_CANH` cuối file `canh.py`.
3. Thêm một dòng từ khoá vào `BANG_CANH` trong `scripts/lam_broll.py`.

`L` cho biết khung ngang hay dọc (`L["wide"]`, `L["square"]`) để cảnh tự xếp bố cục; `M` là bộ màu đã chọn.

## Khi nào NÊN dùng cảnh trám collage

| Hợp | Không hợp |
|---|---|
| quy trình, hệ thống, các bước | cảnh có thật (sản phẩm, lớp học, khách hàng) |
| tiền bạc, thời gian, hiệu suất | mặt người, lời chứng |
| sai lầm, cảnh báo, rủi ro | thao tác màn hình (nên quay màn hình thật) |
| AI, tự động hoá, tương lai | địa điểm cụ thể |

Có cảnh quay thật hợp thì **luôn ưu tiên cảnh thật**. Collage là phương án khi kho cảnh bí.


## Tự kiểm trước khi trả kết quả

Năm mục đầu **công cụ tự làm** (xem `dat_chuan_het`); ba mục cuối cần mắt người:

```
[x] Số khung = làm tròn(giây × fps) - máy đo bằng ffprobe
[x] fps + kích thước khung đúng yêu cầu - máy đo
[x] File câm, không luồng tiếng - máy đo và tự gỡ
[x] Chịu được đường dẫn tiếng Việt có dấu
[x] Xoá sạch dự án tạm sau khi render
[ ] Đã xem khung QA: không mảnh nào cắt cụt / đè lên vật chính
[ ] Nhiều cảnh một loạt: ẩn dụ và màu không lặp nhau liên tiếp
[ ] Ẩn dụ hợp nghĩa câu thoại (máy đoán theo từ khoá, người soi lại)
```

## Ghi chú

Phong cách cắt dán giấy này học từ một công cụ mã nguồn mở cùng ý tưởng, nhưng bản
gốc phải trả tiền cho dịch vụ dựng video bên ngoài mỗi lần làm. Bản này dựng hình
ngay trên máy nên không tốn phí, độ dài tuỳ ý, và khớp đúng từng khung hình khi ghép.
