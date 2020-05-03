from serenity.model.exchange import ExchangeInstrument
from serenity.model.order import Side


class Trade:
    def __init__(self, instrument: ExchangeInstrument, sequence_id: int, trade_id: int, side: Side,
                 qty: float, price: float):
        self.instrument = instrument
        self.sequence_id = sequence_id
        self.trade_id = trade_id
        self.side = side
        self.qty = qty
        self.price = price

    def get_instrument(self) -> ExchangeInstrument:
        return self.instrument

    def get_sequence_id(self) -> int:
        return self.sequence_id

    def get_trade_id(self) -> int:
        return self.trade_id

    def get_side(self) -> Side:
        return self.side

    def get_qty(self) -> float:
        return self.qty

    def get_price(self) -> float:
        return self.price

    def __str__(self):
        return f'{self.instrument} - {self.side.get_type_code()} {self.qty}@{self.price} (ID: {self.trade_id})'
