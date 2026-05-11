from django.apps import AppConfig


class FinancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finances'
    
    def ready(self):
        """
        Importa os signals quando o app está pronto.
        """
        import finances.signals  # noqa