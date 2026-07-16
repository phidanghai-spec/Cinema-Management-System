# Checklist Bảo Vệ Đồ Án — CineVerse (MTKPM)
*Đã verify bằng cách chạy code thật (92/92 unit test pass, không suy đoán từ log/báo cáo)*

---

## PHẦN 0 — Trước khi bước vào phòng bảo vệ (15 phút)

- [ ] Chạy `python manage.py test cinema -v 1` ngay tại máy sẽ demo, xác nhận **92/92 pass**. Nếu máy giám khảo không có MySQL: đặt `DB_ENGINE=django.db.backends.sqlite3` trong `.env` (đã hỗ trợ fallback).
- [ ] Xoá `.env` thật chứa DB_PASSWORD nếu có, thay bằng bản sạch — đừng để lộ trên màn hình chiếu.
- [ ] Seed sẵn ít nhất: 1 tài khoản khách hàng có vé đã đặt, 1 tài khoản admin, 1 suất chiếu còn ghế trống, 1 mã giảm giá còn hiệu lực.
- [ ] Mở sẵn 2 tab trình duyệt: 1 tab khách hàng (đã login), 1 tab admin (đã login) — tránh mất thời gian đăng nhập giữa demo.
- [ ] Test trước luồng MoMo sandbox 1 lần trong ngày demo — nếu server MoMo sandbox down, chuẩn bị sẵn câu trả lời "hệ thống có `mock_momo_gateway` nội bộ để demo không phụ thuộc mạng ngoài" và chuyển sang dùng nó.
- [ ] Có sẵn 1 tab hiển thị `patterns.py` mở ở dòng đầu file (để lật nhanh khi được hỏi "pattern X nằm ở đâu").

---

## PHẦN 1 — Kịch bản demo 5 phút (theo luồng người dùng thật)

| Thời gian | Bước | Route | Pattern đang chứng minh ngầm |
|---|---|---|---|
| 0:00–0:30 | Vào trang chủ, lướt danh sách phim, chọn 1 phim | `/` → `/movie/<id>/` | Repository (lấy dữ liệu phim qua tầng Repository, không query trực tiếp trong view) |
| 0:30–1:00 | Bấm đặt vé, vào sơ đồ ghế, chọn ghế thường + 1 ghế VIP/Couple | `/booking/showtime/<id>/` | **Decorator** (giá ghế VIP/Couple được cộng thêm qua `SeatPriceDecorator`, không phải if/else cứng) |
| 1:00–1:45 | Thêm combo bắp nước, nhập mã giảm giá, bấm áp dụng | cùng trang | **Chain of Responsibility** (mã giảm giá chạy qua chuỗi validator: hạn dùng → số tiền tối thiểu → lượt dùng còn lại...) |
| 1:45–2:15 | Xác nhận đặt vé | `POST /api/booking/create/` | **Builder** (dựng đối tượng Booking phức tạp từng bước) + **Facade** (`BookingFacade` gom toàn bộ logic đặt vé thành 1 lời gọi) |
| 2:15–2:45 | Thanh toán qua MoMo sandbox | `/payment/mock-momo-gateway/` | **Adapter** (MomoAdapter chuyển đổi API MoMo về interface `PaymentGateway` chung) |
| 2:45–3:15 | Vé chuyển trạng thái Pending → Confirmed, có email/thông báo in-app | tự động sau thanh toán | **State** (chuyển trạng thái vé) + **Observer** (bắn thông báo qua `EmailObserver`, `InAppObserver`) |
| 3:15–3:45 | Chuyển qua tab Admin, vào Dashboard xem doanh thu/tỉ lệ lấp đầy | `/admin-dashboard/` | Service Layer (BookingService tổng hợp số liệu thật từ DB, không phải số giả) |
| 3:45–4:15 | Admin quét mã QR vé vừa đặt để xác thực | `/admin-dashboard/` → API verify | Đây là chỗ **đã vá XSS** — có thể chủ động nói: *"Tên khách hàng hiển thị ở đây được escape qua `escapeHtml()` trước khi chèn DOM để chống Stored XSS"* |
| 4:15–4:45 | Vào trang quản lý phim, dùng chức năng "nhân bản phim" (nếu có UI) hoặc nêu bằng lời | `/admin-dashboard/movies/` | **Prototype** (nhân bản Movie/Showtime thay vì tạo lại từ đầu) |
| 4:45–5:00 | Kết — nói câu chốt về kiến trúc | — | Tổng kết 15 pattern |

> Nếu thời gian gấp, có thể bỏ bước 4:15–4:45 (Prototype khó demo trực quan qua UI) và nói bằng lời thay vì click.

---

## PHẦN 2 — Bảng đối chiếu 15 Pattern (đã verify từng dòng bằng code + test thật)

