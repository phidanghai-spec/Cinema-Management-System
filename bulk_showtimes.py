"""
Tạo suất chiếu từ hôm nay đến ngày 3/9/2026
Chạy: .venv\Scripts\python.exe bulk_showtimes.py
"""
import os
import django
import datetime
import pytz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema_project.settings')
django.setup()

from cinema.models import Movie, Screen, Showtime

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.datetime.now(vn_tz)
today = now.date()
end_date = datetime.date(2026, 9, 3)

print(f"Tao suat chieu tu {today.strftime('%d/%m/%Y')} den {end_date.strftime('%d/%m/%Y')}")

movies = list(Movie.objects.filter(status='now_showing'))
screens = list(Screen.objects.all())

if not movies:
    print("Khong co phim nao! Kiem tra lai DB.")
    exit(1)
if not screens:
    print("Khong co man chieu nao! Kiem tra lai DB.")
    exit(1)

print(f"So phim: {len(movies)} | So man chieu: {len(screens)}")
for m in movies:
    print(f"  Movie: [{m.id}] {m.title} ({m.duration} min)")
for s in screens:
    print(f"  Screen: [{s.id}] {s.name}")

# Lich chieu hang ngay: moi man 1 suat sang + 1 chieu + 1 toi
# Schedule: (gio, phut, price_multiplier_theo_gio)
daily_slots = [
    (9,  0,  1.0),   # Sang som
    (11, 30, 1.0),   # Buoi sang
    (14, 0,  1.0),   # Chieu
    (16, 30, 1.1),   # Chieu muon
    (19, 0,  1.2),   # Toi
    (21, 30, 1.1),   # Khuya
]

created = 0
skipped = 0
errors  = 0

current_date = today
movie_idx = 0  # Xoay vong phim theo ngay

while current_date <= end_date:
    is_weekend = current_date.weekday() >= 5  # Sat=5, Sun=6

    for screen_idx, screen in enumerate(screens):
        # Moi man chieu 1 phim khac nhau, xoay vong moi ngay
        movie = movies[(movie_idx + screen_idx) % len(movies)]

        for slot_idx, (hour, minute, multiplier) in enumerate(daily_slots):
            # Cuoi tuan tang gia
            if is_weekend:
                multiplier = min(multiplier * 1.2, 1.5)
                multiplier = round(multiplier, 1)

            start_dt = vn_tz.localize(datetime.datetime(
                current_date.year, current_date.month, current_date.day,
                hour, minute, 0
            ))

            # Bo qua suat da qua
            if start_dt <= now:
                skipped += 1
                continue

            end_dt = start_dt + datetime.timedelta(minutes=movie.duration + 20)

            # Kiem tra trung lich man chieu
            conflict = Showtime.objects.filter(
                screen=screen,
                start_time__lt=end_dt,
                end_time__gt=start_dt,
            ).exists()

            if conflict:
                skipped += 1
                continue

            try:
                Showtime.objects.create(
                    movie=movie,
                    screen=screen,
                    start_time=start_dt,
                    end_time=end_dt,
                    language='Vietnamese',
                    subtitle='English',
                    price_multiplier=multiplier,
                )
                created += 1
            except Exception as e:
                errors += 1

    movie_idx += 1
    current_date += datetime.timedelta(days=1)

print(f"\nKet qua:")
print(f"  Tao moi : {created} suat chieu")
print(f"  Bo qua  : {skipped} (da qua hoac trung lich)")
print(f"  Loi     : {errors}")
print(f"\nKiem tra: vao localhost:8000 -> chon phim -> chon suat la dat duoc!")
