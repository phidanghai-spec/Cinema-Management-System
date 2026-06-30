# 👥 CineVerse - Task Breakdown & Design System Guide

## 🎯 WHO DOES WHAT (Ai sẽ sửa gì?)

### Team Structure (3-4 người)

```
CineVerse Project Team:
│
├─ 👨‍💼 Project Manager / Lead (PhiDang?)
│  └─ Điều phối, review, quản lý timeline
│
├─ 👨‍💻 Backend Developer
│  └─ Add type hints, docstrings, expand tests, API docs
│
├─ 🎨 Frontend Developer  
│  └─ Improve design system, colors, typography, layout
│
└─ 🧪 QA/Testing Engineer
   └─ Write integration tests, API tests, performance tests
```

---

## 📋 TASK BREAKDOWN (Chi tiết công việc)

### **BACKEND DEVELOPER** (7-10 ngày)

#### Task 1: Add Type Hints (2-3 ngày)
```python
# WHO: Backend Developer
# TIME: 2-3 days
# PRIORITY: 🔴 CRITICAL

File: cinema/models.py, cinema/services.py, cinema/repositories.py

# Before:
def create_booking(self, user, showtime, seats):
    return Booking.objects.create(...)

# After:
from typing import List, Optional

def create_booking(
    self, 
    user: User, 
    showtime: Showtime, 
    seats: List[Seat],
    discount: Optional[Discount] = None
) -> Booking:
    """Create new booking with optional discount."""
    return Booking.objects.create(...)

# Apply to all functions in:
- models.py (20+ functions)
- services.py (30+ functions)
- repositories.py (15+ functions)
- views.py (20+ endpoints)
```

**Checklist**:
- [ ] Add type hints to all models
- [ ] Add type hints to all services
- [ ] Add type hints to all repositories
- [ ] Add type hints to all views
- [ ] Add type hints to all utility functions
- [ ] Run: `mypy cinema/` to validate
- [ ] Update requirements.txt with mypy

---

#### Task 2: Add Docstrings (3-4 ngày)
```python
# WHO: Backend Developer
# TIME: 3-4 days
# PRIORITY: 🔴 CRITICAL

# Format: Google-style docstrings

def create_booking(self, user: User, showtime: Showtime, 
                   seats: List[Seat]) -> Booking:
    """
    Create new movie booking for user.
    
    This method creates a booking, calculates price with
    multipliers, applies discounts, and triggers notifications.
    
    Args:
        user: User making the booking
        showtime: Selected showtime (contains price_multiplier)
        seats: List of selected Seat objects
        
    Returns:
        Booking: Created booking object with ID
        
    Raises:
        InvalidSeatError: If any seat unavailable or maintenance
        InvalidShowtimeError: If showtime in past or invalid
        InsufficientCreditsError: If user doesn't have enough points
        
    Examples:
        >>> booking = service.create_booking(user, showtime, [seat1, seat2])
        >>> print(booking.total_price)
        240000
        
    Note:
        - Seats are locked for 10 minutes after booking creation
        - Price is calculated as: base_price * seats * multiplier - discount
        - Notifications are sent automatically
    """
    pass

# Apply to:
- All model methods (20+)
- All service methods (40+)
- All repository methods (20+)
- All API view methods (25+)
```

**Checklist**:
- [ ] Add docstrings to all model methods
- [ ] Add docstrings to all service methods
- [ ] Add docstrings to all repository methods
- [ ] Add docstrings to all view methods
- [ ] Add docstrings to all utility functions
- [ ] Validate with: `pydocs`

---

#### Task 3: Generate Swagger/OpenAPI Documentation (2 ngày)
```python
# WHO: Backend Developer
# TIME: 2 days
# PRIORITY: 🟡 HIGH

# Step 1: Install drf-spectacular
pip install drf-spectacular

# Step 2: Update settings.py
INSTALLED_APPS = [
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Step 3: Update urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]

# Step 4: Add docstrings to API methods
def create_booking(request):
    """
    Create new booking.
    
    Method: POST
    URL: /api/booking/create/
    
    Request:
    {
        "showtime_id": 1,
        "seat_ids": [10, 11, 12],
        "discount_code": "SUMMER2026"  # Optional
    }
    
    Response (201):
    {
        "booking_id": 42,
        "total_price": 240000,
        "discount_applied": 48000,
        "final_price": 192000,
        "qr_code": "base64_data"
    }
    
    Error (400):
    {
        "error": "Invalid seats",
        "code": "INVALID_SEATS",
        "details": "Seats A1, A2 are not available"
    }
    """
    pass

# Result: Auto-generated at /api/docs/
```

