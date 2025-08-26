from django.apps import AppConfig
import logging

log = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        log.warning("CoreConfig.ready() called")
        from . import signals  # noqa
