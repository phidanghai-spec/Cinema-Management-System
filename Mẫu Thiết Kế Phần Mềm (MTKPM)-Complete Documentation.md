# 🎬 Cinema Management System
## Mẫu Thiết Kế Phần Mềm (MTKPM) - Complete Documentation

**Môn học**: Mẫu Thiết Kế Phần Mềm  
**Tech Stack**: Python + Django/FastAPI + MySQL  
**Ngôn ngữ**: Vietnamese + English code examples

---

## 📋 Executive Summary

**Dự Án**: Xây dựng hệ thống quản lý rạp chiếu phim hoàn chỉnh
- **User Side**: 15 chức năng (Browse, Book, Pay, Review, etc)
- **Admin Side**: 15+ chức năng (Manage movies, theaters, revenue, etc)
- **Architecture**: Layered + 12 design patterns
- **Database**: MySQL với 12+ tables
- **Timeline**: 10 tuần phát triển

---

## 👥 USER FEATURES (Chi tiết - 15 Chức Năng)

### 1. **Authentication & Account**

#### 1.1 Đăng Ký (Register)
```
What: User tạo tài khoản mới
How: 
  - Nhập email, password, full name, phone
  - System validate: email unique, password strong
  - Send verification email
  - User confirm → Account active
Why: Cần xác minh danh tính, bảo mật

Flow:
POST /api/auth/register
Input: {email, password, name, phone}
→ Validate (email format, password strength)
→ Hash password (bcrypt)
→ Create user in DB
→ Send verification email
Output: {user_id, verification_token}
```

#### 1.2 Đăng Nhập (Login)
```
What: User xác thực danh tính
How:
  - Nhập email + password
  - System verify password
  - Return JWT token (valid 24h)
  - Token dùng cho các request sau
Why: Cần phân biệt user, bảo mật request

POST /api/auth/login
Input: {email, password}
→ Find user by email
→ Verify password (bcrypt.compare)
→ Generate JWT token
→ Return token + refresh_token
Output: {access_token, refresh_token, user_info}
```

#### 1.3 Quên Mật Khẩu (Reset Password)
```
What: User reset mật khẩu nếu quên
How:
  - Nhập email
  - System send reset link
  - User click link, set password mới
  - Mật khẩu được update
Why: User security, account recovery

POST /api/auth/forgot-password
Input: {email}
→ Generate reset_token (valid 1h)
→ Send email with reset link
Output: {message: "Reset link sent"}

POST /api/auth/reset-password/{token}
Input: {new_password}
→ Verify token
→ Update password
Output: {message: "Password reset successful"}
```

#### 1.4 Xem & Chỉnh Sửa Profile
```
What: User view/update thông tin cá nhân
How:
  - GET: Show current info
  - PUT: Update info (name, phone, avatar)
  - Validate input
Why: User need control over their data

GET /api/users/profile
→ Get current user info (from JWT token)
Output: {id, email, name, phone, avatar, created_at}

PUT /api/users/profile
Input: {name, phone, avatar_url}
→ Validate
→ Update DB
Output: {updated_user}
```

#### 1.5 Quản Lý Địa Chỉ (Address Management)
```
What: User add/edit/delete multiple addresses
How:
  - User add billing & shipping addresses
  - Mark default address
  - Use when booking (auto-fill)
Why: Speed up checkout process

POST /api/users/addresses
Input: {city, district, address, is_default}
→ Create address
Output: {address_id, ...}

GET /api/users/addresses
Output: [{address1}, {address2}, ...]

PUT /api/users/addresses/{id}
DELETE /api/users/addresses/{id}
```

---

### 2. **Movie Browsing & Discovery**

#### 2.1 Xem Danh Sách Phim (List Movies)
```
What: User view tất cả phim hiện có
How:
  - GET all movies
  - Filter by: status (now showing/coming soon), genre, rating
  - Paginate (10 movies per page)
  - Sort by: rating, newest, trending
Why: User need discover new movies

GET /api/movies?status=active&genre=action&sort=rating&page=1
→ Query movies with filters
→ Return paginated results
Output: {
  movies: [{id, title, poster, rating, duration, formats}, ...],
  total: 45,
  page: 1,
  per_page: 10
}
```

#### 2.2 Tìm Kiếm Phim (Search)
```
What: User search phim by title/keyword
How:
  - Full-text search on title, description
  - Return suggestions as user types
  - Highlight matches
Why: Fast find specific movie

GET /api/movies/search?q=avengers
→ Full-text search in title + description
→ Return top 10 matches
Output: [{movie1}, {movie2}, ...]
```

#### 2.3 Xem Chi Tiết Phim (Movie Detail)
```
What: User view full info about 1 movie
How:
  - Get movie: title, poster, trailer, rating, duration
  - Get cast & crew
  - Get user reviews
  - Get available showtimes
Why: User need info before booking

GET /api/movies/{id}
→ Get movie full details
→ Get cast list
→ Get reviews (with pagination)
→ Get available showtimes (next 7 days)
Output: {
  movie: {id, title, poster, trailer, rating, duration, genre, format},
  cast: [{name, character, avatar}, ...],
  reviews: [{user, rating, comment, date}, ...],
  showtimes: [{id, theater, date, time, available_seats}, ...]
}
```

#### 2.4 Xem Trailer (Watch Trailer)
```
What: User watch movie trailer before booking
How:
  - Click trailer button
  - Modal open với video player
  - Embedded YouTube/Vimeo
Why: Preview movie, decide to watch

GET /api/movies/{id}/trailer
→ Get trailer URL
Output: {trailer_url, duration}

(Frontend: Play in modal)
```

#### 2.5 Filter & Sort
```
What: User filter movies by multiple criteria
How:
  - Genre: action, comedy, drama, horror, romance, sci-fi
  - Format: 2D, 3D, IMAX
  - Rating: 8+, 7+, 6+
  - Status: now showing, coming soon, pre-order
  - Sort: newest, rating, trending, price
Why: Find exactly what user want

GET /api/movies?genre=action,comedy&format=3D&rating_min=7&sort=trending
→ Multiple filters apply
Output: Filtered + sorted movies
```

---

### 3. **Booking Flow**

#### 3.1 Chọn Rạp & Suất Chiếu (Select Theater & Showtime)
```
What: User select which rạp & suất chiếu to watch
How:
  - Show theaters near user (by location/distance)
  - Show showtimes by date
  - Show available seats count
  - Show price per seat
Why: User choose where & when to watch

GET /api/movies/{id}/showtimes
→ Get all showtimes for this movie
→ Group by theater & date
Output: {
  movie_id: 1,
  showtimes: [
    {
      id: 101,
      theater: {id, name, city, distance_km},
      screen: {id, name, format},
      start_time: "2024-06-28 20:00",
      available_seats: 45,
      price_per_seat: 100000
    },
    ...
  ]
}

POST /api/bookings/select-showtime
Input: {showtime_id}
→ Create booking draft
→ Lock seats for 10 minutes
Output: {booking_id, showtime_details}
```

