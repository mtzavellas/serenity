import logging
from datetime import timedelta
from typing import Set

from phemex import PhemexConnection, AuthCredentials
from phemex.order import Contract, Side, Trigger, Condition, ConditionalOrder
from tau.core import Event, Network
from tau.math import ExponentialMovingAverage
from tau.signal import Filter, BufferWithTime, Map

from serenity.algo import InvestmentStrategy, StrategyContext
from serenity.model.exchange import ExchangeInstrument
from serenity.signal.marketdata import ComputeOHLC


class Alpha1Trader(Event):
    logger = logging.getLogger(__name__)

    def __init__(self, network: Network, strategy):
        self.network = network
        self.strategy = strategy
        self.order_placer = strategy.trading_conn.get_order_placer()
        self.order_factory = self.order_placer.get_order_factory()

        self.open_orders = list()

    def stop(self):
        for order_hnd in self.open_orders:
            order_hnd.cancel()

    # noinspection DuplicatedCode
    def on_activate(self) -> bool:
        if self.network.has_activated(self.strategy.big_prints):
            big_print = self.strategy.big_prints.get_value()
            self.strategy.logger.info(f'Big print in spot market: {big_print}')

            # 5 minute bin volumes dropping below EMWA
            emwa = self.strategy.emwa.get_value()
            volume = self.strategy.volume.get_value()
            if emwa < volume:
                contract = Contract('BTCUSD')
                if big_print.get_side().get_type_code() == 'Buy':
                    # enter short position with a stop-loss and a take-profit at +/- 5% last trade px
                    self.logger.info(f'Going short, buy print of {big_print} BTC, EMWA={emwa}, volume={volume}')

                    # create a market order for BTCUSD, "cross" (no leverage), sell / short
                    primary_order = self.order_factory.create_market_order(Side.SELL, self.strategy.trade_qty, contract)

                    last_trade_px = self.strategy.futures_trades
                    stop_loss_px = last_trade_px.get_price() * 1.05
                    take_profit_px = last_trade_px.get_price() * 0.95

                    # create stop loss order
                    stop_loss = self.order_factory.create_market_order(Side.Buy, self.strategy.trade_qty, contract)
                    stop_loss_cond = ConditionalOrder(Condition.IF_TOUCHED, Trigger.LAST_PRICE, stop_loss_px, stop_loss)

                    # create take profit order
                    take_profit = self.order_factory.create_market_order(Side.Buy, self.strategy.trade_qty, contract)
                    take_profit_cond = ConditionalOrder(Condition.IF_TOUCHED, Trigger.LAST_PRICE, take_profit_px,
                                                        take_profit)

                    # place the orders
                    self.open_orders.append(self.order_placer.submit(primary_order))
                    self.open_orders.append(self.order_placer.submit(stop_loss_cond))
                    self.open_orders.append(self.order_placer.submit(take_profit_cond))
                else:
                    # enter long position with a stop-loss and a take-profit at +/- 5% last trade px
                    self.logger.info(f'Going long, sell print of {big_print} BTC, EMWA={emwa}, volume={volume}')

                    # create a market order for BTCUSD, "cross" (no leverage), buy / long
                    primary_order = self.order_factory.create_market_order(Side.BUY, self.strategy.trade_qty, contract)

                    last_trade_px = self.strategy.futures_trades
                    stop_loss_px = last_trade_px.get_price() * 0.95
                    take_profit_px = last_trade_px.get_price() * 1.05

                    # create stop loss order
                    stop_loss = self.order_factory.create_market_order(Side.Sell, self.strategy.trade_qty, contract)
                    stop_loss_cond = ConditionalOrder(Condition.IF_TOUCHED, Trigger.LAST_PRICE, stop_loss_px, stop_loss)

                    # create take profit order
                    take_profit = self.order_factory.create_market_order(Side.Sell, self.strategy.trade_qty, contract)
                    take_profit_cond = ConditionalOrder(Condition.IF_TOUCHED, Trigger.LAST_PRICE, take_profit_px,
                                                        take_profit)

                    # place the orders
                    self.open_orders.append(self.order_placer.submit(primary_order))
                    self.open_orders.append(self.order_placer.submit(stop_loss_cond))
                    self.open_orders.append(self.order_placer.submit(take_profit_cond))

            return True
        else:
            return False


class Alpha1(InvestmentStrategy):
    """
    An example investment strategy. This signal has not been backtested & calibrated and you should not
    trade it; this is for example purposes only. Likely this is TOTAL NONSENSE. Furthermore, the fast
    position keeper has not yet been implemented, so it's relying on stop-loss / take-profit to clean
    up positions. There are no limits either, so likely this is also DANGEROUS NONSENSE.
    """

    logger = logging.getLogger(__name__)

    def __init__(self):
        self.ctx = None
        self.trade_qty = None
        self.trading_conn = None
        self.spot_feed = None
        self.futures_feed = None
        self.big_prints = None
        self.futures_trades = None
        self.ohlc_5min = None
        self.volume = None
        self.emwa = None
        self.trader = None

    def get_instrument_universe(self) -> Set[ExchangeInstrument]:
        btc_usd_future = self.ctx.get_instrument_cache().get_exchange_instrument('Phemex', 'BTCUSD')
        return {btc_usd_future}

    def init(self, ctx: StrategyContext):
        self.ctx = ctx

        big_print_qty = float(ctx.getenv('BIG_PRINT_QTY'))
        self.trade_qty = float(ctx.getenv('CONTRACT_TRADE_QTY'))

        api_key = ctx.getenv('PHEMEX_API_KEY')
        api_secret = ctx.getenv('PHEMEX_API_SECRET')
        credentials = AuthCredentials(api_key, api_secret)

        exchange_instance = ctx.getenv('PHEMEX_INSTANCE', 'prod')
        if exchange_instance == 'prod':
            self.trading_conn = PhemexConnection(credentials)
        elif exchange_instance == 'test':
            self.trading_conn = PhemexConnection(credentials, api_url='https://testnet-api.phemex.com')
        else:
            raise ValueError(f'Unknown PHEMEX_INSTANCE value: {exchange_instance}')

        self.logger.info(f'Connected to Phemex {exchange_instance} instance')

        self.spot_feed = ctx.fh_registry.get_feed(f'coinbase:{exchange_instance}:BTC-USD')
        self.futures_feed = ctx.fh_registry.get_feed(f'phemex:{exchange_instance}:BTCUSD')

        self.logger.info(f'Connected to spot & futures {exchange_instance} feeds')

        network = self.ctx.get_network()

        # scan the spot market for large trades
        self.big_prints = Filter(network, self.spot_feed.get_trades(), lambda x: x.get_qty() >= big_print_qty)

        # compute 5 minute bins for the futures market and extract the volume field
        self.futures_trades = self.futures_feed.get_trades()
        buffer_5min = BufferWithTime(network, self.futures_trades, timedelta(seconds=5))
        self.ohlc_5min = ComputeOHLC(network, buffer_5min)
        self.volume = Map(network, self.ohlc_5min, lambda x: x.volume)

        # track the exponentially weighted moving average of the futures volume
        self.emwa = ExponentialMovingAverage(network, self.volume)

    def start(self):
        super().start()

        self.trader = Alpha1Trader(self.ctx.get_network(), self)
        self.ctx.get_network().connect(self.big_prints, self.trader)
        self.ctx.get_network().connect(self.emwa, self.trader)

    def stop(self):
        super().stop()

        self.trader.stop()
        self.ctx.get_network().disconnect(self.big_prints, self.trader)
        self.ctx.get_network().disconnect(self.emwa, self.trader)
        self.trader = None
