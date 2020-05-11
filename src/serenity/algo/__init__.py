from abc import ABC, abstractmethod
from enum import Enum, auto

from tau.core import Signal, NetworkScheduler, Network

from serenity.db import InstrumentCache, TypeCodeCache
from serenity.fh.feedhandler import FeedHandlerRegistry


class StrategyState(Enum):
    INITIALIZING = auto()
    STOPPED = auto()
    LIVE = auto()
    CANCELLED = auto()


class StrategyContext:
    """
    Environment for a running strategy instance, provided by the engine.
    """

    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache,
                 fh_registry: FeedHandlerRegistry, env_vars: dict):
        self.scheduler = scheduler
        self.instrument_cache = instrument_cache
        self.fh_registry = fh_registry
        self.env_vars = env_vars

    def get_scheduler(self) -> NetworkScheduler:
        return self.scheduler

    def get_network(self) -> Network:
        return self.get_scheduler().get_network()

    def get_instrument_cache(self) -> InstrumentCache:
        return self.instrument_cache

    def get_typecode_cache(self) -> TypeCodeCache:
        return self.get_instrument_cache().get_type_code_cache()

    def get_feedhandler_registry(self) -> FeedHandlerRegistry:
        return self.fh_registry

    def getenv(self, key: str, default_value=None):
        if key in self.env_vars:
            return self.env_vars[key]
        else:
            return default_value


class Strategy(ABC):
    """
    An abstract trading strategy, offering basic lifecycle hooks so you can plug in
    your own strategies and run them in the engine.
    """
    def get_state(self) -> Signal:
        """
        Gets a stream of updates for this strategy's current state.
        """
        pass

    @abstractmethod
    def init(self, ctx: StrategyContext):
        """
        Callback made once when strategy is loaded into the engine.
        """
        pass

    def start(self):
        """
        Callback made whenever the strategy is started by a command from the engine.
        This call is only valid for states INITIALIZING and STOPPED.
        """
        pass

    def stop(self):
        """
        Callback made whenever the strategy is paused by a command from the engine.
        This call is only valid for the LIVE state.
        """
        pass

    def cancel(self):
        """
        Callback made whenever the strategy is cancelled by a command from the engine.
        This call is valid for all states except CANCELLED. Subsequent to a cancel the
        strategy needs to be re-created or the engine restarted in order to continue trading.
        """
        pass


class InvestmentStrategy(Strategy):
    @abstractmethod
    def get_instrument_universe(self) -> set:
        """
        Gets the universe of exchange-traded instruments that this strategy trades.
        """
        pass

