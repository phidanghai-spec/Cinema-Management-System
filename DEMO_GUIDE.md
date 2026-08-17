# 🎬 CINEVERSE — TÀI LIỆU DEMO ĐỒ ÁN TOÀN DIỆN

> **Phiên bản:** Final | **Ngày:** 30/07/2026  
> **Hệ thống:** Quản lý Rạp Chiếu Phim CineVerse — Django (Python) + MySQL + Glassmorphism Dark UI  
> **Quy mô:** 92 unit tests | 15 Design Patterns | 8 phim | 4 phòng chiếu | 2 rạp

---

## 📋 MỤC LỤC

1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Hướng Dẫn Demo Nhanh](#2-hướng-dẫn-demo-nhanh)
3. [Toàn Bộ Chức Năng](#3-toàn-bộ-chức-năng)
4. [15 Design Patterns — Giải Thích Chi Tiết](#4-15-design-patterns--giải-thích-chi-tiết)
5. [Kiến Trúc Tổng Thể](#5-kiến-trúc-tổng-thể)
6. [Câu Hỏi Thường Gặp Khi Bảo Vệ](#6-câu-hỏi-thường-gặp-khi-bảo-vệ)

---

## 1. TỔNG QUAN HỆ THỐNG

CineVerse là nền tảng đặt vé rạp chiếu phim trực tuyến đầy đủ chức năng, xây dựng theo mô hình **Layered Architecture** kết hợp **15 Design Patterns** chuẩn Gang of Four.

### Thông Tin Truy Cập

| Vai Trò | Email | Mật Khẩu | Quyền Hạn |
|---------|-------|----------|-----------|
| 👤 Khách hàng | `customer@cinema.com` | `customer123` | Đặt vé, xem lịch sử, quản lý watchlist |
| ⚙️ Quản trị viên | `admin@cinema.com` | `admin123` | Dashboard, quản lý phim/suất chiếu, quét QR |

```
Địa chỉ local: http://127.0.0.1:8000/
Mã giảm giá thử: SUMMER2026 (giảm 20%)
```

---

## 2. HƯỚNG DẪN DEMO NHANH

### Luồng Demo Đề Xuất (15–20 phút)

```
[1] Trang Chủ       → Hero Carousel + Danh sách phim + Suất chiếu hôm nay
[2] Chi Tiết Phim   → Backdrop blur + Rating + Lịch chiếu theo ngày
[3] Đặt Vé (Wizard 3 bước):
      Bước 1: Sơ đồ ghế ngồi - chọn ghế VIP / Thường / Couple
      Bước 2: Chọn Combo thức ăn (Solo / Đôi / Gia Đình / VIP)
      Bước 3: Thanh toán - Stripe Card hoặc MoMo + mã giảm giá
[4] Vé Điện Tử      → QR Code thực + nút In vé
[5] Hồ Sơ          → Lịch sử đặt vé + Điểm tích lũy + Phim yêu thích
[6] Admin Dashboard → Biểu đồ doanh thu Canvas + Quét QR xác thực vé
[7] Quản Lý Phim   → CRUD phim + suất chiếu
```

---

## 3. TOÀN BỘ CHỨC NĂNG

### A. Xác Thực và Tài Khoản

| Chức năng | URL | Mô tả |
|-----------|-----|-------|
| Đăng ký | `/register/` | Tạo tài khoản mới với validation email |
| Đăng nhập | `/login/` | Xác thực email + mật khẩu, kiểm tra banned |
| Quên mật khẩu | `/forgot-password/` | Gửi link đặt lại mật khẩu qua email |
| Đặt lại mật khẩu | `/reset-password/<token>/` | Token có thời hạn 1 giờ |
| Đăng xuất | `/logout/` | Xóa session |

### B. Duyệt Phim

| Chức năng | URL | Mô tả |
|-----------|-----|-------|
| Trang chủ | `/` | Hero carousel, phim nổi bật, suất chiếu hôm nay |
| Danh sách phim | `/?status=now_showing` | Lọc: Đang chiếu / Sắp chiếu |
| Chi tiết phim | `/movie/<id>/` | Thông tin, trailer, lịch suất chiếu, đánh giá |
| Theo thể loại | `/genre/<name>/` | Lọc phim theo thể loại |
| Tìm kiếm | `/?q=<keyword>` | Tìm theo tên phim |

### C. Đặt Vé (Booking Wizard 3 Bước)

| Bước | Nội dung |
|------|---------|
| Bước 1 — Chọn Ghế | Sơ đồ ghế SVG tương tác, phân loại VIP/Thường/Couple |
| Bước 2 — Chọn Combo | 4 combo: Solo 75k / Đôi 105k / Gia Đình 155k / VIP 135k |
| Bước 3 — Thanh Toán | Stripe Card / MoMo Wallet, mã giảm giá, đổi điểm tích lũy |

### D. Sau Đặt Vé

| Chức năng | Mô tả |
|-----------|-------|
| Vé điện tử | QR Code thực, thông tin đầy đủ, nút in |
| Lịch sử đặt vé | Danh sách tất cả đơn hàng, trạng thái |
| Hủy vé | Hoàn tiền 90% nếu trước giờ chiếu 2 tiếng |

### E. Tính Năng Xã Hội và Trung Thành

| Chức năng | Mô tả |
|-----------|-------|
| Phim yêu thích | Toggle thêm/xóa, hiển thị tại tab Profile |
| Watchlist | Danh sách "xem sau" |
| Đánh giá | Rating 1–5 sao + bình luận văn bản |
| Điểm tích lũy | 1 điểm / 10.000đ chi tiêu, đổi giảm giá |
| Hạng thành viên | Bronze / Silver / Gold / Platinum tự động |
| Thông báo In-App | Thông báo xác nhận/hủy vé trong ứng dụng |
| Khuyến mãi | Hiển thị toàn bộ mã giảm giá đang hoạt động |

### F. Module Quản Trị (Admin)

| Chức năng | Mô tả |
|-----------|-------|
| Dashboard | Doanh thu, biểu đồ Canvas, top phim bán chạy |
| Quản lý phim | Thêm/Sửa/Xóa phim |
| Quản lý suất chiếu | Lịch chiếu theo phòng |
| Quản lý người dùng | Ban/Unban tài khoản |
| Xác thực QR vé | Quét mã QR - xác nhận vé tại quầy |
| Hủy vé (admin) | Hủy bất kỳ đơn hàng nào |

---

## 4. 15 DESIGN PATTERNS — GIẢI THÍCH CHI TIẾT

> **File triển khai chính:** `cinema/patterns.py` (1.100+ dòng)

---

### NHÓM CREATIONAL — Khởi Tạo Đối Tượng

---

### 1. SINGLETON — SystemSettings

**Định nghĩa:** Singleton là mẫu thiết kế thuộc nhóm Creational, đảm bảo một class **chỉ có đúng một instance duy nhất** trong toàn bộ vòng đời chương trình và cung cấp một điểm truy cập toàn cục tới instance đó. Thường dùng cho các đối tượng quản lý trạng thái dùng chung: cấu hình hệ thống, kết nối DB, logger.

**Áp dụng trong CineVerse:** Đảm bảo chỉ tồn tại **duy nhất một instance** của cấu hình hệ thống trong suốt vòng đời ứng dụng.

**Cách hoạt động:**
```python
class SystemSettings:
    _instance = None          # Biến lớp lưu instance duy nhất

    def __new__(cls):
        if cls._instance is None:   # Lần đầu gọi -> tạo mới
            cls._instance = super().__new__(cls)
            cls._instance.cancellation_fee_percent = 10   # Phí hủy 10%
            cls._instance.seat_lock_timeout_minutes = 10  # Khóa ghế 10 phút
            cls._instance.tax_rate = 0.08                 # Thuế 8%
            cls._instance.points_conversion_rate = 10000  # 1 điểm / 10.000đ
        return cls._instance    # Lần sau gọi -> trả về instance cũ
```

**Tại sao cần:** Nếu phí hủy vé là 10%, mọi nơi trong hệ thống phải thấy con số này giống nhau. Nếu dùng nhiều instance, mỗi nơi có thể đọc giá trị khác nhau dẫn đến sai lệch tính toán hoàn tiền.

**Demo khi bảo vệ:** Gọi `SystemSettings()` hai lần, kiểm tra `id()` — cùng địa chỉ bộ nhớ, chứng tỏ chỉ có 1 instance.

---

### 2. BUILDER — BookingBuilder

**Định nghĩa:** Builder là mẫu thiết kế thuộc nhóm Creational, tách biệt quá trình **xây dựng một đối tượng phức tạp** ra khỏi phần biểu diễn của nó. Cho phép tạo cùng một kiểu đối tượng theo nhiều cách bằng cách gọi tuần tự các method thiết lập từng thuộc tính — tránh Telescoping Constructor Anti-pattern (constructor quá nhiều tham số).

**Áp dụng trong CineVerse:** Xây dựng đối tượng `Booking` phức tạp theo từng bước, thay vì nhét tất cả vào một constructor khổng lồ.

**Cách hoạt động:**
```python
# KHÔNG dùng Builder (xấu — Telescoping Constructor):
Booking(user, showtime, seats, combo, discount, notes, points, ...)

# DÙNG Builder (tốt):
booking = BookingBuilder(user, showtime) \
    .set_seats([seat_A1, seat_B2])       \
    .apply_combo([combo_id])             \
    .apply_discount("SUMMER2026")        \
    .use_points(50)                      \
    .build()                             # Gọi cuối cùng -> trả về Booking hoàn chỉnh
```

**Tại sao cần:** Một đơn đặt vé có 7+ thành phần (User, Showtime, Seats, Combo, Discount, Notes, Points). Builder giúp mỗi bước chỉ làm 1 việc, code dễ đọc và test từng phần độc lập.

**Demo:** Khi khách đặt vé qua wizard 3 bước, mỗi bước "Tiếp tục" thực ra là gọi một method của Builder.

---

### 3. FACTORY METHOD — PaymentProcessorFactory

**Định nghĩa:** Factory Method là mẫu thiết kế thuộc nhóm Creational, định nghĩa một **interface để tạo đối tượng** nhưng cho phép subclass hoặc logic nội bộ quyết định class nào sẽ được khởi tạo. Caller chỉ biết interface chung — không phụ thuộc vào class cụ thể. Thường dùng khi cần linh hoạt trong lựa chọn implementation tại runtime.

**Áp dụng trong CineVerse:** Tạo đối tượng xử lý thanh toán phù hợp dựa trên phương thức người dùng chọn, không cần biết class cụ thể là gì.

**Cách hoạt động:**
```python
class PaymentProcessorFactory:
    @staticmethod
    def create(method: str) -> PaymentGateway:
        if method == "credit_card":
            return StripeAdapter()    # Trả về adapter Stripe
        elif method == "momo":
            return MomoAdapter()      # Trả về adapter MoMo
        else:
            raise ValueError(f"Unknown payment method: {method}")

# Sử dụng — view không cần biết Stripe hay MoMo:
processor = PaymentProcessorFactory.create(user_choice)
processor.charge(amount, customer_info)   # Cùng một interface!
```

**Tại sao cần:** Thêm phương thức thanh toán mới (VNPay, ZaloPay) chỉ cần thêm 1 class Adapter mới và 1 dòng trong Factory — không sửa code View hay Service.

**Demo:** Bước 3 wizard — chọn Stripe thì Factory trả StripeAdapter, chọn MoMo thì trả MomoAdapter.

---

### 4. PROTOTYPE — MoviePrototype và ShowtimePrototype

**Định nghĩa:** Prototype là mẫu thiết kế thuộc nhóm Creational, cho phép **sao chép (clone) một đối tượng hiện có** để tạo ra đối tượng mới thay vì khởi tạo từ đầu. Hữu ích khi chi phí tạo mới cao hoặc khi đối tượng mới chỉ khác bản gốc một vài thuộc tính nhỏ.

**Áp dụng trong CineVerse:** Nhân bản đối tượng phim/suất chiếu hiện có mà không cần khởi tạo lại từ đầu.
**Cách hoạt động:**
```python
class MoviePrototype:
    def clone(self):
        """Sao chép object này, reset id để tạo bản ghi mới."""
        cloned = copy.copy(self)
        cloned.pk = None          # Reset PK -> Django tạo ID mới khi save
        cloned.title += " (Copy)"
        return cloned
 
# Admin dùng:
original = Movie.objects.get(id=1)
new_movie = MoviePrototype(original).clone()
new_movie.title = "Avatar: Fire and Ash"
new_movie.save()  # Tạo phim mới với toàn bộ thuộc tính giống bản gốc
```

**Tại sao cần:** Khi admin cần tạo 10 suất chiếu cùng phim cho 10 ngày, thay vì nhập lại từng trường — clone() sao chép nhanh, chỉ cần đổi ngày chiếu.

---

### NHÓM STRUCTURAL — Cấu Trúc Liên Kết

---

### 5. ADAPTER — StripeAdapter và MomoAdapter

**Định nghĩa:** Adapter là mẫu thiết kế thuộc nhóm Structural, hoạt động như một **bộ chuyển đổi** giữa hai interface không tương thích. Giống như ổ cắm điện đa năng — cho phép các thiết bị có phích cắm khác nhau (API bên thứ ba) kết nối vào cùng một ổ cắm chung (interface hệ thống) mà không cần thay đổi bên nào.

**Áp dụng trong CineVerse:** Bọc các API bên thứ ba có interface khác nhau (Stripe, MoMo) vào cùng một interface chung `PaymentGateway`.

**Cách hoạt động:**
```
Stripe API gốc:   stripe.make_payment(amount_in_CENTS, token)
MoMo API gốc:     momo.request_payment(order_id, amount_VND, redirect_url, ...)

             ↓ Adapter chuyển đổi ↓

Giao diện chung:  processor.charge(amount_VND, customer_info)
                  processor.refund(transaction_id, amount)
```

**Tại sao cần:** Stripe tính tiền bằng cents (USD), MoMo tính bằng VND và cần redirect URL. Adapter chuẩn hóa sự khác biệt — BookingFacade chỉ gọi `charge()` mà không cần biết đang dùng Stripe hay MoMo.

---

### 6. DECORATOR — VIPSeatPriceDecorator và CoupleSeatPriceDecorator

**Định nghĩa:** Decorator là mẫu thiết kế thuộc nhóm Structural, cho phép **gắn thêm hành vi vào đối tượng một cách động** bằng cách bọc (wrap) đối tượng gốc trong một wrapper class. Là giải pháp thay thế cho kế thừa khi cần kết hợp nhiều tính năng linh hoạt — tránh bùng nổ số lượng subclass.

**Áp dụng trong CineVerse:** Thêm phụ thu động vào giá ghế tại runtime, không cần tạo subclass riêng cho mỗi loại ghế.

**Cách hoạt động:**
```
BaseSeat(price=100.000đ)
  -> VIPSeatPriceDecorator(seat)     -> price = 100.000 x 1.5 = 150.000đ
  -> CoupleSeatPriceDecorator(seat)  -> price = 100.000 x 2.0 = 200.000đ
```

```python
class VIPSeatPriceDecorator(SeatPriceDecorator):
    VIP_MULTIPLIER = 1.5
    def get_price(self):
        return self._seat.get_price() * self.VIP_MULTIPLIER  # Bọc thêm phụ thu

class CoupleSeatPriceDecorator(SeatPriceDecorator):
    COUPLE_MULTIPLIER = 2.0
    def get_price(self):
        return self._seat.get_price() * self.COUPLE_MULTIPLIER
```

**Tại sao cần:** Thay vì tạo riêng `StandardSeat`, `VIPSeat`, `CoupleSeat`... Decorator cho phép chồng lớp tính năng bất kỳ lúc nào mà không bùng nổ số lượng class.

**Demo:** Chọn ghế VIP trên sơ đồ — giá tự động nhân 1.5 hiện ở panel tổng kết phải.

---

### 7. FACADE — BookingFacade

**Định nghĩa:** Facade là mẫu thiết kế thuộc nhóm Structural, cung cấp một **interface đơn giản hóa** cho một hệ thống con phức tạp. Che giấu sự phức tạp bên trong — client chỉ tương tác với Facade mà không cần biết bên dưới có bao nhiêu thành phần và chúng phối hợp với nhau như thế nào.

**Áp dụng trong CineVerse:** Cung cấp một điểm vào duy nhất đơn giản cho toàn bộ quy trình đặt vé phức tạp (8 bước, 5+ subsystems).

**Cách hoạt động:**
```
View.py chỉ gọi:
  BookingFacade.create_booking(user, showtime, seats, payment_method, ...)

Facade tự điều phối bên dưới:
  1. Builder.build_booking(...)       -> Tạo đơn hàng
  2. DiscountChain.validate(code)     -> Kiểm tra mã giảm giá
  3. PricingStrategy.calculate(...)   -> Tính giá theo giờ/ngày
  4. SeatDecorator.wrap(seats)        -> Áp phụ thu ghế VIP/Couple
  5. PaymentFactory.create(method)    -> Lấy processor phù hợp
  6. Processor.charge(amount)         -> Thực hiện thanh toán
  7. BookingWorkflow.execute(...)     -> Chạy Template Method
  8. Observer.notify(booking)         -> Gửi thông báo Email + InApp
```

**Tại sao cần:** Nếu không có Facade, View phải tự biết và gọi tất cả 8 bước trên — God Class. Facade đóng gói độ phức tạp, View chỉ cần 1 lời gọi duy nhất.

---

### NHÓM BEHAVIORAL — Hành Vi Tương Tác

---

### 8. STRATEGY — WeekdayPricing / WeekendPricing / HolidayPricing

**Định nghĩa:** Strategy là mẫu thiết kế thuộc nhóm Behavioral, định nghĩa một **họ các thuật toán**, đóng gói từng thuật toán vào class riêng biệt và cho phép **hoán đổi chúng linh hoạt tại runtime**. Client chỉ làm việc với interface chung, không phụ thuộc vào implementation cụ thể — tuân thủ Open/Closed Principle.

**Áp dụng trong CineVerse:** Thay đổi thuật toán tính giá vé linh hoạt theo ngày/giờ mà không cần `if-else` cứng nhắc.

**Cách hoạt động:**
```python
class WeekdayPricing(PricingStrategy):
    def calculate_price(self, base_price):
        return base_price * 0.9       # Giảm 10% ngày thường

class WeekendPricing(PricingStrategy):
    def calculate_price(self, base_price):
        return base_price * 1.2       # Tăng 20% cuối tuần

class HolidayPricing(PricingStrategy):
    def calculate_price(self, base_price):
        return base_price * 1.3       # Tăng 30% ngày lễ

# Tự động chọn:
def get_pricing_strategy(showtime_dt):
    if is_holiday(showtime_dt):         return HolidayPricing()
    if showtime_dt.weekday() >= 5:      return WeekendPricing()
    return WeekdayPricing()
```

**Tại sao cần:** Khi thêm "Happy Hour giảm 15%" chỉ cần thêm class `HappyHourPricing` — không sửa code cũ, không vi phạm Open/Closed Principle.

---

### 9. OBSERVER — EmailNotifier và InAppNotifier

**Định nghĩa:** Observer là mẫu thiết kế thuộc nhóm Behavioral, định nghĩa mối quan hệ **một-nhiều (one-to-many)** giữa các đối tượng: khi một Subject thay đổi trạng thái, tất cả Observer đăng ký sẽ **tự động được thông báo**. Còn gọi là mô hình Publish-Subscribe.

**Áp dụng trong CineVerse:** Khi trạng thái đơn hàng thay đổi, tự động thông báo nhiều bên (Email, In-App) mà không cặp đôi chúng với nhau.

**Cách hoạt động:**
```
Booking -> trạng thái thay đổi -> notify() -> tất cả Observer

                 Booking (Subject)
                     | notify()
         ┌───────────┴───────────┐
    EmailNotifier          InAppNotifier
    (gửi email mô phỏng)   (tạo thông báo DB)
```

**Tại sao cần:** Nếu sau này thêm "SMS Notifier" — chỉ tạo class mới + attach vào Subject, không cần sửa bất kỳ dòng code nào trong logic đặt vé.

**Demo:** Đặt vé xong — check tab Hộp Thư ở Profile — thấy thông báo In-App mới.

---

### 10. CHAIN OF RESPONSIBILITY — DiscountValidator

**Định nghĩa:** Chain of Responsibility là mẫu thiết kế thuộc nhóm Behavioral, cho phép **truyền request qua một chuỗi các handler** theo thứ tự. Mỗi handler quyết định xử lý request hay chuyển tiếp cho handler tiếp theo. Tách biệt người gửi và người xử lý, tăng tính linh hoạt trong việc thêm/bớt bước xử lý.

**Áp dụng trong CineVerse:** Xử lý yêu cầu áp mã giảm giá qua chuỗi kiểm tra tuần tự, mỗi mắt xích chỉ xử lý phần của mình.

**Cách hoạt động:**
```
Nhập mã "SUMMER2026"
    ↓
ExpiryValidator        -> Hết hạn chưa?            -> CÒN HẠN -> chuyển tiếp
    ↓
MinimumAmountValidator -> Đủ giá trị tối thiểu?    -> ĐỦ -> chuyển tiếp
    ↓
GlobalUsageValidator   -> Còn lượt dùng hệ thống?  -> CÒN -> chuyển tiếp
    ↓
UserUsageLimitValidator -> User đã dùng quá chưa?  -> CHƯA -> Áp dụng thành công!
```

**Tại sao cần:** Thêm điều kiện mới ("chỉ áp dụng cho VIP member") chỉ cần thêm `VIPMemberValidator` vào chuỗi, không sửa các validator cũ.

---

### 11. STATE — PendingState / ConfirmedState / CompletedState / CancelledState

**Định nghĩa:** State là mẫu thiết kế thuộc nhóm Behavioral, cho phép đối tượng **thay đổi hành vi khi trạng thái nội tại thay đổi** — trông như thể đối tượng đó đổi class. Đóng gói mỗi trạng thái vào class riêng, tránh chuỗi `if/else` kiểm tra trạng thái phân tán khắp codebase.

**Áp dụng trong CineVerse:** Quản lý vòng đời đơn đặt vé với các quy tắc chuyển trạng thái nghiêm ngặt.

**Cách hoạt động:**
```
Trạng thái hợp lệ:
  PENDING -> CONFIRMED -> COMPLETED
                 |
            CANCELLED (chỉ khi còn trước 2 tiếng)

Trạng thái KHÔNG hợp lệ -> ném InvalidStateTransitionException
```

```python
class CompletedState(BookingState):
    def cancel(self, booking):
        raise InvalidStateTransitionException(
            "Không thể hủy đơn đã hoàn thành"   # Chặn
        )
```

**Tại sao cần:** Thay vì `if booking.status == "confirmed" and ...` ở khắp nơi — State Pattern tập trung toàn bộ logic chuyển trạng thái vào một nơi duy nhất.

---

### 12. TEMPLATE METHOD — StandardBookingWorkflow

**Định nghĩa:** Template Method là mẫu thiết kế thuộc nhóm Behavioral, định nghĩa **khung xương (skeleton) của một thuật toán** trong base class và để subclass thay thế các bước cụ thể mà không thay đổi cấu trúc tổng thể. Thứ tự các bước luôn được đảm bảo nhất quán — khác với Strategy (hoán đổi hoàn toàn thuật toán).

**Áp dụng trong CineVerse:** Định nghĩa khung xương quy trình đặt vé 6 bước cố định, cho phép subclass thay đổi chi tiết từng bước.

**Cách hoạt động:**
```python
class BookingWorkflow(ABC):
    # Template Method — khung cố định, KHÔNG override
    def execute(self, builder):
        self.validate_seats(builder)      # Bước 1: Kiểm tra ghế
        self.compile_pricing(builder)     # Bước 2: Tính giá
        self.apply_discount(builder)      # Bước 3: Áp mã giảm
        self.process_payment(builder)     # Bước 4: Thanh toán
        self.transition_state(builder)    # Bước 5: Đổi trạng thái
        self.send_notifications(builder)  # Bước 6: Thông báo

    @abstractmethod
    def validate_seats(self, builder): pass   # Subclass tự implement
```

**Tại sao cần:** Mọi loại đặt vé đều phải đi qua đúng 6 bước theo đúng thứ tự. Template Method đảm bảo không bước nào bị bỏ sót.

---

### 13. COMMAND — BookCommand và CancelCommand

**Định nghĩa:** Command là mẫu thiết kế thuộc nhóm Behavioral, **đóng gói một yêu cầu thành một đối tượng độc lập** chứa đầy đủ thông tin để thực hiện hành động đó. Cho phép xếp hàng chờ, ghi log kiểm toán, hỗ trợ undo/redo. Tách biệt hoàn toàn caller (người gọi) và executor (người thực thi).

**Áp dụng trong CineVerse:** Đóng gói yêu cầu đặt/hủy vé thành đối tượng riêng biệt để ghi log kiểm toán tự động và tách biệt View khỏi logic xử lý.

**Cách hoạt động:**
```python
class BookCommand(Command):
    def execute(self):
        # Ghi log kiểm toán TRƯỚC khi thực hiện
        PatternExecutionLog.objects.create(
            pattern_name="Command",
            action="BookCommand.execute",
            user=self.user
        )
        facade = BookingFacade()
        self.booking = facade.create_booking(...)
        return self.booking
```

**Tại sao cần:** View chỉ tạo Command object và gọi `.execute()`. Log kiểm toán tự động ghi lại mọi hành động — nhìn thấy được trên Admin Dashboard dưới mục lịch sử Design Pattern.

---

### NHÓM ARCHITECTURAL — Kiến Trúc Tổng Thể

---

### 14. MODEL-VIEW-TEMPLATE (MVT)

**Định nghĩa:** MVT là biến thể của mẫu kiến trúc MVC do Django sử dụng, **tách biệt ứng dụng thành 3 thành phần độc lập**: Model (dữ liệu + ORM), View (xử lý request + điều phối response), Template (hiển thị HTML). Mỗi thành phần có trách nhiệm riêng biệt — thay đổi một phần không ảnh hưởng phần khác.

**Áp dụng trong CineVerse:** Tách biệt dữ liệu, logic điều hướng, và giao diện thành 3 tầng độc lập xuyên suốt toàn bộ hệ thống.

```
models.py   -> Model: Định nghĩa bảng DB, quan hệ, validation
views.py    -> View (Controller): Xử lý request, session, redirect
templates/  -> Template: HTML render giao diện cho người dùng

HTTP Request -> urls.py -> views.py -> models.py (query DB)
                                    -> templates/ (render HTML)
                                    <- HTTP Response
```

**Tại sao cần:** Nếu giao diện thay đổi chỉ sửa templates, không chạm vào logic. Nếu DB thay đổi chỉ sửa models. Mỗi tầng độc lập, dễ test riêng lẻ.

---

### 15. REPOSITORY — Data Access Layer

**Định nghĩa:** Repository là mẫu kiến trúc tạo ra một **lớp trừu tượng hóa giữa tầng nghiệp vụ và tầng truy cập dữ liệu**. Tập trung toàn bộ logic truy vấn DB vào một nơi duy nhất, giúp business logic không phụ thuộc trực tiếp vào ORM hay SQL. Dễ test (có thể mock Repository) và dễ bảo trì khi đổi DB.

**Áp dụng trong CineVerse:** Tách biệt câu truy vấn DB phức tạp khỏi tầng Service và View vào các Repository class riêng biệt.

**Cách hoạt động:**
```python
# KHÔNG dùng Repository (xấu — query rò rỉ ra View):
def booking_view(request):
    bookings = Booking.objects.filter(user=request.user, status="confirmed") \
        .select_related('showtime__movie')...   # Rò rỉ ra View!

# DÙNG Repository (tốt):
class BookingRepository:
    def get_user_bookings(self, user):
        return Booking.objects.filter(user=user) \
            .select_related('showtime__movie', ...) \
            .prefetch_related('items') \
            .order_by('-created_at')

def booking_view(request):
    bookings = BookingRepository().get_user_bookings(request.user)  # Sạch sẽ!
```

**File:** `cinema/repositories.py` chứa 5 repositories: `MovieRepository`, `BookingRepository`, `ShowtimeRepository`, `UserRepository`, `SeatRepository`.

---

## 5. KIẾN TRÚC TỔNG THỂ

```
┌──────────────────────────────────────────────────┐
│           PRESENTATION LAYER                     │
│  templates/ (HTML + CSS + JavaScript)            │
│  Glassmorphism Dark UI | Poppins + Inter Fonts   │
└──────────────────┬───────────────────────────────┘
                   |
┌──────────────────▼───────────────────────────────┐
│           VIEW / CONTROLLER LAYER                │
│  views.py (Customer) | views_admin.py (Admin)   │
│  urls.py (Routing)   | decorators.py (Auth)     │
└──────────────────┬───────────────────────────────┘
                   |
┌──────────────────▼───────────────────────────────┐
│           SERVICE / BUSINESS LOGIC LAYER         │
│  services.py                                     │
│  (MovieService, BookingService, UserService...)  │
└──────────────────┬───────────────────────────────┘
                   |
┌──────────────────▼───────────────────────────────┐
│           DESIGN PATTERNS ENGINE                 │
│  patterns.py (15 patterns, 1100+ lines)          │
│  Singleton | Builder | Factory | Prototype       │
│  Adapter | Decorator | Facade                    │
│  Strategy | Observer | Chain | State             │
│  Template Method | Command                       │
└──────────────────┬───────────────────────────────┘
                   |
┌──────────────────▼───────────────────────────────┐
│           REPOSITORY / DATA ACCESS LAYER         │
│  repositories.py (5 repositories)               │
└──────────────────┬───────────────────────────────┘
                   |
┌──────────────────▼───────────────────────────────┐
│           DATABASE LAYER                         │
│  MySQL via Django ORM | 15 Models               │
│  User, Movie, Theater, Screen, Seat, Showtime    │
│  Booking, BookingItem, Combo, Payment, Discount  │
│  Review, Favorite, Watchlist, InAppNotification  │
└──────────────────────────────────────────────────┘
```

### Bản Đồ 15 Patterns

| # | Pattern | Nhóm | Chức năng | Class chính |
|---|---------|------|-----------|-------------|
| 1 | Singleton | Creational | Cấu hình hệ thống toàn cục | `SystemSettings` |
| 2 | Builder | Creational | Tạo đơn đặt vé phức tạp | `BookingBuilder` |
| 3 | Factory Method | Creational | Chọn cổng thanh toán | `PaymentProcessorFactory` |
| 4 | Prototype | Creational | Sao chép phim/suất chiếu | `MoviePrototype`, `ShowtimePrototype` |
| 5 | Adapter | Structural | Tích hợp Stripe và MoMo API | `StripeAdapter`, `MomoAdapter` |
| 6 | Decorator | Structural | Phụ thu ghế VIP và Couple | `VIPSeatPriceDecorator`, `CoupleSeatPriceDecorator` |
| 7 | Facade | Structural | Điều phối quy trình đặt vé | `BookingFacade` |
| 8 | Strategy | Behavioral | Tính giá theo ngày/giờ | `WeekdayPricing`, `WeekendPricing`, `HolidayPricing` |
| 9 | Observer | Behavioral | Gửi thông báo đặt/hủy vé | `EmailNotifier`, `InAppNotifier` |
| 10 | Chain of Responsibility | Behavioral | Xác thực mã giảm giá | `ExpiryValidator`, `MinAmountValidator`... |
| 11 | State | Behavioral | Vòng đời trạng thái đơn hàng | `PendingState`, `ConfirmedState`, `CancelledState` |
| 12 | Template Method | Behavioral | Quy trình đặt vé có trật tự | `StandardBookingWorkflow` |
| 13 | Command | Behavioral | Đóng gói và log hành động | `BookCommand`, `CancelCommand` |
| 14 | MVT | Architectural | Tách biệt 3 tầng MVC | Django framework |
| 15 | Repository | Architectural | Tách biệt truy vấn DB | `BookingRepository`, `MovieRepository`... |

---

## 6. CÂU HỎI THƯỜNG GẶP KHI BẢO VỆ

**Q: Tại sao chọn Django thay vì Flask?**
> Django có ORM, admin, auth, migration tích hợp sẵn — phù hợp hệ thống quy mô vừa với nhiều tính năng phức tạp. Flask phù hợp microservice nhỏ hơn.

**Q: Sự khác biệt giữa Facade và Mediator?**
> Facade đơn giản hóa interface với subsystem theo 1 chiều (View gọi Facade). Mediator điều phối 2 chiều giữa các object ngang hàng với nhau.

**Q: Tại sao BookingItem.combo dùng SET_NULL thay CASCADE?**
> Khi admin xóa combo, lịch sử giao dịch (BookingItem) phải được giữ nguyên để bảo toàn tính toàn vẹn dữ liệu lịch sử và số liệu doanh thu. SET_NULL chỉ mất liên kết, không mất dòng doanh thu.

**Q: Observer vs Strategy khác nhau chỗ nào?**
> Observer: 1 sự kiện phát ra cho nhiều subscriber phản ứng (broadcast). Strategy: chọn 1 thuật toán trong nhiều lựa chọn tại runtime (selection).

**Q: 92 test bao phủ những phần nào?**
> Design Patterns, Repositories, Services (booking, cancel, auth, notify), API Endpoints, và các edge cases như: banned user, insufficient points, invalid state transition, unauthorized cancel.

**Q: Tại sao không dùng Django REST Framework?**
> API nội bộ đủ dùng với JsonResponse. DRF thêm overhead không cần thiết cho hệ thống monolithic này. Nếu mở rộng sang mobile app thì DRF là bước tiếp theo tự nhiên.

**Q: Template Method và Strategy khác nhau chỗ nào?**
> Template Method: khung cố định, subclass thay thế từng bước cụ thể (kế thừa). Strategy: hoán đổi hoàn toàn thuật toán tại runtime (composition). Booking dùng cả hai: Template Method cho thứ tự bước, Strategy cho thuật toán giá.

---

*CineVerse — Đồ Án Tốt Nghiệp | Django + Python + MySQL*
