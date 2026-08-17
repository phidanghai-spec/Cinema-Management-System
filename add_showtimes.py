import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema_project.settings')
django.setup()

from cinema.models import Movie, Screen, Showtime
from datetime import datetime, timedelta
import pytz

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
today = datetime.now(vn_tz).replace(hour=0, minute=0, second=0, microsecond=0)

movies = {m.id: m for m in Movie.objects.all()}
screens = {s.id: s for s in Screen.objects.all()}

# (movie_id, screen_id, hour, minute, price_multiplier, day_delta)
# price_multiplier: 1.0=binh thuong, 1.2=IMAX/VIP+20%, 0.9=gio sang giam
schedule = [
    # Hom nay
    (27, 13, 9,  0,  1.2, 0),   # Interstellar - IMAX Hall 1 - 9:00
    (26, 14, 10, 30, 1.0, 0),   # Deadpool - Cinema Room 2 - 10:30
    (28, 15, 11, 0,  1.1, 0),   # Dune Part Two - VIP Hall 1 - 11:00
    (25, 16, 13, 0,  1.0, 0),   # Inside Out 2 - IMAX Hall 2 - 13:00
    (29, 14, 13, 30, 0.9, 0),   # Despicable Me 4 - Cinema Room 2 - 13:30
    (31, 13, 15, 0,  1.3, 0),   # Avatar - IMAX Hall 1 - 15:00
    (32, 15, 16, 30, 1.1, 0),   # Wicked - VIP Hall 1 - 16:30
    (26, 16, 17, 0,  1.0, 0),   # Deadpool - IMAX Hall 2 - 17:00
    (27, 13, 18, 30, 1.2, 0),   # Interstellar - IMAX Hall 1 - 18:30
    (28, 14, 19, 0,  1.1, 0),   # Dune Part Two - Cinema Room 2 - 19:00
    (31, 16, 20, 0,  1.3, 0),   # Avatar - IMAX Hall 2 - 20:00
    (32, 15, 21, 30, 1.1, 0),   # Wicked - VIP Hall 1 - 21:30

    # Ngay mai
    (25, 13, 9,  0,  1.0, 1),
    (30, 14, 10, 0,  1.0, 1),
    (27, 16, 11, 0,  1.2, 1),
    (29, 15, 13, 30, 0.9, 1),
    (31, 13, 15, 0,  1.3, 1),
    (26, 14, 16, 30, 1.0, 1),
    (28, 16, 17, 0,  1.1, 1),
    (32, 15, 19, 0,  1.1, 1),
    (27, 13, 20, 30, 1.2, 1),
    (30, 14, 21, 0,  1.0, 1),

    # Ngay kia
    (31, 13, 9,  30, 1.3, 2),
    (25, 15, 11, 0,  1.0, 2),
    (26, 16, 14, 0,  1.0, 2),
    (28, 13, 16, 0,  1.1, 2),
    (32, 14, 17, 30, 1.1, 2),
    (29, 15, 19, 0,  0.9, 2),
    (27, 16, 20, 0,  1.2, 2),

    # Ngay 3
    (30, 13, 10, 0,  1.0, 3),
    (31, 15, 14, 0,  1.3, 3),
    (26, 14, 17, 0,  1.0, 3),
    (28, 16, 19, 30, 1.1, 3),
    (32, 13, 21, 0,  1.1, 3),
]

created = 0
skipped = 0
for movie_id, screen_id, hour, minute, multiplier, delta in schedule:
    if movie_id not in movies or screen_id not in screens:
        print(f"WARN: movie_id={movie_id} hoac screen_id={screen_id} khong hop le, bo qua")
        continue

    movie = movies[movie_id]
    start = (today + timedelta(days=delta)).replace(hour=hour, minute=minute)
    end = start + timedelta(minutes=movie.duration + 20)  # cong them 20 phut don dep

    if Showtime.objects.filter(screen_id=screen_id, start_time=start).exists():
        skipped += 1
        continue

    Showtime.objects.create(
        movie=movie,
        screen=screens[screen_id],
        start_time=start,
        end_time=end,
        price_multiplier=multiplier,
        language='Vietnamese',
        subtitle='English',
    )
    created += 1

print(f"Ket qua: tao moi {created} suat chieu, bo qua {skipped} suat da ton tai.")

# Tong ket hom nay
today_end = today + timedelta(days=1)
today_shows = Showtime.objects.filter(
    start_time__gte=today, start_time__lt=today_end
).order_by('start_time')

print(f"\nSuat chieu hom nay ({today.strftime('%d/%m/%Y')}): {today_shows.count()} suat")
for st in today_shows:
    local_time = st.start_time.astimezone(vn_tz)
    print(f"  {local_time.strftime('%H:%M')} | x{st.price_multiplier} | {st.movie.title[:28]:28} | {st.screen.name}")