#### 3.2 Chọn Ghế (Select Seats)
```
What: User select cụ thể ghế muốn đặt
How:
  - Show seat map (interactive)
  - Color-coded: green (available), red (booked), blue (selected), gray (maintenance)
  - Show seat type (normal, VIP, couple)
  - Show price per seat
  - Can select multiple seats
  - Real-time availability update
Why: User choose exactly which seats

GET /api/showtimes/{id}/seats
→ Get all seats with status
Output: {
  screen: {name, layout: "10x12"},
  seats: [
    {id, number: "A1", type: "normal", price: 100000, status: "available"},
    {id, number: "A2", type: "vip", price: 150000, status: "available"},
    {id, number: "A3", type: "couple", price: 300000, status: "booked"},
    ...
  ]
}

POST /api/bookings/{id}/select-seats
Input: {seat_ids: [1, 2, 5]}
→ Update booking with selected seats
→ Calculate total price
→ Lock seats
Output: {booking, selected_seats, total_price}
```

#### 3.3 Review Booking (Xem Lại Đơn Hàng)
```
What: User review details trước khi thanh toán
How:
  - Show: Movie, Theater, Time, Seats, Price
  - Allow change seats (back to step 3.2)
  - Allow change showtime (back to step 3.1)
  - Confirm booking
Why: Final check before payment

GET /api/bookings/{id}
→ Get full booking details
Output: {
  booking_id, movie, theater, showtime, 
  selected_seats: [{seat_number, price}, ...],
  subtotal, tax, total_price
}

PUT /api/bookings/{id}/confirm
→ Confirm booking (lock data)
Output: {booking_confirmed, payment_required: total_price}
```

#### 3.4 Thanh Toán (Payment)
```
What: User pay for booking using various methods
How:
  - Multiple payment methods: Credit card, Debit, Momo, ZaloPay
  - Secure payment gateway
  - Confirm payment
  - Generate ticket
Why: Complete booking transaction

POST /api/payments
Input: {booking_id, amount, method: "credit_card", card_details}
→ Validate payment info
→ Process payment (call payment gateway)
→ If success: Update booking status to "completed"
→ If fail: Rollback booking
Output: {payment_id, status: "completed", booking_id}

(Payment success triggers: Email confirmation, Ticket generation, Seat locked)
```

#### 3.5 Nhận Vé (Get Ticket/QR Code)
```
What: User get ticket sau khi payment success
How:
  - Generate QR code (contains booking info)
  - Show ticket details: movie, time, seats
  - Option to: Download PDF, Print, Screenshot
  - Send email with ticket attachment
Why: User need proof of booking for entry

GET /api/bookings/{id}/ticket
→ Generate QR code
→ Create PDF ticket
Output: {
  ticket_url,
  qr_code_url,
  booking_code: "ABC123456",
  details: {movie, theater, time, seats}
}

Ticket format:
┌────────────────────────────┐
│  CINEMA BOOKING TICKET     │
├────────────────────────────┤
│ Booking Code: ABC123456    │
│ Movie: Inside Out 2        │
│ Theater: CGV Royal City    │
│ Date/Time: 28/6 20:00      │
│ Seats: A1, A2, A3          │
│ Total: 300,000 VND         │
│                            │
│ [QR CODE]                  │
└────────────────────────────┘
```

---

### 4. **Purchase History & Management**

#### 4.1 Xem Lịch Sử Đặt Vé (Booking History)
```
What: User view tất cả bookings cũ
How:
  - List all bookings (completed, pending, cancelled)
  - Filter by: status, date range, movie
  - Sort by: date (newest first)
  - Paginate
Why: Track bookings, manage tickets

GET /api/bookings?status=completed&limit=20&offset=0
→ Get user's bookings
→ Include: movie, theater, date, seats, price, status
Output: {
  bookings: [
    {id, movie, theater, date, seats, price, status: "completed", ticket_url},
    ...
  ],
  total: 5,
  page: 1
}
```

#### 4.2 Hủy Đặt Vé (Cancel Booking)
```
What: User cancel booking & get refund
How:
  - Only if not yet used (showtime not started)
  - Cancel charges fee (e.g., 10% of total)
  - Process refund
  - Update booking status to "cancelled"
Why: User flexibility, business policy

PUT /api/bookings/{id}/cancel
Input: {reason: "Changed mind"}
→ Check if showtime already started
→ If yes: Cannot cancel
→ If no: Calculate refund = total_price * 0.9
→ Process refund to original payment method
→ Update booking status
Output: {status: "cancelled", refund_amount, refund_date}
```

#### 4.3 Download/Print Lại Vé (Redownload Ticket)
```
What: User download ticket lại nếu mất
How:
  - User can re-download anytime before showtime
  - Get QR code, PDF, or screenshot
Why: In case user lose ticket, need backup

GET /api/bookings/{id}/ticket?format=pdf
→ Generate PDF ticket
Output: PDF file download

GET /api/bookings/{id}/ticket?format=qr
→ Get QR code URL
Output: QR code image
```

#### 4.4 Share Booking (Chia Sẻ)
```
What: User share booking link với friends
How:
  - Generate shareable link
  - Friend can view details (không mua lại)
  - Share via: link, SMS, WhatsApp, email
Why: Tell friends about movie, meeting location

POST /api/bookings/{id}/share
Input: {share_method: "link"}
→ Generate share token (valid 7 days)
Output: {share_url: "cinema.com/share/abc123"}

Link content (read-only):
- Movie details
- Theater address & map
- Time & seats
- Contact information for change
```

---

### 5. **Favorites & Wishlist**

#### 5.1 Add/Remove Favorites
```
What: User save movies they like
How:
  - Click "Add to Favorites" on movie
  - Can view favorites anytime
  - Remove from favorites
  - Mark as watched
Why: Personalization, quick access

POST /api/users/favorites
Input: {movie_id}
→ Add to favorites
Output: {message: "Added to favorites"}

DELETE /api/users/favorites/{movie_id}
→ Remove from favorites
```

#### 5.2 Xem Danh Sách Yêu Thích
```
What: User view their favorites list
How:
  - Show all saved movies
  - Show which coming soon, now showing
  - Quick actions: Watch trailer, Book now
Why: Easy access to movies they like

GET /api/users/favorites
→ Get all favorite movies with status
Output: {
  favorites: [
    {id, title, poster, status: "coming_soon", release_date},
    {id, title, poster, status: "now_showing", available_showtimes},
    ...
  ]
}
```

#### 5.3 Watchlist (Phim Muốn Xem)
```
What: User add movies to watchlist
How:
  - Similar to favorites
  - Can set reminder (notify before release)
  - Track watched movies
Why: Plan what to watch

POST /api/users/watchlist
Input: {movie_id, remind_me: true}
→ Add to watchlist
→ If remind_me=true: Send notification when released

GET /api/users/watchlist/watched
→ Mark movie as watched
```

---

### 6. **Reviews & Ratings**

#### 6.1 Viết Review (Write Review)
```
What: User rate & review movie
How:
  - User must have completed booking for this movie
  - Rate: 1-5 stars
  - Write optional comment
  - Upload photos (optional)
  - Submit review
Why: Help others decide, community feedback

POST /api/movies/{id}/reviews
Input: {
  rating: 4,
  comment: "Great movie, highly recommend!",
  photos: [upload_file1, upload_file2]
}
→ Verify user watched this movie
→ Create review
→ Store photos in CDN
Output: {review_id, rating, comment, created_at}
```

