from django.apps import AppConfig


class SfapConfig(AppConfig):
    name = "sfap"

    def ready(self):
        import common.signals.department_signals
