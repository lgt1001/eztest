"""Test mode:

Normal Test: Run self.cases one by one.

Continuous Test:
    a. Start to run self.cases one by one;
    b. After all cases are finished, sleep <interval_seconds> seconds to release resources;
    c. Repeat #a and #b with <repeat_times> times.

Simultaneous Test:
    a. Start <thread_count> threads;
    b. Run self.cases one by one in each thread;
    c. After all cases and threads are finished, sleep <interval_seconds> seconds to release resources;
    d. Repeat #a, #b and #c with <repeat_times> times.

ConcurrencyTest Test:
    a. Start <thread_count> threads;
    b. In each thread, do:
        b.1 Run self.cases one by one;
        b.2 After all cases are finished, sleep <interval_seconds> seconds to release resources;
        b.3 Repeat #b.1 and #b.2 with <repeat_times> times.

Frequent Test:
    a. Start <thread_count> threads per <interval_seconds> seconds, and run self.cases one by one in each thread.
    Note: only have <max_thread_count> running if it is set.
"""
import copy
import datetime
import os
import threading
import time
import traceback
import zipfile

from . import utility
from .testcase import BaseCase

NORMAL = 0
CONTINUOUS = 1
SIMULTANEOUS = 2
CONCURRENCY = 3
FREQUENT = 4