#### 6.2 Xem Reviews (View Reviews)
```
What: User see reviews from others
How:
  - Show all reviews for movie
  - Sort by: newest, most helpful, rating
  - Show average rating & review count
  - Pagination
Why: Help decide before booking

GET /api/movies/{id}/reviews?sort=helpful&page=1
→ Get all reviews
→ Calculate average rating
Output: {
  movie_id,
  average_rating: 4.2,
  total_reviews: 156,
  reviews: [
    {user, rating, comment, helpful_count, photos, date},
    ...
  ]
}
```

#### 6.3 Mark Helpful/Unhelpful
```
What: User vote if review helpful
How:
  - Click "Helpful" or "Unhelpful"
  - System track helpfulness
  - Use to sort reviews
Why: Surface best reviews

POST /api/reviews/{id}/helpful
Input: {is_helpful: true}
→ Add vote
→ Recalculate helpful_count
```

#### 6.4 Edit/Delete Own Review
```
What: User edit or delete their review
How:
  - Only own reviews
  - Edit: rating, comment, photos
  - Delete: remove completely
Why: User control over their data

PUT /api/reviews/{id}
Input: {rating, comment, photos}
→ Update review

DELETE /api/reviews/{id}
→ Remove review
```

---

### 7. **Notifications & Communication**

#### 7.1 Email Notifications
```
What: System notify user via email
When:
  ✓ Booking confirmed
  ✓ Payment received
  ✓ Ticket ready (with attachment)
  ✓ Movie coming soon (from watchlist)
  ✓ Showtime reminder (24h before)
  ✓ Refund processed
  ✓ Password reset
  ✓ Account verified

How: System auto-send using email service (SMTP/SendGrid)
Format: HTML template + personalized content
```

#### 7.2 SMS Notifications (Optional)
```
What: Send SMS for critical info
When:
  ✓ Booking confirmed
  ✓ Showtime reminder
  ✓ Payment alert

How: Integrate SMS gateway (Twilio, Vonage)
```

#### 7.3 In-App Notifications
```
What: Notification inside app
When:
  ✓ Booking status change
  ✓ New promotion available
  ✓ Friends' activity

How: Real-time via WebSocket or polling
```

---

### 8. **Loyalty & Rewards (Future)**

#### 8.1 Loyalty Points
```
What: User earn points per booking
How:
  - 1 point per 10,000 VND spent
  - Points redeemable for: discount, free ticket, merchandise
  - Different tiers: Bronze, Silver, Gold, Platinum
  - Tier benefits: faster service, priority seats, extra discounts

GET /api/users/loyalty/points
Output: {total_points, tier: "Gold", benefits: [...]}
```

---

## 🛠️ ADMIN FEATURES (Chi Tiết - 15+ Chức Năng)

### 1. **Dashboard & Analytics**

#### 1.1 Overview Dashboard
```
What: Admin see high-level stats
Display:
  ✓ Total Revenue (Today, This month, This year)
  ✓ Total Bookings (Count, trend chart)
  ✓ Total Users (Active, new this month)
  ✓ Occupancy Rate (Seats filled %)
  ✓ Top Movies (By bookings)
  ✓ Recent Bookings (Last 10)
  ✓ Recent Reviews (Last 10)

GET /api/admin/dashboard
→ Aggregated stats
Output: {
  revenue: {today: 5000000, month: 100000000, year: 1200000000},
  bookings: {total: 1000, trend: [...chart data...]},
  users: {active: 500, new_month: 50},
  occupancy: 75.5,
  top_movies: [{movie, bookings}, ...],
  recent_bookings: [...],
  recent_reviews: [...]
}
```

#### 1.2 Revenue Reports
```
What: Detailed revenue analysis
Filters:
  - Date range
  - Theater
  - Movie
  - Payment method
Metrics:
  - Total revenue
  - Seats sold
  - Average price per seat
  - Refunds
  - Net revenue

GET /api/admin/reports/revenue?start_date=2024-01-01&end_date=2024-06-30
→ Revenue data with breakdown
Output: {
  total_revenue: 500000000,
  total_seats: 5000,
  average_price: 100000,
  refunds: 5000000,
  net_revenue: 495000000,
  breakdown_by_movie: [...],
  breakdown_by_theater: [...]
}
```

#### 1.3 Occupancy Analytics
```
What: Analyze seat occupancy
Show:
  - Overall occupancy %
  - By theater
  - By showtime (peak hours analysis)
  - By seat type (normal vs VIP)
  - Trend over time

GET /api/admin/analytics/occupancy
Output: {
  overall_occupancy: 75.5,
  by_theater: [{theater, occupancy}, ...],
  by_time_slot: [{time, occupancy}, ...],
  by_seat_type: [{type, occupancy}, ...],
  trend: [...chart...]
}
```

---

### 2. **Movie Management**

#### 2.1 Create Movie
```
What: Admin add new movie to system
Input:
  - Title, description
  - Genre (multi-select)
  - Duration, rating
  - Formats: 2D, 3D, IMAX
  - Poster image, trailer URL
  - Release date, end date
  - Status: active/draft/inactive
  - Cast & crew (optional)

POST /api/admin/movies
Input: {title, description, genre[], duration, rating, format[], poster, trailer, release_date, status, cast}
→ Validate input
→ Upload poster to CDN
→ Create movie
Output: {movie_id, ...details...}
```

#### 2.2 Edit Movie
```
What: Admin update movie info
PUT /api/admin/movies/{id}
Input: {title, description, ...any fields...}
→ Validate
→ Update DB
→ Invalidate cache
Output: {updated_movie}
```

#### 2.3 List Movies (Admin View)
```
What: Admin view all movies with controls
Show:
  - Title, genre, rating, duration
  - Status (draft, active, inactive)
  - Start/end date
  - Total bookings
  - Actions: edit, delete, view details, preview

GET /api/admin/movies?status=active&limit=20
→ All movies with admin metadata
Output: {movies: [...], total: 150}
```

#### 2.4 Delete Movie
```
What: Admin remove movie from system
How:
  - Only if no upcoming showtimes
  - Or force delete & cancel bookings
  - Refund affected customers
Why: Remove old/wrong movies

DELETE /api/admin/movies/{id}?force=true
→ If force: Cancel all future showtimes & refund customers
→ Delete movie
Output: {message: "Deleted", refunded_customers: 10}
```

#### 2.5 Bulk Upload Movies
```
What: Admin upload multiple movies at once
How:
  - CSV file with: title, genre, duration, poster_url, etc
  - System parse & create movies
  - Show validation errors
Why: Speed up adding many movies

POST /api/admin/movies/bulk-upload
Input: {file: movies.csv}
→ Parse CSV
→ Validate each row
→ Create movies
Output: {total: 20, success: 19, errors: [{row, error}, ...]}
```

---

### 3. **Theater Management**

