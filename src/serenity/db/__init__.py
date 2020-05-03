import os
from typing import List

import psycopg2

from serenity.model.exchange import Exchange, ExchangeTransferMethod, ExchangeTransferType, \
    ExchangeInstrument, ExchangeOrder, ExchangeAccount, ExchangeFill, ExchangeTransfer
from serenity.model.instrument import InstrumentType, Instrument, Currency, CurrencyPair, CashInstrument
from serenity.model.mark import MarkType
from serenity.model.order import Side, OrderType, DestinationType, TimeInForce


def connect_serenity_db(hostname: str = os.getenv('TIMESCALEDB_NODEPORT_SERVICE_HOST', 'localhost'),
                        port: int = os.getenv('TIMESCALEDB_NODEPORT_SERVICE_PORT', '30432'),
                        username: str = 'postgres', password: str = os.getenv('POSTGRES_PASSWORD', None)):
    return psycopg2.connect(host=hostname, port=port, dbname="serenity", user=username, password=password)


class TypeCodeCache:
    """
    Helper that pre-caches all typecodes in the database and lets the user look up the ID by code.
    """
    def __init__(self, cur):
        self.cur = cur
        self.type_code_map = {
            Exchange: self._load("exchange", Exchange),
            InstrumentType: self._load("instrument_type", InstrumentType),
            Side: self._load("side", Side),
            OrderType: self._load("order_type", OrderType),
            DestinationType: self._load("destination_type", DestinationType),
            TimeInForce: self._load("time_in_force", TimeInForce),
            MarkType: self._load("mark_type", MarkType),
            ExchangeTransferMethod: self._load("exchange_transfer_method", ExchangeTransferMethod),
            ExchangeTransferType: self._load("exchange_transfer_type", ExchangeTransferType)
        }

    def get_by_code(self, klass, type_code):
        return self.type_code_map[klass][0][type_code]

    def get_by_id(self, klass, type_id):
        return self.type_code_map[klass][1][type_id]

    def _load(self, table_name, klass):
        id_column_name = table_name + '_id'
        code_column_name = table_name + '_code'

        type_by_code = {}
        type_by_id = {}
        self.cur.execute("SELECT " + id_column_name + ", " + code_column_name + " FROM serenity." + table_name)
        for row in self.cur.fetchall():
            type_obj = klass(row[0], row[1])
            type_by_code[row[1]] = type_obj
            type_by_id[row[0]] = type_obj
        return type_by_code, type_by_id


