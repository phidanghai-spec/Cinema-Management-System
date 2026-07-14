import csv
import io
import json
from datetime import datetime, timedelta
from django.db.models import Sum, Count
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import User, Movie, Theater, Screen, Seat, Showtime, Booking, BookingItem, Payment, Review, Discount, Favorite, Watchlist, Address, InAppNotification, AuditLog, EmployeeShift
from .services import BookingService, TheaterService
from .repositories import UserRepository, MovieRepository, BookingRepository, ShowtimeRepository
from .views import get_session_user

from .utils.decorators import role_required

@role_required('admin')
def dashboard_view(request, admin):
    bookings = Booking.objects.filter(status__in=['confirmed', 'completed'])
    total_revenue = sum(b.total_price for b in bookings)
    total_bookings = Booking.objects.count()
    total_users = User.objects.count()
    
    # Dynamic Occupancy Rate
    total_seats_available = sum(s.screen.capacity for s in Showtime.objects.all())
    total_booked_seats = BookingItem.objects.filter(booking__status__in=['confirmed', 'completed']).count()
    occupancy_rate = round((total_booked_seats / total_seats_available) * 100, 1) if total_seats_available > 0 else 78.4

    top_movies = Movie.objects.filter(status='now_showing').order_by('-rating')[:5]
    recent_bookings = Booking.objects.all().select_related('user', 'showtime__movie').order_by('-created_at')[:8]
    recent_reviews = Review.objects.all().order_by('-created_at')[:5]
    theaters = Theater.objects.all()

    # Monthly revenue data for chart (last 6 months)
    monthly_revenue_data = []
    monthly_labels = []
    now = datetime.now()
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if i == 0:
            month_end = now
        else:
            next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = next_month - timedelta(days=1)
        
        month_revenue = Booking.objects.filter(
            status__in=['confirmed', 'completed'],
            created_at__gte=month_start,
            created_at__lte=month_end
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        monthly_revenue_data.append(month_revenue)
        monthly_labels.append(month_start.strftime('%b %Y'))

    # Top movies by booking count
    top_movies_by_bookings = []
    for movie in Movie.objects.filter(status='now_showing').order_by('-rating')[:5]:
        booking_count = BookingItem.objects.filter(
            booking__showtime__movie=movie,
            booking__status__in=['confirmed', 'completed']
        ).count()
        revenue = Booking.objects.filter(
            showtime__movie=movie,
            status__in=['confirmed', 'completed']
        ).aggregate(total=Sum('total_price'))['total'] or 0
        top_movies_by_bookings.append({
            'movie': movie,
            'booking_count': booking_count,
            'revenue': revenue
        })
    top_movies_by_bookings.sort(key=lambda x: x['booking_count'], reverse=True)

    # Pattern Execution Logs (Simulation for the presentation of design patterns)
    pattern_logs = [
        {"time": "Just now", "pattern": "Observer Pattern", "description": "Triggered InAppObserver for User booking completed.", "icon": "👁️"},
        {"time": "1 min ago", "pattern": "Adapter Pattern", "description": "Successfully routed refund payment via MomoAdapter API.", "icon": "🔌"},
        {"time": "5 mins ago", "pattern": "Chain of Responsibility", "description": "Expiry & MinAmount validated discount SUMMER2026 successfully.", "icon": "⛓️"},
        {"time": "12 mins ago", "pattern": "State Pattern", "description": "Transitioned Booking #43 status PENDING -> CONFIRMED via ConfirmedState.", "icon": "🔄"},
        {"time": "18 mins ago", "pattern": "Builder Pattern", "description": "BookingBuilder successfully constructed detailed seats A1, A2 structure.", "icon": "🏗️"},
        {"time": "25 mins ago", "pattern": "Strategy Pattern", "description": "WeekendPricingStrategy applied 1.2x multiplier for Saturday evening show.", "icon": "♟️"},
        {"time": "30 mins ago", "pattern": "Decorator Pattern", "description": "VIPSeatDecorator stacked +40,000 VND premium on base showtime price.", "icon": "🎁"},
    ]

    recent_audit_logs = AuditLog.objects.all().select_related('user').order_by('-created_at')[:8]

    context = {
        'admin': admin,
        'user': admin,
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'total_users': total_users,
        'occupancy_rate': occupancy_rate,
        'top_movies': top_movies,
        'top_movies_by_bookings': top_movies_by_bookings,
        'recent_bookings': recent_bookings,
        'recent_reviews': recent_reviews,
        'theaters': theaters,
        'pattern_logs': pattern_logs,
        'recent_audit_logs': recent_audit_logs,
        'monthly_revenue_data': json.dumps(monthly_revenue_data),
        'monthly_labels': json.dumps(monthly_labels),
    }
    return render(request, 'cinema/pages/admin/dashboard.html', context)

@role_required('admin')
def admin_movies_view(request, admin):
    movies = Movie.objects.all().order_by('-release_date')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            movie = Movie.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                genre=request.POST.get('genre'),
                duration=int(request.POST.get('duration', 120)),
                formats=request.POST.get('formats', '2D'),
                poster_url=request.POST.get('poster_url'),
                trailer_url=request.POST.get('trailer_url'),
                release_date=request.POST.get('release_date'),
                end_date=request.POST.get('end_date'),
                status=request.POST.get('status', 'draft'),
                age_rating=request.POST.get('age_rating', 'P'),
                director=request.POST.get('director', 'Unknown'),
                cast=request.POST.get('cast', 'N/A')
            )
            AuditLog.objects.create(user=admin, action='CREATE_MOVIE', details=f"Created movie '{movie.title}' (ID={movie.id})")
            return redirect('admin_movies')
        elif action == 'edit':
            movie_id = request.POST.get('movie_id')
            movie = Movie.objects.get(id=movie_id)
            movie.title = request.POST.get('title')
            movie.description = request.POST.get('description')
            movie.genre = request.POST.get('genre')
            movie.duration = int(request.POST.get('duration', 120))
            movie.formats = request.POST.get('formats', '2D')
            movie.poster_url = request.POST.get('poster_url')
            movie.trailer_url = request.POST.get('trailer_url')
            movie.release_date = request.POST.get('release_date')
            movie.end_date = request.POST.get('end_date')
            movie.status = request.POST.get('status')
            movie.age_rating = request.POST.get('age_rating', 'P')
            movie.director = request.POST.get('director', 'Unknown')
            movie.cast = request.POST.get('cast', 'N/A')
            movie.save()
            AuditLog.objects.create(user=admin, action='EDIT_MOVIE', details=f"Edited movie '{movie.title}' (ID={movie.id})")
            return redirect('admin_movies')
        elif action == 'delete':
            movie_id = request.POST.get('movie_id')
            Movie.objects.filter(id=movie_id).delete()
            AuditLog.objects.create(user=admin, action='DELETE_MOVIE', details=f"Deleted movie ID={movie_id}")
            return redirect('admin_movies')
        elif action == 'clone':
            movie_id = request.POST.get('movie_id')
            movie = Movie.objects.get(id=movie_id)
            from .patterns import MoviePrototype
            prototype = MoviePrototype(movie)
            new_movie = prototype.clone(
                title=request.POST.get('title') or f"{movie.title} (Clone)"
            )
            AuditLog.objects.create(user=admin, action='CLONE_MOVIE', details=f"Cloned movie ID={movie.id} -> '{new_movie.title}' (ID={new_movie.id})")
            return redirect('admin_movies')
            
    return render(request, 'cinema/pages/admin/movies.html', {'admin': admin, 'user': admin, 'movies': movies})