#### 3.1 Create Theater
```
What: Admin add new cinema location
Input:
  - Name, city, district, address
  - GPS coordinates
  - Contact: phone, email, manager
  - Amenities: parking, food court, wheelchair access
  - Operating hours

POST /api/admin/theaters
Input: {name, city, address, latitude, longitude, phone, email, amenities, hours}
→ Validate address
→ Create theater
Output: {theater_id, ...}
```

#### 3.2 Manage Screens
```
What: Admin add/edit screens (rooms) in theater
Each screen has:
  - Name (Screen 1, Screen 2)
  - Format (2D, 3D, IMAX)
  - Capacity (50-300 seats)
  - Configuration (rows x columns, e.g., 15x20)

POST /api/admin/theaters/{theater_id}/screens
Input: {name, format, capacity, layout: {rows: 15, columns: 20}}
→ Create screen
→ Auto-generate seats

Output: {screen_id, seats_generated: 300}
```

#### 3.3 Manage Seats
```
What: Admin configure seats in each screen
For each seat:
  - Position (row + column)
  - Type (normal, VIP, couple)
  - Price
  - Status (available, maintenance)

PUT /api/admin/screens/{screen_id}/seats
Input: {
  seats: [
    {number: "A1", type: "normal", price: 100000},
    {number: "A2", type: "normal", price: 100000},
    {number: "A20", type: "couple", price: 300000},
    ...
  ]
}
→ Update all seats
Output: {total_seats: 300, updated: 300}

Bulk operations:
- Select rows (A, B, C) → Mark as VIP
- Select seats → Mark maintenance
- Change price for VIP seats
```

#### 3.4 View Theater Stats
```
What: Admin see stats for specific theater
Show:
  - Total seats, occupancy rate
  - Revenue this month
  - Top movies at this theater
  - Upcoming showtimes

GET /api/admin/theaters/{id}/stats
Output: {
  theater_id, name, city,
  total_seats: 500,
  occupancy: 72.5,
  revenue_month: 50000000,
  top_movies: [...],
  upcoming_showtimes: [...]
}
```

---

### 4. **Showtime Management**

#### 4.1 Create Showtime
```
What: Admin schedule movie in specific screen/time
Input:
  - Movie
  - Theater & Screen
  - Date & Time
  - Language, subtitles

POST /api/admin/showtimes
Input: {
  movie_id,
  screen_id,
  start_time: "2024-06-28 20:00",
  end_time: "2024-06-28 21:48",
  language: "Vietnamese",
  subtitle: "English"
}
→ Validate: No overlapping showtimes on same screen
→ Create showtime
→ Copy seats from screen template
Output: {showtime_id, seats_created: 300}
```

#### 4.2 Edit Showtime
```
What: Admin change showtime details
Can change:
  - Time (if no bookings yet)
  - Language, subtitles
  - Cancel (if no bookings, refund users)

PUT /api/admin/showtimes/{id}
Input: {start_time, language, subtitle}
→ Validate
→ Update
```

#### 4.3 Bulk Schedule
```
What: Admin create many showtimes at once
How:
  - Select movie, date range
  - Select screens
  - Set times (e.g., 10am, 1pm, 4pm, 7pm, 10pm)
  - System auto-create all combos
Why: Faster than one-by-one

POST /api/admin/showtimes/bulk-schedule
Input: {
  movie_id,
  date_from: "2024-06-28",
  date_to: "2024-07-04",
  screen_ids: [1, 2, 3],
  times: ["10:00", "13:00", "16:00", "19:00", "22:00"]
}
→ Create 5 screens × 5 times × 7 days = 175 showtimes
Output: {created: 175, errors: [...]}
```

#### 4.4 View Availability
```
What: Admin see real-time seat availability
Show:
  - Seat map with current status
  - Bookings made
  - Seats locked (timeout after 10 min)
  - Maintenance seats

GET /api/admin/showtimes/{id}/seats
→ Real-time seat status
Output: {
  seats: [
    {number: "A1", status: "available"},
    {number: "A2", status: "booked", booking_id: 123},
    {number: "A3", status: "locked", timeout: "10:00pm"},
    ...
  ]
}
```

---

### 5. **Booking Management**

#### 5.1 View All Bookings
```
What: Admin view/manage all bookings
Filters:
  - Status (pending, completed, cancelled)
  - Date range
  - Theater, movie
  - User search
Columns:
  - Booking code, user, movie, theater, time, seats, price, status

GET /api/admin/bookings?status=completed&theater_id=1&limit=50
→ All bookings with filters
Output: {
  bookings: [
    {booking_id, user, movie, theater, date, seats, price, status},
    ...
  ],
  total: 500
}
```

#### 5.2 View Booking Details
```
What: Admin see full booking info
GET /api/admin/bookings/{id}
→ Full details: user info, movie, seats, payment method, paid amount
Output: {booking, user, movie, theater, seats, payment, ...}
```

#### 5.3 Manual Refund
```
What: Admin process refund for specific booking
How:
  - Choose booking
  - Reason (customer request, movie cancelled, etc)
  - Amount (full or partial)
  - System refund to original payment method

POST /api/admin/bookings/{id}/refund
Input: {amount: 100000, reason: "Customer request"}
→ Validate (cannot exceed booking total)
→ Process refund
→ Update booking status
→ Send email to customer
Output: {refund_id, amount, status}
```

#### 5.4 Cancel Booking (Admin)
```
What: Admin cancel any booking
How:
  - Can force cancel (even if showtime started)
  - Reason: movie cancelled, technical issue, etc
  - Auto-refund customer

PUT /api/admin/bookings/{id}/cancel
Input: {reason: "Movie cancelled", refund_percentage: 100}
→ Cancel booking
→ Calculate & process refund
→ Release seats
Output: {status: "cancelled", refund_amount}
```

#### 5.5 Verify Booking at Entry
```
What: Ticket checker scan QR at entrance
How:
  - Scan QR code
  - Verify booking details
  - Mark as "used" to prevent re-entry
  - Show green (valid) or red (invalid)
Why: Prevent fraud, one ticket = one entry

POST /api/admin/bookings/verify
Input: {qr_code: "abc123"}
→ Decode QR
→ Get booking
→ Verify: not used, showtime not started, seats valid
→ Mark as used
Output: {valid: true, user: "John Doe", movie: "Inside Out 2", seats: "A1, A2"}
```

---

### 6. **Payment Management**

#### 6.1 View All Payments
```
What: Admin see all payment transactions
Filters:
  - Status (pending, completed, failed)
  - Method (credit card, momo, etc)
  - Date range
  - Amount range
Columns:
  - Payment ID, booking, amount, method, status, date

GET /api/admin/payments?status=completed&limit=100
Output: {payments: [...], total: 5000}
```

#### 6.2 Payment Analytics
```
What: Analyze payment performance
Show:
  - Total received
  - Failed payments (%)
  - By method: card 40%, momo 30%, zalopay 30%
  - Refunds processed

GET /api/admin/reports/payments
Output: {
  total_received: 1000000000,
  total_refunded: 50000000,
  success_rate: 98.5,
  by_method: {
    credit_card: {count: 2000, amount: 400000000},
    momo: {count: 1500, amount: 300000000},
    zalopay: {count: 1500, amount: 300000000}
  }
}
```

