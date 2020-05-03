import decimal
from datetime import datetime

import fire

from serenity.db import connect_serenity_db, TypeCodeCache, InstrumentCache
from serenity.model.exchange import ExchangeInstrument
from serenity.model.instrument import Instrument, Currency
from serenity.model.order import Side


class TradeAnalyzer:
    def __init__(self, cur, type_code_cache: TypeCodeCache, instrument_cache: InstrumentCache):
        self.cur = cur
        self.type_code_cache = type_code_cache
        self.instrument_cache = instrument_cache

        self.trades = {}

        cur.execute("SELECT eo.side_id, eo.exchange_instrument_id, ef.fill_price, ef.quantity, ef.fees, ef.create_time "
                    "FROM serenity.exchange_fill ef "
                    "INNER JOIN serenity.exchange_order eo on eo.exchange_order_id = ef.exchange_order_id "
                    "ORDER BY ef.create_time ASC ")
        for row in cur.fetchall():
            side = type_code_cache.get_by_id(Side, row[0])
            instrument = instrument_cache.get_entity_by_id(ExchangeInstrument, row[1])
            instrument_code = instrument.get_instrument().get_instrument_code()

            if instrument_code not in self.trades:
                self.trades[instrument_code] = {}

            if side.get_type_code() not in self.trades[instrument_code]:
                self.trades[instrument_code][side.get_type_code()] = []

            trade_info = {
                'px': row[2],
                'qty': row[3],
                'remaining': row[3],
                'fee': row[4],
                'ts': row[5],
            }
            self.trades[instrument_code][side.get_type_code()].append(trade_info)

        # explode cross-currency trades into their component parts
        usd_ccy = instrument_cache.get_entity_by_ak(Currency, 'USD')
        for instrument_code in list(self.trades):
            pair_codes = tuple(instrument_code.split('-'))
            base_ccy = instrument_cache.get_entity_by_ak(Currency, pair_codes[0])
            quote_ccy = instrument_cache.get_entity_by_ak(Currency, pair_codes[1])
            if quote_ccy.get_currency_code() != 'USD':
                long = "{}-{}".format(base_ccy.get_currency_code(), usd_ccy.get_currency_code())
                short = "{}-{}".format(quote_ccy.get_currency_code(), usd_ccy.get_currency_code())

                if long not in self.trades:
                    self.trades[long] = {'Buy': [], 'Sell': []}

                if short not in self.trades:
                    self.trades[short] = {'Buy': [], 'Sell': []}

                # for each sell, buy short instrument and sell long instrument
                for sell in self.trades[instrument_code]['Sell']:
                    self.trades[short]['Buy'].append({
                        'px': self.lookup_instrument_mark(short, sell['ts']),
                        'qty': sell['qty'] * sell['px'],
                        'remaining': sell['qty'] * sell['px'],
                        'fee': 0.0,
                        'ts': sell['ts']
                    })

                    self.trades[long]['Sell'].append({
                        'px': self.lookup_instrument_mark(long, sell['ts']),
                        'qty': sell['qty'],
                        'remaining': sell['qty'],
                        'fee': 0.0,
                        'ts': sell['ts']
                    })

                # for each buy, buy long instrument and sell short instrument
                for buy in self.trades[instrument_code]['Buy']:
                    self.trades[long]['Buy'].append({
                        'px': self.lookup_instrument_mark(long, buy['ts']),
                        'qty': buy['qty'],
                        'remaining': buy['qty'],
                        'fee': 0.0,
                        'ts': buy['ts']
                    })

                    self.trades[short]['Sell'].append({
                        'px': self.lookup_instrument_mark(short, buy['ts']),
                        'qty': buy['qty'] * buy['px'],
                        'remaining': buy['qty'] * buy['px'],
                        'fee': 0.0,
                        'ts': buy['ts']
                    })

        # re-sort buys and sells by ts
        for instrument_code in list(self.trades):
            self.trades[instrument_code]['Buy'] = sorted(self.trades[instrument_code]['Buy'], key=lambda k: k['ts'])
            self.trades[instrument_code]['Sell'] = sorted(self.trades[instrument_code]['Sell'], key=lambda k: k['ts'])

    def lookup_instrument_mark(self, instrument_code: str, timestamp: datetime):
        instrument = self.instrument_cache.get_entity_by_ak(Instrument, instrument_code)
        self.cur.execute("SELECT mark FROM serenity.instrument_mark WHERE mark_time = %s AND instrument_id = %s",
                         (timestamp.date(), instrument.get_instrument_id()))
        row = self.cur.fetchone()
        if row is None:
            return 0.0
        else:
            return row[0]

    def run_analysis(self, instrument_codes: list, tax_year: int, tax_rate: float):
        with open('{}.txf'.format(tax_year), 'w') as txf_file:
            print("V042", file=txf_file)
            print("ASerenity", file=txf_file)
            print("D {}".format(datetime.now().date().strftime('%m/%d/%Y')), file=txf_file)
            print("^", file=txf_file)

            total_pnl = decimal.Decimal(0.0)

            for instrument_code in instrument_codes:
                all_trades = self.trades[instrument_code]
                sells = (all_trades['Sell'])

                for sell in sells:
                    proceeds = sell['qty'] * sell['px']
                    in_tax_year = datetime(tax_year, 1, 1) < sell['ts'] < datetime(tax_year, 12, 31)
                    if in_tax_year:
                        print("Sell " + instrument_code.split('-')[0] + " " + str(sell['qty']) + " @ " +
                              str(sell['px']) + " on " + str(sell['ts'].date()) +
                              "; sale yielded " + '${:,.2f}'.format(proceeds))

                    cost_basis = decimal.Decimal(0.0)
                    last_buy = None
                    for candidate_buy in all_trades['Buy']:
                        if candidate_buy['ts'] <= sell['ts'] \
                                and candidate_buy['remaining'] > 0.0 \
                                and sell['remaining'] > 0.0:
                            if candidate_buy['remaining'] < sell['remaining']:
                                qty_bought = candidate_buy['remaining']
                                sell['remaining'] -= qty_bought
                                candidate_buy['remaining'] = decimal.Decimal(0.0)
                            else:
                                qty_bought = sell['remaining']
                                candidate_buy['remaining'] -= qty_bought
                                sell['remaining'] = decimal.Decimal(0.0)

                            if qty_bought > sell['qty']:
                                qty_bought = sell['qty']

                            cost_basis += qty_bought * candidate_buy['px']
                            last_buy = candidate_buy
                    if last_buy is not None and in_tax_year:
                        trade_pnl = proceeds - cost_basis
                        total_pnl += trade_pnl
                        print("\t Buy date: " + str(last_buy['ts'].date()))
                        print("\t Cost basis: ${:,.2f}".format(cost_basis))
                        print("\t Profit/Loss: " + '${:,.2f}'.format(trade_pnl).replace('$-', '-$'))
                        print("\t Cum. PnL: " + '${:,.2f}'.format(total_pnl).replace('$-', '-$'))

                        print("TD", file=txf_file)
                        print("N712", file=txf_file)
                        print("C1", file=txf_file)
                        print("L1", file=txf_file)
                        print("P{}".format(str(sell['qty']) + " " + instrument_code.split('-')[0]), file=txf_file)
                        print("D{}".format(sell['ts'].date().strftime('%m/%d/%Y')), file=txf_file)
                        print("D{}".format(last_buy['ts'].date().strftime('%m/%d/%Y')), file=txf_file)
                        print("${:.2f}".format(cost_basis), file=txf_file)
                        print("${:.2f}".format(proceeds), file=txf_file)
                        print("^", file=txf_file)

            print("\nOverall Profit/Loss: " + '${:,.2f}'.format(total_pnl).replace('$-', '-$'))
            print("Est. Tax: " + '${:,.2f}'.format(total_pnl * decimal.Decimal(tax_rate)).replace('$-', '-$'))


def generate_tax_report():
    conn = connect_serenity_db()
    cur = conn.cursor()
    type_code_cache = TypeCodeCache(cur)
    instrument_cache = InstrumentCache(cur, type_code_cache)

    analyzer = TradeAnalyzer(cur, type_code_cache, instrument_cache)
    analyzer.run_analysis(['BTC-USD', 'ETH-USD'], 2019, 0.35)


if __name__ == '__main__':
    fire.Fire(generate_tax_report)

