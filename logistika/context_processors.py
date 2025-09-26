from django.utils import timezone

from .models import Holiday


def upcoming_holidays(request):
    today = timezone.now().date()
    holidays = (
        Holiday.objects.filter(date__gte=today)
        .order_by("date")[:3]
    )
    return {"upcoming_holidays": holidays}
