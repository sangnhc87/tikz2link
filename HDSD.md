Tuyệt vời! Viết một file hướng dẫn sử dụng (`HDSU.md`) là một thói quen cực kỳ tốt của một lập trình viên chuyên nghiệp. Nó giúp chính bạn và những người khác có thể quản lý và bảo trì dự án trong tương lai một cách dễ dàng.

Dưới đây là một file `HDSU.md` hoàn chỉnh, giải thích rõ ràng cách thay đổi tài khoản Cloudinary và các thông tin quan trọng khác.

---

### **Hướng dẫn sử dụng và bảo trì ứng dụng TikZ Converter**

Bạn có thể tạo một file mới trong dự án tên là `HDSU.md` và dán nội dung dưới đây vào.

```markdown
# Hướng dẫn sử dụng và bảo trì Ứng dụng TikZ Converter

Đây là tài liệu hướng dẫn quản lý, vận hành và bảo trì cho ứng dụng chuyển đổi TikZ sang ảnh, được triển khai trên nền tảng Fly.io và tích hợp với Cloudinary.

## Mục lục
1. [Cấu trúc dự án](#1-cấu-trúc-dự-án)
2. [Các công nghệ chính](#2-các-công-nghệ-chính)
3. [Quy trình triển khai (Deploy)](#3-quy-trình-triển-khai-deploy)
4. [**Cách thay đổi tài khoản Cloudinary**](#4-cách-thay-đổi-tài-khoản-cloudinary)
5. [Quản lý và theo dõi ứng dụng](#5-quản-lý-và-theo-dõi-ứng-dụng)
6. [Gỡ lỗi thường gặp](#6-gỡ-lỗi-thường-gặp)

---

### 1. Cấu trúc dự án

Dự án được tổ chức theo cấu trúc tiêu chuẩn của một ứng dụng Flask:

```
.
├── app.py              # Logic backend chính của ứng dụng
├── Dockerfile          # Công thức để xây dựng Docker image
├── fly.toml            # File cấu hình của Fly.io
├── requirements.txt    # Danh sách các thư viện Python cần thiết
├── static/             # Thư mục chứa các file tĩnh
│   ├── css/
│   │   └── ... (các file .css)
│   └── js/
│       └── ... (các file .js)
└── templates/          # Thư mục chứa các file template HTML
    ├── classic.html
    ├── exam_converter.html
    ├── library.html
    └── pro_uploader.html
```

---

### 2. Các công nghệ chính

- **Backend**: Python 3.11 với framework Flask.
- **Frontend**: HTML, CSS, Javascript.
- **Hosting**: [Fly.io](https://fly.io/)
- **Lưu trữ ảnh**: [Cloudinary](https://cloudinary.com/)
- **Biên dịch LaTeX**: [Tectonic](https://tectonic-typesetting.github.io/)
- **Chuyển đổi PDF -> PNG**: `pdftocairo` (từ bộ công cụ Poppler)
- **Đóng gói**: Docker

---

### 3. Quy trình triển khai (Deploy)

Mỗi khi có sự thay đổi trong code (ví dụ: sửa `app.py` hoặc các file HTML), bạn cần deploy lại để áp dụng thay đổi.

Chạy lệnh sau trong thư mục gốc của dự án:
```bash
flyctl deploy
```

Nếu bạn thay đổi các gói hệ thống trong `Dockerfile` (ví dụ: thêm một gói qua `apt-get`), bạn nên deploy với cờ `--no-cache` để đảm bảo image được build lại từ đầu:
```bash
flyctl deploy --no-cache
```

---

### 4. **Cách thay đổi tài khoản Cloudinary**

Đây là phần quan trọng nhất khi bạn hết dung lượng hoặc muốn chuyển sang một tài khoản Cloudinary khác. **Bạn không cần sửa bất kỳ dòng code nào trong ứng dụng.**

Toàn bộ thông tin nhạy cảm của Cloudinary được lưu trữ dưới dạng **"secrets"** trên Fly.io. Bạn chỉ cần cập nhật lại các secrets này.

**Các bước thực hiện:**

1.  **Chuẩn bị thông tin tài khoản Cloudinary mới:**
    *   Đăng nhập vào tài khoản Cloudinary mới.
    *   Vào **Dashboard** và lấy 3 thông tin sau:
        *   `Cloud Name`
        *   `API Key`
        *   `API Secret`

2.  **Mở Terminal** và di chuyển đến thư mục dự án của bạn.

3.  **Chạy 3 lệnh sau**, thay thế `GIA_TRI_MOI` bằng thông tin bạn vừa lấy. Lệnh `flyctl secrets set` sẽ tự động **ghi đè** lên giá trị cũ.

    ```bash
    # Cập nhật Cloud Name
    flyctl secrets set CLOUDINARY_CLOUD_NAME="GIA_TRI_MOI_CUA_CLOUD_NAME"

    # Cập nhật API Key
    flyctl secrets set CLOUDINARY_API_KEY="GIA_TRI_MOI_CUA_API_KEY"

    # Cập nhật API Secret
    flyctl secrets set CLOUDINARY_API_SECRET="GIA_TRI_MOI_CUA_API_SECRET"
    ```

4.  **Khởi động lại ứng dụng để áp dụng secrets mới:**
    Sau khi set secrets, bạn cần khởi động lại các máy ảo của ứng dụng để chúng nhận các biến môi trường mới.
    ```bash
    flyctl restart
    ```

**Xong!** Từ bây giờ, tất cả các ảnh mới sẽ được upload lên tài khoản Cloudinary mới của bạn. Các ảnh cũ vẫn nằm trên tài khoản cũ.

---

### 5. Quản lý và theo dõi ứng dụng

- **Xem log trực tiếp:**
  ```bash
  flyctl logs
  ```
- **Kiểm tra trạng thái các máy ảo:**
  ```bash
  flyctl status
  ```
- **Mở dashboard trên web:**
  ```bash
  flyctl open
  ```
- **Xem danh sách các secrets đã cài đặt:**
  ```bash
  flyctl secrets list
  ```

---

### 6. Gỡ lỗi thường gặp

- **Lỗi 502 Bad Gateway**: Thường do ứng dụng bị crash lúc khởi động. Chạy `flyctl logs` để xem traceback lỗi. Nguyên nhân phổ biến là thiếu thư viện trong `requirements.txt` hoặc lỗi cấu hình.
- **Lỗi 500 Internal Server Error**: Ứng dụng đã chạy nhưng bị lỗi khi xử lý request. Chạy `flyctl logs` để xem traceback lỗi logic trong `app.py`.
- **Xử lý TikZ thất bại**: Thường do file `.tex` sử dụng một gói LaTeX hiếm chưa được cài đặt trong `Dockerfile`. Cần thêm gói `texlive-...` tương ứng vào `Dockerfile` và deploy lại.
- **`TemplateNotFound`**: Lỗi trong `app.py` khi gọi `render_template` với một tên file không tồn tại trong thư mục `templates`. Kiểm tra lại tên file và cấu trúc thư mục.

```

Chúc bạn quản lý dự án thành công