class InstrumentCache:
    def __init__(self, cur, type_code_cache: TypeCodeCache):
        self.cur = cur
        self.type_code_cache = type_code_cache

        self.entity_by_id = {
            Currency: {},
            Instrument: {},
            CashInstrument: {},
            CurrencyPair: {},
            ExchangeInstrument: {}
        }
        self.entity_by_ak = {
            Currency: {},
            Instrument: {},
            CashInstrument: {},
            CurrencyPair: {},
            ExchangeInstrument: {}
        }

        self.cur.execute("SELECT currency_id, currency_code FROM serenity.currency")
        for row in self.cur.fetchall():
            currency = Currency(row[0], row[1])
            self.entity_by_id[Currency][row[0]] = currency
            self.entity_by_ak[Currency][row[1]] = currency

        self.cur.execute("SELECT instrument_id, instrument_type_id, instrument_code FROM serenity.instrument")
        for row in self.cur.fetchall():
            instrument_type = self.type_code_cache.get_by_id(InstrumentType, row[1])
            instrument = Instrument(row[0], instrument_type, row[2])
            self.entity_by_id[Instrument][row[0]] = instrument
            self.entity_by_ak[Instrument][row[2]] = instrument

        self.cur.execute("SELECT cash_instrument_id, instrument_id, currency_id FROM serenity.cash_instrument")
        for row in self.cur.fetchall():
            cash_instrument_id = row[0]
            instrument = self.entity_by_id[Instrument][row[1]]
            ccy = self.entity_by_id[Currency][row[2]]
            cash_instrument = CashInstrument(cash_instrument_id, instrument, ccy)
            self.entity_by_id[CashInstrument][row[0]] = cash_instrument
            self.entity_by_ak[CashInstrument][ccy.get_currency_code()] = cash_instrument

        self.cur.execute("SELECT currency_pair_id, instrument_id, base_currency_id, quote_currency_id "
                         "FROM serenity.currency_pair")
        for row in self.cur.fetchall():
            currency_pair_id = row[0]
            instrument = self.entity_by_id[Instrument][row[1]]
            base_ccy = self.entity_by_id[Currency][row[2]]
            quote_ccy = self.entity_by_id[Currency][row[3]]
            ccy_pair = CurrencyPair(currency_pair_id, instrument, base_ccy, quote_ccy)
            self.entity_by_id[CurrencyPair][currency_pair_id] = ccy_pair
            self.entity_by_ak[CurrencyPair][(base_ccy, quote_ccy)] = ccy_pair

        self.cur.execute("SELECT exchange_instrument_id, instrument_id, exchange_id, exchange_instrument_code "
                         "FROM serenity.exchange_instrument")
        for row in self.cur.fetchall():
            exchange_instrument_id = row[0]
            instrument = self.entity_by_id[Instrument][row[1]]
            exchange = self.type_code_cache.get_by_id(Exchange, row[2])
            exchange_instrument_code = row[3]
            exch_instr = ExchangeInstrument(exchange_instrument_id, exchange, instrument, exchange_instrument_code)
            self.entity_by_id[ExchangeInstrument][exchange_instrument_id] = exch_instr
            self.entity_by_ak[ExchangeInstrument][(exchange.get_type_code(), exchange_instrument_code)] = exch_instr

    def get_type_code_cache(self) -> TypeCodeCache:
        return self.type_code_cache

    def get_or_create_instrument(self, code: str, instrument_type: InstrumentType) -> Instrument:
        if code in self.entity_by_ak[Instrument]:
            return self.entity_by_ak[Instrument][code]
        else:
            self.cur.execute("INSERT INTO serenity.instrument (instrument_code, instrument_type_id) VALUES (%s, %s) "
                             " RETURNING instrument_id", (code, instrument_type.get_type_id()))
            instrument_id = self.cur.fetchone()[0]
            instrument = Instrument(instrument_id, instrument_type, code)
            self.entity_by_id[Instrument][instrument_id] = instrument
            self.entity_by_ak[Instrument][code] = instrument
            return instrument

    def get_or_create_currency(self, currency_code) -> Currency:
        if currency_code in self.entity_by_ak[Currency]:
            return self.entity_by_ak[Currency][currency_code]
        else:
            self.cur.execute("INSERT INTO serenity.currency (currency_code) VALUES (%s) RETURNING currency_id",
                             (currency_code,))
            currency_id = self.cur.fetchone()[0]
            currency = Currency(currency_id, currency_code)
            self.entity_by_id[Currency][currency_id] = currency
            self.entity_by_ak[Currency][currency_code] = currency

            # create corresponding entry in the cash_instrument table
            self.get_or_create_cash_instrument(currency_code)

            return currency

    def get_or_create_cash_instrument(self, currency_code: str) -> CashInstrument:
        if currency_code in self.entity_by_ak[CashInstrument]:
            return self.entity_by_ak[CashInstrument][currency_code]
        else:
            instrument_code = "{}.CASH".format(currency_code)
            instrument_type = self.type_code_cache.get_by_code(InstrumentType, "Cash")
            instrument = self.get_or_create_instrument(instrument_code, instrument_type)
            currency = self.get_or_create_currency(currency_code)
            self.cur.execute("INSERT INTO serenity.cash_instrument (currency_id, instrument_id) "
                             "VALUES (%s, %s) RETURNING cash_instrument_id", (currency.get_currency_id(),
                                                                              instrument.get_instrument_id()))
            cash_instrument_id = self.cur.fetchone()[0]
            cash_instrument = CashInstrument(cash_instrument_id, instrument, currency)
            self.entity_by_id[CashInstrument][cash_instrument_id] = cash_instrument
            self.entity_by_ak[CashInstrument][currency_code] = cash_instrument
            return cash_instrument

    def get_or_create_currency_pair(self, base_ccy_code, quote_ccy_code) -> CurrencyPair:
        base_ccy = self.get_or_create_currency(base_ccy_code)
        quote_ccy = self.get_or_create_currency(quote_ccy_code)
        pair = (base_ccy, quote_ccy)
        if pair in self.entity_by_ak[CurrencyPair]:
            return self.entity_by_ak[CurrencyPair][pair]
        else:
            instrument_code = "{}-{}".format(base_ccy_code, quote_ccy_code)
            instrument_type = self.type_code_cache.get_by_code(InstrumentType, "CurrencyPair")
            instrument = self.get_or_create_instrument(instrument_code, instrument_type)
            self.cur.execute("INSERT INTO serenity.currency_pair (base_currency_id, quote_currency_id, instrument_id) "
                             "VALUES (%s, %s, %s) RETURNING currency_pair_id", (base_ccy.get_currency_id(),
                                                                                quote_ccy.get_currency_id(),
                                                                                instrument.get_instrument_id()))
            currency_pair_id = self.cur.fetchone()[0]
            ccy_pair = CurrencyPair(currency_pair_id, instrument, base_ccy, quote_ccy)
            self.entity_by_id[CurrencyPair][currency_pair_id] = ccy_pair
            self.entity_by_ak[CurrencyPair][pair] = ccy_pair
            return ccy_pair

    def get_or_create_exchange_instrument(self, exchange_symbol, instrument, exchange_code) -> ExchangeInstrument:
        ak = (exchange_code, exchange_symbol)
        if ak in self.entity_by_ak[ExchangeInstrument]:
            return self.entity_by_ak[ExchangeInstrument][ak]
        else:
            exchange = self.type_code_cache.get_by_code(Exchange, exchange_code)
            self.cur.execute("INSERT INTO serenity.exchange_instrument (exchange_instrument_code, instrument_id, "
                             "exchange_id) VALUES (%s, %s, %s) RETURNING exchange_instrument_id",
                             (exchange_symbol, instrument.get_instrument_id(), exchange.get_type_id()))
            exchange_instrument_id = self.cur.fetchone()[0]
            exchange_instrument = ExchangeInstrument(exchange_instrument_id, exchange, instrument, exchange_symbol)
            self.entity_by_id[ExchangeInstrument][exchange_instrument_id] = exchange_instrument
            self.entity_by_ak[ExchangeInstrument][ak] = exchange_instrument
            return exchange_instrument

    def get_all_exchange_instruments(self, exchange_code) -> List[ExchangeInstrument]:
        instruments = []
        instrument_map = self.entity_by_ak[ExchangeInstrument]
        for instrument in instrument_map.values():
            if instrument.get_exchange().get_type_code() == exchange_code:
                instruments.append(instrument)
        return instruments

    def get_exchange_instrument(self, exchange_code, exchange_symbol):
        return self.get_entity_by_ak((exchange_code, exchange_symbol))

    def get_entity_by_id(self, klass, entity_id):
        return self.entity_by_id[klass][entity_id]

    def get_entity_by_ak(self, klass, ak):
        return self.entity_by_ak[klass][ak]