---

### 7. **User Management**

#### 7.1 View All Users
```
What: Admin see all registered users
Show:
  - Email, name, phone
  - Total bookings, total spent
  - Last login, registration date
  - Status (active, banned)

GET /api/admin/users?limit=50
Output: {users: [...], total: 5000}
```

#### 7.2 User Details
```
What: Admin view specific user profile
GET /api/admin/users/{id}
→ All info: profile, bookings history, total spent, reviews
Output: {user, bookings: [...], total_spent: 5000000, reviews: [...]}
```

#### 7.3 Ban/Unban User
```
What: Admin prevent user access (fraud, abuse)
How:
  - Ban: prevent login, bookings
  - Unban: restore access
Why: Prevent fraud, abuse

PUT /api/admin/users/{id}/ban
Input: {reason: "Multiple fraudulent bookings"}
→ Set user status to "banned"
→ Send email notification
Output: {status: "banned"}

PUT /api/admin/users/{id}/unban
→ Set user status to "active"
```

#### 7.4 Send Notification
```
What: Admin notify specific users
How:
  - Email, SMS, or in-app
  - Custom message
  - Template or free text
Why: Promotions, alerts, surveys

POST /api/admin/users/{id}/notify
Input: {
  channel: "email",
  subject: "New Movie Coming!",
  message: "Check out Deadpool & Wolverine..."
}
→ Send notification
Output: {sent: true, delivery_status: "queued"}
```

---

### 8. **Promotions & Discounts**

#### 8.1 Create Discount Code
```
What: Admin create promo codes
Discount types:
  - Percentage (10% off)
  - Fixed amount (50k discount)
  - Free shipping
  - Buy 2 get 1 free
Rules:
  - Valid date range
  - Minimum booking amount
  - Usage limit (per user, total)
  - Applicable movies/theaters

POST /api/admin/discounts
Input: {
  code: "SUMMER2024",
  type: "percentage",
  value: 20,  // 20% off
  min_amount: 200000,
  valid_from: "2024-06-01",
  valid_to: "2024-08-31",
  usage_limit: 1000,
  per_user_limit: 1
}
→ Create discount
Output: {discount_id, code}
```

#### 8.2 Apply Discount
```
What: User apply discount code at checkout
POST /api/bookings/{id}/apply-discount
Input: {discount_code: "SUMMER2024"}
→ Verify code validity
→ Check usage limits
→ Apply discount
→ Recalculate total
Output: {original_price, discount, final_price}
```

#### 8.3 View Discount Performance
```
What: Admin see how promo codes performing
GET /api/admin/reports/discounts
Show:
  - Code, discount type & value
  - Times used
  - Revenue lost to discounts
Output: {
  discounts: [
    {code: "SUMMER2024", type: "percentage", value: 20, times_used: 234, revenue_lost: 10000000},
    ...
  ]
}
```

---

### 9. **Settings & Configuration**

#### 9.1 System Settings
```
What: Admin configure system behavior
Settings:
  - Booking cancellation fee (%)
  - Seat lock timeout (minutes)
  - Payment methods enabled
  - Notification preferences
  - Business hours
  - Holidays/closure dates

PUT /api/admin/settings
Input: {
  cancellation_fee: 10,
  seat_lock_timeout: 10,
  payment_methods: ["credit_card", "momo", "zalopay"],
  enable_notifications: true,
  email_templates: {booking_confirmed: "<html>..."},
  holidays: ["2024-12-25", "2024-01-01"]
}
→ Update system configuration
Output: {updated: true}
```

#### 9.2 Email Templates
```
What: Admin customize email templates
Can edit:
  - Booking confirmation
  - Payment receipt
  - Ticket ready
  - Password reset
  - Review notification
Show placeholders: {{user_name}}, {{movie}}, {{date}}, etc

PUT /api/admin/settings/email-templates/booking_confirmed
Input: {
  subject: "Your booking for {{movie}} is confirmed!",
  body: "<html>Dear {{user_name}}, ..."
}
→ Update template
Output: {template_id, updated: true}
```

#### 9.3 Business Configuration
```
What: Admin set business rules
- Operating hours (9am-11pm)
- Holidays (no showtimes)
- Maintenance dates
- Tax rate
- Currency & pricing

PUT /api/admin/settings/business
Input: {
  operating_hours: {start: "09:00", end: "23:00"},
  tax_rate: 0.08,
  currency: "VND",
  holidays: ["2024-12-25"],
  maintenance_dates: ["2024-07-01"]
}
```

---

### 10. **Reports & Export**

#### 10.1 Generate Reports
```
What: Admin export data for analysis
Reports:
  - Revenue by period, movie, theater
  - Customer stats (new users, total, active)
  - Occupancy analysis
  - Payment methods
  - Discount effectiveness
  - Reviews & ratings

GET /api/admin/reports/revenue?start_date=2024-01-01&end_date=2024-06-30&format=pdf
→ Generate PDF report
Output: PDF file download
```

#### 10.2 Export Data
```
What: Admin export data to CSV for external analysis
Export options:
  - All bookings
  - All users
  - All payments
  - Movie performance

GET /api/admin/export/bookings?date_from=2024-01-01&date_to=2024-06-30&format=csv
→ Generate CSV
Output: CSV file download

CSV columns:
booking_id, user_email, movie, theater, date, seats, price, status, payment_method, created_date
```

---

## 🧩 12 DESIGN PATTERNS (Mở rộng từ 7 → 12)

### **SET 1: Core Patterns (7 patterns từ trước)**

#### 1. **MVC (Model-View-Controller)** - Architecture Pattern
```python
# models.py (Model)
class Movie(models.Model):
    title = CharField(max_length=255)
    rating = FloatField()
    
# views.py (Controller)
@router.get("/movies")
def list_movies():
    movies = Movie.objects.all()
    return {"movies": movies}

# Serializer (View)
class MovieSerializer:
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "title": instance.title,
            "rating": instance.rating
        }
```

#### 2. **Singleton Pattern** - Database Connection
```python
class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance
```

#### 3. **Factory Pattern** - Payment Processors
```python
class PaymentProcessorFactory:
    @staticmethod
    def create_processor(method):
        if method == "credit_card":
            return CreditCardProcessor()
        elif method == "momo":
            return MomoProcessor()
```

#### 4. **Strategy Pattern** - Pricing
```python
class PricingStrategy:
    def calculate_price(self, base_price):
        pass

class NormalPricing(PricingStrategy):
    def calculate_price(self, base_price):
        return base_price

class WeekdayPricing(PricingStrategy):
    def calculate_price(self, base_price):
        return base_price * 0.8  # 20% discount
```

#### 5. **Observer Pattern** - Notifications
```python
class BookingObserver:
    def update(self, event):
        pass

class EmailObserver(BookingObserver):
    def update(self, event):
        send_email(event['user_email'], event['message'])

# Subject
class BookingSubject:
    def attach(self, observer):
        self.observers.append(observer)
    
    def notify(self, event):
        for observer in self.observers:
            observer.update(event)
```

