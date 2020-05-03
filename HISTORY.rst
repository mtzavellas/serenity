.. :changelog:

Release History
---------------

0.2.0 (2020-05-02)
++++++++++++++++++

- Started framing out algo engine API
- Supported extending mmap journal files on-the-fly
- Improved Azure DevOps integration, including Python 3.7/3.8 cross-build
- Upgraded to Tau 0.4.3

0.1.3 (2020-04-30)
++++++++++++++++++

- Upgraded to Tau 0.4.0
- Cleaned up requirements.txt; removed tornado & APScheduler

0.1.2 (2020-04-26)
++++++++++++++++++

- Upgraded to Tau 0.3.1 to pick up critical bug fix

0.1.1 (2020-04-26)
++++++++++++++++++

- Additional fixes for Tickstore bi-temporal index logic

0.1.0 (2020-04-25)
++++++++++++++++++

- Refactored PhemexFeedHandler
- Added CoinbaseProFeedHandler
- Added BinanceFeedHandler
- Critical fixes for Tickstore bi-temporal index logic
- Upgraded to Tau 0.3.0

0.0.3 (2020-04-19)
+++++++++++++++++++

- Added new generic FeedHandler API
- Implemented PhemexFeedHandler
- Converted Phemex tick upload job to Kubernetes CronJob
- Moved Tickstore and Journal from serenity.mdrecorder to serenity.tickstore
- Critical fix for buy/sell code mapping in Phemex feed
- Upgraded to pandas 1.0.3

0.0.2 (2020-04-13)
+++++++++++++++++++

- Fixed dependencies in setup.py

0.0.1 (2020-04-13)
+++++++++++++++++++

- Initial implementation
