import asyncio
import threading
from django.apps import AppConfig


def start_order_updates(**kwargs):
    from .price_updater import start_order_updater
    asyncio.run(start_order_updater())


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    '''Start Up Function'''
    def ready(self):
        from dashboard.price_updater import start_order_updater

        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_order_updater())

        # Start the async loop in a separate thread
        thread = threading.Thread(target=run_async_loop, daemon=True)
        thread.start()
