from .dispatcher import AlertDispatcher
from .telegram import TelegramNotificationChannel


def build_alert_dispatcher() -> AlertDispatcher:
    dispatcher = AlertDispatcher()
    dispatcher.register(TelegramNotificationChannel())
    return dispatcher


ALERT_DISPATCHER = build_alert_dispatcher()


def get_alert_dispatcher() -> AlertDispatcher:
    return ALERT_DISPATCHER
