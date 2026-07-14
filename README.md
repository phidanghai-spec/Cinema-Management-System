# 🎬 CineVerse — Hệ Thống Quản Lý Rạp Chiếu Phim Chuyên Nghiệp

> **Một ứng dụng quản lý đặt vé rạp chiếu phim chuyên nghiệp được xây dựng bằng Django (Python), tích hợp 12 mẫu thiết kế phần mềm (Design Patterns) chuẩn mực cùng giao diện Glassmorphism Dark UI hiện đại.**

---

## 🔑 Tài Khoản Thử Nghiệm (Test Credentials)

| Vai trò | Email | Mật khẩu | Mô tả |
|---------|-------|----------|-------|
| 👤 **Khách hàng (Customer)** | `customer@cinema.com` | `customer123` | Tài khoản đặt vé, xem lịch sử đặt vé, quản lý watchlist |
| ⚡ **Quản trị viên (Admin)** | `admin@cinema.com` | `admin123` | Truy cập trang Dashboard, xác thực vé QR, quản lý phim/suất chiếu |

🎟️ **Mã giảm giá thử nghiệm:** `SUMMER2026` (Giảm 20% đơn hàng)  
📍 **Địa chỉ chạy local:** http://127.0.0.1:8000/

---

## 🚀 Hướng Dẫn Khởi Chạy Dự Án Nhanh (Quick Start)

### 1. Tạo và Kích hoạt Môi trường ảo (Virtual Environment)
Mở terminal/Command Prompt tại thư mục dự án và chạy:

**Trên Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Trên macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Cài đặt các thư viện phụ thuộc (Dependencies)
```bash
pip install -r requirements.txt
```

### 3. Thực thi di cư Cơ sở dữ liệu (Migrations)
```bash
python manage.py migrate
```

### 4. Tạo dữ liệu mẫu (Seeding Database)
Chạy script seed dữ liệu mẫu để tạo tài khoản, phim, phòng chiếu, suất chiếu và ghế ngồi tự động:
```bash
python seed.py
```