**Checklist**:
- [ ] Install drf-spectacular
- [ ] Update settings.py
- [ ] Update urls.py
- [ ] Add docstrings to all API views
- [ ] Test: Visit /api/docs/
- [ ] Export as OpenAPI.yaml

---

#### Task 4: Expand & Write Tests (4-5 ngày)
```python
# WHO: Backend Developer (or QA)
# TIME: 4-5 days
# PRIORITY: 🟡 HIGH (from 20% → 50% coverage)

Current tests (5):
✓ test_singleton_settings
✓ test_strategy_pricing
✓ test_chain_discount
✓ test_state_booking
✓ test_observer_notify

Add tests (25+):

# Pattern Tests
def test_factory_payment_processor():
    """Test PaymentAdapterFactory creates correct adapter."""
    factory = PaymentAdapterFactory()
    momo_adapter = factory.create_processor("momo")
    assert isinstance(momo_adapter, MomoAdapter)

def test_decorator_seat_price():
    """Test SeatPriceDecorator adds VIP surcharge."""
    seat = Seat(type="normal", price=100000)
    vip_seat = VIPSeatDecorator(seat)
    assert vip_seat.get_price() == 150000  # 50% more

def test_repository_pattern():
    """Test MovieRepository abstracts data access."""
    repo = MovieRepository()
    movies = repo.get_all()
    assert len(movies) > 0

# Model Tests
def test_user_loyalty_points():
    """Test user gets points per booking."""
    user = User.objects.create(...)
    booking = Booking.objects.create(user=user, total_price=100000)
    assert user.loyalty_points == 10  # 1 point per 10k

def test_booking_state_transitions():
    """Test valid booking state transitions."""
    booking = Booking.objects.create(status="pending")
    booking.confirm()
    assert booking.status == "confirmed"
    
    with pytest.raises(InvalidStateError):
        booking.confirm()  # Cannot confirm twice

# API Tests
def test_api_create_booking():
    """Test POST /api/booking/create/ endpoint."""
    response = client.post('/api/booking/create/', {
        'showtime_id': 1,
        'seat_ids': [10, 11]
    })
    assert response.status_code == 201
    assert 'booking_id' in response.json()

def test_api_discount_validation():
    """Test POST /api/discount/validate/ endpoint."""
    response = client.post('/api/discount/validate/', {
        'code': 'SUMMER2026',
        'total_price': 300000
    })
    assert response.status_code == 200
    assert response.json()['valid'] == True

def test_api_cancel_booking():
    """Test cancellation refund."""
    booking = Booking.objects.create(total_price=100000)
    response = client.post(f'/api/booking/{booking.id}/cancel/')
    assert response.status_code == 200
    # Refund = 100000 * 0.9 = 90000 (10% fee)
    assert response.json()['refund_amount'] == 90000

# Integration Tests
def test_complete_booking_workflow():
    """Test entire booking: Browse → Select → Pay → Ticket."""
    # 1. User registers
    user = User.objects.create(email='test@test.com')
    # 2. Get movies
    movie = Movie.objects.get(title='Inside Out 2')
    # 3. Get showtimes
    showtime = Showtime.objects.filter(movie=movie).first()
    # 4. Select seats
    seats = Seat.objects.filter(showtime=showtime, status='available')[:2]
    # 5. Create booking
    booking = BookingService().create_booking(user, showtime, seats)
    assert booking.status == 'pending'
    # 6. Apply discount
    discount = Discount.objects.get(code='SUMMER2026')
    booking.apply_discount(discount)
    # 7. Process payment
    payment = PaymentService().process_payment(booking)
    assert payment.status == 'completed'
    # 8. Generate ticket
    ticket = booking.generate_ticket()
    assert ticket.qr_code is not None

# Run tests
python manage.py test cinema -v 2
# Target: 50%+ coverage
```

