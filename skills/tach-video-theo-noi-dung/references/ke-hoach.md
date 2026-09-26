# Bảng chia nội dung

`bai-hoc.json` trong công việc. Ví dụ cấu trúc (các mốc chỉ minh họa):
```json
{
  "approved": false,
  "allow_reuse": false,
  "lessons": [
    {
      "id": "bai-1",
      "title": "Tên chủ đề theo lời giảng",
      "summary": "Người xem học được gì; những điểm cần xem lại.",
      "segments": [
        {"start": "00:02:00", "end": "00:05:30"},
        {"start": "00:06:10", "end": "00:08:00"}
      ]
    }
  ]
}
```
Mỗi id duy nhất, chỉ chữ/số/gạch ngang. Dùng giây hoặc HH:MM:SS. Các đoạn một bài tăng dần, không chồng nhau; toàn bộ nằm trong phần đã phiên âm. allow_reuse chỉ bật khi chủ ý dùng lại một đoạn cho nhiều bài. Công cụ kiểm tra mốc, không tự hiểu chủ đề thay AI.

Khi đổi đoạn, tên hoặc tóm tắt, bảng cần duyệt lại. Nếu muốn cả bộ bài học và clip ngắn từ cùng nguồn: lập hai công việc với bảng riêng, dùng phiên âm đã có để tránh gọi API lại. Đối với nguồn toàn buổi từ mốc 0, phien-am.json có thể nhập lại trực tiếp. Với công việc bắt đầu khác 0 phải trừ mốc start trước khi nhập, vì file nhập dùng mốc tương đối.
