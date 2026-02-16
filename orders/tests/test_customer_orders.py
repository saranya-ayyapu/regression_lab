from django.test import TestCase
from rest_framework.test import APIClient
from orders.models import Customer, Order, OrderItem

class CustomerOrdersTests(TestCase):
    def test_get_customer_orders(self):
        client = APIClient()
        c = Customer.objects.create(name="Alice", email="alice@example.com")
        o1 = Order.objects.create(customer=c, status=Order.Status.PAID)
        o2 = Order.objects.create(customer=c, status=Order.Status.DRAFT)
        OrderItem.objects.create(order=o1, sku="SKU1", quantity=2, unit_price_cents=100)
        
        res = client.get(f"/api/customers/{c.id}/orders/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        # Check that items are included
        self.assertEqual(len(res.data[0]['items']), 1)
        self.assertEqual(res.data[0]['items'][0]['sku'], "SKU1")
