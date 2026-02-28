from django.contrib import admin

from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "amount", "status", "stripe_charge_id", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("booking__user__email", "stripe_charge_id")# Search by Booking User or Stripe ID

    # Make everything Read-Only. Admins can see payments, but never edit the money data (they cant change "FAILED" payment to "SUCCESS")
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        # By set to False, we hide the "Add" button. This forces payments to only happen through PaymentService, which actually talks to the real bank
        return False

    # Note: We don't use save_model here like other admin, because we blocked 'add' and 'change'.
    # Payments are only created by the PaymentService when the bank says "Yes".
