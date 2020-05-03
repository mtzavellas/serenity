import binance.client
import coinbasepro
import gemini
from serenity.db import connect_serenity_db, InstrumentCache, TypeCodeCache

conn = connect_serenity_db()
conn.autocommit = True
cur = conn.cursor()

type_code_cache = TypeCodeCache(cur)
instrument_cache = InstrumentCache(cur, type_code_cache)

# map all Gemini products to exchange_instrument table
gemini_client = gemini.PublicClient()
for symbol in gemini_client.symbols():
    base_ccy = symbol[0:3].upper()
    quote_ccy = symbol[3:].upper()
    currency_pair = instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
    instrument_cache.get_or_create_exchange_instrument(symbol, currency_pair.get_instrument(), "Gemini")

# map all Coinbase Pro products to exchange_instrument table
cbp_client = coinbasepro.PublicClient()
for product in cbp_client.get_products():
    symbol = product['id']
    base_ccy = product['base_currency']
    quote_ccy = product['quote_currency']
    currency_pair = instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
    instrument_cache.get_or_create_exchange_instrument(symbol, currency_pair.get_instrument(), "CoinbasePro")

# map all Binance products to exchange_instrument table
binance_client = binance.client.Client()
exchange_info = binance_client.get_exchange_info()
for product in exchange_info['symbols']:
    symbol = product['symbol']
    base_ccy = product['baseAsset']
    quote_ccy = product['quoteAsset']
    currency_pair = instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
    instrument_cache.get_or_create_exchange_instrument(symbol, currency_pair.get_instrument(), "Binance")
