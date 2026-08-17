"""
=============================================================
 CINEVERSE — DEMO DATA PREPARATION SCRIPT
=============================================================
 Chạy 1 lần trước khi quay video demo để tạo sẵn:
   1. Showtime ngày thường  (Strategy: WeekdayPricing)
   2. Showtime cuối tuần   (Strategy: WeekendPricing)
   3. Mã giảm giá hết hạn  (Chain of Responsibility demo)
   4. Mã giảm giá hợp lệ   (dùng để demo Adapter/thanh toán)
   5. Tài khoản customer test (nếu chưa có)
   6. Vé đã đặt & confirmed sẵn (State pattern: hủy vé demo)

 Cach chay (sau khi bat MySQL):
   .venv/Scripts/python.exe prepare_demo_data.py

 Kết quả: in ra cheat sheet để copy vào kịch bản quay.
=============================================================
"""

import os
import django
import datetime
import pytz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema_project.settings')
django.setup()

from cinema.models import (
    User, Movie, Screen, Showtime, Seat,
    Discount, Booking, BookingItem, Payment
)

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.datetime.now(vn_tz)
today = now.date()

print("\n" + "="*60)
print("  CINEVERSE --- CHUAN BI DU LIEU DEMO")
print("="*60)

# ----------------------------------------------------------
# BUOC 1: Tim movie va screen de tao showtime
# ----------------------------------------------------------
print("\n[1/6] Kiem tra phim va man chieu...")

movie = Movie.objects.filter(status='now_showing').first()
if not movie:
    movie = Movie.objects.first()

if not movie:
    print("  FAIL: Khong tim thay phim nao trong DB!")
    print("     Hay chay seeder truoc: python manage.py seed_data")
    exit(1)

screen = Screen.objects.first()
if not screen:
    print("  FAIL: Khong tim thay man chieu nao trong DB!")
    exit(1)

print(f"  OK Dung phim: [{movie.id}] {movie.title}")
print(f"  OK Dung man:  [{screen.id}] {screen.name}")

# ----------------------------------------------------------
# BUOC 2: Tao showtime ngay thuong va cuoi tuan
# ----------------------------------------------------------
print("\n[2/6] Tao Showtime cho Strategy Pattern demo...")

def next_weekday_date(current_date, target_weekday):
    """Tim ngay target_weekday (0=Mon, 5=Sat, 6=Sun) tiep theo."""
    days_ahead = target_weekday - current_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return current_date + datetime.timedelta(days=days_ahead)

# Showtime ngay thuong -- Thu 3, 15:00 (ngoai 9-12h => WeekdayPricing x0.9)
next_tuesday = next_weekday_date(today, 1)
weekday_start = vn_tz.localize(datetime.datetime(
    next_tuesday.year, next_tuesday.month, next_tuesday.day, 15, 0, 0
))
weekday_end = weekday_start + datetime.timedelta(minutes=movie.duration + 20)

weekday_showtime, created = Showtime.objects.get_or_create(
    movie=movie,
    screen=screen,
    start_time=weekday_start,
    defaults={
        'end_time': weekday_end,
        'language': 'Vietnamese',
        'subtitle': 'English',
        'price_multiplier': 1.0,
    }
)
lbl = "TAO MOI" if created else "DA TON TAI"
print(f"  [{lbl}] Showtime NGAY THUONG:")
print(f"     ID = {weekday_showtime.id}")
print(f"     Thu 3 ({next_tuesday.strftime('%d/%m/%Y')}) 15:00")
print(f"     Strategy: WeekdayPricing (giam 10%)")
print(f"     URL demo: /booking/showtime/{weekday_showtime.id}/")

# Showtime cuoi tuan -- Thu 7, 19:00 (WeekendPricing x1.2)
next_saturday = next_weekday_date(today, 5)
weekend_start = vn_tz.localize(datetime.datetime(
    next_saturday.year, next_saturday.month, next_saturday.day, 19, 0, 0
))
weekend_end = weekend_start + datetime.timedelta(minutes=movie.duration + 20)

