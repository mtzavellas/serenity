from datetime import datetime
from decimal import Decimal

from serenity.model import TypeCode
from serenity.model.instrument import Instrument


class MarkType(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class InstrumentMark:
    def __init__(self, mark_id: int, instrument: Instrument, mark_type: MarkType, mark: Decimal, mark_time: datetime):
        self.mark_id = mark_id

        self.instrument = instrument
        self.mark_type = mark_type

        self.mark = mark
        self.mark_time = mark_time

    def get_mark_id(self) -> int:
        return self.mark_id

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_mark_type(self) -> MarkType:
        return self.mark_type

    def get_mark(self) -> Decimal:
        return self.mark

    def get_mark_time(self) -> datetime:
        return self.mark_time
