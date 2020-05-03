from tau.core import Network
from tau.signal import Function, BufferWithTime


class OHLC:
    """
    Value class for Open/High/Low/Close prices.
    """
    def __init__(self, open_px: float, high_px: float, low_px: float, close_px: float, volume: float):
        self.open_px = open_px
        self.high_px = high_px
        self.low_px = low_px
        self.close_px = close_px
        self.volume = volume


class ComputeOHLC(Function):
    def __init__(self, network: Network, trades: BufferWithTime):
        super().__init__(network, [trades])
        self.trades = trades

    def _call(self):
        if self.trades.is_valid():
            trade_list = self.trades.get_value()
            if len(trade_list) == 0:
                return

            open_px = trade_list[0]
            high_px = -float('inf')
            low_px = float('inf')
            close_px = trade_list[-1]
            qty = 0
            for trade in trade_list:
                qty += trade.get_qty()
                high_px = max(high_px, trade.get_price())
                low_px = min(low_px, trade.get_price())

            self._update(OHLC(open_px, high_px, low_px, close_px, qty))
