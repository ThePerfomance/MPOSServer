# api/context_processors.py
import json
from django.db.models import Count, Avg, F
from django.utils.timezone import localtime
from api.models import TestResult, StudentCluster


def sppr_dashboard_data(request):
    if not request.path.startswith('/admin'):
        return {}

    try:
        # Хронологическая выборка последних 30 попыток (без схлопывания по дням)
        progress = TestResult.objects.all().order_by('completed_at')[:30]

        sppr_labels = []
        sppr_data = []

        for i, item in enumerate(progress, 1):
            if item.completed_at:
                local_time = localtime(item.completed_at)
                time_str = local_time.strftime('%d.%m %H:%M')
                sppr_labels.append(f"Поп. {i} ({time_str})")
            else:
                sppr_labels.append(f"Поп. {i}")

            earned = item.earned_points or 0
            total = item.total_points or 0
            perf = (earned * 100.0) / total if total > 0 else 0.0
            sppr_data.append(round(float(perf), 2))

        # Агрегация данных из таблицы кластеризации K-Means
        cluster_stats = StudentCluster.objects.values('cluster_label') \
            .annotate(student_count=Count('id')) \
            .order_by('cluster_label')

        cluster_labels = [str(item['cluster_label']) for item in cluster_stats]
        cluster_counts = [int(item['student_count']) for item in cluster_stats]

    except Exception as e:
        sppr_labels, sppr_data = [], []
        cluster_labels, cluster_counts = [], []

    return {
        'sppr_labels': json.dumps(sppr_labels),
        'sppr_data': json.dumps(sppr_data),
        'cluster_labels': json.dumps(cluster_labels),
        'cluster_counts': json.dumps(cluster_counts),
    }