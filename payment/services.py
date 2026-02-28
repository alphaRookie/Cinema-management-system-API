from .models import Payment
from booking.models import Booking
from rest_framework.exceptions import ValidationError

import stripe

class PaymentService:
    @staticmethod
    def process_payment(booking: Booking, payment_token: str): # dont need None, as we dont use PATCH
        try:
            #1. send the request and CATCH the answer in a variable called 'intent' (if we dont save to var otherwise dissapears)
            #stripe.PaymentIntent.create(...) is the machine talking to the bank. The "intent variable" is the digital receipt the bank sends back to you.
            intent = stripe.PaymentIntent.create(
                amount = int(booking.final_price * 100), #If your booking is $10.50, you must send 1050. If you send 10.50, Stripe will think you want to charge 10 cents(avoid rounding error)
                currency = "usd",
                payment_method = payment_token, #This is the ID of the "card" the user wants to use
                confirm = True, #This tells Stripe: "Don't just check the card, take the money now."
                #`enabled: True` auto decide which payment methods (Visa, Mastercard, etc)
                automatic_payment_methods = {"enabled":True, "allow_redirects":"never"} # RN need immediate "Success" or "Fail" result
            )
            
            #2. if success, save the history
            payment_record = Payment.objects.create(
                booking = booking,
                stripe_charge_id = intent.id, #use that 'intent' variable by access its ID to fill DB
                amount = booking.final_price,
                status = "SUCCESS"
            )

            # 3. "Since the money is paid, now we move the temp data in Seatlock to Ticket(permanent) via BookingService
            from booking.services import BookingService
            BookingService.confirm_booking(booking=booking)

            return payment_record #returning success history
    

        except stripe.StripeError as e:
            # Create a FAILED history record so you know they tried
            Payment.objects.create(
                booking = booking,
                amount = booking.final_price,
                status = "FAILED",
                # stripe_charge_id is skipped because it doesn't exist
            )
            raise ValidationError(f"Payment failed: {str(e)}")


# Remove "allow_redirect" part later for frontend use

