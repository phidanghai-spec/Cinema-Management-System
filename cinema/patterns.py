import datetime
from abc import ABC, abstractmethod

# ==========================================
# 2. SINGLETON PATTERN - System Settings
# ==========================================
class SystemSettings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Default configuration values
            cls._instance.cancellation_fee_percent = 10
            cls._instance.seat_lock_timeout_minutes = 10
            cls._instance.tax_rate = 0.08  # 8%
            cls._instance.points_conversion_rate = 10000 # 1 point per 10k VND
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Explicit factory method for Singleton access."""
        return cls()


# ==========================================
# 3. FACTORY & 12. ADAPTER PATTERNS - Payments
# ==========================================

# Target interface for payment processing
class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount, customer_detail):
        pass

    @abstractmethod
    def refund(self, transaction_id, amount):
        pass

# Incompatible 3rd Party APIs
class StripeAPI:
    def make_payment(self, amount_in_cents, token):
        # Stripe expects cents and return transaction info
        return {"id": f"stripe_txn_{int(datetime.datetime.now().timestamp())}", "status": "success"}

    def refund_payment(self, stripe_charge_id, amount_cents):
        return {"status": "refunded"}

class MomoAPI:
    def request_payment(self, phone_number, amount_vnd):
        # Momo expects direct VND amount and phone number
        return {"momo_ref": f"momo_txn_{int(datetime.datetime.now().timestamp())}", "code": 0}

    def refund_momo(self, momo_ref):
        return {"status": "refund_success"}

# Adapters converting 3rd party to PaymentGateway target
class StripeAdapter(PaymentGateway):
    def __init__(self):
        self.api = StripeAPI()

    def charge(self, amount, customer_detail):
        # Convert VND to USD cents (e.g. 1 USD = 25,000 VND)
        amount_cents = int((amount / 25000) * 100)
        res = self.api.make_payment(amount_cents, customer_detail)
        return res["id"]

    def refund(self, transaction_id, amount):
        amount_cents = int((amount / 25000) * 100)
        res = self.api.refund_payment(transaction_id, amount_cents)
        return res["status"] == "refunded"

class MomoAdapter(PaymentGateway):
    def __init__(self):
        self.api = MomoAPI()

    def charge(self, amount, customer_detail):
        # customer_detail is phone number
        res = self.api.request_payment(customer_detail, amount)
        if res["code"] == 0:
            return res["momo_ref"]
        raise Exception("Momo payment failed")

    def refund(self, transaction_id, amount):
        res = self.api.refund_momo(transaction_id)
        return res["status"] == "refund_success"

# Payment Processor Factory
class PaymentProcessorFactory:
    @staticmethod
    def create_processor(method):
        if method == "credit_card":
            return StripeAdapter()
        elif method == "momo":
            return MomoAdapter()
        else:
            raise ValueError(f"Unknown payment method: {method}")


# ==========================================
# 4. STRATEGY PATTERN - Movie Pricing Strategy
# ==========================================
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_base_price(self, base_price):
        pass

class WeekdayPricing(PricingStrategy):
    def calculate_base_price(self, base_price):
        # Weekdays have 10% discount
        return int(base_price * 0.9)

class WeekendPricing(PricingStrategy):
    def calculate_base_price(self, base_price):
        # Weekends have 20% surcharge
        return int(base_price * 1.2)

class HolidayPricing(PricingStrategy):
    def calculate_base_price(self, base_price):
        # Holidays have 30% surcharge
        return int(base_price * 1.3)


# ==========================================
# 5. OBSERVER PATTERN - Booking Notifications
# ==========================================
class BookingObserver(ABC):
    @abstractmethod
    def update(self, booking, message_type):
        pass

class EmailObserver(BookingObserver):
    def __init__(self):
        self.sent_emails = []

    def update(self, booking, message_type):
        # Simulated email send
        subject = f"Cinema Ticket Update: {message_type.title()}"
        body = f"Hello {booking.user.name},\nYour booking #{booking.id} status is now {booking.status}. Total cost: {booking.total_price} VND."
        self.sent_emails.append({"to": booking.user.email, "subject": subject, "body": body})
        print(f"[Email SIMULATOR] Sent email to {booking.user.email}: {subject}")

class InAppObserver(BookingObserver):
    def update(self, booking, message_type):
        from .models import InAppNotification
        # Write actual notification to database
        InAppNotification.objects.create(
            user=booking.user,
            title=f"Booking status: {message_type.title()}",
            message=f"Booking #{booking.id} has been processed successfully. Status: {booking.status.upper()}."
        )
        print(f"[InApp SIMULATOR] Created DB notification for {booking.user.email}")

class BookingSubject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, booking, message_type):
        for observer in self._observers:
            observer.update(booking, message_type)


# ==========================================
# 6. DECORATOR PATTERN - Seat Custom Pricing
# ==========================================
class SeatComponent(ABC):
    @abstractmethod
    def get_price(self):
        pass

class SimpleSeat(SeatComponent):
    def __init__(self, seat_model):
        self.seat_model = seat_model

    def get_price(self):
        return self.seat_model.price

class SeatPriceDecorator(SeatComponent):
    def __init__(self, seat_component):
        self.seat_component = seat_component

    def get_price(self):
        return self.seat_component.get_price()

class VIPSeatPriceDecorator(SeatPriceDecorator):
    def get_price(self):
        # VIP seats are 50% more expensive
        return int(self.seat_component.get_price() * 1.5)

class CoupleSeatPriceDecorator(SeatPriceDecorator):
    def get_price(self):
        # Couple seats are double price (includes 2 seats package)
        return int(self.seat_component.get_price() * 2.0)


# ==========================================
# 9. CHAIN OF RESPONSIBILITY - Promo Validation
# ==========================================
class DiscountValidator(ABC):
    def __init__(self):
        self.next_validator = None

    def set_next(self, validator):
        self.next_validator = validator
        return validator

    @abstractmethod
    def validate(self, discount, booking):
        pass

class ExpiryValidator(DiscountValidator):
    def validate(self, discount, booking):
        today = datetime.date.today()
        if today < discount.valid_from or today > discount.valid_to:
            raise Exception("Voucher has expired or is not yet valid.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class MinimumAmountValidator(DiscountValidator):
    def validate(self, discount, booking):
        if booking.total_price < discount.min_amount:
            raise Exception(f"This code requires a minimum purchase of {discount.min_amount} VND.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class UsageLimitValidator(DiscountValidator):
    def validate(self, discount, booking):
        if discount.usage_count >= discount.usage_limit:
            raise Exception("This discount code is fully redeemed.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class PerUserLimitValidator(DiscountValidator):
    def validate(self, discount, booking):
        from .models import Booking
        user_usage = Booking.objects.filter(
            user=booking.user,
            discount=discount,
            status__in=['confirmed', 'completed']
        ).count()
        if user_usage >= discount.per_user_limit:
            raise Exception("You have already used this discount code.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

def get_discount_validation_chain():
    v1 = ExpiryValidator()
    v2 = MinimumAmountValidator()
    v3 = UsageLimitValidator()
    v4 = PerUserLimitValidator()
    v1.set_next(v2).set_next(v3).set_next(v4)
    return v1


# ==========================================
# 10. STATE PATTERN - Booking Status State Transitions
# ==========================================
class BookingState(ABC):
    @abstractmethod
    def confirm(self, booking):
        pass

    @abstractmethod
    def cancel(self, booking):
        pass

    @abstractmethod
    def complete(self, booking):
        pass

class PendingState(BookingState):
    def confirm(self, booking):
        booking.status = 'confirmed'
        booking.save()
        return True

    def cancel(self, booking):
        booking.status = 'cancelled'
        booking.save()
        return True

    def complete(self, booking):
        raise Exception("Cannot complete a booking from pending state directly. Must confirm/pay first.")

class ConfirmedState(BookingState):
    def confirm(self, booking):
        raise Exception("Booking is already confirmed.")

    def cancel(self, booking):
        # 10% cancellation fee applied
        settings = SystemSettings()
        booking.status = 'cancelled'
        booking.refund_amount = int(booking.total_price * (1 - settings.cancellation_fee_percent / 100))
        booking.save()
        return True

    def complete(self, booking):
        booking.status = 'completed'
        booking.save()
        return True

class CompletedState(BookingState):
    def confirm(self, booking):
        raise Exception("Booking is already completed.")

    def cancel(self, booking):
        raise Exception("Cannot cancel a completed/used booking.")

    def complete(self, booking):
        raise Exception("Booking is already completed.")

class CancelledState(BookingState):
    def confirm(self, booking):
        raise Exception("Cannot confirm a cancelled booking.")

    def cancel(self, booking):
        raise Exception("Booking is already cancelled.")

    def complete(self, booking):
        raise Exception("Cannot complete a cancelled booking.")

def get_booking_state_class(status):
    if status == 'pending':
        return PendingState()
    elif status == 'confirmed':
        return ConfirmedState()
    elif status == 'completed':
        return CompletedState()
    elif status == 'cancelled':
        return CancelledState()
    else:
        raise ValueError(f"Unknown booking status: {status}")


# ==========================================
# 11. BUILDER PATTERN - Complex Booking Builder
# ==========================================
class BookingBuilder:
    def __init__(self):
        self._user = None
        self._showtime = None
        self._seats = []
        self._discount = None
        self._notes = ""

    def set_user(self, user):
        self._user = user
        return self

    def set_showtime(self, showtime):
        self._showtime = showtime
        return self

    def add_seat(self, seat):
        self._seats.append(seat)
        return self

    def set_discount(self, discount):
        self._discount = discount
        return self

    def set_notes(self, notes):
        self._notes = notes
        return self

    def build(self):
        from .models import Booking, BookingItem
        if not self._user:
            raise ValueError("User must be specified")
        if not self._showtime:
            raise ValueError("Showtime must be specified")
        if not self._seats:
            raise ValueError("At least one seat must be selected")

        # Calculate final price utilizing Decorator pattern on seats
        subtotal = 0
        for seat in self._seats:
            component = SimpleSeat(seat)
            if seat.type == 'vip':
                component = VIPSeatPriceDecorator(component)
            elif seat.type == 'couple':
                component = CoupleSeatPriceDecorator(component)
            subtotal += component.get_price()

        # Apply multiplier from Showtime (e.g. 1.2x for IMAX)
        subtotal = int(subtotal * self._showtime.price_multiplier)

        # Apply discount if valid
        discount_amount = 0
        if self._discount:
            if self._discount.type == 'percentage':
                discount_amount = int(subtotal * (self._discount.value / 100.0))
            else:
                discount_amount = self._discount.value
        
        total_price = max(0, subtotal - discount_amount)

        # Create Booking
        booking = Booking.objects.create(
            user=self._user,
            showtime=self._showtime,
            total_price=total_price,
            discount=self._discount,
            notes=self._notes,
            status='pending'
        )

        # Create BookingItems
        for seat in self._seats:
            component = SimpleSeat(seat)
            if seat.type == 'vip':
                component = VIPSeatPriceDecorator(component)
            elif seat.type == 'couple':
                component = CoupleSeatPriceDecorator(component)
            item_price = int(component.get_price() * self._showtime.price_multiplier)
            BookingItem.objects.create(
                booking=booking,
                seat=seat,
                price=item_price
            )

        return booking


# ==========================================
# 8. TEMPLATE METHOD PATTERN - Booking Workflow
# ==========================================
class BookingWorkflow(ABC):
    def execute(self, user, showtime, seats, discount_code=None, notes="", payment_method="credit_card", phone=""):
        # Skeleton of the workflow
        self.validate_user(user)
        self.validate_showtime(showtime)
        self.validate_seats(seats)
        
        discount = None
        if discount_code:
            discount = self.resolve_discount(discount_code)

        # Construct booking step (Builder)
        builder = BookingBuilder().set_user(user).set_showtime(showtime).set_notes(notes)
        for seat in seats:
            builder.add_seat(seat)
        if discount:
            builder.set_discount(discount)
            
        booking = builder.build()

        # Validate discount sequentially if code was provided (Chain of Responsibility)
        if discount:
            try:
                self.validate_discount_code(discount, booking)
            except Exception as e:
                # Rollback/delete the booking draft if invalid discount code applied
                booking.delete()
                raise e

        # Lock seats state
        for seat in seats:
            # Lock seat by reserving it for this booking (Mock real-time lock status)
            pass

        # Complete payment step
        payment = self.process_payment(booking, payment_method, phone)

        # State transition step (State Pattern)
        state_class = get_booking_state_class(booking.status)
        state_class.confirm(booking)  # Move pending to confirmed

        # Post-booking notifications (Observer)
        self.notify_user(booking)

        return booking, payment

    @abstractmethod
    def validate_user(self, user):
        pass

    @abstractmethod
    def validate_showtime(self, showtime):
        pass

    @abstractmethod
    def validate_seats(self, seats):
        pass

    @abstractmethod
    def resolve_discount(self, discount_code):
        pass

    @abstractmethod
    def validate_discount_code(self, discount, booking):
        pass

    @abstractmethod
    def process_payment(self, booking, method, phone):
        pass

    @abstractmethod
    def notify_user(self, booking):
        pass

class StandardBookingWorkflow(BookingWorkflow):
    def validate_user(self, user):
        if user.status == 'banned':
            raise Exception("User is banned from system.")

    def validate_showtime(self, showtime):
        now = datetime.datetime.now(datetime.timezone.utc)
        if showtime.start_time < now:
            raise Exception("Showtime is in the past.")

    def validate_seats(self, seats):
        for seat in seats:
            if seat.status != 'available':
                raise Exception(f"Seat {seat.seat_number} is not available.")

    def resolve_discount(self, discount_code):
        from .models import Discount
        try:
            return Discount.objects.get(code__iexact=discount_code)
        except Discount.DoesNotExist:
            raise Exception("Discount code not found.")

    def validate_discount_code(self, discount, booking):
        chain = get_discount_validation_chain()
        chain.validate(discount, booking)

    def process_payment(self, booking, method, phone):
        from .models import Payment
        factory = PaymentProcessorFactory()
        processor = factory.create_processor(method)
        txn_id = processor.charge(booking.total_price, phone if method == "momo" else "stripe_token")

        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            method=method,
            transaction_id=txn_id,
            status='completed'
        )
        return payment

    def notify_user(self, booking):
        subject = BookingSubject()
        email_observer = EmailObserver()
        inapp_observer = InAppObserver()
        subject.attach(email_observer)
        subject.attach(inapp_observer)
        subject.notify(booking, "booking_confirmed")
