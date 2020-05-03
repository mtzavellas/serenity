import datetime
import shutil

from serenity.tickstore.journal import Journal
from pathlib import Path


def test_journal():
    journal = Journal(Path('tmp'))
    appender = journal.create_appender()

    for i in range(0, 1000):
        appender.write_string('BTC-USD')
        appender.write_int(77571114)
        appender.write_short(1)
        appender.write_double(0.00452635)
        appender.write_double(8797.78)
        appender.write_long(i)

    appender.close()

    reader = journal.create_reader(datetime.datetime.utcnow().date())
    assert 38000 == reader.get_length()

    for i in range(0, 1000):
        assert 'BTC-USD' == reader.read_string()
        assert 77571114 == reader.read_int()
        assert 1 == reader.read_short()
        assert 0.00452635 == reader.read_double()
        assert 8797.78 == reader.read_double()
        assert i == reader.read_long()


def teardown_function():
    shutil.rmtree('tmp', True)
