Project
-------
eztest

A Python package used for performance/load testing.

Home page: <https://github.com/lgt1001/eztest>

Features
--------
- Normal: Run selected cases only once.
- Continuous: Run cases [repeat] times with [interval] seconds' sleeping.
- Simultaneous: Start [stress] threads and run cases in each thread, sleep [interval] seconds after all cases are finished, and then start testing again with [repeat] times.
- Concurrency: Start [stress] threads and each thread will continuously run cases with [interval] seconds' sleeping.
- Frequent: Start [stress] threads per [interval] seconds and do this [repeat] times. And only can have [limit] available threads running.

Prerequisites
--------
- C Python 2.7 or higher.

Authors
-------
lgt

License
-------
GNU GPL v2, see http://www.gnu.org/licenses/gpl-2.0.html