### 5. Chạy máy chủ phát triển (Run Server)
```bash
python manage.py runserver
```
Sau khi chạy thành công, truy cập trình duyệt tại địa chỉ [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🧪 Hệ Thống Kiểm Thử (Unit Tests)

Dự án sở hữu bộ unit test bao phủ toàn bộ chức năng từ Design Patterns, Repositories, Services đến API Endpoints với **92 ca kiểm thử** hoàn chỉnh.

Chạy toàn bộ unit tests bằng lệnh:
```bash
python manage.py test cinema -v 2
```

---

## 🏗️ Thiết Kế Kiến Trúc & 15 Design Patterns Áp Dụng

Hệ thống được thiết kế theo mô hình phân lớp chuẩn:
`Template / Frontend (MVT)` ➔ `View (Controller)` ➔ `Service (Business Logic)` ➔ `Repository (Data Access)` ➔ `Database (MySQL)`

Dưới đây là danh sách các mẫu thiết kế phần mềm được tích hợp trực tiếp trong mã nguồn:

1. **Model-View-Template (MVT):** Cấu trúc chuẩn của Django phân tách rõ ràng giao diện, cơ sở dữ liệu và logic điều hướng.
2. **Singleton (`SystemSettings`):** Quản lý cấu hình toàn hệ thống (phí hủy vé, thuế suất, tỷ lệ quy đổi điểm) đảm bảo duy nhất một thực thể cấu hình tồn tại.
3. **Factory (`PaymentProcessorFactory`):** Khởi tạo bộ xử lý thanh toán tương ứng dựa trên phương thức người dùng chọn (`momo` hoặc `credit_card`).
4. **Strategy (Pricing Strategy):** Tính toán giá vé linh hoạt dựa trên thời gian chiếu (`WeekdayPricing` - giảm 10%, `WeekendPricing` - tăng 20%, `HolidayPricing` - tăng 30`).
5. **Observer (Booking Notifications):** Tự động gửi Email mô phỏng và cập nhật thông báo In-App (`InAppNotification`) khi trạng thái đơn hàng thay đổi.
6. **Decorator (Seat Price Decorators):** Tính toán phụ thu động dựa trên loại ghế ngồi (`VIPSeatPriceDecorator` tăng 1.5 lần, `CoupleSeatPriceDecorator` tăng 2.0 lần trên giá gốc).
7. **Repository (Data Access Layer):** Phân tách các câu truy vấn phức tạp ra khỏi tầng xử lý logic nghiệp vụ qua lớp [`repositories.py`](cinema/repositories.py).
8. **Template Method (`StandardBookingWorkflow`):** Định nghĩa khung quy trình đặt vé chuẩn (Tạo nháp ➔ Áp mã ➔ Thanh toán ➔ Xác nhận ➔ Gửi thông báo).
9. **Chain of Responsibility (Discount Validation):** Chuỗi kiểm tra điều kiện áp dụng Voucher (Hạn sử dụng ➔ Giá trị tối thiểu ➔ Lượt dùng toàn hệ thống ➔ Lượt dùng của User).
10. **State (Booking Lifecycle):** Quản lý vòng đời đơn đặt vé (`PendingState` ➔ `ConfirmedState` ➔ `CompletedState` hoặc `CancelledState`) đi kèm điều kiện chuyển trạng thái nghiêm ngặt.
11. **Builder (`BookingBuilder`):** Hỗ trợ lắp ráp các thành phần phức tạp của đối tượng đặt vé (User, Showtime, Seats, Combo items, Discount, Notes) một cách tuần tự.
12. **Adapter (Payment Adapters):** Bọc các API không tương thích của bên thứ ba (`MomoAPI`, `StripeAPI`) về một giao diện chung duy nhất (`PaymentGateway`).
13. **Facade (`BookingFacade`):** Cung cấp giao diện cấp cao đơn giản điều phối đặt vé giữa builder, strategies, và workflow.
14. **Command (`BookCommand`, `CancelCommand`):** Đóng gói yêu cầu đặt vé/hủy vé thành các đối tượng riêng biệt để ghi log kiểm toán và quản lý giao dịch.
15. **Prototype (`MoviePrototype`, `ShowtimePrototype`):** Cho phép nhân bản đối tượng Phim/Suất chiếu nhanh chóng để hỗ trợ thiết lập lịch chiếu quy mô lớn.


---

## 🎨 Giao Diện Người Dùng (Glassmorphism Dark Theme)

* **Trang chủ (`pages/movie_list.html`):** Hero Carousel tự động trượt hiển thị 3 phim nổi bật, các thẻ phim ứng dụng hiệu ứng Hover Scale & Stagger Fade-in mượt mà.
* **Chi tiết phim (`pages/movie_detail.html`):** Ảnh nền mờ điện ảnh (Cinematic backdrop blur), widget chấm điểm sao tương tác trực quan.
* **Luồng đặt vé (`pages/booking_flow.html`):** Thanh tiến trình 3 bước trực quan, sơ đồ chọn ghế có armrest mô phỏng thực tế kèm hiệu ứng nảy (bounce) sinh động khi chọn.
* **Vé điện tử (`pages/booking_ticket.html`):** Render mã QR thực bằng `qrcode.js` từ CDN, hỗ trợ nút in vé nhanh và sao chép mã đặt vé kèm Toast thông báo.
* **Profile cá nhân (`pages/profile.html`):** Phân chia 5 tab nội dung (Lịch sử đặt vé, Phim yêu thích, Phim xem sau, Hộp thư thông báo, Cài đặt tài khoản) kèm thanh cấp độ thành viên (Loyalty progress bar) chuyển động mượt mà.
* **Trang Dashboard Admin (`pages/admin/dashboard.html`):** Biểu đồ doanh thu dạng đường cong Bezier vẽ bằng Canvas thuần, bảng xếp hạng phim bán chạy tích hợp thanh tỷ lệ phần trưng trực quan, ô quét QR xác thực vé trực tiếp tại quầy và lịch sử thực thi các design pattern.