weekend_showtime, created = Showtime.objects.get_or_create(
    movie=movie,
    screen=screen,
    start_time=weekend_start,
    defaults={
        'end_time': weekend_end,
        'language': 'Vietnamese',
        'subtitle': 'English',
        'price_multiplier': 1.0,
    }
)
lbl = "TAO MOI" if created else "DA TON TAI"
print(f"\n  [{lbl}] Showtime CUOI TUAN:")
print(f"     ID = {weekend_showtime.id}")
print(f"     Thu 7 ({next_saturday.strftime('%d/%m/%Y')}) 19:00")
print(f"     Strategy: WeekendPricing (tang 20%)")
print(f"     URL demo: /booking/showtime/{weekend_showtime.id}/")

# ----------------------------------------------------------
# BUOC 3: Ma giam gia HET HAN (Chain of Responsibility demo)
# ----------------------------------------------------------
print("\n[3/6] Tao ma giam gia HET HAN (demo Chain of Responsibility)...")

expired_discount, created = Discount.objects.get_or_create(
    code='DEMO_EXPIRED',
    defaults={
        'type': 'percentage',
        'value': 20,
        'min_amount': 0,
        'valid_from': datetime.date(2024, 1, 1),
        'valid_to': datetime.date(2024, 12, 31),   # da het han
        'usage_limit': 9999,
        'usage_count': 0,
        'per_user_limit': 99,
        'min_tier': 'Bronze',
        'allow_points_combination': True,
        'is_golden_hour_only': False,
    }
)
if not created:
    expired_discount.valid_to = datetime.date(2024, 12, 31)
    expired_discount.save()

lbl = "TAO MOI" if created else "DA TON TAI"
print(f"  [{lbl}] Ma giam gia het han:")
print(f"     Ma: DEMO_EXPIRED")
print(f"     Hieu luc: 01/01/2024 -> 31/12/2024  [HET HAN]")
print(f"     Demo: nhap ma nay o buoc Thanh Toan")
print(f"           ExpiryValidator se bao loi ngay lap tuc")

# ----------------------------------------------------------
# BUOC 4: Ma giam gia HOP LE (Adapter/thanh toan demo)
# ----------------------------------------------------------
print("\n[4/6] Tao ma giam gia HOP LE (demo Adapter/thanh toan)...")

valid_discount, created = Discount.objects.get_or_create(
    code='DEMO10',
    defaults={
        'type': 'percentage',
        'value': 10,
        'min_amount': 0,
        'valid_from': today - datetime.timedelta(days=30),
        'valid_to': today + datetime.timedelta(days=60),
        'usage_limit': 9999,
        'usage_count': 0,
        'per_user_limit': 99,
        'min_tier': 'Bronze',
        'allow_points_combination': True,
        'is_golden_hour_only': False,
    }
)
if not created:
    valid_discount.valid_to = today + datetime.timedelta(days=60)
    valid_discount.save()

lbl = "TAO MOI" if created else "DA TON TAI"
print(f"  [{lbl}] Ma giam gia hop le:")
print(f"     Ma: DEMO10")
print(f"     Giam: 10%, het han: {valid_discount.valid_to.strftime('%d/%m/%Y')}")
print(f"     Demo: dung khi demo buoc thanh toan thanh cong")

# ----------------------------------------------------------
# BUOC 5: Tai khoan customer test
# ----------------------------------------------------------
print("\n[5/6] Kiem tra tai khoan customer test...")

test_email = 'demo_customer@cineverse.test'
test_password = 'Demo@12345'

customer, created = User.objects.get_or_create(
    email=test_email,
    defaults={
        'name': 'Demo Customer',
        'phone': '0901234567',
        'status': 'active',
        'role': 'customer',
        'tier': 'Silver',
        'points': 500,
    }
)
if created:
    customer.set_password(test_password)
    customer.save()
    lbl = "TAO MOI"