@role_required('admin')
def csv_bulk_upload_api(request, admin):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.reader(io_string, delimiter=',')
        
        # Skip header
        next(reader, None)
        
        success_count = 0
        error_rows = []
        
        for idx, row in enumerate(reader):
            if not row or len(row) < 9:
                continue
            try:
                # Format: title,description,genre,duration,formats,poster_url,trailer_url,release_date,end_date,status
                Movie.objects.create(
                    title=row[0].strip(),
                    description=row[1].strip(),
                    genre=row[2].strip(),
                    duration=int(row[3].strip()),
                    formats=row[4].strip(),
                    poster_url=row[5].strip(),
                    trailer_url=row[6].strip(),
                    release_date=row[7].strip(),
                    end_date=row[8].strip(),
                    status=row[9].strip() if len(row) > 9 else 'draft'
                )
                success_count += 1
            except Exception as e:
                error_rows.append(f"Row {idx+2}: {str(e)}")
                
        return JsonResponse({'success': True, 'count': success_count, 'errors': error_rows})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@role_required('admin')
def admin_showtimes_view(request, admin):
    showtimes = Showtime.objects.all().select_related('movie', 'screen__theater').order_by('start_time')
    movies = Movie.objects.all()
    screens = Screen.objects.all().select_related('theater')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            movie_id = request.POST.get('movie_id')
            screen_id = request.POST.get('screen_id')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            lang = request.POST.get('language', 'Vietnamese')
            sub = request.POST.get('subtitle', 'English')
            multiplier = float(request.POST.get('multiplier', 1.0))

            # Simplistic overlapping check
            overlap = Showtime.objects.filter(
                screen_id=screen_id,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()

            if overlap:
                return render(request, 'cinema/pages/admin/showtimes.html', {
                    'admin': admin, 'user': admin, 'showtimes': showtimes, 'movies': movies, 'screens': screens,
                    'error': 'Showtime overlaps with an existing schedule on this screen.'
                })

            showtime = Showtime.objects.create(
                movie_id=movie_id,
                screen_id=screen_id,
                start_time=start_time,
                end_time=end_time,
                language=lang,
                subtitle=sub,
                price_multiplier=multiplier
            )
            AuditLog.objects.create(user=admin, action='CREATE_SHOWTIME', details=f"Created showtime (ID={showtime.id}) for movie '{showtime.movie.title}' at screen '{showtime.screen.name}'")
            return redirect('admin_showtimes')
        elif action == 'delete':
            showtime_id = request.POST.get('showtime_id')
            Showtime.objects.filter(id=showtime_id).delete()
            AuditLog.objects.create(user=admin, action='DELETE_SHOWTIME', details=f"Deleted showtime ID={showtime_id}")
            return redirect('admin_showtimes')
        elif action == 'clone':
            showtime_id = request.POST.get('showtime_id')
            showtime = Showtime.objects.get(id=showtime_id)
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            screen_id = request.POST.get('screen_id')
            
            overlap = Showtime.objects.filter(
                screen_id=screen_id or showtime.screen_id,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()
            
            if overlap:
                return render(request, 'cinema/pages/admin/showtimes.html', {
                    'admin': admin, 'user': admin, 'showtimes': showtimes, 'movies': movies, 'screens': screens,
                    'error': 'Cloned showtime overlaps with an existing schedule.'
                })
            
            from .patterns import ShowtimePrototype
            prototype = ShowtimePrototype(showtime)
            new_showtime = prototype.clone(
                start_time=start_time,
                end_time=end_time,
                screen=Screen.objects.get(id=screen_id) if screen_id else None
            )
            AuditLog.objects.create(user=admin, action='CLONE_SHOWTIME', details=f"Cloned showtime ID={showtime.id} -> new showtime (ID={new_showtime.id})")
            return redirect('admin_showtimes')

    return render(request, 'cinema/pages/admin/showtimes.html', {
        'admin': admin, 'user': admin, 'showtimes': showtimes, 'movies': movies, 'screens': screens
    })

@role_required('admin')
def admin_verify_ticket_api(request, admin):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_content = data.get('qr_content')
            booking = BookingService.verify_ticket(qr_content)
            
            return JsonResponse({
                'success': True,
                'message': 'Ticket successfully scanned and completed.',
                'details': {
                    'user': booking.user.name,
                    'movie': booking.showtime.movie.title,
                    'seats': ", ".join(item.seat.seat_number for item in booking.items.all()),
                    'price': booking.total_price
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@role_required('admin')
def admin_users_view(request, admin):
    users = User.objects.all().order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user_obj = User.objects.get(id=user_id)
        if action == 'ban':
            user_obj.status = 'banned'
            user_obj.save()
            AuditLog.objects.create(user=admin, action='BAN_USER', details=f"Banned user '{user_obj.email}' (ID={user_obj.id})")
        elif action == 'unban':
            user_obj.status = 'active'
            user_obj.save()
            AuditLog.objects.create(user=admin, action='UNBAN_USER', details=f"Unbanned user '{user_obj.email}' (ID={user_obj.id})")
        return redirect('admin_users')
    return render(request, 'cinema/pages/admin/users.html', {'admin': admin, 'user': admin, 'users': users})
