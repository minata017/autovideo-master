# Điều phối autovideo-master

Đọc README.md, NOTICE.md và skill liên quan trước khi thực thi. Dùng Python của `.venv`; nếu thiếu chạy installer. Mọi chức năng cốt lõi gọi `autovideo.py`; không dùng hoặc tải các script khóa học cũ.

Nhận yêu cầu bằng tiếng Việt: xác định tạo từ kịch bản hay sửa video, khung hình, đoạn muốn xử lý. Chuẩn bị công việc riêng; kiểm tra phiên âm, đề xuất điểm cắt và cảnh trước khi xuất. Không tự cắt câu có nghĩa. Video riêng tư: có sự đồng ý trước khi đưa âm thanh lên Groq, phạm vi đồng ý phải khớp đoạn xử lý. Không in API key hay URL chứa key.

Tìm cảnh: xét nội dung, nguồn, kích thước từng file, không mặc định medium=1080p hoặc dùng orientation không được API hỗ trợ. Ghi selected trong canh.json sau khi xem ứng viên. Không tải cả kho. Không dùng SFX/BGM chưa xác minh quyền. Thành phẩm AI soạn đánh dấu [?] chờ chủ video duyệt.

Sau xuất đọc ket-qua.json, kiểm tra khung hình và âm thanh; báo đường dẫn thực, thời lượng đo và giới hạn. Không hứa đã nghe âm thanh nếu chưa nghe, không coi file tồn tại là đã kiểm thử tính năng. Không nén lại sau xuat. Giữ video gốc, .env và thành phẩm cũ.

Tách bản ghi thành bài học hoặc clip ngắn: đọc skills/tach-video-theo-noi-dung/SKILL.md và gọi tach-video.py. Cùng một workflow, hai mục đích lựa chọn theo yêu cầu. Lập bảng cụ thể chờ duyệt trước xuất. Chỉ sản xuất video; website khóa học là công việc khác, chưa nằm trong phạm vi.

Tách bản ghi thành bài học hoặc clip ngắn: đọc skills/tach-video-theo-noi-dung/SKILL.md và gọi tach-video.py. Cùng một workflow, hai mục đích lựa chọn theo yêu cầu. Lập bảng cụ thể chờ duyệt trước xuất. Chỉ sản xuất video; website khóa học là công việc khác, chưa nằm trong phạm vi.
