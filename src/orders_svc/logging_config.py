import logging.config

from asgi_correlation_id import CorrelationIdFilter


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": CorrelationIdFilter,
                    "uuid_length": 8,
                    "default_value": "-",
                }
            },
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s "
                        "%(levelname)s "
                        "[%(correlation_id)s] "
                        "%(name)s "
                        "%(message)s"
                    )
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "filters": ["correlation_id"],
                    "formatter": "default",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO",
            },
        }
    )