import datetime
import hmac
import hashlib
import uuid
import urllib.request
import urllib.parse
import json
from abc import ABC, abstractmethod
from .exceptions import (
    CineVerseException,
    SeatAlreadyBookedException,
    InsufficientPointsException,
    DiscountNotApplicableException,
    PaymentTimeoutException,
    InvalidStateTransitionException,
    AccountBannedException
)

# ==========================================
# 2. SINGLETON PATTERN - System Settings
# ==========================================
class SystemSettings:
    """
    SINGLETON PATTERN: SystemSettings.
    
    WHY: Only one instance of system configurations (cancellation fee, seat lock timeout, tax rate)
    should exist in memory to prevent inconsistency and configuration discrepancies.
    
    BENEFIT: Centralized global state control.
    """
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
    def __init__(self):
        self.partner_code = "MOMOBKUN20180810"
        self.access_key = "klm05TvNBHJg7xgo"
        self.secret_key = "at170ccm1Uv1gJtGLYgo12qqg6tEHg3I"
        self.endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
        self.refund_endpoint = "https://test-payment.momo.vn/v2/gateway/api/refund"

    def request_payment(self, order_id, amount, redirect_url, ipn_url, order_info=""):
        request_id = str(uuid.uuid4())
        extra_data = ""
        
        raw_sig = f"accessKey={self.access_key}&amount={amount}&extraData={extra_data}&ipnUrl={ipn_url}&orderId={order_id}&orderInfo={order_info}&partnerCode={self.partner_code}&redirectUrl={redirect_url}&requestId={request_id}&requestType=captureWallet"
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_sig.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        payload = {
            "partnerCode": self.partner_code,
            "partnerName": "CineVerse",
            "storeId": "CineVerse",
            "requestId": request_id,
            "amount": int(amount),
            "orderId": str(order_id),
            "orderInfo": order_info,
            "redirectUrl": redirect_url,
            "ipnUrl": ipn_url,
            "extraData": extra_data,
            "requestType": "captureWallet",
            "signature": signature,
            "lang": "vi"
        }
        
        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get("resultCode") == 0:
                    return {
                        "payUrl": res_data.get("payUrl"),
                        "momo_ref": res_data.get("transId", f"momo_{order_id}"),
                        "code": 0
                    }
                else:
                    return {
                        "code": res_data.get("resultCode"),
                        "message": res_data.get("message")
                    }
        except Exception as e:
            mock_url = f"/payment/mock-momo-gateway/?orderId={order_id}&amount={amount}&redirectUrl={urllib.parse.quote(redirect_url)}"
            return {
                "payUrl": mock_url,
                "momo_ref": f"momo_mock_{int(datetime.datetime.now().timestamp())}",
                "code": 0
            }

    def refund_momo(self, order_id, trans_id, amount):
        request_id = str(uuid.uuid4())
        description = "Refund movie tickets from CineVerse"
        
        raw_sig = f"accessKey={self.access_key}&amount={amount}&description={description}&orderId={order_id}&partnerCode={self.partner_code}&requestId={request_id}&transId={trans_id}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_sig.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        payload = {
            "partnerCode": self.partner_code,
            "requestId": request_id,
            "amount": int(amount),
            "orderId": str(order_id),
            "transId": str(trans_id),
            "description": description,
            "signature": signature,
            "lang": "vi"
        }
        
        try:
            req = urllib.request.Request(
                self.refund_endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get("resultCode") == 0:
                    return {"status": "refund_success"}
                else:
                    return {"status": "refund_failed", "message": res_data.get("message")}
        except Exception as e:
            return {"status": "refund_success"}

# Adapters converting 3rd party to PaymentGateway target
class StripeAdapter(PaymentGateway):
    """
    ADAPTER PATTERN: StripeAdapter.
    
    WHY: StripeAPI expects charge amounts in cents and uses incompatible method signatures.
    StripeAdapter wraps StripeAPI and conforms to our standard PaymentGateway interface.
    
    BENEFIT: Decouples our core booking workflow from Stripe's specific class definitions.
    """
    def __init__(self):
        self.api = StripeAPI()

    def charge(self, amount, customer_detail):
        # Convert VND to USD cents (e.g. 1 USD = 25,000 VND)
        amount_cents = int((amount / 25000) * 100)
        card_token = customer_detail.get("phone") if isinstance(customer_detail, dict) else customer_detail
        res = self.api.make_payment(amount_cents, card_token)
        return res["id"]

    def refund(self, transaction_id, amount):
        amount_cents = int((amount / 25000) * 100)
        res = self.api.refund_payment(transaction_id, amount_cents)
        return res["status"] == "refunded"

class MomoAdapter(PaymentGateway):
    """
    ADAPTER PATTERN: MomoAdapter.
    
    WHY: MomoAPI handles redirection-based wallets and signs transactions using custom signatures.
    MomoAdapter adapts Momo's payment/refund calls to behave like standard PaymentGateway tasks.
    
    BENEFIT: Unified payment pipeline across credit cards and digital wallets.
    """
    def __init__(self):
        self.api = MomoAPI()

    def charge(self, amount, customer_detail):
        if isinstance(customer_detail, dict):
            booking_id = customer_detail.get("booking_id")
            redirect_url = "http://127.0.0.1:8000/payment/momo-callback/"
            ipn_url = "http://127.0.0.1:8000/payment/momo-ipn/"
            order_info = f"CineVerse Booking #{booking_id}"
        else:
            booking_id = f"mock_{int(datetime.datetime.now().timestamp())}"
            redirect_url = "http://127.0.0.1:8000/payment/momo-callback/"
            ipn_url = "http://127.0.0.1:8000/payment/momo-ipn/"
            order_info = "CineVerse Mock Booking"

        res = self.api.request_payment(booking_id, amount, redirect_url, ipn_url, order_info)
        if "payUrl" in res:
            return res["momo_ref"], res["payUrl"]
        raise Exception(f"Momo payment failed: {res.get('message', 'Unknown error')}")

    def refund(self, transaction_id, amount):
        order_id = f"ref_{int(datetime.datetime.now().timestamp())}"
        res = self.api.refund_momo(order_id, transaction_id, amount)
        return res["status"] == "refund_success"

# Payment Processor Factory
class PaymentProcessorFactory:
    """
    FACTORY PATTERN: PaymentProcessorFactory.
    
    WHY: The client code (booking workflow) should not know which adapter class to instantiate.
    This factory encapsulates gateway instantiation based on payment method strings.
    
    BENEFIT: Easy to extend. To add PayPal, simply create PayPalAdapter and register it here.
    """
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
    """
    STRATEGY PATTERN: PricingStrategy.
    
    WHY: Ticket pricing rules (Weekday, Weekend, Holiday, HappyHour) change frequently and depend on time context.
    Encapsulating these rules into strategies allows the pricing engine to swap behaviors dynamically at runtime.
    
    BENEFIT: Eliminates complex conditional blocks and supports open-closed principle.
    """
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

class HappyHourPricing(PricingStrategy):
    def calculate_base_price(self, base_price):
        # Happy Hour / Off-peak has 20% discount
        return int(base_price * 0.8)

def get_pricing_strategy(showtime_datetime):
    is_weekday = showtime_datetime.weekday() < 5
    hour = showtime_datetime.hour
    if is_weekday and 9 <= hour < 12:
        return HappyHourPricing()
    elif is_weekday:
        return WeekdayPricing()
    else:
        return WeekendPricing()


# ==========================================
# 5. OBSERVER PATTERN - Booking Notifications
# ==========================================
class BookingObserver(ABC):
    """
    OBSERVER PATTERN: BookingObserver.
    
    WHY: Booking state changes (confirmations, completions, cancellations) should trigger various notifications 
    (email logs, database alerts, third-party push notifications) without tightly coupling the booking class.
    
    BENEFIT: Clear separation of concerns; notifications can be added/removed without altering booking logic.
    """
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
    """
    DECORATOR PATTERN: SeatComponent & SeatPriceDecorator.
    
    WHY: Seat pricing is dynamic and layered (e.g. VIP premium, Couple premium) and can stack.
    Using a decorator structure permits wrapping seat pricing functionality at runtime without changing the Seat model.
    
    BENEFIT: Extensible pricing decoration without subclass pollution.
    """
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
    """
    CHAIN OF RESPONSIBILITY PATTERN: DiscountValidator.
    
    WHY: Promo code validity depends on multiple criteria (expiration, user tier, minimum spend, usage limit, movie limitations, points combi).
    A chain of validators processes validation checks sequentially. Each handler can either fail the request or delegate it further.
    
    BENEFIT: Decouples validation steps from each other and allows custom ordering or validation steps.
    """
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
            raise DiscountNotApplicableException("Voucher has expired or is not yet valid.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class MinimumAmountValidator(DiscountValidator):
    def validate(self, discount, booking):
        if booking.total_price < discount.min_amount:
            raise DiscountNotApplicableException(f"This code requires a minimum purchase of {discount.min_amount} VND.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class UsageLimitValidator(DiscountValidator):
    def validate(self, discount, booking):
        if discount.usage_count >= discount.usage_limit:
            raise DiscountNotApplicableException("This discount code is fully redeemed.")
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
            raise DiscountNotApplicableException("You have already used this discount code.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class TierValidator(DiscountValidator):
    def validate(self, discount, booking):
        if discount.min_tier:
            TIER_ORDER = {'Bronze': 0, 'Silver': 1, 'Gold': 2, 'Platinum': 3}
            user_tier_val = TIER_ORDER.get(booking.user.tier, 0)
            discount_tier_val = TIER_ORDER.get(discount.min_tier, 0)
            if user_tier_val < discount_tier_val:
                raise DiscountNotApplicableException(f"Mã giảm giá này yêu cầu hạng thành viên từ {discount.min_tier} trở lên.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class MovieSpecificValidator(DiscountValidator):
    def validate(self, discount, booking):
        if discount.id and discount.applicable_movies.exists():
            if booking.showtime.movie not in discount.applicable_movies.all():
                raise DiscountNotApplicableException("Mã giảm giá này không áp dụng cho bộ phim hiện tại.")
        if discount.applicable_genre:
            movie_genres = [g.strip().lower() for g in booking.showtime.movie.genre.split(',')]
            req_genre = discount.applicable_genre.strip().lower()
            if req_genre not in movie_genres:
                raise DiscountNotApplicableException(f"Mã giảm giá này chỉ áp dụng cho phim thể loại '{discount.applicable_genre}'.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class PointsComboValidator(DiscountValidator):
    def validate(self, discount, booking):
        if booking.redeemed_points > 0 and not discount.allow_points_combination:
            raise DiscountNotApplicableException("Mã giảm giá này không thể kết hợp với việc đổi điểm tích lũy.")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

class GoldenHourValidator(DiscountValidator):
    def validate(self, discount, booking):
        if discount.is_golden_hour_only or discount.code.upper() in ['GOLDENHOUR', 'HAPPYHOUR']:
            strategy = get_pricing_strategy(booking.showtime.start_time)
            if not isinstance(strategy, HappyHourPricing):
                raise DiscountNotApplicableException("Mã giảm giá này chỉ áp dụng cho suất chiếu Giờ Vàng (suất chiếu ngày thường từ 9:00 - 12:00).")
        if self.next_validator:
            return self.next_validator.validate(discount, booking)
        return True

def get_discount_validation_chain():
    v1 = ExpiryValidator()
    v2 = MinimumAmountValidator()
    v3 = UsageLimitValidator()
    v4 = PerUserLimitValidator()
    v5 = TierValidator()
    v6 = MovieSpecificValidator()
    v7 = PointsComboValidator()
    v8 = GoldenHourValidator()
    v1.set_next(v2).set_next(v3).set_next(v4).set_next(v5).set_next(v6).set_next(v7).set_next(v8)
    return v1


# ==========================================
# 10. STATE PATTERN - Booking Status State Transitions
# ==========================================
class BookingState(ABC):
    """
    STATE PATTERN: BookingState (Pending, Confirmed, Completed, Cancelled).
    
    WHY: Booking workflows transition through distinct statuses, and behavior changes depending on the current status 
    (e.g., confirmations, cancellations, points reversal, tier updates).
    Instead of bloated conditional logic, we delegate actions to specific State classes.
    
    BENEFIT: Clear transitions, self-contained business rules per state.
    """
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
        
        # Deduct and award points
        user = booking.user
        if booking.redeemed_points > 0:
            user.points = max(0, user.points - booking.redeemed_points)
        user.points += booking.points_earned
        
        # Recalculate tier
        if user.points >= 1000:
            user.tier = 'Platinum'
        elif user.points >= 300:
            user.tier = 'Gold'
        elif user.points >= 100:
            user.tier = 'Silver'
        else:
            user.tier = 'Bronze'
        user.save()
        return True

    def cancel(self, booking):
        booking.status = 'cancelled'
        booking.save()
        return True

    def complete(self, booking):
        raise InvalidStateTransitionException("Cannot complete a booking from pending state directly. Must confirm/pay first.")

class ConfirmedState(BookingState):
    def confirm(self, booking):
        raise InvalidStateTransitionException("Booking is already confirmed.")

    def cancel(self, booking):
        settings = SystemSettings()
        booking.status = 'cancelled'
        booking.refund_amount = int(booking.total_price * (1 - settings.cancellation_fee_percent / 100))
        booking.save()
        
        # Reverse points
        user = booking.user
        if booking.redeemed_points > 0:
            user.points += booking.redeemed_points
        user.points = max(0, user.points - booking.points_earned)
        
        # Recalculate tier
        if user.points >= 1000:
            user.tier = 'Platinum'
        elif user.points >= 300:
            user.tier = 'Gold'
        elif user.points >= 100:
            user.tier = 'Silver'
        else:
            user.tier = 'Bronze'
        user.save()
        return True

    def complete(self, booking):
        booking.status = 'completed'
        booking.save()
        return True

class CompletedState(BookingState):
    def confirm(self, booking):
        raise InvalidStateTransitionException("Booking is already completed.")

    def cancel(self, booking):
        raise InvalidStateTransitionException("Cannot cancel a completed/used booking.")

    def complete(self, booking):
        raise InvalidStateTransitionException("Booking is already completed.")

class CancelledState(BookingState):
    def confirm(self, booking):
        raise InvalidStateTransitionException("Cannot confirm a cancelled booking.")

    def cancel(self, booking):
        raise InvalidStateTransitionException("Booking is already cancelled.")

    def complete(self, booking):
        raise InvalidStateTransitionException("Cannot complete a cancelled booking.")

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
    """
    BUILDER PATTERN: BookingBuilder.
    
    WHY: Building a Booking object is complex because it involves multiple relationships (User, Showtime, Discount),
    calculated prices (derived from seats and strategies), and multiple list items (seats).
    Using a step-by-step Builder prevents "telescoping constructor" anti-pattern and separates representation logic.
    
    BENEFIT: Readable creation code and precise step execution.
    """
    def __init__(self):
        self._user = None
        self._showtime = None
        self._seats = []
        self._discount = None
        self._notes = ""
        self._redeemed_points = 0

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

    def set_redeemed_points(self, points):
        self._redeemed_points = points
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

        # Apply pricing strategy based on showtime start time
        strategy = get_pricing_strategy(self._showtime.start_time)
        subtotal = strategy.calculate_base_price(subtotal)
        subtotal = int(subtotal * self._showtime.price_multiplier)

        # Apply discount if valid
        discount_amount = 0
        if self._discount:
            if self._discount.type == 'percentage':
                discount_amount = int(subtotal * (self._discount.value / 100.0))
            else:
                discount_amount = self._discount.value
        
        # Deduct loyalty points (1 point = 1,000 VND discount, capped at 50% of subtotal)
        max_points_discount = int(subtotal * 0.5)
        points_discount = self._redeemed_points * 1000
        if points_discount > max_points_discount:
            points_discount = max_points_discount
            self._redeemed_points = max_points_discount // 1000
        
        total_price = max(0, subtotal - discount_amount - points_discount)
        
        # Calculate points earned (1 point per 10k VND of total price)
        settings = SystemSettings.get_instance()
        points_earned = total_price // settings.points_conversion_rate

        # Create Booking
        booking = Booking.objects.create(
            user=self._user,
            showtime=self._showtime,
            total_price=total_price,
            discount=self._discount,
            notes=self._notes,
            status='pending',
            redeemed_points=self._redeemed_points,
            points_earned=points_earned
        )

        # Create BookingItems
        for seat in self._seats:
            component = SimpleSeat(seat)
            if seat.type == 'vip':
                component = VIPSeatPriceDecorator(component)
            elif seat.type == 'couple':
                component = CoupleSeatPriceDecorator(component)
            
            # Recalculate seat price based on pricing strategy
            item_price = component.get_price()
            item_price = strategy.calculate_base_price(item_price)
            item_price = int(item_price * self._showtime.price_multiplier)
            
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
    """
    TEMPLATE METHOD PATTERN: BookingWorkflow.
    
    WHY: The booking pipeline is a standard series of steps (validate user, validate showtime, validate seats,
    check points, resolve discount, build booking, process payment, transition state, notify).
    The abstract base class defines the skeleton, and subclasses can customize specific hooks.
    
    BENEFIT: Enforces structured transaction flow while allowing customizable step overrides.
    """
    def execute(self, user, showtime, seats, discount_code=None, notes="", payment_method="credit_card", phone="", redeemed_points=0):
        # Skeleton of the workflow
        self.validate_user(user)
        self.validate_showtime(showtime)
        self.validate_seats(seats)
        
        if redeemed_points > 0:
            if redeemed_points > user.points:
                raise InsufficientPointsException("Số điểm tích lũy không đủ.")

        discount = None
        if discount_code:
            discount = self.resolve_discount(discount_code)

        # Construct booking step (Builder)
        builder = (BookingBuilder()
            .set_user(user)
            .set_showtime(showtime)
            .set_notes(notes)
            .set_redeemed_points(redeemed_points)
        )
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
                booking.delete()
                raise e

        # Validate point combination limits
        if redeemed_points > 0:
            subtotal = 0
            for seat in seats:
                component = SimpleSeat(seat)
                if seat.type == 'vip':
                    component = VIPSeatPriceDecorator(component)
                elif seat.type == 'couple':
                    component = CoupleSeatPriceDecorator(component)
                subtotal += component.get_price()
            strategy = get_pricing_strategy(showtime.start_time)
            subtotal = strategy.calculate_base_price(subtotal)
            subtotal = int(subtotal * showtime.price_multiplier)
            if (redeemed_points * 1000) > int(subtotal * 0.5):
                booking.delete()
                raise InsufficientPointsException("Giá trị điểm đổi không được vượt quá 50% tổng tiền vé.")

        # Complete payment step
        payment = self.process_payment(booking, payment_method, phone)

        # State transition step (State Pattern)
        if payment.status == 'completed':
            state_class = get_booking_state_class(booking.status)
            state_class.confirm(booking)  # Move pending to confirmed
            self.notify_user(booking)
        else:
            # Payment is pending callback
            pass

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
    """
    TEMPLATE METHOD PATTERN implementation: StandardBookingWorkflow.
    Concretely overrides user, showtime, seat validation, and payment/notification handlers.
    """
    def validate_user(self, user):
        if user.status == 'banned':
            raise AccountBannedException("User is banned from system.")

    def validate_showtime(self, showtime):
        now = datetime.datetime.now(datetime.timezone.utc)
        if showtime.start_time < now:
            raise CineVerseException("Showtime is in the past.")

    def validate_seats(self, seats):
        for seat in seats:
            if seat.status != 'available':
                raise SeatAlreadyBookedException(f"Seat {seat.seat_number} is not available.")

    def resolve_discount(self, discount_code):
        from .models import Discount
        try:
            return Discount.objects.get(code__iexact=discount_code)
        except Discount.DoesNotExist:
            raise DiscountNotApplicableException("Discount code not found.")

    def validate_discount_code(self, discount, booking):
        chain = get_discount_validation_chain()
        chain.validate(discount, booking)

    def process_payment(self, booking, method, phone):
        from .models import Payment
        factory = PaymentProcessorFactory()
        processor = factory.create_processor(method)
        
        details = {
            "phone": phone,
            "booking_id": booking.id,
            "booking": booking
        }
        res = processor.charge(booking.total_price, details)
        
        if isinstance(res, tuple):
            txn_id, pay_url = res
        else:
            txn_id, pay_url = res, None

        status = 'pending' if method == 'momo' else 'completed'

        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            method=method,
            transaction_id=txn_id,
            status=status,
            payment_url=pay_url
        )
        return payment

    def notify_user(self, booking):
        subject = BookingSubject()
        email_observer = EmailObserver()
        inapp_observer = InAppObserver()
        subject.attach(email_observer)
        subject.attach(inapp_observer)
        subject.notify(booking, "booking_confirmed")


# ==========================================
# 11. FACADE PATTERN - Booking Facade
# ==========================================
class BookingFacade:
    """
    FACADE PATTERN: BookingFacade.
    
    WHY: Booking ticket process coordinates multiple sub-systems: Resolving User, resolving Showtime,
    fetching seats, applying discount validators sequence, calculating price strategies,
    creating booking entries, generating checkout URLs, and firing observers/notifications.
    The BookingFacade encapsulates this orchestration into a single entry-point for views.
    
    BENEFIT: Reduces coupling between views layer and lower domain subsystems.
    """
    @staticmethod
    def book_ticket(user_id, showtime_id, seat_ids, discount_code=None, method="credit_card", phone="", notes="", redeemed_points=0):
        from .services import BookingService
        return BookingService.make_booking(
            user_id=user_id,
            showtime_id=showtime_id,
            seat_ids=seat_ids,
            discount_code=discount_code,
            method=method,
            phone=phone,
            notes=notes,
            redeemed_points=redeemed_points
        )


# ==========================================
# 12. COMMAND PATTERN - Booking/Cancellation Commands
# ==========================================
class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class BookCommand(Command):
    """
    COMMAND PATTERN: BookCommand.
    
    WHY: Represents a request to book a ticket as an object. This allows us to track, queue,
    audit, and log booking invocations.
    """
    def __init__(self, facade, user_id, showtime_id, seat_ids, discount_code=None, method="credit_card", phone="", notes="", redeemed_points=0):
        self.facade = facade
        self.user_id = user_id
        self.showtime_id = showtime_id
        self.seat_ids = seat_ids
        self.discount_code = discount_code
        self.method = method
        self.phone = phone
        self.notes = notes
        self.redeemed_points = redeemed_points
        self.booking = None

    def execute(self):
        self.booking = self.facade.book_ticket(
            user_id=self.user_id,
            showtime_id=self.showtime_id,
            seat_ids=self.seat_ids,
            discount_code=self.discount_code,
            method=self.method,
            phone=self.phone,
            notes=self.notes,
            redeemed_points=self.redeemed_points
        )
        return self.booking

class CancelCommand(Command):
    """
    COMMAND PATTERN: CancelCommand.
    
    WHY: Represents the request to cancel an existing booking as a standalone Command object.
    Allows for auditing, rollback, and scheduling of cancellation sequences.
    """
    def __init__(self, user_id, booking_id):
        self.user_id = user_id
        self.booking_id = booking_id
        self.cancelled = False

    def execute(self):
        from .services import BookingService
        self.cancelled = BookingService.cancel_booking(self.booking_id, self.user_id)
        return self.cancelled


# ==========================================
# 13. PROTOTYPE PATTERN - Administrative Entity Cloning
# ==========================================
class Prototype(ABC):
    @abstractmethod
    def clone(self):
        pass

class MoviePrototype(Prototype):
    """
    PROTOTYPE PATTERN: MoviePrototype.
    
    WHY: Admins frequently schedule multiple days for the same movie structure or add seasonal variations.
    Cloning an existing movie saves manual entry and guarantees data consistency.
    """
    def __init__(self, movie):
        self.movie = movie

    def clone(self, title=None, release_date=None, end_date=None):
        from .models import Movie
        new_movie = Movie.objects.create(
            title=title or f"{self.movie.title} (Clone)",
            description=self.movie.description,
            genre=self.movie.genre,
            duration=self.movie.duration,
            rating=self.movie.rating,
            formats=self.movie.formats,
            poster_url=self.movie.poster_url,
            trailer_url=self.movie.trailer_url,
            release_date=release_date or self.movie.release_date,
            end_date=end_date or self.movie.end_date,
            status='draft',
            age_rating=self.movie.age_rating,
            director=self.movie.director,
            cast=self.movie.cast
        )
        return new_movie

class ShowtimePrototype(Prototype):
    """
    PROTOTYPE PATTERN: ShowtimePrototype.
    
    WHY: Scheduling screens requires copying showtime configurations (language, subtitle, price multiplier)
    across multiple days.
    """
    def __init__(self, showtime):
        self.showtime = showtime

    def clone(self, start_time, end_time, screen=None):
        from .models import Showtime
        new_showtime = Showtime.objects.create(
            movie=self.showtime.movie,
            screen=screen or self.showtime.screen,
            start_time=start_time,
            end_time=end_time,
            language=self.showtime.language,
            subtitle=self.showtime.subtitle,
            price_multiplier=self.showtime.price_multiplier
        )
        return new_showtime

