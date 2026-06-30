import json
import functools
from datetime import date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User, Movie, Theater, Screen, Seat, Showtime, Booking, BookingItem, Payment, Review, Discount, Favorite, Watchlist, Address, InAppNotification
from .services import (
    UserService, MovieService, BookingService,
    DuplicateEmailException, InvalidCredentialsException,
    AccountBannedException, MovieNotFoundException,
    UserNotFoundException, ShowtimeNotFoundException,
    SeatNotFoundException, BookingNotFoundException,
    UnauthorizedActionException, InvalidTicketException
)
from .repositories import UserRepository, MovieRepository, BookingRepository, ShowtimeRepository, DiscountRepository

# Helper to get current session user
def get_session_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        return UserRepository.get_by_id(user_id)
    return None

def login_required_view(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        user = get_session_user(request)
        if not user:
            return redirect('login')
        return func(request, user, *args, **kwargs)
    return wrapper

# Authentication Views
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        try:
            user = UserService.register(email, password, name, phone)
            request.session['user_id'] = user.id
            return redirect('index')
        except Exception as e:
            return render(request, 'cinema/register.html', {'error': str(e)})
    return render(request, 'cinema/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = UserService.login(email, password)
            request.session['user_id'] = user.id
            request.session['is_admin'] = (user.email == 'admin@cinema.com')
            return redirect('index')
        except Exception as e:
            return render(request, 'cinema/login.html', {'error': str(e)})
    return render(request, 'cinema/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

# Movies Browsing Views
def index_view(request):
    user = get_session_user(request)
    status = request.GET.get('status', 'now_showing')
    genre = request.GET.get('genre')
    format_type = request.GET.get('format')
    search = request.GET.get('q')
    sort = request.GET.get('sort', 'newest')

    movies = MovieService.get_movies(status, genre, format_type, search, sort)
    
    # Spotlight films for the hero carousel (top 3 now showing by rating)
    spotlight_movies = list(Movie.objects.filter(status='now_showing').order_by('-rating')[:3])
    coming_soon_movies = list(Movie.objects.filter(status='coming_soon').order_by('release_date')[:4])
    
    context = {
        'user': user,
        'movies': movies,
        'genres': ['Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Romance', 'Animation'],
        'formats': ['2D', '3D', 'IMAX'],
        'current_status': status,
        'current_genre': genre,
        'current_format': format_type,
        'current_sort': sort,
        'search_query': search,
        'spotlight_movies': spotlight_movies,
        'coming_soon_movies': coming_soon_movies,
    }
    return render(request, 'cinema/movie_list.html', context)

def movie_detail_view(request, movie_id):
    user = get_session_user(request)
    try:
        movie = MovieService.get_details(movie_id)
        showtimes = ShowtimeRepository.get_movie_showtimes(movie_id)
        reviews = movie.reviews.all().order_by('-created_at')
        
        # Group showtimes by date and theater name
        grouped_showtimes = {}
        for s in showtimes:
            date_str = s.start_time.strftime('%Y-%m-%d')
            t_name = s.screen.theater.name
            if date_str not in grouped_showtimes:
                grouped_showtimes[date_str] = {}
            if t_name not in grouped_showtimes[date_str]:
                grouped_showtimes[date_str][t_name] = []
            grouped_showtimes[date_str][t_name].append(s)

        is_favorite = False
        is_watchlist = False
        if user:
            is_favorite = Favorite.objects.filter(user=user, movie=movie).exists()
            is_watchlist = Watchlist.objects.filter(user=user, movie=movie).exists()
        
        # Calculate points-based loyalty progress
        tier_thresholds = {'Bronze': 0, 'Silver': 100, 'Gold': 300, 'Platinum': 1000}

        context = {
            'user': user,
            'movie': movie,
            'grouped_showtimes': grouped_showtimes,
            'reviews': reviews,
            'is_favorite': is_favorite,
            'is_watchlist': is_watchlist
        }
        return render(request, 'cinema/movie_detail.html', context)
    except Exception as e:
        return redirect('index')

# Booking Views
@login_required_view
def booking_flow_view(request, user, showtime_id):
    showtime = ShowtimeRepository.get_by_id(showtime_id)
    if not showtime:
        return redirect('index')

    # Get already booked seats for this showtime
    booked_seat_ids = BookingItem.objects.filter(
        booking__showtime=showtime,
        booking__status__in=['confirmed', 'completed']
    ).values_list('seat_id', flat=True)

    # Fetch all seats for the screen and group them by row label
    seats = showtime.screen.seats.all().order_by('row', 'column')
    seats_by_row = {}
    for seat in seats:
        if seat.row not in seats_by_row:
            seats_by_row[seat.row] = []
        seats_by_row[seat.row].append(seat)

    context = {
        'user': user,
        'showtime': showtime,
        'seats_by_row': seats_by_row,
        'booked_seat_ids': list(booked_seat_ids),
    }
    return render(request, 'cinema/booking_flow.html', context)

@csrf_exempt
@login_required_view
def create_booking_api(request, user):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            showtime_id = data.get('showtime_id')
            seat_ids = data.get('seat_ids', [])
            discount_code = data.get('discount_code')
            payment_method = data.get('payment_method', 'credit_card')
            phone = data.get('phone', '')
            notes = data.get('notes', '')

            booking = BookingService.make_booking(
                user_id=user.id,
                showtime_id=showtime_id,
                seat_ids=seat_ids,
                discount_code=discount_code,
                method=payment_method,
                phone=phone,
                notes=notes
            )
            return JsonResponse({'success': True, 'booking_id': booking.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required_view
def booking_ticket_view(request, user, booking_id):
    booking = BookingRepository.get_by_id(booking_id)
    if not booking or booking.user_id != user.id:
        return redirect('index')

    # Ticket structure
    context = {
        'user': user,
        'booking': booking,
        'qr_content': f"CINEMA-BOOKING-ID:{booking.id}"
    }
    return render(request, 'cinema/booking_ticket.html', context)

# Profile, Favorites & Social Reviews
@login_required_view
def profile_view(request, user):
    bookings = BookingRepository.get_user_bookings(user.id)
    favorites = Favorite.objects.filter(user=user).select_related('movie')
    watchlist = Watchlist.objects.filter(user=user).select_related('movie')
    notifications = user.notifications.all().order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            user.name = request.POST.get('name')
            user.phone = request.POST.get('phone')
            user.save()
            return redirect('profile')
        elif action == 'add_address':
            Address.objects.create(
                user=user,
                city=request.POST.get('city'),
                district=request.POST.get('district'),
                address=request.POST.get('address'),
                is_default=False
            )
            return redirect('profile')

    # Calculate dynamic loyalty progress
    tier_thresholds = [
        ('Bronze', 0), ('Silver', 100), ('Gold', 300), ('Platinum', 1000)
    ]
    points = user.points
    current_tier_idx = 0
    for i, (tier, threshold) in enumerate(tier_thresholds):
        if points >= threshold:
            current_tier_idx = i
    
    # Progress within current tier
    if current_tier_idx < len(tier_thresholds) - 1:
        current_min = tier_thresholds[current_tier_idx][1]
        next_max = tier_thresholds[current_tier_idx + 1][1]
        tier_progress = min(100, int((points - current_min) / (next_max - current_min) * 100))
        next_tier = tier_thresholds[current_tier_idx + 1][0]
        points_to_next = next_max - points
    else:
        tier_progress = 100
        next_tier = 'Max'
        points_to_next = 0

    unread_count = notifications.filter(status='unread').count()

    context = {
        'user': user,
        'bookings': bookings,
        'favorites': favorites,
        'watchlist': watchlist,
        'notifications': notifications,
        'tiers': ['Bronze', 'Silver', 'Gold', 'Platinum'],
        'tier_progress': tier_progress,
        'next_tier': next_tier,
        'points_to_next': points_to_next,
        'unread_count': unread_count,
    }
    return render(request, 'cinema/profile.html', context)

@csrf_exempt
@login_required_view
def cancel_booking_api(request, user, booking_id):
    if request.method == 'POST':
        try:
            booking = BookingService.cancel_booking(booking_id, user.id)
            return JsonResponse({'success': True, 'refund_amount': booking.refund_amount})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required_view
def validate_discount_api(request, user):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            subtotal = data.get('subtotal', 0)
            
            discount = DiscountRepository.get_by_code(code)
            if not discount:
                return JsonResponse({'success': False, 'error': 'Invalid coupon code.'})
            
            # Simple check before formal validation chain binds it to a booking
            today = date.today()
            if today < discount.valid_from or today > discount.valid_to:
                return JsonResponse({'success': False, 'error': 'Coupon has expired.'})
            if subtotal < discount.min_amount:
                return JsonResponse({'success': False, 'error': f"Minimum purchase of {discount.min_amount:,} VND required."})
            
            # Calculate discount value preview
            val = discount.value
            if discount.type == 'percentage':
                calc_val = int(subtotal * (val / 100.0))
            else:
                calc_val = val
                
            return JsonResponse({'success': True, 'discount_amount': calc_val, 'code': discount.code})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required_view
def toggle_favorite_api(request, user):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            movie_id = data.get('movie_id')
            movie = MovieRepository.get_by_id(movie_id)
            if not movie:
                return JsonResponse({'success': False, 'error': 'Movie not found.'})
            
            fav, created = Favorite.objects.get_or_create(user=user, movie=movie)
            if not created:
                fav.delete()
                state = 'removed'
            else:
                state = 'added'
            return JsonResponse({'success': True, 'state': state})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required_view
def toggle_watchlist_api(request, user):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            movie_id = data.get('movie_id')
            movie = MovieRepository.get_by_id(movie_id)
            if not movie:
                return JsonResponse({'success': False, 'error': 'Movie not found.'})
            
            wl, created = Watchlist.objects.get_or_create(user=user, movie=movie)
            if not created:
                wl.delete()
                state = 'removed'
            else:
                state = 'added'
            return JsonResponse({'success': True, 'state': state})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required_view
def mark_notifications_read_api(request, user):
    if request.method == 'POST':
        user.notifications.filter(status='unread').update(status='read')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required_view
def submit_review_view(request, user, movie_id):
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')
        movie = MovieRepository.get_by_id(movie_id)
        if movie:
            Review.objects.create(
                user=user,
                movie=movie,
                rating=rating,
                comment=comment
            )
            # Re-calculate average rating for movie
            all_reviews = movie.reviews.all()
            movie.rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
            movie.save()
    return redirect('movie_detail', movie_id=movie_id)