| # | Pattern | Class chính trong `patterns.py` | Test class (số test) | Câu chốt 1 dòng khi bị hỏi |
|---|---------|----------------------------------|------------------------|------------------------------|
| 1 | Singleton | `SystemSettings` | `SingletonPatternTests` (3 test) | Đảm bảo cấu hình hệ thống (phí huỷ vé, tỉ lệ thuế...) chỉ tồn tại 1 instance duy nhất trong bộ nhớ |
| 2 | Factory | `PaymentProcessorFactory` | `FactoryPatternTests` (3 test) | Sinh đúng đối tượng cổng thanh toán (Stripe/MoMo) mà nơi gọi không cần biết chi tiết khởi tạo |
| 3 | Adapter | `StripeAdapter`, `MomoAdapter` | (gộp trong Factory tests) | Chuyển API bên thứ 3 (MoMo) về cùng 1 interface `PaymentGateway` chung |
| 4 | Strategy | `WeekdayPricing`, `WeekendPricing`, `HolidayPricing`, `HappyHourPricing` | `StrategyPatternTests` (4 test) | Đổi công thức tính giá vé theo ngày mà không sửa code nơi gọi |
| 5 | Observer | `EmailObserver`, `InAppObserver`, `BookingSubject` | `ObserverPatternTests` (2 test) | Khi đặt vé thành công, tự động bắn nhiều kênh thông báo mà không hard-code trong service |
| 6 | Decorator | `SeatPriceDecorator`, `VIPSeatPriceDecorator`, `CoupleSeatPriceDecorator` | `DecoratorPatternTests` (3 test) | Cộng thêm phụ phí ghế VIP/Couple bằng cách bọc lớp, không sửa class ghế gốc |
| 7 | Chain of Responsibility | `DiscountValidator` + 7 validator con | `ChainOfResponsibilityTests` (3 test) | Mã giảm giá phải đi qua chuỗi điều kiện độc lập, dễ thêm/bớt điều kiện mới |
| 8 | State | `PendingState`, `ConfirmedState`, `CompletedState`, `CancelledState` | `StatePatternTests` (4 test) | Vé chỉ được chuyển trạng thái hợp lệ (không thể Completed → Pending), logic nằm trong từng State class |
| 9 | Builder | `BookingBuilder` | `BuilderPatternTests` (5 test) | Dựng 1 booking phức tạp (ghế + combo + giảm giá + điểm thưởng) từng bước, tránh constructor 10 tham số |
| 10 | Template Method | `BookingWorkflow`, `StandardBookingWorkflow` | `TemplateMethodTests` (2 test) | Định nghĩa khung quy trình đặt vé cố định, cho phép override từng bước con |
| 11 | Repository | (trong `repositories.py`) | `RepositoryTests` (10 test) | Tách toàn bộ truy vấn DB khỏi Service — Service không biết ORM query cụ thể |
| 12 | Service Layer | `UserService`, `MovieService`, `BookingService` | `UserServiceTests`, `MovieServiceTests`, `BookingServiceTests` | Chứa business logic thuần, tách khỏi View (View chỉ điều phối HTTP) |
| 13 | Facade | `BookingFacade` | `FacadePatternTests` (1 test) | Gom toàn bộ bước đặt vé phức tạp (validate → build → thanh toán → thông báo) thành 1 lời gọi duy nhất cho View |
| 14 | Command | `BookCommand`, `CancelCommand` | `CommandPatternTests` (1 test) | Đóng gói hành động đặt/huỷ vé thành object — mở đường cho undo/queue/log sau này |
| 15 | Prototype | `MoviePrototype`, `ShowtimePrototype` | `PrototypePatternTests` (1 test) | Nhân bản phim/suất chiếu có sẵn để tạo suất mới nhanh, không nhập lại từ đầu |

**Cách chứng minh khi bị hỏi "em có chắc pattern này thật sự chạy không hay chỉ đặt tên class cho có?"**
→ Mở terminal, chạy trực tiếp:
```
python manage.py test cinema.tests.SingletonPatternTests -v 2
```
(thay tên class tương ứng) — cho giám khảo thấy test chạy pass ngay tại chỗ, không phải ảnh chụp màn hình.

---

## PHẦN 3 — Câu hỏi hay gặp + cách trả lời KHÔNG học thuộc lòng

Đọc kỹ 1 lần, hiểu bản chất, rồi **diễn đạt lại bằng lời của bạn** khi vào phòng — hội đồng dễ nhận ra câu trả lời học thuộc.

1. **"Sao không dùng Django Auth có sẵn mà tự viết?"**
   → Ý chính: `User` model là entity nghiệp vụ riêng, không kế thừa `AbstractUser`, để chủ động 100% logic phân quyền qua `role_required` decorator, tránh phụ thuộc cứng vào cơ chế auth mặc định của framework.

2. **"Repository và Service Layer khác nhau chỗ nào, sao cần cả 2?"**
   → Repository lo phần "lấy/lưu dữ liệu" (biết ORM, biết query). Service lo "nghiệp vụ" (tính điểm thưởng, kiểm tra điều kiện đặt vé...). Tách ra để đổi DB hoặc đổi ORM sau này không phải sửa logic nghiệp vụ.

3. **"Stored XSS là gì, em vá bằng cách nào?"**
   → Tên người dùng lấy từ DB bị chèn thẳng vào HTML qua `innerHTML` không escape → nếu tên chứa thẻ `<script>`, trình duyệt admin sẽ chạy đoạn script đó khi quét vé. Đã vá bằng hàm `escapeHtml()` mã hoá 5 ký tự đặc biệt (`& < > " '`) trước khi chèn vào DOM.

4. **"Dữ liệu nhạy cảm (SECRET_KEY, mật khẩu DB) em bảo mật thế nào?"**
   → Tách ra `.env`, đọc qua `python-decouple`, `.env` nằm trong `.gitignore` nên không lên GitHub. Có `.env.example` làm mẫu cho người khác chạy thử.

5. **"92 test case có thật sự chạy hết không hay là số ảo?"**
   → Chạy trực tiếp `python manage.py test cinema` ngay tại chỗ, cho giám khảo thấy kết quả `OK` với 92 test — không phải trình bày bằng slide.

---

*File này được tạo dựa trên việc đọc trực tiếp code trong repo (`patterns.py`, `tests.py`, `urls.py`) và chạy thật bộ test — không suy đoán từ tài liệu tự khai.*
