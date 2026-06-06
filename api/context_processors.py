# api/context_processors.py
import json
from django.db.models import Avg, F
from django.db.models.functions import TruncDate
from api.models import TestResult, GroupMember

def sppr_dashboard_data(request):
    if not request.path.startswith('/admin'):
        return {}

    try:
        user = request.user
        # Фильтр: берем только тех студентов, которые состоят в группах этого преподавателя
        # Если юзер - админ, берем всех
        if getattr(user, 'role', '') == 'admin':
            queryset = TestResult.objects.filter(completed_at__isnull=False, total_points__gt=0)
        else:
            student_ids = GroupMember.objects.filter(
                group__group_teachers__teacher=user
            ).values_list('user_id', flat=True)
            queryset = TestResult.objects.filter(
                user_id__in=student_ids,
                completed_at__isnull=False,
                total_points__gt=0
            )

        # Агрегируем по дням
        daily_progress = queryset.annotate(date=TruncDate('completed_at')) \
            .values('date') \
            .annotate(avg_perf=Avg(F('earned_points') * 100.0 / F('total_points'))) \
            .order_by('date')

        sppr_labels = [str(item['date']) for item in daily_progress]
        sppr_data = [round(item['avg_perf'], 2) for item in daily_progress]

    except Exception:
        sppr_labels, sppr_data = [], []

    return {
        'sppr_labels': json.dumps(sppr_labels),
        'sppr_data': json.dumps(sppr_data),
    }