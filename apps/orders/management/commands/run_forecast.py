from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.stalls.models import FoodStall
from apps.orders.models import DemandForecast, BREAK_SLOT_CHOICES
from apps.orders.ai_demand import predict_demand_for_slot

class Command(BaseCommand):
    help = 'Generates demand forecasts for the upcoming day'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=1,
            help='Number of days ahead to forecast for'
        )

    def handle(self, *args, **options):
        days_ahead = options['days_ahead']
        target_date = timezone.now().date() + timezone.timedelta(days=days_ahead)
        stalls = FoodStall.objects.all()
        
        self.stdout.write(f'Generating forecasts for {target_date}...')
        
        created_count = 0
        updated_count = 0

        for stall in stalls:
            for slot_value, _ in BREAK_SLOT_CHOICES:
                predicted, confidence = predict_demand_for_slot(stall.id, slot_value, target_date)
                
                # Create or update the forecast
                obj, created = DemandForecast.objects.update_or_create(
                    stall=stall,
                    break_slot=slot_value,
                    forecast_date=target_date,
                    defaults={
                        'day_of_week': target_date.weekday(),
                        'predicted_quantity': predicted,
                        'confidence_score': confidence
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully generated forecasts: {created_count} created, {updated_count} updated.'))
