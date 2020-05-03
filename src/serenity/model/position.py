from datetime import date, datetime
from decimal import Decimal
from typing import List

from serenity.model.account import TradingAccount
from serenity.model.instrument import Instrument
from serenity.model.order import Fill


class Position:
    def __init__(self, position_id: int, instrument: Instrument, trading_account: TradingAccount, position_date: date,
                 quantity: Decimal, update_time: datetime):
        self.position_id = position_id

        self.instrument = instrument
        self.trading_account = trading_account

        self.position_date = position_date
        self.quantity = quantity
        self.update_time = update_time

        self.fills = list()

    def get_position_id(self) -> int:
        return self.position_id

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_trading_account(self) -> TradingAccount:
        return self.trading_account

    def get_position_date(self) -> date:
        return self.position_date

    def get_quantity(self) -> Decimal:
        return self.quantity

    def get_update_time(self) -> datetime:
        return self.update_time

    def get_fills(self) -> List[Fill]:
        return self.fills

    def set_fills(self, fills: List[Fill]):
        self.fills = fills
