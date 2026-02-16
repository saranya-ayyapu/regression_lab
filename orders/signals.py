"""Signals for orders app.

There is an intentional bug here for the take-home assignment.

Scenario:
  - A user cancels an order (POST /api/orders/<id>/cancel/)
  - Something unrelated breaks (customer endpoints start returning 404)

Your job as candidate is to find the root cause and fix it safely with tests.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order

@receiver(post_save, sender=Order)
def on_order_saved(sender, instance: Order, created, **kwargs):
    # Fixed regression: Cancelling an order should not delete the customer.
    pass
