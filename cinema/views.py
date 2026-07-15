import json
import functools
import hmac
import hashlib
import uuid
import datetime
from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User, Movie, Theater, Screen, Seat, Showtime, Booking, BookingItem, Payment, Review, Discount, Favorite, Watchlist, Address, InAppNotification, ReviewHelpfulVote, ReviewReply
from .services import (
    UserService, MovieService, BookingService,
    DuplicateEmailException, InvalidCredentialsException,
    AccountBannedException, MovieNotFoundException,
    UserNotFoundException, ShowtimeNotFoundException,
    SeatNotFoundException, BookingNotFoundException,
    UnauthorizedActionException, InvalidTicketException
)
from .repositories import UserRepository, MovieRepository, BookingRepository, ShowtimeRepository, DiscountRepository
from .patterns import BookingFacade, BookCommand, CancelCommand

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
            return render(request, 'cinema/auth/register.html', {'error': str(e)})
    return render(request, 'cinema/auth/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = UserService.login(email, password)
            request.session['user_id'] = user.id
            request.session['is_admin'] = (user.role == 'admin')
            return redirect('index')
        except Exception as e:
            return render(request, 'cinema/auth/login.html', {'error': str(e)})
    return render(request, 'cinema/auth/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email__iexact=email)
            import uuid
            token = str(uuid.uuid4())
            user.reset_token = token
            user.save()
            
            reset_url = request.build_absolute_uri(f"/reset-password/{token}/")
            print(f"[Email SIMULATOR] Password reset link for {email}: {reset_url}")
            
            return render(request, 'cinema/auth/forgot_password.html', {
                'success': "We've generated a mock password reset link.",
                'mock_reset_url': reset_url
            })
        except User.DoesNotExist:
            return render(request, 'cinema/auth/forgot_password.html', {'error': "Email address is not registered."})
    return render(request, 'cinema/auth/forgot_password.html')

def reset_password_view(request, token):
    try:
        user = User.objects.get(reset_token=token)
    except User.DoesNotExist:
        return render(request, 'cinema/auth/reset_password.html', {'error': "Invalid or expired reset token.", 'token': token})
        
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            return render(request, 'cinema/auth/reset_password.html', {'error': "Passwords do not match.", 'token': token})
        if len(password) < 8:
            return render(request, 'cinema/auth/reset_password.html', {'error': "Password must be at least 8 characters.", 'token': token})
            
        user.set_password(password)
        user.reset_token = None
        user.save()
        return render(request, 'cinema/auth/login.html', {'success': "Password reset successfully. Please sign in with your new password."})
        
    return render(request, 'cinema/auth/reset_password.html', {'token': token})

def offers_view(request):
    user = get_session_user(request)
    import datetime
    today = datetime.date.today()
    discounts = Discount.objects.filter(valid_to__gte=today, valid_from__lte=today)
    return render(request, 'cinema/pages/offers.html', {'user': user, 'discounts': discounts})

def watchlist_view(request):
    user = get_session_user(request)
    if not user:
        return redirect('login')
    watchlist_items = Watchlist.objects.filter(user=user).select_related('movie')
    watchlist_ids = watchlist_items.values_list('movie_id', flat=True)
    is_favorites = Favorite.objects.filter(user=user).values_list('movie_id', flat=True)
    return render(request, 'cinema/pages/watchlist.html', {
        'user': user,
        'watchlist_items': watchlist_items,
        'favorite_ids': list(is_favorites),
        'watchlist_ids': list(watchlist_ids),
    })

def faq_view(request):
    user = get_session_user(request)
    return render(request, 'cinema/pages/faq.html', {'user': user})

def genre_movies_view(request, genre_slug):
    user = get_session_user(request)
    from django.db.models import Q
    clean_genre_hyphen = genre_slug.replace(' ', '-').title()
    clean_genre_space = genre_slug.replace('-', ' ').title()
    movies = Movie.objects.filter(
        Q(genre__icontains=clean_genre_hyphen) | 
        Q(genre__icontains=clean_genre_space) |
        Q(genre__icontains=genre_slug)
    ).exclude(status='inactive').order_by('-release_date')
    return render(request, 'cinema/pages/genre_movies.html', {
        'user': user,
        'genre_name': clean_genre_space,
        'genre_slug': genre_slug,
        'movies': movies,
    })

def theaters_view(request):
    user = get_session_user(request)
    theaters = Theater.objects.all().order_by('city', 'name')
    for t in theaters:
        if t.amenities:
            t.amenity_list = [a.strip() for a in t.amenities.split(',')]
        else:
            t.amenity_list = []
    return render(request, 'cinema/pages/theaters.html', {
        'user': user,
        'theaters': theaters,
    })

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
    
    # Fetch 3-4 closest upcoming showtimes today (personalized dynamic content)
    now = timezone.now()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    upcoming_showtimes = list(Showtime.objects.filter(
        start_time__gte=now,
        start_time__lte=today_end,
        movie__status='now_showing'
    ).select_related('movie', 'screen__theater').order_by('start_time')[:4])
    
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
        'upcoming_showtimes': upcoming_showtimes,
    }
    return render(request, 'cinema/pages/movie_list.html', context)

def movie_detail_view(request, movie_id):
    user = get_session_user(request)
    try:
        movie = MovieService.get_details(movie_id)
        showtimes = ShowtimeRepository.get_movie_showtimes(movie_id)
        
        # Run lazy seat release
        BookingService.cleanup_expired_bookings()
        
        # Sorting and filtering reviews
        sort_by = request.GET.get('sort_reviews', 'newest')
        verified_only = request.GET.get('verified_reviews') == 'true'
        
        reviews_qs = movie.reviews.all()
        
        # Verified purchase user IDs
        verified_user_ids = set(Booking.objects.filter(
            showtime__movie=movie,
            status__in=['confirmed', 'completed']
        ).values_list('user_id', flat=True).distinct())
        
        if verified_only:
            reviews_qs = reviews_qs.filter(user_id__in=verified_user_ids)
            
        if sort_by == 'highest_rating':
            reviews_qs = reviews_qs.order_by('-rating', '-created_at')
        elif sort_by == 'lowest_rating':
            reviews_qs = reviews_qs.order_by('rating', '-created_at')
        elif sort_by == 'most_helpful':
            reviews_qs = reviews_qs.order_by('-helpful_count', '-created_at')
        else:
            reviews_qs = reviews_qs.order_by('-created_at')
            
        # Attach dynamic fields for verified purchase & helpful votes
        for r in reviews_qs:
            r.is_verified_purchase = r.user_id in verified_user_ids
            r.user_voted_helpful = False
            if user:
                r.user_voted_helpful = r.helpful_votes.filter(user=user).exists()
        
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
        can_review = False
        if user:
            is_favorite = Favorite.objects.filter(user=user, movie=movie).exists()
            is_watchlist = Watchlist.objects.filter(user=user, movie=movie).exists()
            can_review = user.id in verified_user_ids
        
        context = {
            'user': user,
            'movie': movie,
            'grouped_showtimes': grouped_showtimes,
            'reviews': reviews_qs,
            'is_favorite': is_favorite,
            'is_watchlist': is_watchlist,
            'can_review': can_review,
            'sort_reviews': sort_by,
            'verified_reviews': 'true' if verified_only else 'false'
        }
        return render(request, 'cinema/pages/movie_detail.html', context)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return redirect('index')

# Booking Views
@login_required_view
def booking_flow_view(request, user, showtime_id):
    showtime = ShowtimeRepository.get_by_id(showtime_id)
    if not showtime:
        return redirect('index')

    # Run lazy seat release
    BookingService.cleanup_expired_bookings()

    from .patterns import SystemSettings
    settings = SystemSettings.get_instance()
    timeout_minutes = settings.seat_lock_timeout_minutes
    cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)

    # Get already booked seats (including unexpired pending ones)
    booked_seat_ids = BookingItem.objects.filter(
        models.Q(booking__showtime=showtime) & (
            models.Q(booking__status__in=['confirmed', 'completed']) |
            (models.Q(booking__status='pending') & models.Q(booking__created_at__gte=cutoff_time))
        )
    ).values_list('seat_id', flat=True)

    # Fetch all seats for the screen and group them by row label
    seats = showtime.screen.seats.all().order_by('row', 'column')
    seats_by_row = {}
    for seat in seats:
        if seat.row not in seats_by_row:
            seats_by_row[seat.row] = []
        seats_by_row[seat.row].append(seat)

    from .models import Combo
    combos = Combo.objects.all()

    context = {
        'user': user,
        'showtime': showtime,
        'seats_by_row': seats_by_row,
        'booked_seat_ids': list(booked_seat_ids),
        'combos': combos,
    }
    return render(request, 'cinema/pages/booking_flow.html', context)

