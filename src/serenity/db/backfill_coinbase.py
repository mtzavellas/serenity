from datetime import datetime

import fire

from serenity.db import connect_serenity_db, ExchangeEntityService, TypeCodeCache, InstrumentCache
from serenity.model.exchange import ExchangeAccount, ExchangeOrder, Exchange, ExchangeFill
from serenity.model.instrument import InstrumentType
from serenity.model.order import Side, OrderType, TimeInForce


def backfill_coinbase():
    conn = connect_serenity_db()
    cur = conn.cursor()
    type_code_cache = TypeCodeCache(cur)
    instrument_cache = InstrumentCache(cur, type_code_cache)
    exch_service = ExchangeEntityService(cur, type_code_cache, instrument_cache)

    # create a default account for Coinbase
    exchange = type_code_cache.get_by_code(Exchange, 'Coinbase')
    account = exch_service.get_or_create_account(ExchangeAccount(0, exchange, 'default'))

    # create a BTC-USD symbol for Coinbase
    product_id = 'BTC-USD'
    instrument_type = type_code_cache.get_by_code(InstrumentType, 'CurrencyPair')
    instrument = instrument_cache.get_or_create_instrument(product_id, instrument_type)
    exchange_instrument = instrument_cache.get_or_create_exchange_instrument(product_id, instrument, 'Coinbase')

    # synthesize market orders and fills for Coinbase purchases
    side = type_code_cache.get_by_code(Side, 'Buy')
    order_type = type_code_cache.get_by_code(OrderType, 'Market')
    tif = type_code_cache.get_by_code(TimeInForce, 'Day')

    # noinspection DuplicatedCode
    def create_exchange_order_and_fill(price, quantity, fees, order_id, create_time):
        order = ExchangeOrder(0, exchange, exchange_instrument, order_type, account, side, tif, order_id, price,
                              quantity, create_time)
        order = exch_service.get_or_create_exchange_order(order)
        conn.commit()
        fill = ExchangeFill(0, price, quantity, fees, order_id, create_time)
        fill.set_order(order)
        exch_service.get_or_create_exchange_fill(fill)
        conn.commit()

    # investment purchase
    create_exchange_order_and_fill(265.39, 1.13, 2.9993, 1, datetime(2015, 1, 26))

    # residual left in account after payment by Bitcoin
    create_exchange_order_and_fill(238.47, 2.1 - 1.68136, 5.013, 2, datetime(2015, 2, 13))

    # investment purchase
    create_exchange_order_and_fill(249.05, 0.5, 1.25, 3, datetime(2015, 2, 14))


if __name__ == '__main__':
    fire.Fire(backfill_coinbase)
