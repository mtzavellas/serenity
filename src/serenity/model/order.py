from abc import ABC
from datetime import datetime
from decimal import Decimal
from typing import List

from serenity.model import TypeCode
from serenity.model.account import TradingAccount
from serenity.model.instrument import Instrument


class DestinationType(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class Destination(ABC):
    def __init__(self, destination_id: int, destination_type: DestinationType):
        self.destination_id = destination_id
        self.destination_type = destination_type

    def get_destination_id(self):
        return self.destination_id

    def get_destination_type(self):
        return self.destination_type


class OrderType(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class Side(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class TimeInForce(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class Order:
    pass


class Fill:
    def __init__(self, fill_id: int, trade_id: int, fill_price: Decimal, quantity: Decimal, create_time: datetime):
        self.fill_id = fill_id
        self.trade_id = trade_id
        self.fill_price = fill_price
        self.quantity = quantity
        self.create_time = create_time

        self.order = None

    def get_fill_id(self) -> int:
        return self.fill_id

    def get_trade_id(self) -> int:
        return self.trade_id

    def get_fill_price(self) -> Decimal:
        return self.fill_price

    def get_quantity(self) -> Decimal:
        return self.quantity

    def get_create_time(self) -> datetime:
        return self.create_time

    def get_order(self) -> Order:
        return self.order

    def set_order(self, order: Order):
        self.order = order


# noinspection PyRedeclaration
class Order:
    def __init__(self, order_id: int, order_type: OrderType, side: Side, instrument: Instrument,
                 trading_account: TradingAccount, destination: Destination, time_in_force: TimeInForce, price: Decimal,
                 quantity: Decimal, create_time: datetime):
        self.order_id = order_id

        self.order_type = order_type
        self.side = side
        self.instrument = instrument
        self.trading_account = trading_account
        self.destination = destination
        self.time_in_force = time_in_force

        self.price = price
        self.quantity = quantity
        self.create_time = create_time

        self.parent_order = None
        self.fills = list()

    def get_order_id(self) -> int:
        return self.order_id

    def get_order_type(self) -> OrderType:
        return self.order_type

    def get_side(self) -> Side:
        return self.side

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_trading_account(self) -> TradingAccount:
        return self.trading_account

    def get_destination(self) -> Destination:
        return self.destination

    def get_time_in_force(self) -> TimeInForce:
        return self.time_in_force

    def get_price(self) -> Decimal:
        return self.price

    def get_quantity(self) -> Decimal:
        return self.quantity

    def get_create_time(self) -> datetime:
        return self.create_time

    def get_parent_order(self) -> Order:
        return self.parent_order

    def set_parent_order(self, parent_order: Order):
        self.parent_order = parent_order

    def get_fills(self) -> List[Fill]:
        return self.fills