**Checklist**:
- [ ] Write 25+ new test cases
- [ ] Target 50% code coverage
- [ ] Run all tests pass
- [ ] Check coverage: `coverage run manage.py test && coverage report`

---

#### Task 5: Add Logging & Error Handling (2 ngày)
```python
# WHO: Backend Developer
# TIME: 2 days
# PRIORITY: 🟠 MEDIUM

# Add logging
import logging
logger = logging.getLogger(__name__)

def create_booking(self, user, showtime, seats):
    logger.info(f"Creating booking for user {user.id}")
    try:
        # Validate
        if not user.is_active:
            logger.warning(f"User {user.id} inactive")
            raise InvalidUserError("User not active")
        
        # Create
        booking = Booking.objects.create(...)
        logger.info(f"Booking {booking.id} created successfully")
        
        # Notify
        self.send_notification(booking)
        
        return booking
        
    except InvalidSeatError as e:
        logger.error(f"Invalid seat: {e}")
        raise
    except PaymentError as e:
        logger.error(f"Payment failed: {e}", exc_info=True)
        # Rollback
        booking.delete()
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise

# Add custom exceptions
class BookingException(Exception):
    """Base booking exception."""
    pass

class InvalidSeatError(BookingException):
    """Seat is not available."""
    pass

class InvalidShowtimeError(BookingException):
    """Showtime is invalid."""
    pass

class PaymentError(BookingException):
    """Payment processing failed."""
    pass
```

---

### **FRONTEND DEVELOPER** (7-10 ngày)

#### Task 1: Design System Audit (1 ngày)
```
# WHO: Frontend Developer
# TIME: 1 day
# PRIORITY: 🔴 CRITICAL

# Based on awesome-design-systems, analyze:

Current CineVerse Design:
├─ Color scheme
│  ├─ Background: hsl(222, 28%, 7%) - Good (dark)
│  ├─ Accent: hsl(271, 91%, 65%) - Purple
│  ├─ Secondary: hsl(192, 95%, 50%) - Cyan  
│  └─ Tertiary: hsl(40, 100%, 55%) - Gold
│
├─ Typography
│  ├─ Font: Outfit (Google Fonts) - Good choice
│  ├─ Weights: 300-900 - Good range
│  ├─ H1-H6: Should define sizes
│  └─ Body: Should define sizes
│
├─ Spacing
│  ├─ Base unit: 4px or 8px? (not defined)
│  ├─ Gaps, padding, margins: Inconsistent
│  └─ Need consistent scale
│
└─ Components
   ├─ Buttons: Multiple variants?
   ├─ Cards: Consistent styling?
   ├─ Forms: Validation states?
   └─ Modals: Animation?

# Reference from awesome-design-systems:
- Netflix: Bold typography, large spacing
- Material Design: 8px baseline grid
- Ant Design: Consistent component library
- Tailwind: Utility-first approach
```

---

