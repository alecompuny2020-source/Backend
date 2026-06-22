from django.apps import AppConfig


class HrmsConfig(AppConfig):
    name = "hrms"

    def ready(self):
        import common.signals.department_signals
