# CineVerse — Day 1 Structure, Models & Migrations Review Notes

**Date:** July 10, 2026  
**Auditor:** Antigravity (AI Pair Programmer)  
**Status:** Baseline Established (`v-before-refactor` tagged & pushed). Tests passing 100%.

---

## 1. Project Directory Structure Review

The CineVerse project template organization has been refactored from a flat structure to a modular, decoupled layout:

```
d:\Cinema Management System
├── cinema/
│   ├── static/cinema/                # Static assets (CSS, JS)
│   ├── templates/cinema/             # Django HTML templates
│   │   ├── auth/                     # login.html, register.html, forgot_password.html, reset_password.html
│   │   ├── components/               # navbar.html, footer.html, sidebar_admin.html
│   │   └── pages/                    # movie_list.html, movie_detail.html, booking_flow.html, etc.
│   │       └── admin/                # dashboard.html, movies.html, showtimes.html, users.html
│   ├── utils/
│   │   └── decorators.py             # Role-based decorators (@role_required)
│   ├── exceptions.py                 # Core domain exceptions
│   ├── models.py                     # Database models schema
│   ├── patterns.py                   # Design patterns implementations
│   ├── repositories.py               # Database query isolation layers
│   ├── services.py                   # Main business logic services
│   ├── views.py                      # Customer flow views
│   └── views_admin.py                # Admin dashboard views
└── cinema_project/                   # Django settings and routing root
```

* **Observation:** The organization is highly professional. Decoupling templates into `auth/`, `components/`, and `pages/` (along with sub-nested `admin/`) ensures high maintainability. The division of customer and admin views (`views.py` and `views_admin.py`) avoids monolithic controller bloat.

---

## 2. Models Schema Audit

We audited the model configurations in `cinema/models.py`:

| Model Name | Key Fields & Configuration | Audit Notes |
|---|---|---|
| **User** | `email` (unique), `password_hash`, `points`, `tier` (Bronze-Platinum), `status` (unverified, active, banned), `role` (customer, admin, staff) | **Excellent design.** Integrates loyalty features (`points`, `tier`) and role-based control (`role`) directly in the schema without hardcoding. |
| **Movie** | `age_rating` (P, C13, C16, C18), `director`, `cast`, standard meta | Movie age classification and casting details allow professional CGV-standard presentation on client-side pages. |
| **Theater / Screen / Seat** | Screen capacity, Rows/Columns, Seat types (normal, vip, couple), Seat base pricing | Complete hierarchy for seat layout grids and customizable screen layouts. |
| **Showtime** | Movie & Screen references, start/end times, `price_multiplier` | Allows runtime price decoration (e.g., higher pricing for weekend/IMAX slots). |
| **Discount** | `code`, `type` (fixed/percentage), advanced conditions (`min_tier`, `allow_points_combination`, `is_golden_hour_only`) | Directly supports the Chain of Responsibility discount validator pattern dynamically. |
| **Booking & BookingItem** | Showtime reference, status (pending, confirmed, completed, cancelled), pricing breakdown, points usage | Integrates state transitioning and tracking of loyalty points earned/redeemed. |
| **Payment** | Booking, method (momo, zalopay, credit_card), status, payment URL | Isolated transaction model supporting multiple gateways via Adapter pattern. |
| **Review / HelpfulVote / Reply** | Verified review check, admin responses, user votes | Review replying is locked strictly to admin users. |

---

## 3. Migration Sequence Check

Migrations inside `cinema/migrations/` are structured chronologically:
1. `0001_initial.py`: Set up the initial cinema structure (Users, Movies, Bookings, Payments, etc.).
2. `0002_movie_age_rating_movie_cast_movie_director.py`: Added CGV-standard cinema fields to the Movie model.
3. `0003_booking_points_earned_booking_redeemed_points_and_more.py`: Added loyalty points tracking and discount condition options.
4. `0004_payment_payment_url.py`: Added Momo gateway checkout URL redirect field.
5. `0005_user_role.py`: Added User role field and choices.

* **Status:** The migration sequence is cleanly structured and fully applied. The database migrations align completely with current models.

---

## 4. Role-based Auth Refactoring (Day 1 Done)

We successfully identified and resolved the remaining hardcoded admin email checks in views/templates to complete Day 1 requirements:

* **Views:** Updated the admin reply API `submit_review_reply_api` in `views.py` from `user.email != 'admin@cinema.com'` to `user.role != 'admin'`.
* **Client Template:** Updated the admin comment reply block visibility in `movie_detail.html` to check `user.role == 'admin'`.
* **Admin Template:** Updated the admin member management screen in `users.html` to safeguard admins from getting banned by checking `u.role != 'admin'`.

This guarantees that authorization controls are 100% scalable and support standard roles (such as staff/moderators) without code modification.