#### 6. **Decorator Pattern** - Seat Pricing
```python
class SeatDecorator:
    def __init__(self, seat):
        self.seat = seat

class VIPSeatDecorator(SeatDecorator):
    def get_price(self):
        return self.seat.get_price() * 1.5
```

#### 7. **Repository Pattern** - Data Access
```python
class MovieRepository:
    def get_all(self):
        return Movie.objects.all()
    
    def get_by_id(self, id):
        return Movie.objects.get(id=id)
```

---

### **SET 2: Additional Patterns (5 mới)**

#### 8. **Template Method Pattern** - Booking Workflow
```python
from abc import ABC, abstractmethod

class BookingWorkflow(ABC):
    """Template for booking process"""
    
    def execute(self, user, showtime, seats):
        # Template defines structure
        user = self.validate_user(user)
        showtime = self.validate_showtime(showtime)
        seats = self.validate_seats(seats)
        booking = self.create_booking(user, showtime, seats)
        self.send_notification(booking)
        return booking
    
    @abstractmethod
    def validate_user(self, user):
        pass
    
    @abstractmethod
    def validate_showtime(self, showtime):
        pass
    
    @abstractmethod
    def validate_seats(self, seats):
        pass
    
    @abstractmethod
    def create_booking(self, user, showtime, seats):
        pass
    
    @abstractmethod
    def send_notification(self, booking):
        pass

# Concrete implementation
class StandardBookingWorkflow(BookingWorkflow):
    def validate_user(self, user):
        if not user.is_active:
            raise Exception("User inactive")
        return user
    
    def validate_showtime(self, showtime):
        if showtime.start_time < datetime.now():
            raise Exception("Showtime in past")
        return showtime
    
    def validate_seats(self, seats):
        for seat in seats:
            if seat.status != "available":
                raise Exception(f"Seat {seat.number} not available")
        return seats
    
    def create_booking(self, user, showtime, seats):
        return Booking.objects.create(
            user=user,
            showtime=showtime,
            total_price=sum(s.price for s in seats)
        )
    
    def send_notification(self, booking):
        BookingSubject().notify({
            'type': 'booking_created',
            'booking_id': booking.id
        })

# Usage
booking_workflow = StandardBookingWorkflow()
booking = booking_workflow.execute(user, showtime, seats)
```

**Tại sao dùng Template Method?**
- Định nghĩa skeleton của booking process
- Subclasses customize cụ thể steps
- Dễ add new booking workflows (VIP booking, group booking, etc)
- Tránh code duplication

---

#### 9. **Chain of Responsibility Pattern** - Discount Validation
```python
from abc import ABC, abstractmethod

class DiscountValidator(ABC):
    """Chain validators để check discount validity"""
    
    def __init__(self):
        self.next_validator = None
    
    def set_next(self, validator):
        self.next_validator = validator
        return validator
    
    @abstractmethod
    def validate(self, discount, booking):
        pass

class ExpiryValidator(DiscountValidator):
    def validate(self, discount, booking):
        from datetime import datetime
        if discount.valid_to < datetime.now():
            raise Exception("Discount expired")
        return self.next_validator.validate(discount, booking) if self.next_validator else True

class MinimumAmountValidator(DiscountValidator):
    def validate(self, discount, booking):
        if booking.total_price < discount.min_amount:
            raise Exception(f"Booking must be at least {discount.min_amount}")
        return self.next_validator.validate(discount, booking) if self.next_validator else True

class UsageLimitValidator(DiscountValidator):
    def validate(self, discount, booking):
        if discount.usage_count >= discount.usage_limit:
            raise Exception("Discount usage limit reached")
        return self.next_validator.validate(discount, booking) if self.next_validator else True

class PerUserLimitValidator(DiscountValidator):
    def validate(self, discount, booking):
        user_usage = Booking.objects.filter(
            user=booking.user,
            discount=discount
        ).count()
        if user_usage >= discount.per_user_limit:
            raise Exception("User already used this discount")
        return self.next_validator.validate(discount, booking) if self.next_validator else True

# Build chain
def build_validator_chain():
    expiry = ExpiryValidator()
    min_amount = MinimumAmountValidator()
    usage_limit = UsageLimitValidator()
    per_user = PerUserLimitValidator()
    
    expiry.set_next(min_amount).set_next(usage_limit).set_next(per_user)
    return expiry

# Usage
validator = build_validator_chain()
try:
    validator.validate(discount, booking)
    # Apply discount
    booking.discount = discount
    booking.save()
except Exception as e:
    print(f"Discount invalid: {e}")
```

**Tại sao dùng Chain of Responsibility?**
- Multiple validation steps
- Mỗi validator focus một job
- Dễ add/remove validators
- Linh hoạt trong order validation

---

#### 10. **State Pattern** - Booking Status
```python
from abc import ABC, abstractmethod

class BookingState(ABC):
    """Abstract state"""
    
    @abstractmethod
    def confirm(self, booking):
        pass
    
    @abstractmethod
    def cancel(self, booking):
        pass
    
    @abstractmethod
    def complete(self, booking):
        pass

class PendingState(BookingState):
    def confirm(self, booking):
        booking.state = ConfirmedState()
        booking.status = "confirmed"
        booking.save()
        return True
    
    def cancel(self, booking):
        booking.state = CancelledState()
        booking.status = "cancelled"
        booking.refund_amount = booking.total_price * 0.9  # 10% fee
        booking.save()
        return True
    
    def complete(self, booking):
        raise Exception("Cannot complete from pending state")

class ConfirmedState(BookingState):
    def confirm(self, booking):
        raise Exception("Already confirmed")
    
    def cancel(self, booking):
        raise Exception("Cannot cancel after confirmation")
    
    def complete(self, booking):
        booking.state = CompletedState()
        booking.status = "completed"
        booking.save()
        return True

class CompletedState(BookingState):
    def confirm(self, booking):
        raise Exception("Already completed")
    
    def cancel(self, booking):
        raise Exception("Cannot cancel completed booking")
    
    def complete(self, booking):
        raise Exception("Already completed")

class CancelledState(BookingState):
    def confirm(self, booking):
        raise Exception("Cannot confirm cancelled booking")
    
    def cancel(self, booking):
        raise Exception("Already cancelled")
    
    def complete(self, booking):
        raise Exception("Cannot complete cancelled booking")

# Usage
booking = Booking(state=PendingState(), ...)
booking.state.confirm(booking)  # PendingState → ConfirmedState
booking.state.complete(booking)  # ConfirmedState → CompletedState
# booking.state.cancel(booking)  # Will raise exception
```

**Tại sao dùng State Pattern?**
- Rõ ràng state transitions
- Mỗi state define valid actions
- Prevent invalid transitions
- Dễ add new states

---