#### Task 2: Improve Color & Typography (2 ngày)
```css
/* WHO: Frontend Developer
/* TIME: 2 days
/* PRIORITY: 🔴 CRITICAL

/* Before: No color/type system documented */

/* After: Define Design Token System */

:root {
  /* Primary colors */
  --color-primary: hsl(271, 91%, 65%);    /* Purple */
  --color-primary-dark: hsl(271, 91%, 55%);
  --color-primary-light: hsl(271, 91%, 75%);
  
  /* Secondary */
  --color-secondary: hsl(192, 95%, 50%);  /* Cyan */
  --color-secondary-dark: hsl(192, 95%, 40%);
  
  /* Tertiary */
  --color-accent: hsl(40, 100%, 55%);     /* Gold */
  
  /* Backgrounds */
  --color-bg-primary: hsl(222, 28%, 7%);  /* Dark navy */
  --color-bg-secondary: hsl(222, 28%, 12%);
  --color-bg-tertiary: hsl(222, 28%, 16%);
  
  /* Text */
  --color-text-primary: #ffffff;
  --color-text-secondary: #b0b0b0;
  --color-text-disabled: #666666;
  
  /* Semantic */
  --color-success: hsl(142, 76%, 36%);    /* Green */
  --color-warning: hsl(38, 92%, 50%);     /* Orange */
  --color-error: hsl(0, 100%, 50%);       /* Red */
  --color-info: hsl(216, 100%, 50%);      /* Blue */
  
  /* Typography */
  --font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-weight-light: 300;
  --font-weight-regular: 400;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --font-weight-extrabold: 900;
  
  /* Font sizes - 8px baseline */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  --text-5xl: 3rem;      /* 48px */
  
  /* Spacing - 4px baseline */
  --spacing-0: 0;
  --spacing-1: 0.25rem;  /* 4px */
  --spacing-2: 0.5rem;   /* 8px */
  --spacing-3: 0.75rem;  /* 12px */
  --spacing-4: 1rem;     /* 16px */
  --spacing-6: 1.5rem;   /* 24px */
  --spacing-8: 2rem;     /* 32px */
  --spacing-12: 3rem;    /* 48px */
  
  /* Border radius */
  --radius-sm: 0.375rem;   /* 6px */
  --radius-md: 0.5rem;     /* 8px */
  --radius-lg: 0.75rem;    /* 12px */
  --radius-xl: 1rem;       /* 16px */
  --radius-2xl: 1.5rem;    /* 24px */
  
  /* Shadows - Glassmorphism */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-fast: 150ms ease-out;
  --transition-base: 250ms ease-out;
  --transition-slow: 350ms ease-out;
}

/* Apply to elements */
h1 {
  font-size: var(--text-5xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

h2 {
  font-size: var(--text-4xl);
  font-weight: var(--font-weight-bold);
}

button {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-md);
  background-color: var(--color-primary);
  color: var(--color-text-primary);
  transition: all var(--transition-base);
}

button:hover {
  background-color: var(--color-primary-dark);
  box-shadow: var(--shadow-lg);
}

.card {
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  background: var(--color-bg-secondary);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: var(--shadow-md);
}
```

**Checklist**:
- [ ] Define color tokens
- [ ] Define typography scale
- [ ] Define spacing scale
- [ ] Define border radius scale
- [ ] Define shadow scale
- [ ] Apply to all CSS
- [ ] Update style.css with tokens

---

#### Task 2: Refactor CSS Architecture (2 ngày)
```css
/* WHO: Frontend Developer
/* TIME: 2 days
/* PRIORITY: 🟡 HIGH

/* Before: 750 lines of CSS, might be inconsistent */

/* After: Organized CSS */

/* 1. Reset & Base */
/* 2. Design Tokens (vars) */
/* 3. Typography */
/* 4. Colors & Backgrounds */
/* 5. Spacing & Layout */
/* 6. Components:
     - Buttons
     - Cards
     - Forms
     - Navigation
     - Tables
/* 7. Utilities */
/* 8. Responsive Design */
/* 9. Animations & Transitions */
/* 10. Dark Theme */

/* Structure:
style.css (750 lines)
├─ 1. Reset (50 lines)
├─ 2. Tokens (100 lines)
├─ 3. Typography (80 lines)
├─ 4. Colors (100 lines)
├─ 5. Spacing (80 lines)
├─ 6. Components (200 lines)
├─ 7. Utilities (50 lines)
├─ 8. Responsive (50 lines)
└─ 9. Animations (40 lines)
*/
```

---

