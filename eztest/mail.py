"""Send email."""
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from . import utility


class Mail:
    __slots__ = ['server', 'port', 'timeout', 'key_file', 'cert_file', 'is_ssl',
                 'from_addr', 'to_addrs', 'cc_addrs', 'bcc_addrs', 'subject',
                 'username', 'password', 'need_authentication', 'is_html']

    def __init__(self, server=None, port=25):
        """Init.

        :param str server: mail server name.
        :param int port: port number.
        """
        self.server = server
        self.port = port
        self.timeout = 30
        self.key_file=None
        self.cert_file=None
        self.is_ssl = False
        
        self.from_addr = None
        self.to_addrs = None
        self.cc_addrs = None
        self.bcc_addrs = None

        self.subject = None
        self.username = None
        self.password = None

        self.need_authentication = False

        self.is_html = False

    @classmethod
    def _add_attachment(cls, file_path, msg):
        """Add attachment to message.

        :param str file_path: File path.
        :param MIMEMultipart msg: message.
        """
        if not os.path.isabs(file_path):
            file_path = os.path.normpath(os.path.join(os.getcwd(), file_path))
        if not os.path.isfile(file_path):
            return
        part = MIMEBase('application', 'octet-stream')
        with open(file_path, 'rb') as fp:
            part.set_payload(fp.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
        msg.attach(part)

    def send(self, subject, body=None, attachments=None):
        """Send mail.

        :param str subject: Subject.
        :param str body: Body.
        :param list|str attachments: Attachments.
        """
        if not self.server:
            raise ValueError('Should set SMTP server and port first.')

        if not self.from_addr or not self.to_addrs:
            raise ValueError('Should set email information of from_addr and to_addrs.')

        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = ','.join(self.to_addrs) if isinstance(self.to_addrs, list) else self.to_addrs
        if self.to_addrs:
            msg['CC'] = ','.join(self.to_addrs) if isinstance(self.to_addrs, list) else self.to_addrs
        if self.bcc_addrs:
            msg['BCC'] = ','.join(self.bcc_addrs) if isinstance(self.bcc_addrs, list) else self.bcc_addrs
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)

        if body:
            msg.attach(MIMEText(body, 'html') if self.is_html else MIMEText(body, 'plain'))

        if attachments:
            if isinstance(attachments, list):
                for f in attachments:
                    self._add_attachment(f, msg)
            else:
                self._add_attachment(attachments, msg)
        if self.is_ssl:
            s = smtplib.SMTP_SSL(host=self.server, port=int(self.port or 0), timeout=int(self.timeout),
                                 keyfile=self.key_file, certfile=self.cert_file)
        else:
            s = smtplib.SMTP(host=self.server, port=int(self.port or 0), timeout=int(self.timeout))
        if utility.to_boolean(self.need_authentication) and self.username and self.password:
            s.login(self.username, self.password)
        s.sendmail(from_addr=self.from_addr,
                   to_addrs=self.to_addrs if isinstance(self.to_addrs, list) else self.to_addrs.split(','),
                   msg=msg.as_string())
        s.quit()
