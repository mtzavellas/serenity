from datetime import datetime

import gemini
import fire

from serenity.db import connect_serenity_db, TypeCodeCache, InstrumentCache, ExchangeEntityService
from serenity.model.exchange import ExchangeOrder, Exchange, ExchangeFill, ExchangeAccount, \
    ExchangeTransferType, ExchangeTransferMethod, ExchangeTransfer
from serenity.model.instrument import InstrumentType
from serenity.model.order import OrderType, Side, TimeInForce


def backfill_gemini(gemini_api_key: str, gemini_api_secret: str):
    conn = connect_serenity_db()
    cur = conn.cursor()
    type_code_cache = TypeCodeCache(cur)
    instrument_cache = InstrumentCache(cur, type_code_cache)
    exch_service = ExchangeEntityService(cur, type_code_cache, instrument_cache)
    client = gemini.PrivateClient(gemini_api_key, gemini_api_secret)

    for exchange_symbol in ('BTCUSD', 'ETHBTC', 'ZECBTC'):
        instrument_symbol = exchange_symbol[0:3] + '-' + exchange_symbol[3:]
        instrument_type = type_code_cache.get_by_code(InstrumentType, 'CurrencyPair')
        instrument = instrument_cache.get_or_create_instrument(instrument_symbol, instrument_type)
        exchange_instrument = instrument_cache.get_or_create_exchange_instrument(exchange_symbol.lower(),
                                                                                 instrument, 'Gemini')

        conn.commit()

        exchange = type_code_cache.get_by_code(Exchange, 'Gemini')

        for trade in client.get_past_trades(exchange_symbol):
            fill_price = trade['price']
            quantity = trade['amount']
            fees = trade['fee_amount']
            side = type_code_cache.get_by_code(Side, trade['type'])
            trade_id = trade['tid']
            order_uuid = trade['order_id']
            create_time_ms = trade['timestampms']
            create_time = datetime.utcfromtimestamp(create_time_ms // 1000).\
                replace(microsecond=create_time_ms % 1000 * 1000)

            # because we cannot get historical exchange orders past 7 days, we need to synthesize limit orders
            exchange_account = ExchangeAccount(0, exchange, 'default')
            exchange_account = exch_service.get_or_create_account(exchange_account)
            order_type = type_code_cache.get_by_code(OrderType, 'Limit')
            tif = type_code_cache.get_by_code(TimeInForce, 'GTC')
            order = ExchangeOrder(0, exchange, exchange_instrument, order_type, exchange_account, side, tif, order_uuid,
                                  fill_price, quantity, create_time)
            order = exch_service.get_or_create_exchange_order(order)
            conn.commit()

            # create the fills and insert, linking back to the synthetic order
            fill = ExchangeFill(0, fill_price, quantity, fees, trade_id, create_time)
            fill.set_order(order)
            exch_service.get_or_create_exchange_fill(fill)
            conn.commit()

    for transfer in client.api_query('/v1/transfers', {}):
        transfer_type = type_code_cache.get_by_code(ExchangeTransferType, transfer['type'])
        transfer_method = type_code_cache.get_by_code(ExchangeTransferMethod, "Blockchain")
        currency = instrument_cache.get_or_create_currency(transfer['currency'])
        quantity = transfer['amount']
        transfer_ref = transfer['txHash']
        transfer_time_ms = transfer['timestampms']
        transfer_time = datetime.utcfromtimestamp(transfer_time_ms // 1000). \
            replace(microsecond=transfer_time_ms % 1000 * 1000)

        transfer = ExchangeTransfer(0, exchange, transfer_type, transfer_method, currency, quantity, transfer_ref,
                                    transfer_time)
        exch_service.get_or_create_exchange_transfer(transfer)

    conn.commit()


if __name__ == '__main__':
    fire.Fire(backfill_gemini)
