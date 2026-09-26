# Bổ sung tách video theo nội dung — 26/09/2026 [?]

Một skill chung cho bài học và clip ngắn, engine tach-video.py. Phiên âm Groq chia phần, checkpoint từng phần, thử lại giới hạn; nhận dạng câu lặp để đối chiếu. Bảng nhiều đoạn một bài, kiểm tra mốc/range và duyệt lại khi đổi nội dung. Xuất hàng loạt, kiểm tra thời lượng hình/tiếng/phụ đề, giữ bản cũ; phục hồi bài lỗi/mất file và danh mục CSV/JSON/Markdown cục bộ. Khóa tiến trình tự giải phóng khi thoát. Bài học giữ kích thước nguồn, phụ đề rời; có lựa chọn gắn phụ đề/crop khi cần.

K31: phiên âm đủ 11 phần, 15.592 từ; phát hiện 34 mốc câu lặp cần đối chiếu. Đề xuất 16 bài từ cả buổi, chưa duyệt nội dung và chưa xuất toàn bộ bảng. Các mốc câu vẫn cần nghe lại khi duyệt.

Đã xuất thử hai bài từ video thật: 21s và 18s; hình/tiếng đúng thời lượng. 7 kiểm thử logic, thêm thử FFmpeg thật với video tự tạo: ghép đoạn, phụ đề rời, bỏ qua bài đã đạt và chỉ phục hồi bài thiếu phụ đề. Trạng thái cài mới/CI được ghi thêm sau khi chạy, không suy ra từ việc có file script.

Bộ cài Windows trong thư mục mới tự tải CPython 3.13.15 qua uv; doctor không có lỗi, khóa mẫu rỗng. Các hướng dẫn AI nằm trong dự án, không sửa cấu hình cá nhân. GitHub Actions chạy bộ cài trên windows-latest và macos-latest đều thành công tại commit 4366883: 5 kiểm thử timeline, 7 kiểm thử tách bài và xuất/tiếp tục/phục hồi phụ đề bằng FFmpeg trên video tổng hợp. Không gửi video K31 lên GitHub. Xem https://github.com/minata017/autovideo-master/actions/runs/36238843325 . Chưa kiểm thử giao diện thực tế của cả bốn trợ lý AI; dự án đã có file hướng dẫn tương ứng. Linux chưa kiểm thử native.
