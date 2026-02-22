import json
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.db import transaction

from apps.stalls.models import FoodStall, MenuItem
from .models import Order, OrderItem, BREAK_SLOT_CHOICES, DemandForecast
from .forms import OrderForm
from .ai_demand import (
    get_slot_congestion_level, get_recommended_slot,
    get_peak_hours_analysis, predict_demand_for_slot
)


def home(request):
    stalls = FoodStall.objects.filter(is_open=True)[:6]
    today = timezone.now().date()

    # Today's stats
    today_orders = Order.objects.filter(pickup_date=today)

    # Slot congestion for today
    slot_info = []
    for slot_value, slot_label in BREAK_SLOT_CHOICES:
        count = today_orders.filter(break_slot=slot_value).count()
        if count < 20:
            level = 'low'
        elif count < 40:
            level = 'medium'
        else:
            level = 'high'
        slot_info.append({
            'value': slot_value,
            'label': slot_label,
            'count': count,
            'level': level,
        })

    context = {
        'stalls': stalls,
        'slot_info': slot_info,
        'today_total_orders': today_orders.count(),
    }
    return render(request, 'orders/home.html', context)


@login_required
def place_order(request, stall_id):
    stall = get_object_or_404(FoodStall, pk=stall_id, is_open=True)
    menu_items = stall.menu_items.filter(is_available=True)
    today = timezone.now().date()

    # Get slot recommendations
    slot_recommendations = get_recommended_slot(stall_id, today)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        cart_data = request.POST.get('cart_data', '[]')
        try:
            cart = json.loads(cart_data)
        except json.JSONDecodeError:
            cart = []

        if not cart:
            messages.error(request, 'Your cart is empty. Please add items.')
            return redirect('place_order', stall_id=stall_id)

        # if form.is_valid():
        #     # Check slot capacity
        #     slot = form.cleaned_data['break_slot']
        #     pickup_date = form.cleaned_data['pickup_date']
        #     level, current_count = get_slot_congestion_level(stall_id, slot, pickup_date)

        #     if level == 'high':
        #         messages.warning(request, f'The {slot} slot is very busy ({current_count} orders). Consider choosing another slot.')

        #     order = form.save(commit=False)
        #     order.user = request.user
        #     order.stall = stall
        #     order.status = 'pending'
        #     order.save()

        #     # Create order items
        #     from decimal import Decimal
        #     total = Decimal('0.00')

        #     for cart_item in cart:
        #         try:
        #             menu_item = MenuItem.objects.get(pk=cart_item['id'], stall=stall, is_available=True)
        #             qty = int(cart_item.get('quantity', 1))
        #             OrderItem.objects.create(
        #                 order=order,
        #                 menu_item=menu_item,
        #                 quantity=qty,
        #                 price_at_order=menu_item.price,
        #                 customization=cart_item.get('customization', '')
        #             )
        #             total += menu_item.price * qty
        #         except (MenuItem.DoesNotExist, KeyError, ValueError):
        #             pass

        #     order.total_amount = total
        #     order.save()

        #     messages.success(request, f'Order placed! Your token number is #{order.token_number}')
        #     return redirect('order_detail', pk=order.pk)

        from decimal import Decimal
        from django.db import transaction

        if form.is_valid():
            with transaction.atomic():

                slot = form.cleaned_data['break_slot']
                pickup_date = form.cleaned_data['pickup_date']

                level, current_count = get_slot_congestion_level(stall_id, slot, pickup_date)

                if level == 'high':
                    messages.warning(request, f'The {slot} slot is very busy ({current_count} orders).')

                order = form.save(commit=False)
                order.user = request.user
                order.stall = stall
                order.status = 'pending'
                order.save()

                total = Decimal('0.00')

                for cart_item in cart:
                    try:
                        menu_item = MenuItem.objects.get(
                            pk=cart_item['id'],
                            stall=stall,
                            is_available=True
                        )

                        qty = int(cart_item.get('quantity', 1))

                        OrderItem.objects.create(
                            order=order,
                            menu_item=menu_item,
                            quantity=qty,
                            price_at_order=menu_item.price,
                            customization=cart_item.get('customization', '')
                        )

                        total += menu_item.price * qty

                    except (MenuItem.DoesNotExist, KeyError, ValueError):
                        continue

                if total == 0:
                    order.delete()
                    messages.error(request, "Invalid cart items.")
                    return redirect('place_order', stall_id=stall_id)

                order.total_amount = total
                order.save()

                messages.success(request, f'Order placed! Your token number is #{order.token_number}')
                return redirect('order_detail', pk=order.pk)        
    else:
        form = OrderForm()

    context = {
        'stall': stall,
        'menu_items': menu_items,
        'form': form,
        'slot_recommendations': slot_recommendations,
        'break_slots': BREAK_SLOT_CHOICES,
    }
    return render(request, 'orders/place_order.html', context)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed']

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'statuses': statuses,
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).select_related('stall').prefetch_related('order_items__menu_item')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'orders/my_orders.html', {
        'orders': orders,
        'status_filter': status_filter,
    })


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status in ('pending', 'confirmed'):
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Order cancelled successfully.')
    else:
        messages.error(request, 'This order cannot be cancelled.')
    return redirect('my_orders')


