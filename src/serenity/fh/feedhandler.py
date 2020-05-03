import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import List

from tau.core import Signal, MutableSignal, NetworkScheduler, Event
from tau.event import Do

from serenity.db import TypeCodeCache, InstrumentCache, connect_serenity_db
from serenity.model.exchange import ExchangeInstrument
from serenity.model.order import Side
from serenity.tickstore.journal import Journal
from serenity.utils import init_logging, custom_asyncio_error_handler


class FeedHandlerState(Enum):
    """
    Supported lifecycle states for a FeedHandler. FeedHandlers always start in INITIALIZING state.
    """

    INITIALIZING = auto()
    STARTING = auto()
    LIVE = auto()
    STOPPED = auto()


class Feed:
    """
    A marketdata feed with ability to subscribe to trades, quotes, etc..
    """

    def __init__(self, instrument: ExchangeInstrument, trades: Signal, quotes: Signal):
        self.instrument = instrument
        self.trades = trades
        self.quotes = quotes

    def get_instrument(self) -> ExchangeInstrument:
        """
        Gets the trading instrument for which we are feeding data.
        """
        return self.instrument

    def get_trades(self) -> Signal:
        """
        Gets all trade prints for this instrument on the connected exchange.
        """
        return self.trades

    def get_quotes(self) -> Signal:
        """
        Gets the top-of-book quote for this instrument on the connected exchange.
        """
        return self.quotes


class FeedHandler(ABC):
    """
    A connector for exchange marketdata.
    """

    @staticmethod
    def get_uri_scheme() -> str:
        """
        Gets the short string name like 'phemex' or 'kraken' for this feedhandler.
        """
        pass

    @abstractmethod
    def get_instance_id(self) -> str:
        """
        Gets the specific instance connected to, e.g. 'prod' or 'test'
        """
        pass

    @abstractmethod
    def get_instruments(self) -> List[ExchangeInstrument]:
        """
        Gets the instruments supported by this feedhandler.
        """
        pass

    @abstractmethod
    def get_state(self) -> Signal:
        """
        Gets a stream of FeedHandlerState enums that updates as the FeedHandler transitions between states.
        """
        pass

    @abstractmethod
    def get_feed(self, uri: str) -> Feed:
        """
        Acquires a feed for the given URI of the form scheme:instance:instrument_id, e.g.
        phemex:prod:BTCUSD or coinbase:test:BTC-USD. Raises an exception if the scheme:instance
        portion does not match this FeedHandler.
        """
        pass

    @abstractmethod
    async def start(self):
        """
        Starts the subscription to the exchange
        """
        pass


class WebsocketFeedHandler(FeedHandler):
    logger = logging.getLogger(__name__)

    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache,
                 instance_id: str):
        self.scheduler = scheduler
        self.instrument_cache = instrument_cache
        self.type_code_cache = instrument_cache.get_type_code_cache()
        self.instance_id = instance_id

        self.buy_code = self.type_code_cache.get_by_code(Side, 'Buy')
        self.sell_code = self.type_code_cache.get_by_code(Side, 'Sell')

        self.instruments = []
        self.known_instrument_ids = {}
        self.price_scaling = {}
        self._load_instruments()

        self.state = MutableSignal(FeedHandlerState.INITIALIZING)
        self.scheduler.get_network().graph.add_node(self.state)

    def get_instance_id(self) -> str:
        return self.instance_id

    def get_instruments(self) -> List[ExchangeInstrument]:
        return self.instruments

    def get_state(self) -> Signal:
        return self.state

    def get_feed(self, uri: str) -> Feed:
        (scheme, instance_id, instrument_id) = uri.split(':')
        if scheme != self.get_uri_scheme():
            raise ValueError(f'Unsupported URI scheme: {scheme}')
        if instance_id != self.get_instance_id():
            raise ValueError(f'Unsupported instance ID: {instance_id}')
        if instrument_id not in self.known_instrument_ids:
            raise ValueError(f'Unknown exchange Instrument: {instrument_id}')
        self.logger.info(f'Acquiring Feed for {uri}')

        return self._create_feed(self.known_instrument_ids[instrument_id])

    async def start(self):
        self.scheduler.schedule_update(self.state, FeedHandlerState.STARTING)
        await self._subscribe_trades_and_quotes()

    @abstractmethod
    def _create_feed(self, instrument: ExchangeInstrument):
        pass

    @abstractmethod
    def _load_instruments(self):
        pass

    @abstractmethod
    async def _subscribe_trades_and_quotes(self):
        pass


