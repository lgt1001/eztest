"""Internal Class for building case object for functions."""
import datetime
import sys

from .testcase import BaseCase, INFO


class BuildCase(BaseCase):
    """Build case for external function."""
    def __init__(self):
        super(BuildCase, self).__init__()

    def __deepcopy__(self, obj):
        new = super(BuildCase, self).__deepcopy__(obj)
        new.initialize = self.initialize
        new.run = self.run
        new.dispose = self.dispose
        return new

    def log(self, message, to_console=False, level=INFO, no_format=False):
        """Output log message to sys.stdout.

        :param str message: message.
        :param bool to_console: print to console.
        :param str level: log level.
        :param bool no_format: print log message without format, otherwise the format will be "datetime level message"
        """
        if message and to_console:
            msg = "%s\t%s\t%s" % (datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S.%f"), level, message) if not no_format else str(message)
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()

    def do_case(self):
        """Will call initialize, run if initialize is True, verify if run is True, and dispose in sequence."""
        try:
            flag = self.initialize()
            if flag is None or flag:
                self.start_datetime = datetime.datetime.now()
                self.run()
                self.end_datetime = datetime.datetime.now()
                self.set_status(True)
            else:
                self.set_status(False)
        except Exception:
            self.end_datetime = datetime.datetime.now()
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
            if self.on_finished:
                self.on_finished(self)