@login_required_view
def create_booking_api(request, user):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            showtime_id = data.get('showtime_id')
            seat_ids = data.get('seat_ids', [])
            combo_items = data.get('combo_items', [])
            discount_code = data.get('discount_code')
            payment_method = data.get('payment_method', 'credit_card')
            phone = data.get('phone', '')
            notes = data.get('notes', '')
            redeemed_points = int(data.get('redeemed_points', 0))

            facade = BookingFacade()
            command = BookCommand(
                facade=facade,
                user_id=user.id,
                showtime_id=showtime_id,
                seat_ids=seat_ids,
                combo_items=combo_items,
                discount_code=discount_code,
                method=payment_method,
                phone=phone,
                notes=notes,
                redeemed_points=redeemed_points
            )
            booking = command.execute()
            
            payment = booking.payments.first()
            redirect_url = payment.payment_url if payment else None
            
            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'redirect_url': redirect_url
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required_view
def booking_ticket_view(request, user, booking_id):
    # Run lazy seat release
    BookingService.cleanup_expired_bookings()

    booking = BookingRepository.get_by_id(booking_id)
    if not booking or booking.user_id != user.id:
        return redirect('index')

    context = {
        'user': user,
        'booking': booking,
        'qr_content': f"CINEMA-BOOKING-ID:{booking.id}"
    }
    return render(request, 'cinema/pages/booking_ticket.html', context)

