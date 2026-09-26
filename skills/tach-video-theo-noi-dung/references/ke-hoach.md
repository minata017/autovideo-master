# Cấu trúc bài học và video

Một bài học có thể gồm nhiều video; ghi chú/hoạt động là khối nằm giữa các video trong cùng bài. Ví dụ mốc chỉ minh họa:

```json
{
  "approved": false,
  "allow_reuse": false,
  "lessons": [{
    "id": "bai-1",
    "title": "Đọc sách và chọn hành động",
    "blocks": [
      {"type":"video", "id":"clip-1", "title":"Hướng dẫn đọc", "segments":[{"start":120,"end":150}]},
      {"type":"activity", "id":"tap-1", "kind":"practice", "instructions":"Đọc 8 phút rồi xem phần 2 bên dưới.", "duration_minutes":8, "duration_basis":"Theo lời giảng", "next_video":"clip-2", "placement":"between_videos", "removed_source":[150,630]},
      {"type":"video", "id":"clip-2", "title":"Chọn hành động", "segments":[{"start":630,"end":690}]}
    ]
  }]
}
```

Mỗi id bài học và mỗi id khối là duy nhất trong nhóm tương ứng, chỉ chữ/số/gạch ngang. Video có 1–100 segments theo giây hoặc HH:MM:SS; đoạn tăng dần, không chồng nhau và nằm trong phần đã phiên âm. allow_reuse chỉ bật khi chủ ý dùng lại nguồn.

Hoạt động có thể là practice, open-link hoặc assignment. instructions là lời hướng dẫn cho người học; có thể thêm url, completion_condition, duration_minutes (null nếu không có số phút), removed_source và verification. next_video phải là video phía sau trong cùng bài. Một hoạt động có thể nằm sau video cuối để giao bài tập sau buổi; khi đó không cần next_video. Phần thực hành cần xem liền mạch được giữ trong segments của video.

Không tạo bài học mới chỉ vì tách file video. Đổi mục tiêu học/chủ đề mới là cơ sở tạo bài mới. Bảng cũ chỉ có lessons[].segments vẫn đọc được, được hiểu là mỗi bài có một video.

Công cụ tạo danh-muc.json/CSV theo từng video có lesson_id, lesson_title, part_number và activities_after; cau-truc-bai-hoc.json giữ đủ bài và blocks có thứ tự kèm đường dẫn/status đầu ra để làm web sau này. Thư mục xuất nhóm theo bài, bên trong mỗi video có ghi-chu-bai-hoc.json. Không xây hoặc đăng web trong bước sản xuất video.

Đổi cách nhóm, thứ tự hoặc ghi chú cần duyệt lại, cũng như đổi tên/đoạn/tóm tắt. Nếu muốn cả bộ bài học và clip ngắn, lập hai công việc với bảng riêng, dùng phiên âm đã có. File nhập dùng mốc tương đối: công việc bắt đầu khác 0 phải trừ mốc start trước khi nhập.
