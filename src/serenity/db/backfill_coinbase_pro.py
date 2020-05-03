import coinbasepro
import fire

from serenity.db import connect_serenity_db, ExchangeEntityService, TypeCodeCache, InstrumentCache
from serenity.model.exchange import ExchangeAccount, ExchangeOrder, Exchange, ExchangeFill
from serenity.model.instrument import InstrumentType
from serenity.model.order import Side, OrderType, TimeInForce


def backfill_coinbasepro(api_key: str, api_secret: str, api_passphrase: str):
    conn = connect_serenity_db()
    cur = conn.cursor()
    type_code_cache = TypeCodeCache(cur)
    instrument_cache = InstrumentCache(cur, type_code_cache)
    exch_service = ExchangeEntityService(cur, type_code_cache, instrument_cache)
    auth_client = coinbasepro.AuthenticatedClient(key=api_key, secret=api_secret, passphrase=api_passphrase)

    # Coinbase Pro has a notion of account per currency for tracking balances, so we want to pull
    # out what it calls the profile, which is the parent exchange account
    profile_set = set()
    for account in auth_client.get_accounts():
        profile_set.add(account['profile_id'])

    exchange = type_code_cache.get_by_code(Exchange, "CoinbasePro")
    account_by_profile_id = {}
    for profile in profile_set:
        account = exch_service.get_or_create_account(ExchangeAccount(0, exchange, profile))
        account_by_profile_id[profile] = account

    # load up all the orders
    for order in auth_client.get_orders(status=['done']):
        order_uuid = order['id']

        # market orders have no price
        if 'price' in order:
            price = order['price']
        else:
            price = None

        # market orders that specify "funds" have no size
        if 'size' in order:
            size = order['size']
        else:
            size = order['filled_size']

        exchange_account = account_by_profile_id[order['profile_id']]
        instrument_type = type_code_cache.get_by_code(InstrumentType, 'CurrencyPair')
        instrument = instrument_cache.get_or_create_instrument(order['product_id'], instrument_type)
        exchange_instrument = instrument_cache.get_or_create_exchange_instrument(order['product_id'], instrument,
                                                                                 exchange.get_type_code())
        side = type_code_cache.get_by_code(Side, order['side'].capitalize())

        if order['type'] is None:
            order['type'] = 'Market'

        order_type = type_code_cache.get_by_code(OrderType, order['type'].capitalize())
        if 'time_in_force' in order:
            tif = type_code_cache.get_by_code(TimeInForce, order['time_in_force'])
        else:
            tif = type_code_cache.get_by_code(TimeInForce, 'Day')
        create_time = order['created_at']

        order = ExchangeOrder(0, exchange, exchange_instrument, order_type, exchange_account,
                              side, tif, order_uuid, price, size, create_time)
        exch_service.get_or_create_exchange_order(order)

    conn.commit()

    # load up all the fills, linking back to the orders
    for product in ['BTC-USD', 'ETH-BTC']:
        for fill in auth_client.get_fills(product_id=product):
            order_id = fill['order_id']
            trade_id = fill['trade_id']
            price = fill['price']
            size = fill['size']
            fees = fill['fee']
            create_time = fill['created_at']

            order = exch_service.get_entity_by_ak(ExchangeOrder, (exchange.get_type_code(), order_id))
            fill = ExchangeFill(0, price, size, fees, trade_id, create_time)
            fill.set_order(order)
            exch_service.get_or_create_exchange_fill(fill)

        conn.commit()


if __name__ == '__main__':
    fire.Fire(backfill_coinbasepro)
