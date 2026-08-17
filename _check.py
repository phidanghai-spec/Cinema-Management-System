import os, django, pytz, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema_project.settings')
django.setup()
from cinema.models import Showtime
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.datetime.now(vn_tz)
upcoming = Showtime.objects.filter(start_time__gt=now).order_by('start_time')[:12]
print(f"Suat chieu sap toi ({Showtime.objects.filter(start_time__gt=now).count()} tong):")
for st in upcoming:
    local = st.start_time.astimezone(vn_tz)
    print(f"  ID={st.id}  {local.strftime('%d/%m %H:%M')}  {st.movie.title[:22]}  {st.screen.name}")
