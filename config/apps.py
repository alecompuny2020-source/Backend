from django.apps import AppConfig


class ConfigConfig(AppConfig):
    name = "config"

    def ready(self):
        import common.signals.config_signals