else:
    if customer.status != 'active':
        customer.status = 'active'
        customer.save()
    lbl = "DA TON TAI"

print(f"  [{lbl}] Tai khoan customer:")
print(f"     Email   : {test_email}")
print(f"     Password: {test_password}")
print(f"     Tier    : {customer.tier} | Points: {customer.points}")

# ----------------------------------------------------------
# BUOC 6: Booking CONFIRMED san de demo huy ve (State Pattern)
# ----------------------------------------------------------
print("\n[6/6] Tao Booking CONFIRMED san (demo State Pattern - huy ve)...")

demo_seat = Seat.objects.filter(
    screen=screen,
    status='available',
    type='normal'
).first()

if not demo_seat:
    print("  WARN: Khong tim thay ghe available trong man chieu nay.")
    print("        Tu tao thu cong qua UI truoc khi quay phan State.")
else:
    existing_confirmed = Booking.objects.filter(
        user=customer,
        status='confirmed',
        showtime__start_time__gte=now,
    ).first()

    if existing_confirmed:
        lbl = "DA TON TAI"
        demo_booking = existing_confirmed
    else:
        total_price = int(demo_seat.price * weekend_showtime.price_multiplier)
        demo_booking = Booking.objects.create(
            user=customer,
            showtime=weekend_showtime,
            total_price=total_price,
            status='confirmed',
            redeemed_points=0,
            points_earned=total_price // 10000,
        )
        BookingItem.objects.create(
            booking=demo_booking,
            seat=demo_seat,
            price=demo_seat.price,
        )
        Payment.objects.create(
            booking=demo_booking,
            amount=total_price,
            method='credit_card',
            transaction_id=f'stripe_demo_{demo_booking.id}',
            status='completed',
        )
        lbl = "TAO MOI"

    hoanlai = int(demo_booking.total_price * 0.9)
    print(f"  [{lbl}] Booking confirmed:")
    print(f"     Booking ID  : {demo_booking.id}")
    print(f"     Tong tien   : {demo_booking.total_price:,} VND")
    print(f"     Hoan khi huy: {hoanlai:,} VND (tru 10% phi - Singleton SystemSettings)")

# ----------------------------------------------------------
# TONG KET CHEAT SHEET
# ----------------------------------------------------------
print("\n" + "="*60)
print("  CHEAT SHEET -- DAN LEN BAN TRUOC KHI BAM RECORD")
print("="*60)
print(f"""
  TAI KHOAN DEMO
    Customer : {test_email}
    Password : {test_password}
    => Dung Tab An Danh trong trinh duyet

  SHOWTIME CAN NHO
    Ngay thuong (Weekday Strategy):
      ID = {weekday_showtime.id}
      URL: localhost:8000/booking/showtime/{weekday_showtime.id}/
      Thu 3, {next_tuesday.strftime('%d/%m/%Y')} 15:00 -- giam 10%

    Cuoi tuan (Weekend Strategy):
      ID = {weekend_showtime.id}
      URL: localhost:8000/booking/showtime/{weekend_showtime.id}/
      Thu 7, {next_saturday.strftime('%d/%m/%Y')} 19:00 -- tang 20%

  MA GIAM GIA
    DEMO_EXPIRED => nhap ma nay => bao loi "Voucher has expired"
    DEMO10       => giam 10%, dung khi demo thanh toan thanh cong

  VE HUY (State Pattern)
    localhost:8000/profile/ (account demo_customer)
    Tim ve Booking ID={demo_booking.id if demo_seat else 'N/A'} -- status=confirmed
    Bam HUY VE => phi huy 10% => so tien hoan hien ra
""")
print("Chay server: .venv\\Scripts\\python.exe manage.py runserver")
print("Good luck! 🎬\n")
