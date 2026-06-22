from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        import common.signals.groups_signals
        import common.signals.permission_signals