#### Task 3: Improve HTML Semantics & Accessibility (2 ngày)
```html
<!-- WHO: Frontend Developer
     TIME: 2 days
     PRIORITY: 🟡 HIGH

<!-- Before: Basic HTML, missing ARIA -->

<!-- After: Semantic + Accessible -->

<!-- ADD SEMANTIC HTML -->
<main>
  <header>
    <nav aria-label="Main navigation">
      <ul>
        <li><a href="/" aria-current="page">Home</a></li>
        <li><a href="/movies">Movies</a></li>
      </ul>
    </nav>
  </header>
  
  <section aria-labelledby="hero-title">
    <h1 id="hero-title">Cinema Management System</h1>
  </section>
  
  <article>
    <h2>Now Showing</h2>
    <ul role="list">
      <li role="listitem" aria-label="Movie card for Inside Out 2">
        <img src="poster.jpg" alt="Inside Out 2 poster">
        <h3>Inside Out 2</h3>
      </li>
    </ul>
  </article>
  
  <footer role="contentinfo">
    <p>&copy; 2024 CineVerse. All rights reserved.</p>
  </footer>
</main>

<!-- ADD FORM ACCESSIBILITY -->
<form>
  <label for="email">Email Address</label>
  <input 
    id="email"
    type="email"
    required
    aria-required="true"
    aria-describedby="email-hint"
  >
  <small id="email-hint">We'll never share your email.</small>
  
  <label for="password">Password</label>
  <input 
    id="password"
    type="password"
    required
    aria-required="true"
  >
  
  <button type="submit" aria-label="Sign in to your account">
    Sign In
  </button>
</form>

<!-- ADD INTERACTIVE ACCESSIBILITY -->
<div role="alertdialog" aria-labelledby="dialog-title" aria-describedby="dialog-desc">
  <h2 id="dialog-title">Confirm Booking</h2>
  <p id="dialog-desc">Are you sure you want to book these seats?</p>
  <button aria-label="Confirm booking">Confirm</button>
  <button aria-label="Cancel booking">Cancel</button>
</div>
```

**Checklist**:
- [ ] Use semantic HTML5 elements
- [ ] Add ARIA labels
- [ ] Add alt text to images
- [ ] Make forms accessible
- [ ] Test with screen reader
- [ ] Validate WCAG 2.1 AA

---

#### Task 4: Enhance JavaScript Functionality (2-3 ngày)
```javascript
// WHO: Frontend Developer
// TIME: 2-3 days
// PRIORITY: 🟡 HIGH

// Add features:

// 1. Form Validation
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

function validatePassword(password) {
  // Min 8 chars, 1 uppercase, 1 number
  return /^(?=.*[A-Z])(?=.*\d).{8,}$/.test(password);
}

// 2. Error Handling
try {
  const response = await fetch('/api/booking/create/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    const error = await response.json();
    showToast(`Error: ${error.message}`, 'error');
    return;
  }
  
  const booking = await response.json();
  showToast('Booking created successfully!', 'success');
  
} catch (error) {
  console.error('Request failed:', error);
  showToast('Network error. Please try again.', 'error');
}

// 3. Loading States
function showLoading(element, isLoading = true) {
  if (isLoading) {
    element.innerHTML = '<div class="spinner"></div>';
    element.setAttribute('aria-busy', 'true');
  } else {
    element.innerHTML = '';
    element.setAttribute('aria-busy', 'false');
  }
}

// 4. Dark/Light Mode Toggle
function toggleDarkMode() {
  document.documentElement.classList.toggle('dark-mode');
  const isDark = document.documentElement.classList.contains('dark-mode');
  localStorage.setItem('darkMode', isDark);
}

// 5. Better Animations
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('fade-in');
      observer.unobserve(entry.target);
    }
  });
});

document.querySelectorAll('.card').forEach(card => {
  observer.observe(card);
});
```

---

### **QA / TESTING ENGINEER** (5-7 ngày)

#### Task 1: API Testing (2 ngày)
```python
# WHO: QA/Testing Engineer
# TIME: 2 days
# PRIORITY: 🟡 HIGH

# Write comprehensive API tests

import requests
from django.test import TestCase, Client

class APITestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com',
            password='TestPass123'
        )
    
    def test_api_create_booking_success(self):
        """Test successful booking creation."""
        response = self.client.post('/api/booking/create/', {
            'showtime_id': 1,
            'seat_ids': [1, 2, 3]
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('booking_id', response.json())
    
    def test_api_create_booking_invalid_seats(self):
        """Test booking with invalid seats fails."""
        response = self.client.post('/api/booking/create/', {
            'showtime_id': 1,
            'seat_ids': [999]  # Invalid seat
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_api_discount_validation_valid_code(self):
        """Test discount validation with valid code."""
        response = self.client.post('/api/discount/validate/', {
            'code': 'SUMMER2026',
            'total_price': 300000
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['valid'])
    
    def test_api_discount_validation_expired_code(self):
        """Test discount validation with expired code."""
        response = self.client.post('/api/discount/validate/', {
            'code': 'EXPIRED2024',
            'total_price': 300000
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['valid'])
    
    def test_api_cancel_booking(self):
        """Test booking cancellation with refund."""
        booking = Booking.objects.create(
            user=self.user,
            total_price=100000,
            status='pending'
        )
        response = self.client.post(f'/api/booking/{booking.id}/cancel/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['refund_amount'], 90000)
```

