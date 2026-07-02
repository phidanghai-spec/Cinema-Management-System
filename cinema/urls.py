from django.urls import path
from . import views, views_admin

urlpatterns = [
    # User / Customer routes
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    path('offers/', views.offers_view, name='offers'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('faq/', views.faq_view, name='faq'),
    path('genre/<str:genre_slug>/', views.genre_movies_view, name='genre_movies'),
    path('theaters/', views.theaters_view, name='theaters'),
    path('movie/<int:movie_id>/', views.movie_detail_view, name='movie_detail'),
    path('movie/<int:movie_id>/review/', views.submit_review_view, name='submit_review'),
    path('booking/showtime/<int:showtime_id>/', views.booking_flow_view, name='booking_flow'),
    path('booking/ticket/<int:booking_id>/', views.booking_ticket_view, name='booking_ticket'),
    path('profile/', views.profile_view, name='profile'),

    # Async APIs
    path('api/booking/create/', views.create_booking_api, name='api_create_booking'),
    path('api/booking/cancel/<int:booking_id>/', views.cancel_booking_api, name='api_cancel_booking'),
    path('api/discount/validate/', views.validate_discount_api, name='api_validate_discount'),
    path('api/favorite/toggle/', views.toggle_favorite_api, name='api_toggle_favorite'),
    path('api/watchlist/toggle/', views.toggle_watchlist_api, name='api_toggle_watchlist'),
    path('api/notifications/read/', views.mark_notifications_read_api, name='api_mark_notifications_read'),

    # Admin routes
    path('admin-dashboard/', views_admin.dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/movies/', views_admin.admin_movies_view, name='admin_movies'),
    path('admin-dashboard/showtimes/', views_admin.admin_showtimes_view, name='admin_showtimes'),
    path('admin-dashboard/users/', views_admin.admin_users_view, name='admin_users'),

    # Admin APIs
    path('api/admin/bulk-upload/', views_admin.csv_bulk_upload_api, name='api_admin_bulk_upload'),
    path('api/admin/verify-ticket/', views_admin.admin_verify_ticket_api, name='api_admin_verify_ticket'),
]
