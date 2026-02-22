"""
Management command to seed demo data for the Smart Food Stall system.
Usage: python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.stalls.models import FoodStall, MenuItem
from apps.orders.models import Order, OrderItem
from datetime import date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for Smart Food Stall system'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding demo data...')

        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@school.edu', 'admin123')
            admin.first_name = 'Admin'
            admin.last_name = 'User'
            admin.role = 'admin'
            admin.save()
            self.stdout.write('✅ Admin user created (admin/admin123)')

        # Create stall owner
        if not User.objects.filter(username='stall_owner1').exists():
            owner1 = User.objects.create_user('stall_owner1', 'owner1@school.edu', 'pass1234')
            owner1.first_name = 'Rahul'
            owner1.last_name = 'Sharma'
            owner1.role = 'stall_owner'
            owner1.save()
        else:
            owner1 = User.objects.get(username='stall_owner1')

        # Create student users
        students = []
        for i in range(1, 6):
            username = f'student{i}'
            if not User.objects.filter(username=username).exists():
                s = User.objects.create_user(username, f'student{i}@school.edu', 'pass1234')
                s.first_name = ['Priya', 'Amit', 'Neha', 'Raj', 'Anjali'][i-1]
                s.last_name = 'Kumar'
                s.role = 'student'
                s.student_id = f'2024CS{100+i}'
                s.phone = f'98765432{i:02d}'
                s.save()
                students.append(s)
            else:
                students.append(User.objects.get(username=username))

        self.stdout.write(f'✅ Created {len(students)} student users')

        # Create food stalls
        stalls_data = [
            {
                'name': 'Tiffin Corner',
                'description': 'Home-style South Indian and North Indian meals, freshly prepared every day.',
                'location': 'Block A - Ground Floor',
                'items': [
                    ('Masala Dosa', 'meals', 45, True, 180, 10),
                    ('Idli Sambar (3 pcs)', 'meals', 35, True, 120, 8),
                    ('Chicken Biryani', 'meals', 90, False, 450, 20),
                    ('Veg Biryani', 'meals', 70, True, 380, 15),
                    ('Curd Rice', 'meals', 30, True, 200, 5),
                    ('Chapati (3 pcs)', 'meals', 25, True, 150, 10),
                    ('Filter Coffee', 'beverages', 15, True, 60, 3),
                    ('Buttermilk', 'beverages', 10, True, 40, 2),
                ]
            },
            {
                'name': 'Quick Bites',
                'description': 'Fast snacks, sandwiches, and beverages. Perfect for a quick break.',
                'location': 'Block B - Cafeteria',
                'items': [
                    ('Veg Sandwich', 'snacks', 40, True, 220, 7),
                    ('Egg Sandwich', 'snacks', 50, False, 280, 8),
                    ('Samosa (2 pcs)', 'snacks', 20, True, 150, 5),
                    ('Pav Bhaji', 'snacks', 55, True, 320, 12),
                    ('French Fries', 'snacks', 50, True, 250, 10),
                    ('Cold Coffee', 'beverages', 40, True, 200, 5),
                    ('Fresh Lime Soda', 'beverages', 25, True, 30, 3),
                    ('Combo: Sandwich + Cold Coffee', 'combos', 75, True, 420, 10),
                ]
            },
            {
                'name': 'Sweet Tooth',
                'description': 'Desserts, sweets, and snacks to satisfy your cravings.',
                'location': 'Block C - Near Library',
                'items': [
                    ('Gulab Jamun (2 pcs)', 'desserts', 25, True, 200, 5),
                    ('Jalebi (100g)', 'desserts', 20, True, 250, 5),
                    ('Ice Cream', 'desserts', 35, True, 180, 3),
                    ('Chocolate Brownie', 'desserts', 40, True, 280, 8),
                    ('Banana Shake', 'beverages', 45, True, 250, 5),
                    ('Mango Lassi', 'beverages', 40, True, 220, 4),
                ]
            }
        ]

        stalls = []
        for sd in stalls_data:
            stall, created = FoodStall.objects.get_or_create(
                name=sd['name'],
                defaults={
                    'description': sd['description'],
                    'location': sd['location'],
                    'owner': owner1,
                    'is_open': True
                }
            )
            stalls.append(stall)
            if created:
                for item_data in sd['items']:
                    name, cat, price, is_veg, cal, prep = item_data
                    MenuItem.objects.create(
                        stall=stall,
                        name=name,
                        category=cat,
                        price=price,
                        is_vegetarian=is_veg,
                        calories=cal,
                        prep_time_minutes=prep,
                        is_available=True,
                        description=f'Fresh {name.lower()} prepared daily.'
                    )

        self.stdout.write(f'✅ Created {len(stalls)} food stalls with menu items')

        # Create sample orders for the past 2 weeks
        slots = ['10:00', '12:00', '13:00', '15:00']
        statuses = ['completed', 'completed', 'completed', 'cancelled']
        order_count = 0

        for days_back in range(14, 0, -1):
            order_date = date.today() - timedelta(days=days_back)
            for stall in stalls:
                items = list(stall.menu_items.filter(is_available=True))
                if not items:
                    continue
                slot_counts = {'10:00': random.randint(5, 20), '12:00': random.randint(15, 45),
                               '13:00': random.randint(20, 40), '15:00': random.randint(5, 15)}
                for slot, count in slot_counts.items():
                    for _ in range(min(count, 10)):  # Cap at 10 sample orders per slot
                        student = random.choice(students)
                        selected_items = random.sample(items, min(random.randint(1, 3), len(items)))
                        order = Order.objects.create(
                            user=student,
                            stall=stall,
                            break_slot=slot,
                            pickup_date=order_date,
                            status=random.choice(statuses),
                            total_amount=0,
                            special_instructions=''
                        )
                        total = 0
                        for menu_item in selected_items:
                            qty = random.randint(1, 2)
                            OrderItem.objects.create(
                                order=order,
                                menu_item=menu_item,
                                quantity=qty,
                                price_at_order=menu_item.price
                            )
                            total += menu_item.price * qty
                        order.total_amount = total
                        order.save()
                        order_count += 1

        self.stdout.write(f'✅ Created {order_count} historical orders')

        # Today's pending orders
        today_orders = 0
        for stall in stalls:
            items = list(stall.menu_items.filter(is_available=True))
            for slot in slots:
                for i in range(random.randint(2, 8)):
                    student = random.choice(students)
                    selected_items = random.sample(items, min(random.randint(1, 2), len(items)))
                    order = Order.objects.create(
                        user=student, stall=stall, break_slot=slot,
                        pickup_date=date.today(),
                        status=random.choice(['pending', 'confirmed', 'preparing']),
                        total_amount=0
                    )
                    total = 0
                    for item in selected_items:
                        qty = random.randint(1, 2)
                        OrderItem.objects.create(order=order, menu_item=item, quantity=qty, price_at_order=item.price)
                        total += item.price * qty
                    order.total_amount = total
                    order.save()
                    today_orders += 1

        self.stdout.write(f'✅ Created {today_orders} orders for today')
        self.stdout.write(self.style.SUCCESS('\n🎉 Demo data seeded successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('  Students: student1 / pass1234 (through student5)')
        self.stdout.write('\nRun: python manage.py runserver')
