Project
-------
eztest

A Python package used for performance/load testing.

Home page: <https://github.com/lgt1001/eztest>

Features:
(a)0 or normal: Run selected cases only once.
(b)1 or continuous: Run cases [repeat] times with [interval] seconds' sleeping.
(c)2 or simultaneous: Start [stress] threads and run cases in each thread, sleep [interval] seconds after all cases are finished, and then start testing again with [repeat] times.
(d)3 or concurrency: Start [stress] threads and each thread will continuously run cases with [interval] seconds' sleeping.
(e)4 or frequent: Start [stress] threads per [interval] seconds and do this [repeat] times. And only can have [limit] available threads running.

Prerequisites:
* C Python 2.7 or higher.

Authors
-------
lgt

License
-------
GNU GPL v2, see http://www.gnu.org/licenses/gpl-2.0.html
