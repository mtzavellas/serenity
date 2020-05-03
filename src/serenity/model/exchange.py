from datetime import datetime
from decimal import Decimal

from serenity.model import TypeCode
from serenity.model.instrument import Instrument, Currency
from serenity.model.order import OrderType, TimeInForce, Side, Destination, DestinationType


class Exchange(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class ExchangeInstrument:
    def __init__(self, exchange_instrument_id: int, exchange: Exchange, instrument: Instrument,
                 exchange_instrument_code: str):
        self.exchange_instrument_id = exchange_instrument_id

        self.exchange = exchange
        self.instrument = instrument

        self.exchange_instrument_code = exchange_instrument_code

    def get_exchange(self) -> Exchange:
        return self.exchange

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_exchange_instrument_id(self) -> int:
        return self.exchange_instrument_id

    def get_exchange_instrument_code(self) -> str:
        return self.exchange_instrument_code

    def __str__(self):
        return f'{self.exchange}[{self.exchange_instrument_code}]'


class ExchangeAccount:
    def __init__(self, exchange_account_id: int, exchange: Exchange, exchange_account_num: str):
        self.exchange_account_id = exchange_account_id

        self.exchange = exchange

        self.exchange_accont_num = exchange_account_num

    def get_exchange_account_id(self) -> int:
        return self.exchange_account_id

    def set_exchange_account_id(self, exchange_account_id: int):
        self.exchange_account_id = exchange_account_id

    def get_exchange(self) -> Exchange:
        return self.exchange

    def get_exchange_account_num(self) -> str:
        return self.exchange_accont_num


# noinspection DuplicatedCode
class ExchangeOrder:
    def __init__(self, exchange_order_id: int, exchange: Exchange, instrument: ExchangeInstrument,
                 order_type: OrderType, exchange_account: ExchangeAccount, side: Side, time_in_force: TimeInForce,
                 exchange_order_uuid: str, price: Decimal, quantity: Decimal, create_time: datetime):
        self.exchange_order_id = exchange_order_id
        self.exchange = exchange
        self.instrument = instrument
        self.order_type = order_type
        self.exchange_account = exchange_account
        self.side = side
        self.time_in_force = time_in_force
        self.exchange_order_uuid = exchange_order_uuid
        self.price = price
        self.quantity = quantity
        self.create_time = create_time

    def get_exchange_order_id(self) -> int:
        return self.exchange_order_id

    def set_exchange_order_id(self, exchange_order_id: int):
        self.exchange_order_id = exchange_order_id

    def get_exchange(self) -> Exchange:
        return self.exchange

    def get_instrument(self) -> ExchangeInstrument:
        return self.instrument

    def get_order_type(self) -> OrderType:
        return self.order_type

    def get_exchange_account(self) -> ExchangeAccount:
        return self.exchange_account

    def get_side(self) -> Side:
        return self.side

    def get_time_in_force(self) -> TimeInForce:
        return self.time_in_force

    def get_exchange_order_uuid(self):
        return self.exchange_order_uuid

    def get_price(self):
        return self.price

    def get_quantity(self):
        return self.quantity

    def get_create_time(self):
        return self.create_time


class ExchangeFill:
    def __init__(self, exchange_fill_id: int, fill_price: Decimal, quantity: Decimal, fees: Decimal,
                 trade_id: int, create_time: datetime):
        self.exchange_fill_id = exchange_fill_id
        self.fill_price = fill_price
        self.quantity = quantity
        self.fees = fees
        self.trade_id = trade_id
        self.create_time = create_time

        self.order = None

    def get_exchange_fill_id(self) -> int:
        return self.exchange_fill_id

    def set_exchange_fill_id(self, exchange_fill_id: int):
        self.exchange_fill_id = exchange_fill_id

    def get_fill_price(self) -> Decimal:
        return self.fill_price

    def get_quantity(self) -> Decimal:
        return self.quantity

    def get_fees(self) -> Decimal:
        return self.fees

    def get_trade_id(self) -> int:
        return self.trade_id

    def get_create_time(self) -> datetime:
        return self.create_time

    def get_order(self) -> ExchangeOrder:
        return self.order

    def set_order(self, order: ExchangeOrder):
        self.order = order


class ExchangeTransferMethod(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class ExchangeTransferType(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


# noinspection DuplicatedCode
class ExchangeTransfer:
    def __init__(self, exchange_transfer_id: int, exchange: Exchange, exchange_transfer_type: ExchangeTransferType,
                 exchange_transfer_method: ExchangeTransferMethod, currency: Currency, quantity: Decimal,
                 transfer_ref: str, transfer_time: datetime):
        self.exchange_transfer_id = exchange_transfer_id

        self.exchange = exchange
        self.exchange_transfer_type = exchange_transfer_type
        self.exchange_transfer_method = exchange_transfer_method
        self.currency = currency

        self.quantity = quantity
        self.transfer_ref = transfer_ref
        self.cost_basis = None
        self.transfer_time = transfer_time

    def get_exchange_transfer_id(self) -> int:
        return self.exchange_transfer_id

    def set_exchange_transfer_id(self, exchange_transfer_id: int):
        self.exchange_transfer_id = exchange_transfer_id

    def get_exchange(self) -> Exchange:
        return self.exchange

    def get_exchange_transfer_method(self) -> ExchangeTransferMethod:
        return self.exchange_transfer_method

    def get_exchange_transfer_type(self) -> ExchangeTransferType:
        return self.exchange_transfer_type

    def get_currency(self) -> Currency:
        return self.currency

    def get_quantity(self) -> Decimal:
        return self.quantity

    def get_transfer_ref(self) -> str:
        return self.transfer_ref

    def get_cost_basis(self) -> Decimal:
        return self.cost_basis

    def set_cost_basis(self, cost_basis: Decimal):
        self.cost_basis = cost_basis

    def get_transfer_time(self) -> datetime:
        return self.transfer_time


class ExchangeDestination(Destination):
    def __init__(self, destination_id: int, destination_type: DestinationType, exchange: Exchange):
        super().__init__(destination_id, destination_type)
        self.exchange = exchange