#### 11. **Builder Pattern** - Complex Booking Creation
```python
class BookingBuilder:
    """Build complex booking object step-by-step"""
    
    def __init__(self):
        self._user = None
        self._showtime = None
        self._seats = []
        self._discount = None
        self._notes = None
    
    def set_user(self, user):
        self._user = user
        return self
    
    def set_showtime(self, showtime):
        self._showtime = showtime
        return self
    
    def add_seat(self, seat):
        self._seats.append(seat)
        return self
    
    def add_seats(self, seats):
        self._seats.extend(seats)
        return self
    
    def set_discount(self, discount):
        self._discount = discount
        return self
    
    def set_notes(self, notes):
        self._notes = notes
        return self
    
    def build(self):
        # Validate
        if not self._user:
            raise Exception("User required")
        if not self._showtime:
            raise Exception("Showtime required")
        if not self._seats:
            raise Exception("At least one seat required")
        
        # Calculate price
        total_price = sum(s.price for s in self._seats)
        if self._discount:
            total_price = total_price * (1 - self._discount.value / 100)
        
        # Create booking
        booking = Booking(
            user=self._user,
            showtime=self._showtime,
            total_price=total_price,
            discount=self._discount,
            notes=self._notes
        )
        
        # Add seats
        for seat in self._seats:
            BookingItem.objects.create(
                booking=booking,
                seat=seat,
                price=seat.price
            )
        
        booking.save()
        return booking

# Usage
booking = (BookingBuilder()
    .set_user(user)
    .set_showtime(showtime)
    .add_seats(selected_seats)
    .set_discount(discount_code)
    .set_notes("Group booking")
    .build())
```

**Tại sao dùng Builder?**
- Tạo complex objects dễ dàng
- Step-by-step construction
- Optional parameters (no need huge constructor)
- Readability cao

---

#### 12. **Adapter Pattern** - Payment Gateway Integration
```python
from abc import ABC, abstractmethod

# Target interface (what we want)
class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount, card_info):
        pass
    
    @abstractmethod
    def refund(self, transaction_id, amount):
        pass

# Existing 3rd-party APIs (incompatible interfaces)
class StripeAPI:
    """Stripe payment API - different interface"""
    def create_charge(self, amount_cents, payment_source):
        # Stripe expects amount in cents
        return {"charge_id": "ch_123", "status": "succeeded"}
    
    def cancel_charge(self, charge_id):
        return {"status": "refunded"}

class MomoAPI:
    """Momo payment API - different interface"""
    def pay(self, amount_vnd, phone):
        # Momo expects different format
        return {"transaction": "TXN_123", "result": "success"}
    
    def refund_transaction(self, transaction_id):
        return {"refund_id": "REF_123"}

# Adapters
class StripeAdapter(PaymentGateway):
    def __init__(self):
        self.stripe = StripeAPI()
    
    def charge(self, amount, card_info):
        # Convert amount from VND to cents
        amount_cents = int(amount / 23000 * 100)  # 1 USD ≈ 23,000 VND
        result = self.stripe.create_charge(amount_cents, card_info)
        return result['charge_id']
    
    def refund(self, transaction_id, amount):
        return self.stripe.cancel_charge(transaction_id)

class MomoAdapter(PaymentGateway):
    def __init__(self):
        self.momo = MomoAPI()
    
    def charge(self, amount, card_info):  # card_info here is phone
        result = self.momo.pay(amount, card_info)
        return result['transaction']
    
    def refund(self, transaction_id, amount):
        return self.momo.refund_transaction(transaction_id)

# Usage - same interface for different gateways
def process_payment(booking, payment_method, card_info):
    if payment_method == "stripe":
        gateway = StripeAdapter()
    elif payment_method == "momo":
        gateway = MomoAdapter()
    else:
        raise Exception(f"Unknown method: {payment_method}")
    
    # Same code for any payment method
    transaction_id = gateway.charge(booking.total_price, card_info)
    
    payment = Payment.objects.create(
        booking=booking,
        amount=booking.total_price,
        method=payment_method,
        transaction_id=transaction_id,
        status="completed"
    )
    
    return payment
```

**Tại sao dùng Adapter?**
- Integrate different 3rd-party APIs
- Convert incompatible interfaces
- Single interface for multiple implementations
- Easy to add new payment gateways

---

## 📊 Summary: 12 Design Patterns

| # | Pattern | Purpose | Áp dụng trong Cinema |
|---|---------|---------|-------------------|
| 1 | MVC | Architecture | Core structure |
| 2 | Singleton | Single instance | Database connection |
| 3 | Factory | Object creation | Payment processors |
| 4 | Strategy | Multiple algorithms | Pricing strategies |
| 5 | Observer | Event notifications | Booking notifications |
| 6 | Decorator | Add responsibilities | Seat pricing |
| 7 | Repository | Data access | Database abstraction |
| 8 | Template Method | Fixed process | Booking workflow |
| 9 | Chain of Responsibility | Sequential validation | Discount validation |
| 10 | State | Status transitions | Booking states |
| 11 | Builder | Complex construction | Booking creation |
| 12 | Adapter | Interface conversion | Payment gateways |

---

## 🏗️ LAYERED ARCHITECTURE (Chi tiết)

```
┌──────────────────────────────────────────────────────┐
│          PRESENTATION LAYER (HTTP API)               │
│  ├─ REST Endpoints (/api/movies, /api/bookings)     │
│  ├─ Request validation                               │
│  └─ Response serialization                           │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│      APPLICATION LAYER (Controllers/Views)           │
│  ├─ ViewSets (Django REST Framework)                │
│  ├─ Request handling                                 │
│  ├─ Authentication & Authorization                   │
│  ├─ Input validation (Serializers)                   │
│  └─ Response formatting                              │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│       SERVICE LAYER (Business Logic)                 │
│  ├─ MovieService (query, filter, search)            │
│  ├─ BookingService (create, cancel, refund)         │
│  ├─ PaymentService (process, verify)                │
│  ├─ UserService (register, profile, favorites)      │
│  ├─ NotificationService (email, SMS, in-app)        │
│  ├─ DiscountService (apply, validate)               │
│  ├─ TheaterService (manage screens, seats)          │
│  └─ ReportService (analytics, export)               │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│       DOMAIN LAYER (Business Entities)               │
│  ├─ User model                                       │
│  ├─ Movie model                                      │
│  ├─ Theater & Screen models                          │
│  ├─ Seat model                                       │
│  ├─ Showtime model                                   │
│  ├─ Booking & BookingItem models                     │
│  ├─ Payment model                                    │
│  ├─ Review model                                     │
│  ├─ Discount model                                   │
│  └─ Favorite & Watchlist models                      │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│ PERSISTENCE LAYER (Repository + ORM)                 │
│  ├─ MovieRepository                                  │
│  ├─ BookingRepository                                │
│  ├─ PaymentRepository                                │
│  ├─ UserRepository                                   │
│  ├─ ...other repositories                            │
│  └─ Django ORM / SQLAlchemy                          │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│        DATABASE LAYER (MySQL)                        │
│  ├─ 12+ tables with relationships                    │
│  ├─ Indexes for performance                          │
│  ├─ Constraints & validations                        │
│  └─ Transactions for consistency                     │
└──────────────────────────────────────────────────────┘

Cross-cutting concerns:
├─ Logging (all layers)
├─ Error handling (all layers)
├─ Caching (presentation + persistence)
├─ Security (application layer)
└─ Monitoring (all layers)
```

