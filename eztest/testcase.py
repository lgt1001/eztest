"""Test case class."""
import datetime
import os
import re
import sys
import traceback
import uuid

from . import utility, stringbuilder

INFO = "INFO"
WARNING = "WARN"
ERROR = "ERROR"


class BaseCase(object):
    """A abstract class used for sending request to web service and getting response."""
    def __init__(self):
        """Init."""
        self.description = None
        self.id = None
        self.repeat_index = 0

        self.no_log = True
        self.log_folder = "reports"
        self._file = None
        self.log_path = None

        self.received = None
        self.expected = None
        self.output_messages = []
        self.additional_messages = []

        self.status = None
        self.on_finished = None
        self.start_datetime = None
        self.end_datetime = None
        self.time_taken = None
        self.is_under_stress_test = False

    def __eq__(self, other):
        if isinstance(other, str):
            return utility.compare_str(self.id, other, True) == 0
        else:
            return self.id == other.id

    def __deepcopy__(self, obj):
        """Deep copy object.

        :param BaseCase obj: object.
        :return BaseCase: new object.
        """
        new = self.__class__()
        new.description = self.description
        new.id = self.id
        new.expected = self.expected
        new.no_log = self.no_log
        new.log_folder = self.log_folder
        new.output_messages = []
        new.additional_messages = []
        return new

    def get_time_taken(self):
        """Get time taken.

        :return float: time taken in seconds.
        """
        if self.time_taken is None and self.start_datetime is not None and self.end_datetime is not None:
            self.time_taken = utility.total_seconds(self.start_datetime, self.end_datetime)
        return self.time_taken

    def log(self, message, to_console=False, level=INFO, no_format=False):
        """Output log message to file or console.

        :param str message: message.
        :param bool to_console: print to console.
        :param str level: log level.
        :param bool no_format: print log message without format, otherwise the format will be "datetime level message"
        """
        if message is None:
            return
        msg = "%s\t%s\t%s" % (datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S.%f"), level, message) if not no_format else str(message)
        if to_console:
            print(msg)
        if not self.no_log and self._file:
            self._file.write(msg + "\n")
            self._file.flush()

    def initialize(self):
        """Do some preparation before run this case.

        :return bool: will not call "run" if it is False."""
        return True

    def run(self):
        """Run this case after prepared.

        :return bool: will not call "verify" if it is False."""
        return True

    def verify(self):
        """Verify received against expected. Set self.status after verification is done."""
        pass

    def dispose(self):
        """Release some resources, such as memory."""
        pass

    def generate_log(self):
        """Generate log file."""
        if not os.path.exists(self.log_folder):
            os.mkdir(self.log_folder)
        filename = "log_%s_%s.txt" % (self.id, uuid.uuid1())
        self.log_path = os.path.join(self.log_folder, re.sub(r'[^\w_\\.-]', '', filename))
        self._file = open(self.log_path, 'w')

    def print_tb(self, tb, sb):
        """Print up to 'limit' stack trace entries from the traceback 'tb'.

        If 'limit' is omitted or None, all entries are printed.  If 'file'
        is omitted or None, the output goes to sys.stderr; otherwise
        'file' should be an open file or file-like object with a write()
        method.
        """
        import linecache
        limit = None
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
        n = 0
        tb = tb.tb_next
        while tb is not None and (limit is None or n < limit):
            f = tb.tb_frame
            lineno = tb.tb_lineno
            co = f.f_code
            filename = co.co_filename
            name = co.co_name
            sb.append_line('  File "%s", line %d, in %s' % (filename, lineno, name))
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, f.f_globals)
            if line:
                sb.append_line('    ' + line.strip())
            tb = tb.tb_next
            n += 1

    def set_end_time(self):
        """Set end_datetime if it is not set."""
        if self.end_datetime is None:
            self.end_datetime = datetime.datetime.now()

    def set_status(self, value):
        if self.status is None:
            self.status = value

    def log_exception(self):
        """Log exception"""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sb = stringbuilder.StringBuilder()
        sb.append_line("Traceback (most recent call last): ")
        self.print_tb(exc_traceback, sb)
        lines = traceback.format_exception_only(exc_type, exc_value)
        for line in lines:
            sb.append_line(line)
        msg = sb.to_string().rstrip('\n')
        self.log(msg, True)
        self.output_messages.append(msg)

    def do_case(self):
        """Will call initialize, run if initialize is True, verify if run is True, and dispose in sequence."""
        if not self.no_log:
            self.generate_log()
        try:
            flag = self.initialize()
            if flag is None or flag:
                self.start_datetime = datetime.datetime.now()
                flag = self.run()
                self.set_end_time()
                if flag is None or flag:
                    self.verify()
                    self.set_status(True)
                else:
                    self.set_status(False)
            else:
                self.set_status(False)
        except Exception:
            self.set_end_time()
            self.status = False
            self.log_exception()
        finally:
            try:
                self.dispose()
            except Exception:
                pass
            self.log("-" * 40, True)
            if self.status:
                self.log("Case[%s] is Pass." % self.id, True)
            else:
                self.log("Case[%s] is Fail." % self.id, True)
            if self._file is not None and (not self._file.closed):
                self._file.close()
            if self.on_finished:
                self.on_finished(self)

    @classmethod
    def setup(cls):
        pass

    @classmethod
    def teardown(cls):
        pass