---

#### Task 2: Frontend Testing (2 ngày)
```javascript
// WHO: QA/Testing Engineer
// TIME: 2 days
// PRIORITY: 🟠 MEDIUM

// Use Jest or Vitest for frontend testing

describe('Booking Form', () => {
  
  test('should show validation error for invalid email', () => {
    const form = document.querySelector('form');
    const email = form.querySelector('#email');
    
    email.value = 'invalid-email';
    form.dispatchEvent(new Event('submit'));
    
    const error = form.querySelector('.error');
    expect(error).toBeTruthy();
  });
  
  test('should calculate price correctly', () => {
    const seats = [
      { type: 'normal', price: 100000 },
      { type: 'vip', price: 150000 }
    ];
    const multiplier = 1.2;  // Weekend
    
    const total = seats.reduce((sum, seat) => {
      return sum + (seat.price * multiplier);
    }, 0);
    
    expect(total).toBe(300000);
  });
  
  test('should apply discount correctly', () => {
    const total = 300000;
    const discountPercent = 20;
    const discounted = total * (1 - discountPercent / 100);
    
    expect(discounted).toBe(240000);
  });
});
```

---

#### Task 3: Performance Testing (1-2 ngày)
```python
# WHO: QA/Testing Engineer
# TIME: 1-2 days
# PRIORITY: 🟠 MEDIUM

# Use Django Debug Toolbar, Lighthouse, or PageSpeed Insights

# Metrics to test:
# - Page load time < 2 seconds
# - API response time < 500ms
# - Database query optimization
# - Image optimization
# - CSS/JS minification

import time

def test_api_response_time(self):
    """Test API response time."""
    start = time.time()
    response = self.client.get('/api/movies/?limit=20')
    elapsed = time.time() - start
    
    self.assertLess(elapsed, 0.5)  # Less than 500ms
    self.assertEqual(response.status_code, 200)
```

---

#### Task 4: Integration Testing (1-2 ngày)
```python
# WHO: QA/Testing Engineer
# TIME: 1-2 days
# PRIORITY: 🟠 MEDIUM

def test_complete_booking_workflow_integration(self):
    """
    Integration test: Complete user journey.
    Browse → Select → Book → Pay → Ticket
    """
    # 1. Register user
    user = User.objects.create_user(
        email='integration@test.com',
        password='TestPass123'
    )
    
    # 2. Get available movie
    movie = Movie.objects.filter(status='active').first()
    self.assertIsNotNone(movie)
    
    # 3. Get showtimes
    showtime = Showtime.objects.filter(movie=movie).first()
    self.assertIsNotNone(showtime)
    
    # 4. Get available seats
    seats = Seat.objects.filter(
        screen=showtime.screen,
        status='available'
    )[:2]
    self.assertEqual(len(seats), 2)
    
    # 5. Create booking via API
    response = self.client.post('/api/booking/create/', {
        'showtime_id': showtime.id,
        'seat_ids': [s.id for s in seats]
    })
    self.assertEqual(response.status_code, 201)
    booking_id = response.json()['booking_id']
    
    # 6. Verify booking created
    booking = Booking.objects.get(id=booking_id)
    self.assertEqual(booking.status, 'pending')
    self.assertEqual(booking.user, user)
    
    # 7. Apply discount
    discount = Discount.objects.get(code='SUMMER2026')
    response = self.client.post('/api/discount/validate/', {
        'code': 'SUMMER2026',
        'total_price': booking.total_price
    })
    self.assertTrue(response.json()['valid'])
    
    # 8. Process payment
    response = self.client.post('/api/booking/payment/', {
        'booking_id': booking_id,
        'method': 'credit_card',
        'amount': booking.total_price
    })
    self.assertEqual(response.status_code, 200)
    
    # 9. Verify ticket generated
    booking.refresh_from_db()
    self.assertEqual(booking.status, 'completed')
    self.assertIsNotNone(booking.qr_code)
```

