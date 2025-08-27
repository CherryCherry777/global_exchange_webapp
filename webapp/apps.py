from django.apps import AppConfig

class WebappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webapp'

    def ready(self):
        import webapp.signals
        from django.db.models.signals import post_migrate
        post_migrate.connect(webapp.signals.clear_sessions, sender=self)
