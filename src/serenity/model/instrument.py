from serenity.model import TypeCode


class Currency:
    def __init__(self, currency_id: int, currency_code: str):
        self.currency_id = currency_id
        self.currency_code = currency_code

    def get_currency_id(self) -> int:
        return self.currency_id

    def get_currency_code(self) -> str:
        return self.currency_code


class InstrumentType(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class Instrument:
    def __init__(self, instrument_id: int, instrument_type: InstrumentType, instrument_code: str):
        self.instrument_id = instrument_id
        self.instrument_type = instrument_type
        self.instrument_code = instrument_code

    def get_instrument_id(self) -> int:
        return self.instrument_id

    def get_instrument_code(self) -> str:
        return self.instrument_code

    def get_instrument_type(self) -> InstrumentType:
        return self.instrument_type


class CashInstrument:
    def __init__(self, cash_instrument_id: int, instrument: Instrument, currency: Currency):
        self.cash_instrument_id = cash_instrument_id
        self.instrument = instrument
        self.currency = currency

    def get_cash_instrument_id(self) -> int:
        return self.cash_instrument_id

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_currency(self) -> Currency:
        return self.currency


class CurrencyPair:
    def __init__(self, currency_pair_id: int, instrument: Instrument,
                 base_currency: Currency, quote_currency: Currency):
        self.currency_pair_id = currency_pair_id
        self.instrument = instrument
        self.base_currency = base_currency
        self.quote_currency = quote_currency

    def get_currency_pair_id(self) -> int:
        return self.currency_pair_id

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_base_currency(self) -> Currency:
        return self.base_currency

    def get_quote_currency(self) -> Currency:
        return self.quote_currency
