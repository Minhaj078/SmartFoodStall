from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import FoodStall, MenuItem, StallReview


def stall_list(request):
    stalls = FoodStall.objects.filter(is_open=True)
    category = request.GET.get('category')
    search = request.GET.get('search', '')
    if search:
        stalls = stalls.filter(name__icontains=search)
    return render(request, 'stalls/stall_list.html', {
        'stalls': stalls,
        'search': search,
    })


def stall_detail(request, pk):
    stall = get_object_or_404(FoodStall, pk=pk)
    menu_items = stall.menu_items.filter(is_available=True)
    category = request.GET.get('category')
    if category:
        menu_items = menu_items.filter(category=category)
    reviews = stall.reviews.all().order_by('-created_at')
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    return render(request, 'stalls/stall_detail.html', {
        'stall': stall,
        'menu_items': menu_items,
        'reviews': reviews,
        'user_review': user_review,
        'categories': MenuItem.CATEGORY_CHOICES,
        'selected_category': category,
    })


@login_required
def add_review(request, pk):
    stall = get_object_or_404(FoodStall, pk=pk)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        if rating:
            StallReview.objects.update_or_create(
                stall=stall,
                user=request.user,
                defaults={'rating': int(rating), 'comment': comment}
            )
            messages.success(request, 'Review submitted successfully!')
        return redirect('stall_detail', pk=pk)


def get_menu_item_api(request, pk):
    """API endpoint to get menu item details for cart"""
    item = get_object_or_404(MenuItem, pk=pk, is_available=True)
    return JsonResponse({
        'id': item.id,
        'name': item.name,
        'price': str(item.price),
        'stall_id': item.stall.id,
        'stall_name': item.stall.name,
        'prep_time': item.prep_time_minutes,
        'is_vegetarian': item.is_vegetarian,
    })
