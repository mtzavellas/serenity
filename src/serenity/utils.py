import logging

from tau.core import Signal, NetworkScheduler, MutableSignal, Event


def init_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_logger = logging.StreamHandler()
    console_logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_logger.setFormatter(formatter)
    logger.addHandler(console_logger)


def custom_asyncio_error_handler(loop, context):
    # first, handle with default handler
    loop.default_exception_handler(context)

    # force shutdown
    loop.stop()

