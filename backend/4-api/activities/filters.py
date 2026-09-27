from django.db.models import QuerySet


def filter_by_date_range(
    queryset: QuerySet,
    desde: str | None,
    hasta: str | None,
) -> QuerySet:
    if desde:
        queryset = queryset.filter(start_datetime__gte=desde)
    if hasta:
        queryset = queryset.filter(start_datetime__lte=hasta)
    return queryset
