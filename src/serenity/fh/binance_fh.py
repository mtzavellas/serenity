import json

import binance.client
import fire
import websockets
from tau.core import MutableSignal, NetworkScheduler, Event
from tau.signal import Map, Filter

from serenity.db import InstrumentCache
from serenity.fh.feedhandler import FeedHandlerState, WebsocketFeedHandler, ws_fh_main, Feed
from serenity.model.exchange import ExchangeInstrument
from serenity.model.marketdata import Trade


class BinanceFeedHandler(WebsocketFeedHandler):
    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id: str = 'prod'):
        if instance_id == 'prod':
            self.ws_uri = 'wss://stream.binance.com:9443/stream'
            self.binance_client = binance.client.Client()
        else:
            raise ValueError(f'Unknown instance_id: {instance_id}')

        # ensure we've initialized PhemexConnection before loading instruments in super()
        super().__init__(scheduler, instrument_cache, instance_id)

        self.instrument_trades = {}
        self.instrument_quotes = {}

    @staticmethod
    def get_uri_scheme() -> str:
        return 'binance'

    def _load_instruments(self):
        self.logger.info("Downloading supported products")

        # noinspection PyProtectedMember
        exchange_info = self.binance_client.get_exchange_info()
        for product in exchange_info['symbols']:
            symbol = product['symbol']
            base_ccy = product['baseAsset']
            quote_ccy = product['quoteAsset']
            ccy_pair = self.instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
            instrument = ccy_pair.get_instrument()
            exch_instr = self.instrument_cache.get_or_create_exchange_instrument(symbol, instrument, "Binance")

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
            symbols.append(f'{symbol.lower()}@aggTrade')

            self.instrument_trades[symbol] = MutableSignal()
            self.instrument_quotes[symbol] = MutableSignal()

            # magic: inject the bare Signal into the graph so we can
            # fire events on it without any downstream connections
            # yet made
            network.graph.add_node(self.instrument_trades[symbol])
            network.graph.add_node(self.instrument_quotes[symbol])

        messages = MutableSignal()
        json_messages = Map(network, messages, lambda x: json.loads(x))
        trade_messages = Filter(network, json_messages, lambda x: 'data' in x)
        trades = Map(network, trade_messages, lambda x: self.__extract_trade(x))

        class TradeScheduler(Event):
            def __init__(self, fh: BinanceFeedHandler):
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
            ndx = 1
            n = 250
            symbols_chunked = [symbols[i:i + n] for i in range(0, len(symbols), n)]

            for symbols in symbols_chunked:
                self.logger.info(f'Sending subscription request for {len(symbols)} symbols: {symbols}')
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": symbols,
                    "id": ndx
                }
                await sock.send(json.dumps(subscribe_msg))
                ndx = ndx + 1

            self.scheduler.schedule_update(self.state, FeedHandlerState.LIVE)
            while True:
                self.scheduler.schedule_update(messages, await sock.recv())

    def __extract_trade(self, msg) -> Trade:
        sequence = msg['data']['E']
        trade_id = msg['data']['a']
        symbol = msg['data']['s']
        side = self.buy_code if msg['data']['m'] else self.sell_code
        qty = float(msg['data']['q'])
        price = float(msg['data']['p'])
        instrument = self.known_instrument_ids[symbol]
        return Trade(instrument, sequence, trade_id, side, qty, price)


def create_fh(scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id):
    return BinanceFeedHandler(scheduler, instrument_cache, instance_id)


def main(instance_id: str = 'prod', journal_path: str = '/behemoth/journals/'):
    ws_fh_main(create_fh, BinanceFeedHandler.get_uri_scheme(), instance_id, journal_path, 'BINANCE_TRADES')


if __name__ == '__main__':
    fire.Fire(main)