---

## 🗄️ DATABASE SCHEMA (12+ Tables)

```sql
-- Core tables
1. users (User accounts)
2. movies (Movie catalog)
3. theaters (Cinema locations)
4. screens (Theater rooms)
5. seats (Individual seats)
6. showtimes (Movie schedules)
7. bookings (Customer bookings)
8. booking_items (Seats in booking)
9. payments (Payment transactions)
10. reviews (Movie reviews)
11. discounts (Promo codes)
12. favorites (Saved movies)
13. watchlist (Want-to-watch)
14. addresses (User addresses)
15. payment_methods (Saved cards)
```

---

## 🚀 DEVELOPMENT ROADMAP (10 Tuần Chi Tiết)

### **Week 1-2: Setup & Architecture**
- [ ] Tạo Django/FastAPI project structure
- [ ] Setup MySQL database
- [ ] Create all models (MVC - Model layer)
- [ ] Setup Django ORM migrations
- [ ] Install dependencies (Django REST, auth, etc)
- [ ] Design API endpoints
- [ ] **Deliverable**: Project structure, database schema, API docs

### **Week 3-4: Core Features - User Side**
- [ ] Authentication (register, login, password reset)
- [ ] Movie browsing (list, search, filter, sort)
- [ ] Movie detail (info, cast, reviews, showtimes)
- [ ] Trailer viewing (embed video player)
- [ ] **Deliverable**: User can browse & view movies

### **Week 5-6: Booking System**
- [ ] Select theater & showtime (API + logic)
- [ ] Seat selection (interactive, validation)
- [ ] Booking confirmation (review details)
- [ ] Payment processing (integrate payment gateway)
- [ ] Ticket generation (QR code)
- [ ] **Deliverable**: Full booking workflow end-to-end

### **Week 7: User Profile & Management**
- [ ] View profile (GET /api/users/profile)
- [ ] Edit profile (PUT /api/users/profile)
- [ ] Booking history (GET /api/bookings)
- [ ] Cancel booking (with refund)
- [ ] Download ticket (PDF, QR)
- [ ] Favorites & wishlist
- [ ] **Deliverable**: User profile complete

### **Week 8: Reviews, Ratings, Notifications**
- [ ] Write reviews (POST /api/movies/{id}/reviews)
- [ ] View reviews (rating aggregation)
- [ ] Email notifications (confirmation, reminder)
- [ ] SMS notifications (optional)
- [ ] In-app notifications
- [ ] **Deliverable**: User engagement features

### **Week 9: Admin Dashboard & Management**
- [ ] Admin dashboard (stats, charts)
- [ ] Movie management (CRUD, bulk upload)
- [ ] Theater management (screens, seats)
- [ ] Showtime management (schedule, bulk create)
- [ ] Booking management (view, refund, verify)
- [ ] User management (view, ban)
- [ ] **Deliverable**: Admin panel functional

### **Week 10: Reports, Testing, Documentation**
- [ ] Revenue reports (by movie, theater, date)
- [ ] Occupancy analytics
- [ ] Payment reports
- [ ] Unit tests (services, models)
- [ ] Integration tests (booking workflow)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Deployment preparation
- [ ] **Deliverable**: Production-ready system

---

## 💻 TECHNOLOGY STACK (Chi tiết)

### Backend
```
Language: Python 3.10+
Framework: Django 4.2+ hoặc FastAPI 0.95+
  - Django: Full-featured, built-in ORM, admin
  - FastAPI: Modern, async, auto-documentation

Database: MySQL 8.0+
ORM: Django ORM hoặc SQLAlchemy
Cache: Redis (optional, for caching)
Task Queue: Celery (optional, for async tasks)
Auth: Django Auth hoặc python-jose JWT
API: Django REST Framework hoặc FastAPI routers
```

### Frontend (Optional - for testing)
```
HTML5, CSS3, JavaScript
or React/Vue for better UX
Bootstrap/Tailwind CSS
```

### Deployment
```
Server: Python Virtual Environment
Web Server: Gunicorn (WSGI) or Uvicorn (ASGI)
Reverse Proxy: Nginx
Database: MySQL Server
Email: SMTP hoặc SendGrid
Storage: Local disk hoặc S3 (for images)
```

---

## ❓ FAQ: Những Câu Hỏi Thường Gặp

### Q1: Cần clone awesome-design-systems repo không?
**A**: **KHÔNG**. Repo đó chỉ là danh sách các design systems, không có code để chạy.
- Dùng để tham khảo design approaches từ Netflix, Apple, Google
- BẠN sẽ code Cinema Management System từ đầu
- Không clone, mà tạo project Django/FastAPI riêng

### Q2: Trong 10 tuần, làm được hết không?
**A**: Có thể, nếu:
- Chia team (backend, frontend, database)
- Làm song song
- Focus MVP (core features)
- Bỏ qua advanced features (loyalty, real payment, mobile app)

Nếu solo: 12-14 tuần cho full system

### Q3: Nên chọn Django hay FastAPI?
**A**: 
- **Django**: Tốt nếu cần admin panel, built-in features, project lớn
- **FastAPI**: Tốt nếu cần modern, async, clean code, team nhỏ

Recommend: **Django** cho MTKPM (more complete, easier for learning)

### Q4: Cần real payment gateway không?
**A**: Cho MVP, có thể mock payment (trong tests). Sau dùng:
- Stripe (international)
- Momo, ZaloPay (Vietnam)

### Q5: Database design có thể đơn giản hơn không?
**A**: Có thể, nhưng:
- 12 tables là complete & realistic
- Can start with 5-6 core tables, expand sau
- Modern systems prefer explicit relationships

### Q6: Cần Docker không?
**A**: Optional nhưng recommended:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver"]
```

### Q7: Testing quan trọng không?
**A**: **CÓ**. Cần:
- Unit tests (services)
- Integration tests (booking workflow)
- API tests (endpoints)
- Tối thiểu: 50% code coverage

### Q8: Cần SSL/HTTPS không?
**A**: Có. Dùng:
- Django: django-cors-headers, django-extensions
- Nginx: auto-redirect HTTP → HTTPS
- Let's Encrypt (free certificates)

---

## 📝 NHỮNG ĐIỂM QUAN TRỌNG CẦN NHỚ

1. **12 Design Patterns** rõ ràng, có code examples
2. **Layered Architecture** đầy đủ (5 layers)
3. **Database Schema** chi tiết (12+ tables)
4. **15+ User Features** + **15+ Admin Features**
5. **10-week development roadmap**
6. **Không cần clone repo** - tạo project riêng
7. **Tập trung vào MTKPM** - áp dụng patterns rõ ràng

---

**Document Status**: ✅ Complete & Ready  
**Total Content**: 50+ pages equivalent  
**Design Patterns**: 12 (với code examples)  
**Development Timeline**: 10 weeks  
**Team Size**: 3-4 people recommended

**Tiếp theo**: 
- [ ] Tạo Django project
- [ ] Implement 12 models
- [ ] Viết API endpoints
- [ ] Tests & documentation