---

## 🎨 DESIGN SYSTEM GUIDE (từ awesome-design-systems)

### Reference Collections (Best Practices)

```
From awesome-design-systems:

1. NETFLIX
   → Dark theme (like CineVerse)
   → Bold typography
   → Large spacing
   → Red accent (#E50914)
   → Apply: Hero banner, cards, CTAs

2. MATERIAL DESIGN (Google)
   → 8px baseline grid
   → Clear hierarchy
   → Subtle shadows
   → Color palette (Primary, Secondary, Accent)
   → Apply: Forms, buttons, spacing

3. ANT DESIGN (Alibaba)
   → Component library structure
   → Consistent spacing
   → Clear states (hover, active, disabled)
   → Good form design
   → Apply: Admin dashboard, tables

4. TAILWIND CSS
   → Utility-first approach
   → Consistent naming
   → Responsive design
   → Design tokens
   → Apply: Already using, continue!

5. APPLE (iOS Human Interface)
   → Clean minimalism
   → Generous whitespace
   → Subtle animations
   → SF Pro Display font
   → Apply: Movie detail page, profile
```

### Recommended Improvements for CineVerse

```
✅ Keep:
- Dark theme (Netflix-inspired)
- Glassmorphism effect
- Purple + Cyan + Gold colors
- Outfit font (modern, readable)

⚠️ Improve:
- Add 8px baseline grid (like Material Design)
- More generous whitespace (like Apple)
- Consistent component states
- Better form design (like Ant Design)
- Utility classes (like Tailwind)

❌ Remove:
- Inconsistent spacing
- Random color usages
- Unclear typography scale
- Missing component states
```

---

## 📅 TIMELINE & PRIORITY

### Week 1 (Backend)
```
Mon-Tue: Add type hints → DocStrings
Wed-Thu: Generate Swagger docs
Fri: Write tests (5→20 tests)

Status: Backend 90% ready
```

### Week 1 (Frontend)
```
Mon: Design system audit
Tue-Wed: Improve colors & typography
Thu-Fri: Accessibility improvements

Status: Frontend design improved
```

### Week 2 (Testing & Polish)
```
Mon-Tue: API tests + Performance tests
Wed: Bug fixes
Thu-Fri: Final polish & deployment

Status: Ready for presentation!
```

---

## ✅ FINAL CHECKLIST

### Backend Tasks
- [ ] Type hints (all files)
- [ ] Docstrings (all functions)
- [ ] Swagger documentation
- [ ] Tests (50+ coverage)
- [ ] Logging & error handling
- [ ] API response validation

### Frontend Tasks
- [ ] Design tokens defined
- [ ] Colors consistent
- [ ] Typography scale defined
- [ ] Accessibility (ARIA labels)
- [ ] Responsive design tested
- [ ] Performance optimized

### Testing Tasks
- [ ] API tests (all endpoints)
- [ ] Frontend tests (forms, interactions)
- [ ] Integration tests (workflows)
- [ ] Performance tests (< 2s load)
- [ ] Accessibility audit (WCAG AA)

### Documentation Tasks
- [ ] API Swagger docs
- [ ] Code comments
- [ ] Deployment guide
- [ ] Architecture diagrams
- [ ] Design system guide

---

## 🎯 RESULT

**After completing all tasks:**
- ✅ Professional code quality
- ✅ Beautiful, accessible frontend
- ✅ Comprehensive API documentation
- ✅ High test coverage
- ✅ Production-ready system
- ✅ **Ready for A+ grade!**

---

**Document Date**: 2024-06-30  
**Team Size**: 3-4 people  
**Total Timeline**: 2-3 weeks  
**Estimated Effort**: 80-100 person-hours
