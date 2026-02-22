"""
AI-based demand prediction module using simple statistical analysis.
This uses historical order data to predict future demand patterns.
"""
from datetime import date, timedelta
from collections import defaultdict
from django.db.models import Count, Sum, Avg


def predict_demand_for_slot(stall_id, break_slot, target_date):
    """
    Predict demand for a given stall, break slot, and date.
    Uses weighted moving average of historical data.
    Returns predicted order count and confidence score.
    """
    from apps.orders.models import Order

    # Get last 4 weeks of same day orders
    target_day = target_date.weekday()
    past_data = []

    for weeks_back in range(1, 5):
        past_date = target_date - timedelta(weeks=weeks_back)
        count = Order.objects.filter(
            stall_id=stall_id,
            break_slot=break_slot,
            pickup_date=past_date,
            status__in=['completed', 'ready', 'confirmed', 'preparing']
        ).count()
        past_data.append(count)

    if not any(past_data):
        return 0, 0.0

    # Weighted average (more recent = higher weight)
    weights = [4, 3, 2, 1]
    weighted_sum = sum(d * w for d, w in zip(past_data, weights))
    total_weight = sum(weights[:len(past_data)])
    predicted = round(weighted_sum / total_weight)

    # Confidence based on data consistency
    if len(past_data) >= 3:
        mean = sum(past_data) / len(past_data)
        if mean > 0:
            variance = sum((x - mean) ** 2 for x in past_data) / len(past_data)
            cv = (variance ** 0.5) / mean  # coefficient of variation
            confidence = max(0.0, min(1.0, 1 - cv))
        else:
            confidence = 0.5
    else:
        confidence = 0.3

    return predicted, round(confidence, 2)


def get_peak_hours_analysis(stall_id, days=30):
    """
    Analyze peak hours for a stall over the past N days.
    Returns dict with slot -> avg orders mapping.
    """
    from apps.orders.models import Order
    from django.utils import timezone

    since = timezone.now().date() - timedelta(days=days)
    slot_data = Order.objects.filter(
        stall_id=stall_id,
        pickup_date__gte=since,
        status__in=['completed', 'ready', 'confirmed', 'preparing', 'pending']
    ).values('break_slot').annotate(total=Count('id'))

    result = {item['break_slot']: item['total'] for item in slot_data}
    max_val = max(result.values()) if result else 1

    # Mark slots as peak if they exceed 70% of max
    peak_slots = {slot for slot, count in result.items() if count >= max_val * 0.7}
    return result, peak_slots


def get_slot_congestion_level(stall_id, break_slot, pickup_date):
    """
    Returns congestion level: low, medium, high
    Based on current confirmed orders vs capacity.
    """
    from apps.orders.models import Order

    MAX_CAPACITY = 50  # configurable
    current_count = Order.objects.filter(
        stall_id=stall_id,
        break_slot=break_slot,
        pickup_date=pickup_date,
        status__in=['pending', 'confirmed', 'preparing']
    ).count()

    ratio = current_count / MAX_CAPACITY
    if ratio < 0.4:
        return 'low', current_count
    elif ratio < 0.75:
        return 'medium', current_count
    else:
        return 'high', current_count


def get_recommended_slot(stall_id, pickup_date):
    """Recommend the least congested slot for a given date."""
    from apps.orders.models import BREAK_SLOT_CHOICES

    slot_loads = []
    for slot_value, slot_label in BREAK_SLOT_CHOICES:
        level, count = get_slot_congestion_level(stall_id, slot_value, pickup_date)
        slot_loads.append((slot_value, slot_label, level, count))

    # Sort by count ascending - recommend least busy
    slot_loads.sort(key=lambda x: x[3])
    return slot_loads