# ---- Admin/Stall Owner Views ----

@login_required
def admin_dashboard(request):
    if not request.user.is_staff and not request.user.is_stall_owner:
        messages.error(request, 'Access denied.')
        return redirect('home')

    today = timezone.now().date()
    stalls = FoodStall.objects.all()
    if request.user.is_stall_owner:
        stalls = stalls.filter(owner=request.user)

    # Today's orders
    today_orders = Order.objects.filter(pickup_date=today)
    if request.user.is_stall_owner:
        today_orders = today_orders.filter(stall__owner=request.user)

    # Slot-wise breakdown
    slot_breakdown = []
    for slot_value, slot_label in BREAK_SLOT_CHOICES:
        slot_orders = today_orders.filter(break_slot=slot_value)
        slot_breakdown.append({
            'slot': slot_label,
            'value': slot_value,
            'count': slot_orders.count(),
            'revenue': slot_orders.aggregate(r=Sum('total_amount'))['r'] or 0,
            'pending': slot_orders.filter(status='pending').count(),
            'preparing': slot_orders.filter(status='preparing').count(),
            'ready': slot_orders.filter(status='ready').count(),
            'completed': slot_orders.filter(status='completed').count(),
        })

    # Demand predictions for tomorrow
    tomorrow = today + timezone.timedelta(days=1)
    predictions = []
    for stall in stalls:
        for slot_value, slot_label in BREAK_SLOT_CHOICES:
            predicted, confidence = predict_demand_for_slot(stall.id, slot_value, tomorrow)
            predictions.append({
                'stall': stall.name,
                'slot': slot_label,
                'predicted': predicted,
                'confidence': round(confidence * 100),
            })

    # Recent orders
    recent_orders = today_orders.order_by('-created_at')[:20]

    context = {
        'today': today,
        'tomorrow': tomorrow,
        'stalls': stalls,
        'today_orders_count': today_orders.count(),
        'today_revenue': today_orders.aggregate(r=Sum('total_amount'))['r'] or 0,
        'slot_breakdown': slot_breakdown,
        'predictions': predictions,
        'recent_orders': recent_orders,
        'pending_count': today_orders.filter(status='pending').count(),
    }
    return render(request, 'orders/admin_dashboard.html', context)


@login_required
@require_POST
def update_order_status(request, pk):
    if not request.user.is_staff and not request.user.is_stall_owner:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    valid_statuses = [s[0] for s in Order._meta.get_field('status').choices]

    if new_status in valid_statuses:
        order.status = new_status
        order.save()
        return JsonResponse({'success': True, 'status': new_status, 'status_display': order.get_status_display()})
    return JsonResponse({'error': 'Invalid status'}, status=400)


def slot_demand_api(request):
    """Real-time slot demand data API"""
    stall_id = request.GET.get('stall_id')
    pickup_date_str = request.GET.get('date', date.today().isoformat())

    try:
        pickup_date = date.fromisoformat(pickup_date_str)
    except ValueError:
        pickup_date = date.today()

    result = []
    for slot_value, slot_label in BREAK_SLOT_CHOICES:
        level, count = get_slot_congestion_level(stall_id, slot_value, pickup_date) if stall_id else ('low', 0)
        result.append({
            'slot': slot_value,
            'label': slot_label,
            'count': count,
            'level': level,
        })

    return JsonResponse({'slots': result, 'date': pickup_date_str})


def order_status_api(request, pk):
    """Real-time order status check"""
    try:
        order = Order.objects.get(pk=pk, user=request.user)
        return JsonResponse({
            'status': order.status,
            'status_display': order.get_status_display(),
            'token': order.token_number,
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    print("RAW POST:", request.POST)
    print("CART DATA:", request.POST.get("cart_data"))