@login_required_view
def mock_momo_gateway_view(request, user):
    order_id = request.GET.get('orderId')
    amount = request.GET.get('amount')
    redirect_url = request.GET.get('redirectUrl')
    
    context = {
        'user': user,
        'order_id': order_id,
        'amount': amount,
        'redirect_url': redirect_url,
    }
    return render(request, 'cinema/pages/mock_momo_gateway.html', context)

@csrf_exempt
def mock_momo_submit_view(request):
    if request.method == 'POST':
        order_id = request.POST.get('orderId')
        amount = request.POST.get('amount')
        redirect_url = request.POST.get('redirectUrl')
        status = request.POST.get('status')
        
        request_id = str(uuid.uuid4())
        trans_id = f"trans_{int(datetime.datetime.now().timestamp())}"
        result_code = 0 if status == 'success' else 49
        message = "Thành công" if status == 'success' else "Giao dịch bị từ chối"
        response_time = str(int(datetime.datetime.now().timestamp() * 1000))
        
        partner_code = getattr(settings, 'MOMO_PARTNER_CODE', "MOMOBKUN20180810")
        access_key = getattr(settings, 'MOMO_ACCESS_KEY', "klm05TvNBHJg7xgo")
        secret_key = getattr(settings, 'MOMO_SECRET_KEY', "at170ccm1Uv1gJtGLYgo12qqg6tEHg3I")
        
        raw_sig = f"accessKey={access_key}&amount={amount}&extraData=&message={message}&orderId={order_id}&orderInfo=CineVerse Booking #{order_id}&orderType=momo_wallet&partnerCode={partner_code}&requestId={request_id}&responseTime={response_time}&resultCode={result_code}&payType=qr&transId={trans_id}"
        signature = hmac.new(
            secret_key.encode('utf-8'),
            raw_sig.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Build callback redirect URL
        import urllib.parse
        params = {
            'partnerCode': partner_code,
            'orderId': order_id,
            'requestId': request_id,
            'amount': amount,
            'orderInfo': f"CineVerse Booking #{order_id}",
            'orderType': 'momo_wallet',
            'transId': trans_id,
            'resultCode': result_code,
            'message': message,
            'payType': 'qr',
            'responseTime': response_time,
            'extraData': '',
            'signature': signature
        }
        query_string = urllib.parse.urlencode(params)
        
        if redirect_url:
            target = f"{redirect_url}?{query_string}"
        else:
            target = f"/payment/momo-callback/?{query_string}"
            
        return redirect(target)
    return redirect('index')

def handle_momo_payment_update(params):
    order_id = params.get('orderId')
    result_code = int(params.get('resultCode', 1))
    trans_id = params.get('transId')
    
    try:
        booking = Booking.objects.get(id=int(order_id))
    except (Booking.DoesNotExist, ValueError):
        return False
        
    payment = booking.payments.filter(method='momo').first()
    if not payment:
        return False
        
    if result_code == 0:
        if booking.status == 'pending':
            from .patterns import get_booking_state_class, BookingSubject, EmailObserver, InAppObserver
            payment.status = 'completed'
            payment.transaction_id = trans_id
            payment.save()
            
            state_class = get_booking_state_class(booking.status)
            state_class.confirm(booking)
            
            subject = BookingSubject()
            subject.attach(EmailObserver())
            subject.attach(InAppObserver())
            subject.notify(booking, "booking_confirmed")
    else:
        if booking.status == 'pending':
            from .patterns import get_booking_state_class
            payment.status = 'failed'
            payment.transaction_id = trans_id
            payment.save()
            
            state_class = get_booking_state_class(booking.status)
            state_class.cancel(booking)
            
    return True

@login_required_view
def momo_callback_view(request, user):
    params = request.GET.dict()
    secret_key = getattr(settings, 'MOMO_SECRET_KEY', "at170ccm1Uv1gJtGLYgo12qqg6tEHg3I")
    access_key = getattr(settings, 'MOMO_ACCESS_KEY', "klm05TvNBHJg7xgo")
    raw_sig = f"accessKey={access_key}&amount={params.get('amount')}&extraData={params.get('extraData', '')}&message={params.get('message', '')}&orderId={params.get('orderId')}&orderInfo={params.get('orderInfo', '')}&orderType={params.get('orderType', '')}&partnerCode={params.get('partnerCode')}&requestId={params.get('requestId')}&responseTime={params.get('responseTime', '')}&resultCode={params.get('resultCode')}&payType={params.get('payType', '')}&transId={params.get('transId', '')}"
    
    computed_sig = hmac.new(
        secret_key.encode('utf-8'),
        raw_sig.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    is_valid = (computed_sig == params.get('signature'))
    order_id = params.get('orderId')
    
    if is_valid:
        handle_momo_payment_update(params)
        result_code = int(params.get('resultCode', 1))
        if result_code == 0:
            return redirect('booking_ticket', booking_id=order_id)
        else:
            return render(request, 'cinema/pages/booking_ticket.html', {
                'user': user,
                'error': f"Thanh toán MoMo thất bại: {params.get('message')}"
            })
    else:
        return render(request, 'cinema/pages/booking_ticket.html', {
            'user': user,
            'error': "Xác minh chữ ký số MoMo thất bại."
        })

@csrf_exempt
def momo_ipn_view(request):
    if request.method == 'POST':
        try:
            params = json.loads(request.body)
        except Exception:
            params = request.POST.dict()
            
        secret_key = getattr(settings, 'MOMO_SECRET_KEY', "at170ccm1Uv1gJtGLYgo12qqg6tEHg3I")
        access_key = getattr(settings, 'MOMO_ACCESS_KEY', "klm05TvNBHJg7xgo")
        raw_sig = f"accessKey={access_key}&amount={params.get('amount')}&extraData={params.get('extraData', '')}&message={params.get('message', '')}&orderId={params.get('orderId')}&orderInfo={params.get('orderInfo', '')}&orderType={params.get('orderType', '')}&partnerCode={params.get('partnerCode')}&requestId={params.get('requestId')}&responseTime={params.get('responseTime', '')}&resultCode={params.get('resultCode')}&payType={params.get('payType', '')}&transId={params.get('transId', '')}"
        
        computed_sig = hmac.new(
            secret_key.encode('utf-8'),
            raw_sig.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if computed_sig == params.get('signature'):
            handle_momo_payment_update(params)
            return JsonResponse({'message': 'IPN received successfully'}, status=200)
            
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

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
    return render(request, 'cinema/pages/profile.html', context)

@login_required_view
def cancel_booking_api(request, user, booking_id):
    if request.method == 'POST':
        try:
            command = CancelCommand(user_id=user.id, booking_id=booking_id)
            booking = command.execute()
            return JsonResponse({'success': True, 'refund_amount': booking.refund_amount})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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
            # Enforce verified purchase check
            has_booked = Booking.objects.filter(
                user=user,
                showtime__movie=movie,
                status__in=['confirmed', 'completed']
            ).exists()
            if not has_booked:
                return redirect('movie_detail', movie_id=movie_id)

            # Handle photo uploads
            photos = []
            uploaded_files = request.FILES.getlist('photos')
            if uploaded_files:
                import os
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                
                os.makedirs(os.path.join('media', 'reviews'), exist_ok=True)
                
                for f in uploaded_files:
                    path = default_storage.save(os.path.join('reviews', f.name), ContentFile(f.read()))
                    photos.append('/media/' + path.replace('\\', '/'))

            Review.objects.create(
                user=user,
                movie=movie,
                rating=rating,
                comment=comment,
                photos=photos
            )
            # Re-calculate average rating for movie
            all_reviews = movie.reviews.all()
            if all_reviews.exists():
                movie.rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
                movie.save()
    return redirect('movie_detail', movie_id=movie_id)

@login_required_view
def toggle_review_helpful_api(request, user, review_id):
    if request.method == 'POST':
        try:
            review = Review.objects.get(id=review_id)
            vote, created = ReviewHelpfulVote.objects.get_or_create(user=user, review=review)
            if not created:
                vote.delete()
                review.helpful_count = max(0, review.helpful_count - 1)
                state = 'unvoted'
            else:
                review.helpful_count += 1
                state = 'voted'
            review.save()
            return JsonResponse({'success': True, 'state': state, 'helpful_count': review.helpful_count})
        except Review.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Đánh giá không tồn tại.'})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@login_required_view
def submit_review_reply_api(request, user, review_id):
    if request.method == 'POST':
        if user.role != 'admin':
            return JsonResponse({'success': False, 'error': 'Bạn không có quyền thực hiện chức năng này.'})
            
        reply_text = request.POST.get('reply_text', '').strip()
        if not reply_text:
            return JsonResponse({'success': False, 'error': 'Nội dung phản hồi không được để trống.'})
            
        try:
            review = Review.objects.get(id=review_id)
            reply, created = ReviewReply.objects.update_or_create(
                review=review,
                defaults={'admin': user, 'reply_text': reply_text}
            )
            return JsonResponse({
                'success': True,
                'reply_text': reply.reply_text,
                'admin_name': user.name,
                'created_at': reply.created_at.strftime('%d/%m/%Y %H:%M')
            })
        except Review.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Đánh giá không tồn tại.'})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@login_required_view
def suggest_discount_api(request, user):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subtotal = int(data.get('subtotal', 0))
            showtime_id = data.get('showtime_id')
            seat_ids = data.get('seat_ids', [])
            redeemed_points = int(data.get('redeemed_points', 0))
            
            showtime = Showtime.objects.filter(id=showtime_id).first()
            if not showtime:
                return JsonResponse({'success': False, 'error': 'Suất chiếu không tồn tại.'})
                
            seats = Seat.objects.filter(id__in=seat_ids)
            if not seats.exists():
                return JsonResponse({'success': False, 'error': 'Chưa chọn ghế.'})
            
            today = date.today()
            discounts = Discount.objects.filter(valid_to__gte=today, valid_from__lte=today)
            
            best_discount = None
            best_amount = 0
            
            from django.db import transaction
            from .patterns import get_discount_validation_chain, BookingBuilder
            
            for d in discounts:
                try:
                    with transaction.atomic():
                        builder = (BookingBuilder()
                            .set_user(user)
                            .set_showtime(showtime)
                            .set_discount(d)
                            .set_redeemed_points(redeemed_points)
                        )
                        for s in seats:
                            builder.add_seat(s)
                        booking = builder.build()
                        
                        chain = get_discount_validation_chain()
                        chain.validate(d, booking)
                        
                        subtotal_val = 0
                        for s in seats:
                            from .patterns import SimpleSeat, VIPSeatPriceDecorator, CoupleSeatPriceDecorator, get_pricing_strategy
                            comp = SimpleSeat(s)
                            if s.type == 'vip':
                                comp = VIPSeatPriceDecorator(comp)
                            elif s.type == 'couple':
                                comp = CoupleSeatPriceDecorator(comp)
                            subtotal_val += comp.get_price()
                        
                        strategy = get_pricing_strategy(showtime.start_time)
                        subtotal_val = strategy.calculate_base_price(subtotal_val)
                        subtotal_val = int(subtotal_val * showtime.price_multiplier)
                        
                        val = d.value
                        if d.type == 'percentage':
                            calc_val = int(subtotal_val * (val / 100.0))
                        else:
                            calc_val = val
                        
                        if calc_val > best_amount:
                            best_amount = calc_val
                            best_discount = d
                            
                        raise Exception("Rollback intentional")
                except Exception as e:
                    if str(e) != "Rollback intentional":
                        pass
            
            if best_discount:
                return JsonResponse({
                    'success': True,
                    'suggested': True,
                    'code': best_discount.code,
                    'discount_amount': best_amount
                })
            else:
                return JsonResponse({
                    'success': True,
                    'suggested': False,
                    'message': 'Không có mã giảm giá khả dụng phù hợp.'
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})
