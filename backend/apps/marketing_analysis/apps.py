from django.apps import AppConfig


class MarketingAnalysisConfig(AppConfig):
    name = "apps.marketing_analysis"
    verbose_name = "Маркетинговый анализ с маршрутом согласования"

    def ready(self):
        from . import services  # noqa: F401 — регистрирует обработчик ответов поставщиков на запросы КП