class ExchangeEntityService:
    def __init__(self, cur, type_code_cache: TypeCodeCache, instrument_cache: InstrumentCache):
        self.cur = cur
        self.type_code_cache = type_code_cache
        self.instrument_cache = instrument_cache

        self.entity_by_id = {
            ExchangeAccount: {},
            ExchangeOrder: {},
            ExchangeFill: {},
            ExchangeTransfer: {}
        }
        self.entity_by_ak = {
            ExchangeAccount: {},
            ExchangeOrder: {},
            ExchangeFill: {},
            ExchangeTransfer: {}
        }

        self.cur.execute("SELECT exchange_account_id, exchange_id, exchange_account_num "
                         "FROM serenity.exchange_account")
        for row in self.cur.fetchall():
            exchange = self.type_code_cache.get_by_id(Exchange, row[1])
            ak = (exchange.get_type_code(), row[2])
            exchange_account = ExchangeAccount(row[0], exchange, row[2])
            self.entity_by_id[ExchangeAccount][row[0]] = exchange_account
            self.entity_by_ak[ExchangeAccount][ak] = exchange_account

        self.cur.execute("SELECT exchange_order_id, exchange_id, exchange_instrument_id, order_type_id, "
                         "exchange_account_id, side_id, time_in_force_id, exchange_order_uuid, price,"
                         "quantity, create_time FROM serenity.exchange_order")
        for row in self.cur.fetchall():
            exchange_order_id = row[0]
            exchange = self.type_code_cache.get_by_id(Exchange, row[1])
            exch_instr = self.instrument_cache.get_entity_by_id(ExchangeInstrument, row[2])
            order_type = self.type_code_cache.get_by_id(OrderType, row[3])
            exchange_account = self.entity_by_id[ExchangeAccount][row[4]]
            side = self.type_code_cache.get_by_id(Side, row[5])
            time_in_force = self.type_code_cache.get_by_id(TimeInForce, row[6])
            order_uuid = row[7]
            price = row[8]
            quantity = row[9]
            create_time = row[10]
            ak = (exchange.get_type_code(), order_uuid)

            exchange_order = ExchangeOrder(exchange_order_id, exchange, exch_instr, order_type, exchange_account,
                                           side, time_in_force, order_uuid, price, quantity, create_time)
            self.entity_by_id[ExchangeOrder][exchange_order_id] = exchange_order
            self.entity_by_ak[ExchangeOrder][ak] = exchange_order

        self.cur.execute("SELECT exchange_fill_id, exchange_order_id, fill_price, quantity, fees, trade_id,"
                         "create_time FROM serenity.exchange_fill")
        for row in self.cur.fetchall():
            exchange_fill_id = row[0]
            order = self.entity_by_id[ExchangeOrder][row[1]]
            fill_price = row[2]
            quantity = row[3]
            fees = row[4]
            trade_id = row[5]
            create_time = row[6]
            ak = (order.get_exchange().get_type_code(), trade_id)

            exchange_fill = ExchangeFill(exchange_fill_id, fill_price, quantity, fees, trade_id, create_time)
            exchange_fill.set_order(order)
            self.entity_by_id[ExchangeFill][exchange_fill_id] = exchange_fill
            self.entity_by_ak[ExchangeFill][ak] = exchange_fill

        self.cur.execute("SELECT exchange_transfer_id, exchange_id, exchange_transfer_method_id, "
                         "exchange_transfer_type_id, currency_id, quantity, transfer_ref, transfer_time "
                         "FROM serenity.exchange_transfer")
        for row in self.cur.fetchall():
            exchange_transfer_id = row[0]
            exchange = self.type_code_cache.get_by_id(Exchange, row[1])
            exchange_transfer_method = self.type_code_cache.get_by_id(ExchangeTransferMethod, row[2])
            exchange_transfer_type = self.type_code_cache.get_by_id(ExchangeTransferType, row[3])
            currency = self.instrument_cache.get_entity_by_id(Currency, row[4])
            quantity = row[5]
            transfer_ref = row[6]
            transfer_time = row[7]
            ak = (exchange.get_type_code(), transfer_ref)

            exchange_transfer = ExchangeTransfer(exchange_transfer_id, exchange, exchange_transfer_method,
                                                 exchange_transfer_type, currency, quantity, transfer_ref,
                                                 transfer_time)
            self.entity_by_id[ExchangeTransfer][exchange_transfer_id] = exchange_transfer
            self.entity_by_ak[ExchangeTransfer][ak] = exchange_transfer

    def get_or_create_account(self, account: ExchangeAccount):
        ak = (account.get_exchange().get_type_code(), account.get_exchange_account_num())
        if ak in self.entity_by_ak[ExchangeAccount]:
            return self.entity_by_ak[ExchangeAccount][ak]
        else:
            self.cur.execute("INSERT INTO serenity.exchange_account (exchange_id, exchange_account_num) "
                             "VALUES (%s, %s) RETURNING exchange_account_id", (account.get_exchange().get_type_id(),
                                                                               account.get_exchange_account_num()))
            exchange_account_id = self.cur.fetchone()[0]
            account.set_exchange_account_id(exchange_account_id)
            self.entity_by_id[ExchangeAccount][exchange_account_id] = account
            self.entity_by_ak[ExchangeAccount][ak] = account
            return account

    def get_or_create_exchange_order(self, order: ExchangeOrder):
        ak = (order.get_exchange().get_type_code(), order.get_exchange_order_uuid())
        if ak in self.entity_by_ak[ExchangeOrder]:
            return self.entity_by_ak[ExchangeOrder][ak]
        else:
            self.cur.execute("INSERT INTO serenity.exchange_order (exchange_id, exchange_instrument_id, order_type_id, "
                             "exchange_account_id, side_id, time_in_force_id, exchange_order_uuid, price, quantity, "
                             "create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING exchange_order_id",
                             (order.get_exchange().get_type_id(), order.get_instrument().get_exchange_instrument_id(),
                              order.get_order_type().get_type_id(),
                              order.get_exchange_account().get_exchange_account_id(),
                              order.get_side().get_type_id(), order.get_time_in_force().get_type_id(),
                              order.get_exchange_order_uuid(), order.get_price(), order.get_quantity(),
                              order.get_create_time()))
            exchange_order_id = self.cur.fetchone()[0]
            order.set_exchange_order_id(exchange_order_id)
            self.entity_by_id[ExchangeOrder][exchange_order_id] = order
            self.entity_by_ak[ExchangeOrder][ak] = order
            return order

    def get_or_create_exchange_fill(self, fill: ExchangeFill):
        ak = (fill.get_order().get_exchange().get_type_code(), fill.get_trade_id())
        if ak in self.entity_by_ak[ExchangeFill]:
            return self.entity_by_ak[ExchangeFill][ak]
        else:
            self.cur.execute("INSERT INTO serenity.exchange_fill (exchange_order_id, fill_price, quantity,"
                             "fees, trade_id, create_time) VALUES (%s, %s, %s, %s, %s, %s) RETURNING exchange_fill_id",
                             (fill.get_order().get_exchange_order_id(), fill.get_fill_price(), fill.get_quantity(),
                              fill.get_fees(), fill.get_trade_id(), fill.get_create_time()))
            exchange_fill_id = self.cur.fetchone()[0]
            fill.set_exchange_fill_id(exchange_fill_id)
            self.entity_by_id[ExchangeFill][exchange_fill_id] = fill
            self.entity_by_ak[ExchangeFill][ak] = fill
            return fill

    def get_or_create_exchange_transfer(self, transfer: ExchangeTransfer):
        ak = (transfer.get_exchange().get_type_code(), transfer.get_transfer_ref())
        if ak in self.entity_by_ak[ExchangeTransfer]:
            return self.entity_by_ak[ExchangeTransfer][ak]
        else:
            self.cur.execute("INSERT INTO serenity.exchange_transfer (exchange_id, exchange_transfer_method_id, "
                             "exchange_transfer_type_id, currency_id, quantity, transfer_ref, transfer_time) "
                             "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING exchange_transfer_id",
                             (transfer.get_exchange().get_type_id(),
                              transfer.get_exchange_transfer_method().get_type_id(),
                              transfer.get_exchange_transfer_type().get_type_id(),
                              transfer.get_currency().get_currency_id(), transfer.get_quantity(),
                              transfer.get_transfer_ref(), transfer.get_transfer_time()))
            exchange_transfer_id = self.cur.fetchone()[0]
            transfer.set_exchange_transfer_id(exchange_transfer_id)
            self.entity_by_id[ExchangeTransfer][exchange_transfer_id] = transfer
            self.entity_by_ak[ExchangeTransfer][ak] = transfer
            return transfer

    def get_entity_by_ak(self, klass, ak):
        return self.entity_by_ak[klass][ak]
