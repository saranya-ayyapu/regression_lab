from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Order, OrderItem
from .serializers import CustomerSerializer, OrderSerializer, OrderItemSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-id")
    serializer_class = CustomerSerializer

    @action(detail=True, methods=["get"])
    def orders(self, request, pk=None):
        customer = self.get_object()
        # Efficiently fetch orders with their items to avoid N+1
        orders = customer.orders.all().prefetch_related("items")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Default behavior: hide archived orders in list views.
        # (Note: detail views should still retrieve by id.)
        if self.action == "list":
            qs = qs.filter(is_archived=False)
        return qs

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return Response({"id": order.id, "status": order.status})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        order = self.get_object()
        order.is_archived = True
        order.save(update_fields=["is_archived", "updated_at"])
        return Response({"id": order.id, "is_archived": order.is_archived})

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all().order_by("-id")
    serializer_class = OrderItemSerializer

class OrdersSummaryView(APIView):
    """Intentionally slow summary endpoint.

    Returns top customers by total spent (paid orders only).
    This is written in a purposely inefficient way to give candidates a perf target.
    """

    def get(self, request):
        limit = int(request.query_params.get("limit", 50))
        from django.db.models import Sum, Count

        # Ultra-Optimized: 
        # 1. Aggregate directly on the Order table to find top customer IDs by spend.
        # This avoids expensive JOINs during the GROUP BY phase.
        top_aggregates = Order.objects.filter(
            status=Order.Status.PAID, 
            is_archived=False,
            customer__is_active=True
        ).values('customer_id').annotate(
            total_cents_spent=Sum('total_cents'),
            paid_order_count=Count('id')
        ).order_by("-total_cents_spent")[:limit]

        # 2. Fetch customer emails for those specific top IDs in one hit.
        customer_ids = [item['customer_id'] for item in top_aggregates]
        customers = {c.id: c.email for c in Customer.objects.filter(id__in=customer_ids)}

        rows = []
        for entry in top_aggregates:
            rows.append({
                "customer_id": entry['customer_id'],
                "email": customers.get(entry['customer_id'], "N/A"),
                "order_count": entry['paid_order_count'],
                "total_cents": entry['total_cents_spent'],
            })

        return Response({"limit": limit, "rows": rows})
