from pytest_mock import MockFixture

from serenity.fh.feedhandler import FeedHandlerRegistry


def test_feedhandler_registry(mocker: MockFixture):
    mock_feed = mocker.patch('serenity.fh.feedhandler.Feed').return_value
    fh = mocker.patch('serenity.fh.feedhandler.FeedHandler').return_value
    fh.get_uri_scheme.return_value = 'phemex'
    fh.get_instance_id.return_value = 'test'
    fh.get_feed.return_value = mock_feed

    registry = FeedHandlerRegistry()
    registry.register(fh)
    feed = registry.get_feed('phemex:test:BTCUSD')
    assert(feed == mock_feed)
