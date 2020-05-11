import asyncio
import importlib
import logging
import os
import sys

import fire
import yaml
from tau.core import NetworkScheduler

from serenity.algo import StrategyContext
from serenity.db import InstrumentCache, connect_serenity_db, TypeCodeCache
from serenity.fh.binance_fh import BinanceFeedHandler
from serenity.fh.coinbasepro_fh import CoinbaseProFeedHandler
from serenity.fh.feedhandler import FeedHandlerRegistry
from serenity.fh.phemex_fh import PhemexFeedHandler
from serenity.utils import init_logging, custom_asyncio_error_handler


class Environment:
    def __init__(self, config_yaml):
        self.values = {}
        for entry in config_yaml:
            key = entry['key']
            value = None
            if 'value' in entry:
                value = entry['value']
            elif 'value-source' in entry:
                source = entry['value-source']
                if source == 'SYSTEM_ENV':
                    value = os.getenv(key)
            else:
                raise ValueError(f'Unsupported value type in Environment entry: {entry}')

            self.values[key] = value

    def getenv(self, key: str, default_val: str = None) -> str:
        if key in self.values:
            return self.values[key]
        else:
            return default_val


class AlgoEngine:
    """"
    Algorithmic trading engine.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, config_path: str, strategy_dir: str):
        sys.path.append(strategy_dir)

        with open(config_path, 'r') as config_yaml:
            logger = logging.getLogger(__name__)

            logger.info('Serenity starting up')
            config = yaml.safe_load(config_yaml)
            api_version = config['api-version']
            if api_version != 'v1Beta':
                raise ValueError(f'Unsupported API version: {api_version}')

            self.engine_env = Environment(config['environment'])
            instance_id = self.engine_env.getenv('FEED_INSTANCE', 'prod')
            self.fh_registry = FeedHandlerRegistry()

            logger.info('Connecting to Serenity database')
            conn = connect_serenity_db()
            conn.autocommit = True
            cur = conn.cursor()

            scheduler = NetworkScheduler()
            instrument_cache = InstrumentCache(cur, TypeCodeCache(cur))
            if 'feedhandlers' in config:
                logger.info('Registering feedhandlers')
                for feedhandler in config['feedhandlers']:
                    fh_name = feedhandler['exchange']
                    if fh_name == 'Phemex':
                        self.fh_registry.register(PhemexFeedHandler(scheduler, instrument_cache, instance_id))
                    elif fh_name == 'Binance':
                        self.fh_registry.register(BinanceFeedHandler(scheduler, instrument_cache, instance_id))
                    elif fh_name == 'CoinbasePro':
                        self.fh_registry.register(CoinbaseProFeedHandler(scheduler, instrument_cache, instance_id))
                    else:
                        raise ValueError(f'Unsupported feedhandler type: {fh_name}')

            self.strategies = []
            for strategy in config['strategies']:
                strategy_name = strategy['name']
                self.logger.info(f'Loading strategy: {strategy_name}')
                module = strategy['module']
                strategy_class = strategy['strategy-class']
                env = Environment(strategy['environment'])

                module = importlib.import_module(module)
                klass = getattr(module, strategy_class)
                strategy_instance = klass()
                ctx = StrategyContext(scheduler, instrument_cache, self.fh_registry, env.values)
                self.strategies.append((strategy_instance, ctx))

    def start(self):
        for feedhandler in self.fh_registry.get_feedhandlers():
            asyncio.ensure_future(feedhandler.start())

        def start_strategies():
            for (strategy, ctx) in self.strategies:
                strategy.init(ctx)
                strategy.start()

        asyncio.get_event_loop().call_later(5, start_strategies)
        self.logger.info('<READY FOR TRADING>')

        # crash out on any exception
        asyncio.get_event_loop().set_exception_handler(custom_asyncio_error_handler)

        # go!
        asyncio.get_event_loop().run_forever()


def main(config_path: str, strategy_dir='.'):
    init_logging()
    engine = AlgoEngine(config_path, strategy_dir)
    engine.start()


if __name__ == '__main__':
    fire.Fire(main)
