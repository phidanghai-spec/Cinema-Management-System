# CineVerse Software Design Patterns

This document details the mapping, rationale, and implementation details of the **15 Software Design Patterns** applied in **CineVerse**.

---

## 🛠️ Creational Patterns

### 1. Singleton (`SystemSettings`)
* **Purpose**: Manages a single global instance of configuration values.
* **Why**: Settings such as cancellation fees, seat lock timeouts, and loyalty point conversion rates must remain consistent across the app. Having duplicate settings instances could lead to inconsistencies.
* **Benefit**: Ensures a centralized, thread-safe config registry.

### 2. Builder (`BookingBuilder`)
* **Purpose**: Builds a complex `Booking` instance step-by-step.
* **Why**: A `Booking` requires loading several entities (User, Showtime, Seats, Discount, Notes) and performing dependent computations (subtotal, points discounts, strategy premiums). Combining this in a single constructor call results in telescoping parameters.
* **Benefit**: Highly readable creation pipeline.

### 3. Factory Method (`PaymentProcessorFactory`)
* **Purpose**: Instantiates payment gateway adapters.
* **Why**: The booking workflow should not couple itself to concrete adapters like `StripeAdapter` or `MomoAdapter`. The factory isolates instantiation logic behind a lookup string.
* **Benefit**: High flexibility; adding a new payment gateway (e.g. PayPal) does not touch core booking workflow files.

### 4. Prototype (`MoviePrototype` & `ShowtimePrototype`)
* **Purpose**: Creates duplicate objects from existing prototype templates.
* **Why**: Admins frequently create duplicate movies or copy showtimes over multiple screen dates. Copying existing objects minimizes repetitive manual data entries.
* **Benefit**: Highly performant replication of model properties.

---

## 🔌 Structural Patterns

### 5. Adapter (`StripeAdapter` & `MomoAdapter`)
* **Purpose**: Adapts third-party APIs to a standard interface.
* **Why**: Incompatible interfaces (Stripe charges in cents, MoMo returns redirection payment URLs) must conform to our standard `PaymentGateway` model.
* **Benefit**: Decouples third-party library dependencies from the core system.

### 6. Decorator (`SeatPriceDecorator` & subclasses)
* **Purpose**: Adds dynamic pricing wrappers to seats.
* **Why**: Standard seat prices can be wrapped dynamically if the seat type is VIP (50% premium) or Couple (2x price). Building separate seat subclasses for every type of premium combination pollutes the model class tree.
* **Benefit**: Stacking seat modifiers at runtime.

### 7. Facade (`BookingFacade`)
* **Purpose**: Provides a simplified high-level interface to the complex booking workflows and validation subsystems.
* **Why**: Making a booking requires seat decorators, pricing strategies, user checks, point redemption calculations, and discount validation chains. Client code (views) should not manage these subsystems manually.
* **Benefit**: Simplifies the entry point for API views and decreases architectural coupling.

---

## ⚙️ Behavioral Patterns

### 8. Strategy (`PricingStrategy` & subclasses)
* **Purpose**: Selects ticket pricing rules dynamically.
* **Why**: Pricing modifiers vary depending on showtime hours and calendar schedules (Weekday discount, Weekend surcharge, Holiday premiums, Happy Hour specials).
* **Benefit**: Swapping algorithms dynamically based on showtime datetime without hardcoding nested `if-else` loops.

### 9. Observer (`BookingObserver` & subclasses)
* **Purpose**: Dispatches state change alerts.
* **Why**: Confirming or cancelling a booking must notify other modules (Email system, In-App notifier, Loyalty points manager) without coupling them to the `Booking` class.
* **Benefit**: Clean, modular notifications.

### 10. Chain of Responsibility (`DiscountValidator` & subclasses)
* **Purpose**: Runs a pipeline of voucher validation rules.
* **Why**: Validation parameters (expiration date, minimum amount, usage count limit, user tier eligibility, movie specific conditions) must execute sequentially.
* **Benefit**: Adding or removing rules is done by simply changing the link reference in the validation chain structure.

### 11. State (`BookingState` & subclasses)
* **Purpose**: Directs lifecycle states of a booking.
* **Why**: States (`pending`, `confirmed`, `completed`, `cancelled`) have strict state-transition validations and business side-effects (points deduction, tier recalculation).
* **Benefit**: Avoids complex state transition status check conditions.

### 12. Template Method (`BookingWorkflow` & `StandardBookingWorkflow`)
* **Purpose**: Outlines the skeleton of the booking transaction pipeline.
* **Why**: The transaction pipeline consists of structured sequences (validate ➔ compile ➔ discount ➔ pay ➔ state change ➔ notify). 
* **Benefit**: Enforces transaction execution flow sequence.

### 13. Command (`BookCommand` & `CancelCommand`)
* **Purpose**: Encapsulates a request as an object, allowing for parameterization, logging, and execution boundaries.
* **Why**: Allows decouplement between views/controllers and the actual operations, standardizing transactional triggers.
* **Benefit**: Streamlines transaction control and makes execution log auditing natural.

---

## 🏛️ Architectural Patterns

### 14. Model-View-Template (MVT)
* **Description**: Standard architectural pattern in Django separating database representations (Models), request routing and view controller logic (Views), and client HTML design pages (Templates).

### 15. Repository (Data Access Object)
* **Description**: Isolates DB queries and filters from views and business workflows (found in `repositories.py`).
