# api/context_processors.py
import json
from django.db.models import Count
from django.utils.timezone import localtime
from .models import TestResult, StudentCluster


def sppr_dashboard_data(request):
    # Проверяем, что мы в админке (startswith надежнее, чем точное совпадение)
    if not request.path.startswith('/admin'):
        return {}

    try:
        # УБРАЛИ ФИЛЬТР total_points__gt=0. Теперь берем ВСЕ завершенные тесты.
        progress = TestResult.objects.filter(
            completed_at__isnull=False
        ).order_by('completed_at')[:30]

        sppr_labels = []
        sppr_data = []

        for i, item in enumerate(progress, 1):
            # Конвертируем время в локальное
            try:
                local_time = localtime(item.completed_at)
                time_str = local_time.strftime('%d.%m %H:%M')
            except Exception:
                time_str = "Неизвестно"

            sppr_labels.append(f"Поп. {i} ({time_str})")

            # РУЧНОЙ РАСЧЕТ ПРОЦЕНТОВ (Защита от деления на ноль)
            earned = item.earned_points or 0
            total = item.total_points or 0

            if total > 0:
                perf = (earned * 100.0) / total
            else:
                perf = 0.0  # Если максимум баллов 0, ставим 0% успеваемости

            sppr_data.append(round(perf, 2))

        # 2. Круговой график (без изменений)
        cluster_stats = StudentCluster.objects.values('cluster_label') \
            .annotate(student_count=Count('id')) \
            .order_by('cluster_label')

        cluster_labels = [item['cluster_label'] for item in cluster_stats]
        cluster_counts = [item['student_count'] for item in cluster_stats]

    except Exception as e:
        print(f"ОШИБКА КОНТЕКСТНОГО ПРОЦЕССОРА: {e}")
        sppr_labels, sppr_data = [], []
        cluster_labels, cluster_counts = [], []

    return {
        'sppr_labels': json.dumps(sppr_labels),
        'sppr_data': json.dumps(sppr_data),
        'cluster_labels': json.dumps(cluster_labels),
        'cluster_counts': json.dumps(cluster_counts),
    }