class NormalTest(object):
    """Normal Test:
    Run self.cases one by one.

    All cases should inherit from testcase.BaseCase.
    """
    __slots__ = ['cases', 'setup', 'teardown', 'no_report', 'report_folder', 'mail', 'additional_report_header',
                 'test_mode', 'starts_time', 'ends_time', '_mutex', '_stop_test_timer', '_f', '_report_path',
                 'is_cancelled', 'round_finished', 'round_started']

    def __init__(self):
        self.cases = []
        self.setup = None
        self.teardown = None
        self.no_report = False
        self.report_folder = "reports"
        self.mail = None
        self.additional_report_header = []
        self.test_mode = NORMAL
        self.starts_time = None
        self.ends_time = None

        self._mutex = threading.Lock()
        self._stop_test_timer = None
        self._f = None
        self._report_path = None
        self.is_cancelled = False
        self.round_finished = 0
        self.round_started = 0

    def process_finished(self):
        """Process after testing is finished: close report file, send mail, invoke teardown function."""
        if self._f is not None and (not self._f.closed):
            self._f.close()
        if self.mail is not None:
            print("-" * 80)
            print("Sending email...")
            dtnow = datetime.datetime.now()
            report_fname = os.path.basename(self._report_path)
            report_zipname = '{}_{}.zip'.format(os.path.splitext(report_fname)[0], dtnow.strftime('%Y%m%d%H%M%S'))
            is_file_compressed = False
            try:
                with zipfile.ZipFile(report_zipname, 'w') as myzip:
                    myzip.write(self._report_path, report_fname)
                is_file_compressed = True
                self.mail.send(subject='{}. {}'.format(self.mail.subject, dtnow.strftime('%Y-%m-%d %H:%M:%S')),
                               attachments=report_zipname)
            except Exception:
                traceback.print_exc()
            finally:
                if is_file_compressed:
                    try:
                        os.remove(self._report_path)
                    except:
                        pass
        print("-" * 80)
        if self.teardown:
            self.teardown()
        print("Completed all test cases!")

    def case_finished(self, case):
        """Process after case is finished: log output from case to report file.

        :param BaseCase case: case."""
        msg = ""
        for message in case.output_messages:
            msg += (message.replace('"', '""') if message else "") + "\n"
        tt = case.get_time_taken()
        report_msg = '''"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"''' % (
            case.repeat_index, case.id,
            case.description.replace('"', '""') if case.description else "",
                            "Pass" if case.status else "Fail",
            case.expected.replace('"', '""') if case.expected else "",
            case.received.replace('"', '""') if case.received else "",
            msg, utility.date2str(case.start_datetime), utility.date2str(case.end_datetime),
            tt if tt is not None else "",
            case.log_path if case.log_path else "")
        if case.additional_messages:
            for message in case.additional_messages:
                report_msg += ',"%s"' % (str(message).replace('"', '""') if message is not None else "")
        report_msg += "\n"
        with self._mutex:
            if self._f:
                self._f.write(report_msg)
                self._f.flush()

    def run_cases(self, cases):
        """Run cases in sequence.

        :param list cases: cases."""
        for case in cases:
            if self.is_cancelled:
                break
            if case is not None:
                if hasattr(case, "on_finished"):
                    case.on_finished = self.case_finished
                case.do_case()
        with self._mutex:
            self.round_finished += 1

    def cancel(self):
        """Cancel testing."""
        self.is_cancelled = True
        print("Cancelled at %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

    def stop_test(self):
        """Stop testing."""
        self._stop_test_timer.cancel()
        self._stop_test_timer = None
        self.cancel()

    def start_test(self):
        """Start testing."""
        print("Starting testing...")
        self.round_started = len(self.cases)
        try:
            self.run_cases(self.cases)
        except Exception:
            print("-" * 80)
            traceback.print_exc()
        finally:
            self.process_finished()

    def reset(self):
        """Reset: cancel existed testing, clean captured data."""
        self.is_cancelled = False
        self.round_finished = 0
        self.round_started = 0

    def run(self):
        """Do all cases in self.cases. All cases should inherit from BaseCase."""
        if len(self.cases) > 0:
            self.reset()
            try:
                if not self.no_report:
                    if not os.path.exists(self.report_folder):
                        os.mkdir(self.report_folder)
                    self._report_path = os.path.join(
                        self.report_folder, "report_%s.csv" % datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"))
                    f = open(self._report_path, 'w')
                    f.write('"Repeat Index","Id","Description","Status","Expected","Received","Output",'
                            '"Starts DateTime","Ends DateTime","E2E Taken","Log Path"')
                    if self.additional_report_header:
                        for h in self.additional_report_header:
                            f.write(',%s' % h)
                    f.write("\n")
                    self._f = f
                if self.starts_time:
                    print("Waiting until %s..." % self.starts_time)
                    total_seconds = (self.starts_time - datetime.datetime.now()).total_seconds()
                    if total_seconds > 0:
                        time.sleep(total_seconds)
                if self.ends_time:
                    print("Will be stopped at %s..." % self.ends_time)
                    total_seconds = (self.ends_time - datetime.datetime.now()).total_seconds()
                    if total_seconds > 0:
                        self._stop_test_timer = threading.Timer(total_seconds, self.stop_test)
                        self._stop_test_timer.start()
                    else:
                        return
                if self.setup:
                    self.setup()
                print("-" * 80)
                self.start_test()
            except Exception:
                print("-" * 80)
                traceback.print_exc()


class ContinuousTest(NormalTest):
    """Continuous Test:
    a. Start to run self.cases one by one;
    b. After all cases are finished, sleep <interval_seconds> seconds to release resources;
    c. Repeat #a and #b with <repeat_times> times.

    All cases should inherit from testcase.BaseCase.
    """
    __slots__ = ['cases', 'setup', 'teardown', 'no_report', 'report_folder', 'mail', 'additional_report_header',
                 'test_mode', 'starts_time', 'ends_time', '_mutex', '_stop_test_timer', '_f', '_report_path',
                 'is_cancelled', 'round_finished', 'round_started',
                 'repeat_times', 'interval_seconds', 'current_round']

    def __init__(self):
        super(ContinuousTest, self).__init__()
        self.repeat_times = 1
        self.interval_seconds = 0
        self.current_round = 0
        self.test_mode = CONTINUOUS

    def start_test(self):
        """Start Continuous testing."""
        try:
            for rp1 in range(self.repeat_times):
                self.current_round = rp1
                print("Starting (%d) round..." % rp1)
                new_cases = []
                for c in self.cases:
                    c2 = copy.deepcopy(c)
                    c2.repeat_index = rp1
                    new_cases.append(c2)
                self.round_started += 1
                self.run_cases(new_cases)
                if self.interval_seconds > 0:
                    time.sleep(self.interval_seconds)
        except Exception:
            print("-" * 80)
            traceback.print_exc()
        finally:
            self.process_finished()

    def reset(self):
        """Reset: cancel existed testing, clean captured data."""
        super(ContinuousTest, self).reset()
        self.current_round = 0


class SimultaneousTest(ContinuousTest):
    """Simultaneous Test:
    a. Start <thread_count> threads;
    b. Run self.cases one by one in each thread;
    c. After all cases and threads are finished, sleep <interval_seconds> seconds to release resources;
    d. Repeat #a, #b and #c with <repeat_times> times.

    All cases should inherit from testcase.BaseCase.
    """
    __slots__ = ['cases', 'setup', 'teardown', 'no_report', 'report_folder', 'mail', 'additional_report_header',
                 'test_mode', 'starts_time', 'ends_time', '_mutex', '_stop_test_timer', '_f', '_report_path',
                 'is_cancelled', 'round_finished', 'round_started',
                 'repeat_times', 'interval_seconds', 'current_round',
                 'thread_count', '_repeat_capture_timer', 'is_repeat_started']

    def __init__(self):
        super(SimultaneousTest, self).__init__()
        self.thread_count = 1
        self._repeat_capture_timer = None
        self.is_repeat_started = False
        self.test_mode = SIMULTANEOUS

    def repeat_capture_timer_method(self):
        """Timer callback method: start next round of Simultaneous testing."""
        run_required = False
        if self.current_round >= self.repeat_times:
            if self.round_finished >= self.round_started:
                self._repeat_capture_timer.cancel()
                self.process_finished()
                return
        elif self.is_repeat_started:
            if self.round_finished >= self.round_started:
                if self.interval_seconds > 0:
                    time.sleep(self.interval_seconds)
                run_required = True
        else:
            run_required = True
        if run_required:
            print("Starting (%d) round..." % self.current_round)
            tds = []
            for i in range(self.thread_count):
                new_cases = []
                for c in self.cases:
                    c2 = copy.deepcopy(c)
                    c2.is_under_stress_test = True
                    c2.repeat_index = self.current_round
                    new_cases.append(c2)
                td = threading.Thread(target=self.run_cases, args=(new_cases,))
                tds.append(td)
            for td in tds:
                if self.is_cancelled:
                    return
                self.round_started += 1
                td.start()
            self.current_round += 1
            self.is_repeat_started = True
        self._repeat_capture_timer = threading.Timer(1, self.repeat_capture_timer_method)
        self._repeat_capture_timer.start()

    def start_test(self):
        """Start Simultaneous testing."""
        self._repeat_capture_timer = threading.Timer(1, self.repeat_capture_timer_method)
        self._repeat_capture_timer.start()

    def reset(self):
        """Reset: cancel existed testing, clean captured data."""
        super(SimultaneousTest, self).reset()
        self.is_repeat_started = False


class ConcurrencyTest(NormalTest):
    """ConcurrencyTest Test:
    a. Start <thread_count> threads;
    b. In each thread, do:
        b.1 Run self.cases one by one;
        b.2 After all cases are finished, sleep <interval_seconds> seconds to release resources;
        b.3 Repeat #b.1 and #b.2 with <repeat_times> times.

    All cases should inherit from testcase.BaseCase.
    """
    __slots__ = ['cases', 'setup', 'teardown', 'no_report', 'report_folder', 'mail', 'additional_report_header',
                 'test_mode', 'starts_time', 'ends_time', '_mutex', '_stop_test_timer', '_f', '_report_path',
                 'is_cancelled', 'round_finished', 'round_started',
                 'thread_count', 'interval_seconds', '_mutex_count', '_count_capture_timer']

    def __init__(self):
        super(ConcurrencyTest, self).__init__()
        self.thread_count = 1
        self.interval_seconds = 0
        self._mutex_count = threading.Lock()
        self._count_capture_timer = None
        self.test_mode = CONCURRENCY

    def _do_in_thread(self):
        """Continuously run cases in each thread."""
        rpi = 0
        while not self.is_cancelled:
            new_cases = []
            for c in self.cases:
                c2 = copy.deepcopy(c)
                c2.is_under_stress_test = True
                c2.repeat_index = rpi
                new_cases.append(c2)
            rpi += 1
            with self._mutex_count:
                self.round_started += 1
            self.run_cases(new_cases)
            if self.interval_seconds > 0:
                time.sleep(self.interval_seconds)

    def _count_capture_timer_method(self):
        """Timer callback method: start next round of Concurrency testing."""
        if self.round_finished >= self.round_started:
            self._count_capture_timer.cancel()
            self.process_finished()
        else:
            self._count_capture_timer = threading.Timer(1, self._count_capture_timer_method)
            self._count_capture_timer.start()

    def start_test(self):
        """Start Concurrency testing."""
        tds = []
        for i in range(self.thread_count):
            td = threading.Thread(target=self._do_in_thread)
            tds.append(td)
        for td in tds:
            if self.is_cancelled:
                return
            td.start()
        self._count_capture_timer = threading.Timer(1, self._count_capture_timer_method)
        self._count_capture_timer.start()


class FrequentTest(NormalTest):
    """Frequent Test:
    a. Start <thread_count> threads per <interval_seconds> seconds, and run self.cases one by one in each thread.

    Note: only have <max_thread_count> running if it is set.

    All cases should inherit from testcase.BaseCase.
    """
    __slots__ = ['cases', 'setup', 'teardown', 'no_report', 'report_folder', 'mail', 'additional_report_header',
                 'test_mode', 'starts_time', 'ends_time', '_mutex', '_stop_test_timer', '_f', '_report_path',
                 'is_cancelled', 'round_finished', 'round_started', 'current_round',
                 'interval_seconds', 'thread_count', '_repeat_capture_timer',
                 'max_thread_count', 'thread_started', 'thread_finished']

    def __init__(self):
        super(FrequentTest, self).__init__()
        self.thread_count = 1
        self.current_round = 0
        self.max_thread_count = 0
        self.thread_started = 0
        self.thread_finished = 0
        self.test_mode = FREQUENT

    def reset(self):
        """Reset: cancel existed testing, clean captured data."""
        super(FrequentTest, self).reset()
        self.thread_started = 0
        self.thread_finished = 0

    def run_cases(self, cases):
        """Run cases in sequence.

        :param list cases: cases."""
        super(FrequentTest, self).run_cases(cases)
        self.thread_finished += 1

    def repeat_capture_timer_method(self):
        """Timer callback method: start next round of Frequent testing."""
        if self.is_cancelled:
            if self.round_finished >= self.round_started:
                self._repeat_capture_timer.cancel()
                self.process_finished()
                return
        else:
            print("Starting (%d) round..." % self.current_round)
            if self.max_thread_count <= self.thread_count:
                available_count = self.thread_count
            else:
                available_count = self.max_thread_count - (self.thread_started - self.thread_finished)
                if available_count > self.thread_count:
                    available_count = self.thread_count
            tds = []
            for i in range(available_count):
                new_cases = []
                for c in self.cases:
                    c2 = copy.deepcopy(c)
                    c2.is_under_stress_test = True
                    c2.repeat_index = self.current_round
                    new_cases.append(c2)
                td = threading.Thread(target=self.run_cases, args=(new_cases,))
                tds.append(td)
            for td in tds:
                if self.is_cancelled:
                    return
                self.round_started += 1
                td.start()
            self.current_round += 1
            self.thread_started += available_count
            print("Initialized %d threads" % available_count)

        self._repeat_capture_timer = threading.Timer(self.interval_seconds, self.repeat_capture_timer_method)
        self._repeat_capture_timer.start()

    def start_test(self):
        """Start Frequent testing."""
        if self.interval_seconds is None or self.interval_seconds < 1:
            self.interval_seconds = 1
        self.repeat_capture_timer_method()