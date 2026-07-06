from django.db import models
import bcrypt

class User(models.Model):
    STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('active', 'Active'),
        ('banned', 'Banned'),
    ]
    TIER_CHOICES = [
        ('Bronze', 'Bronze'),
        ('Silver', 'Silver'),
        ('Gold', 'Gold'),
        ('Platinum', 'Platinum'),
    ]
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    points = models.IntegerField(default=0)
    tier = models.CharField(max_length=15, choices=TIER_CHOICES, default='Bronze')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='unverified')
    verification_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __str__(self):
        return self.email

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.address}, {self.district}, {self.city}"

class Movie(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('now_showing', 'Now Showing'),
        ('coming_soon', 'Coming Soon'),
        ('inactive', 'Inactive'),
    ]
    AGE_RATINGS = [
        ('P', 'P - General (Mọi đối tượng)'),
        ('C13', 'C13 - 13+ (Từ 13 tuổi trở lên)'),
        ('C16', 'C16 - 16+ (Từ 16 tuổi trở lên)'),
        ('C18', 'C18 - 18+ (Từ 18 tuổi trở lên)'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.CharField(max_length=100) # e.g. "Action, Sci-Fi"
    duration = models.IntegerField() # in minutes
    rating = models.FloatField(default=0.0) # average review rating
    formats = models.CharField(max_length=50, default='2D') # e.g. "2D, 3D, IMAX"
    poster_url = models.CharField(max_length=500, blank=True, null=True)
    trailer_url = models.CharField(max_length=500, blank=True, null=True)
    release_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    age_rating = models.CharField(max_length=10, choices=AGE_RATINGS, default='P')
    director = models.CharField(max_length=100, default='Unknown')
    cast = models.TextField(default='N/A')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Theater(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    amenities = models.CharField(max_length=255, blank=True, null=True) # e.g. "Parking, Food Court, Wheelchair"
    operating_hours = models.CharField(max_length=100, default='09:00 - 23:00')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

class Screen(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=50) # e.g. "Screen 1"
    format = models.CharField(max_length=20, default='2D') # 2D, 3D, IMAX
    capacity = models.IntegerField(default=0)
    rows = models.IntegerField(default=10)
    columns = models.IntegerField(default=12)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.theater.name} - {self.name} ({self.format})"

class Seat(models.Model):
    SEAT_TYPES = [
        ('normal', 'Normal'),
        ('vip', 'VIP'),
        ('couple', 'Couple'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('maintenance', 'Maintenance'),
    ]
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=5) # e.g. "A", "B"
    column = models.IntegerField() # e.g. 1, 2
    seat_number = models.CharField(max_length=10) # e.g. "A1", "A2"
    type = models.CharField(max_length=15, choices=SEAT_TYPES, default='normal')
    price = models.IntegerField(default=100000)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"{self.screen} - {self.seat_number} ({self.type})"

class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='showtimes')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='showtimes')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    language = models.CharField(max_length=50, default='Vietnamese')
    subtitle = models.CharField(max_length=50, default='English')
    price_multiplier = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movie.title} | {self.screen} | {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class Discount(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=15, choices=DISCOUNT_TYPES, default='percentage')
    value = models.IntegerField() # 10 for 10%, 50000 for 50k VND
    min_amount = models.IntegerField(default=0)
    valid_from = models.DateField()
    valid_to = models.DateField()
    usage_limit = models.IntegerField(default=1000)
    usage_count = models.IntegerField(default=0)
    per_user_limit = models.IntegerField(default=1)
    
    # New fields for advanced validators
    min_tier = models.CharField(max_length=15, choices=User.TIER_CHOICES, default='Bronze', blank=True, null=True)
    applicable_movies = models.ManyToManyField(Movie, blank=True, related_name='applicable_discounts')
    applicable_genre = models.CharField(max_length=100, blank=True, null=True)
    allow_points_combination = models.BooleanField(default=True)
    is_golden_hour_only = models.BooleanField(default=False)

    def __str__(self):
        return self.code

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name='bookings')
    total_price = models.IntegerField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    refund_amount = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields for points
    redeemed_points = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)

    def __str__(self):
        return f"Booking #{self.id} - {self.user.email} - {self.status}"

class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    price = models.IntegerField()

    def __str__(self):
        return f"Booking #{self.booking.id} - Seat {self.seat.seat_number}"

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('momo', 'Momo'),
        ('zalopay', 'ZaloPay'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.IntegerField()
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    payment_url = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - Booking #{self.booking.id} - {self.status}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField() # 1 to 5
    comment = models.TextField()
    photos = models.JSONField(default=list, blank=True) # list of photo URLs
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.movie.title} ({self.rating}*)"

class ReviewHelpfulVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.email} helpful vote for Review #{self.review.id}"

class ReviewReply(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='reply')
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    reply_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to Review #{self.review.id} by {self.admin.email}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.email} likes {self.movie.title}"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    remind_me = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.email} watchlist: {self.movie.title}"

class InAppNotification(models.Model):
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='unread')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.status})"
