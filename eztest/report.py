"""Report server and report handler."""
import datetime
import importlib
import os
import re
import socket
import sys
import traceback

from eztest import calc_report, utility

try:
    from _collections import OrderedDict
except ImportError:
    from collections import OrderedDict

try:
    import cPickle as pickle
except ImportError:
    import pickle


class ReportBaseHandler(object):
    """Base report handler."""
    def __init__(self):
        self.group_summary = OrderedDict()
        self.case_summary = dict()
        self.start_times = dict()
        self.group_gap = datetime.timedelta(seconds=3600)

    def write(self, case_result):
        """Add case result to summary.

        :param dict case_result: case result.
            {
                "repeat_index": int(...),
                "id": "case id",
                "description": "case description",
                "status": bool(...),  # True or False
                "expected": "output expected",
                "received": "output received",
                "output_messages": [...],   # other output messages
                "start_time": datetime.datetime(...),   # start datetime
                "end_time": datetime.datetime(...), # end datetime
                "time_taken": float(...)  # time taken
            )
        """
        calc_report.analyze_case(
            case_id=case_result['id'],
            is_pass=case_result['status'],
            start_date=case_result['start_time'],
            end_date=case_result['end_time'],
            time_taken=case_result['time_taken'],
            case_summary=self.case_summary,
            start_times=self.start_times,
            group_summary=self.group_summary,
            group_gap=self.group_gap
        )

    def dump(self):
        """Dump summary.

        :return str: summary.
        """
        if self.group_summary:
            return calc_report.output_summary(case_summary=self.case_summary,
                                              group_summary=self.group_summary,
                                              group_gap=self.group_gap)
        else:
            return 'No data found.'


class ReportFileHandler(ReportBaseHandler):
    """Report handler which will save case result into CSV file."""
    def __init__(self):
        super(ReportFileHandler, self).__init__()
        self.report_folder_name = 'reports'
        self.filename = 'report.csv'
        self.max_bytes = 10485760
        self.file_index = 1
        self._stream = None

    def _open(self):
        """Create and open report file.

        :return: file object.
        """
        stream = open(os.path.join(self.report_folder_name, self.filename), 'a', encoding='utf-8')
        stream.write('"Repeat Index","Id","Description","Status","Expected","Received","Output","Starts DateTime","Ends DateTime","E2E Taken"\n')
        stream.flush()
        return stream

    def should_rollover(self, message):
        """Check whether need to do roll over.

        :param str message: message
        :return bool: True or False.
        """
        if self._stream is None:
            if os.path.exists(self.report_folder_name):
                os.rename(self.report_folder_name, '{}_{}'.format(self.report_folder_name, datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
            os.mkdir(self.report_folder_name)
            self._stream = self._open()
        else:
            self._stream.seek(0, 2)  #due to non-posix-compliant Windows feature
            if self._stream.tell() + len(message) >= self.max_bytes:
                return True
        return False

    def do_rollover(self):
        """Do file roll over."""
        if self._stream:
            self._stream.close()
            self._stream = None
        source = os.path.join(self.report_folder_name, self.filename)
        destination = '{}.{}'.format(source, self.file_index)
        if os.path.exists(source):
            os.rename(source, destination)
            self.file_index += 1
        self._stream = self._open()

    @classmethod
    def format(cls, case_result):
        """Format case result.

        :param dict case_result: case result.
            {
                "repeat_index": int(...),
                "id": "case id",
                "description": "case description",
                "status": bool(...),  # True or False
                "expected": "output expected",
                "received": "output received",
                "output_messages": [...],   # other output messages
                "start_time": datetime.datetime(...),   # start datetime
                "end_time": datetime.datetime(...), # end datetime
                "time_taken": float(...)  # time taken
            )
        :return str: case output.
        """
        output_messages = '\n'.join(
            utility.csv_format(message) for message in case_result.get('output_messages', [])
        )
        return '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (
            case_result['repeat_index'],
            case_result['id'],
            utility.csv_format(case_result['description']),
            'Pass' if case_result['status'] else 'Fail',
            utility.csv_format(case_result['expected']),
            utility.csv_format(case_result['received']),
            output_messages,
            utility.date2str(case_result['start_time']),
            utility.date2str(case_result['end_time']),
            case_result['time_taken'])

    def write(self, case_result):
        """Write case result into report file.

        :param dict case_result: case result.
        """
        message = self.format(case_result)
        if self.should_rollover(message):
            self.do_rollover()
        self._stream.write(message)
        self._stream.flush()
        super(ReportFileHandler, self).write(case_result)


def start_udp_report_server(port=8765, handler_name=None):
    """Start report server.

    :param int port: report server port number.
    :param str handler_name: handler_file_path:handler_class_name  or handler_module_name:handler_class_name.
    """
    _socket = None
    try:
        if handler_name:
            fname, hanname = handler_name.split(':')
            if os.path.isfile(fname):
                mymodule = utility.import_module(fname)
            else:
                m_name = re.sub(r'[/\\]', '.', fname).strip('.')
                try:
                    mymodule = importlib.import_module(m_name)
                except(SystemError, ImportError):
                    sys.path.append(os.getcwd())
                    mymodule = importlib.import_module(m_name)
            handler = getattr(mymodule, hanname)()
        else:
            handler = ReportFileHandler()
        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _socket.bind(('', port))
        print('Serving UDP on port:%s...' % port)
        while True:
            try:
                data, client = _socket.recvfrom(65535)
                if data == b'dump':
                    _socket.sendto(handler.dump().encode('utf-8'), client)
                else:
                    handler.write(pickle.loads(data))
            except Exception:
                traceback.print_exc()
    except Exception:
        traceback.print_exc()
    finally:
        _socket.close()
