import json

import coinbasepro
import fire
import websockets
from tau.core import MutableSignal, NetworkScheduler, Event
from tau.signal import Map, Filter

from serenity.db import InstrumentCache
from serenity.fh.feedhandler import FeedHandlerState, WebsocketFeedHandler, ws_fh_main, Feed
from serenity.model.exchange import ExchangeInstrument
from serenity.model.marketdata import Trade


class CoinbaseProFeedHandler(WebsocketFeedHandler):
    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id: str = 'prod'):
        if instance_id == 'prod':
            self.ws_uri = 'wss://ws-feed.pro.coinbase.com'
            self.cbp_client = coinbasepro.PublicClient()
        elif instance_id == 'test':
            self.ws_uri = 'wss://ws-feed-public.sandbox.pro.coinbase.com'
            self.cbp_client = coinbasepro.PublicClient(api_url='https://api-public.sandbox.pro.coinbase.com')
        else:
            raise ValueError(f'Unknown instance_id: {instance_id}')

        # ensure we've initialized PhemexConnection before loading instruments in super()
        super().__init__(scheduler, instrument_cache, instance_id)

        self.instrument_trades = {}
        self.instrument_quotes = {}

    @staticmethod
    def get_uri_scheme() -> str:
        return 'coinbasepro'

    def _load_instruments(self):
        self.logger.info("Downloading supported products")

        for product in self.cbp_client.get_products():
            symbol = product['id']
            base_ccy = product['base_currency']
            quote_ccy = product['quote_currency']
            currency_pair = self.instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
            instrument = currency_pair.get_instrument()
            exch_instr = self.instrument_cache.get_or_create_exchange_instrument(symbol, instrument, "CoinbasePro")

            self.logger.info(f'\t{symbol} - {base_ccy}/{quote_ccy} [ID #{instrument.get_instrument_id()}]')
            self.known_instrument_ids[symbol] = exch_instr
            self.instruments.append(exch_instr)

    def _create_feed(self, instrument: ExchangeInstrument):
        symbol = instrument.get_exchange_instrument_code()
        return Feed(instrument, self.instrument_trades[symbol], self.instrument_quotes[symbol])

    # noinspection DuplicatedCode
    async def _subscribe_trades_and_quotes(self):
        network = self.scheduler.get_network()

        symbols = []
        for instrument in self.get_instruments():
            symbol = instrument.get_exchange_instrument_code()
            symbols.append(f'{symbol}')

            self.instrument_trades[symbol] = MutableSignal()
            self.instrument_quotes[symbol] = MutableSignal()

            # magic: inject the bare Signal into the graph so we can
            # fire events on it without any downstream connections
            # yet made
            network.graph.add_node(self.instrument_trades[symbol])
            network.graph.add_node(self.instrument_quotes[symbol])

        subscribe_msg = {
            'type': 'subscribe',
            'product_ids': symbols,
            'channels': ['matches', 'heartbeat']
        }

        messages = MutableSignal()
        json_messages = Map(network, messages, lambda x: json.loads(x))
        match_messages = Filter(network, json_messages, lambda x: x.get('type', None) == 'match')
        trades = Map(network, match_messages, lambda x: self.__extract_trade(x))

        class TradeScheduler(Event):
            def __init__(self, fh: CoinbaseProFeedHandler):
                self.fh = fh

            def on_activate(self) -> bool:
                if trades.is_valid():
                    trade = trades.get_value()
                    trade_symbol = trade.get_instrument().get_exchange_instrument_code()
                    trade_signal = self.fh.instrument_trades[trade_symbol]
                    self.fh.scheduler.schedule_update(trade_signal, trade)
                    return True
                else:
                    return False

        network.connect(trades, TradeScheduler(self))

        async with websockets.connect(self.ws_uri) as sock:
            await sock.send(json.dumps(subscribe_msg))
            self.scheduler.schedule_update(self.state, FeedHandlerState.LIVE)
            while True:
                self.scheduler.schedule_update(messages, await sock.recv())

    def __extract_trade(self, msg) -> Trade:
        sequence = msg['sequence']
        trade_id = msg['trade_id']
        side = self.buy_code if msg['side'] == 'buy' else self.sell_code
        qty = float(msg['size'])
        price = float(msg['price'])

        symbol = msg['product_id']
        instrument = self.known_instrument_ids[symbol]
        return Trade(instrument, sequence, trade_id, side, qty, price)


def create_fh(scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id):
    return CoinbaseProFeedHandler(scheduler, instrument_cache, instance_id)


def main(instance_id: str = 'prod', journal_path: str = '/behemoth/journals/'):
    ws_fh_main(create_fh, CoinbaseProFeedHandler.get_uri_scheme(), instance_id, journal_path, 'COINBASE_PRO_TRADES')


if __name__ == '__main__':
    fire.Fire(main)