class FeedHandlerRegistry:
    """
    A central registry of all known FeedHandlers.
    """

    logger = logging.getLogger(__name__)

    def __init__(self):
        self.fh_registry = {}

    def get_feed(self, uri: str) -> Feed:
        """
        Acquires a Feed for a FeedHandler based on a URI of the form scheme:instrument:instrument_id,
        e.g. phemex:prod:BTCUSD or coinbase:test:BTC-USD. Raises an exception if there is no
        registered handler for the given URI.
        """
        (scheme, instance, instrument_id) = uri.split(':')
        fh = self.fh_registry[f'{scheme}:{instance}']
        if not fh:
            raise ValueError(f'Unknown FeedHandler URI: {uri}')
        return fh.get_feed(uri)

    def register(self, feedhandler: FeedHandler):
        """
        Registers a FeedHandler so its feeds can be acquired centrally with get_feed().
        """
        fh_key = FeedHandlerRegistry._get_fh_key(feedhandler)
        self.fh_registry[fh_key] = feedhandler
        self.logger.info(f'registered FeedHandler: {fh_key}')

    @staticmethod
    def _get_fh_key(feedhandler: FeedHandler) -> str:
        return f'{feedhandler.get_uri_scheme()}:{feedhandler.get_instance_id()}'


def ws_fh_main(create_fh, uri_scheme: str, instance_id: str, journal_path: str, db: str):
    init_logging()
    logger = logging.getLogger(__name__)

    conn = connect_serenity_db()
    conn.autocommit = True
    cur = conn.cursor()

    instr_cache = InstrumentCache(cur, TypeCodeCache(cur))

    scheduler = NetworkScheduler()
    registry = FeedHandlerRegistry()
    fh = create_fh(scheduler, instr_cache, instance_id)
    registry.register(fh)

    for instrument in fh.get_instruments():
        symbol = instrument.get_exchange_instrument_code()

        # subscribe to FeedState in advance so we know when the Feed is ready to subscribe trades
        class SubscribeTrades(Event):
            def __init__(self, trade_symbol):
                self.trade_symbol = trade_symbol
                self.appender = None

            def on_activate(self) -> bool:
                if fh.get_state().get_value() == FeedHandlerState.LIVE:
                    feed = registry.get_feed(f'{uri_scheme}:{instance_id}:{self.trade_symbol}')
                    instrument_code = feed.get_instrument().get_exchange_instrument_code()
                    journal = Journal(Path(f'{journal_path}/{db}/{instrument_code}'))
                    self.appender = journal.create_appender()

                    trades = feed.get_trades()
                    Do(scheduler.get_network(), trades, lambda: self.on_trade_print(trades.get_value()))
                return False

            def on_trade_print(self, trade):
                logger.info(trade)

                self.appender.write_double(datetime.utcnow().timestamp())
                self.appender.write_long(trade.get_trade_id())
                self.appender.write_long(trade.get_trade_id())
                self.appender.write_string(trade.get_instrument().get_exchange_instrument_code())
                self.appender.write_short(1 if trade.get_side().get_type_code() == 'Buy' else 0)
                self.appender.write_double(trade.get_qty())
                self.appender.write_double(trade.get_price())

        scheduler.get_network().connect(fh.get_state(), SubscribeTrades(symbol))

    # async start the feedhandler
    asyncio.ensure_future(fh.start())

    # crash out on any exception
    asyncio.get_event_loop().set_exception_handler(custom_asyncio_error_handler)

    # go!
    asyncio.get_event_loop().run_forever()
