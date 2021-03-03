import gzip
import logging
import logging.handlers
from copy import copy
import sys

try:
    import colorama
    is_win = sys.platform == 'win32'
    stream_logger = colorama.AnsiToWin32(sys.stdout, convert=is_win, strip=is_win).stream
except ImportError:
    stream_logger = sys.stdout

from six.moves.urllib.error import URLError
import os
import time
from multiprocessing import current_process

import zmq
import pickle

raven_available = True
try:
    from raven import Client
    from raven.handlers.logging import SentryHandler
except ImportError:
    raven_available = False
    Client = None
    SentryHandler = None

logger = logging.getLogger(__name__)

STATISTICS = 21
NOTIFICATION = 25

LOG_FORMAT = '%(asctime)s %(relativeCreated)8g %(levelname)-16s %(processName)8s ' \
             '%(threadName)s %(filename)s:%(lineno)d: %(message)s'

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = [30+c for c in range(8)]

# These are the sequences need to get colored output
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[%dm"

COLORS = {
    'WARNING': YELLOW,
    'INFO': CYAN,
    'STATISTICS': MAGENTA,
    'DEBUG': GREEN,
    'CRITICAL': BLUE,
    'ERROR': RED,
    'NOTIFICATION': BLACK
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt, use_color=True, date_fmt=None):
        logging.Formatter.__init__(self, fmt, date_fmt)
        self.use_color = use_color

    def format(self, record):
        r = copy(record)
        if self.use_color and record.levelname in COLORS:
            r.msg = COLOR_SEQ % COLORS[r.levelname] + r.msg + RESET_SEQ
            r.levelname = "{}{}{}".format(COLOR_SEQ % COLORS[r.levelname], r.levelname, RESET_SEQ)
        return logging.Formatter.format(self, r)


def epoch_time(record, datefmt=None):
    ret_data = int(record.created)*1000 + int(record.msecs)
    print("ret_data = {0}".format(ret_data))
    return ret_data


class TimedCompressedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
            # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)
        if os.path.exists(dfn):
            os.remove(dfn)
        os.rename(self.baseFilename, dfn)

        data = open(dfn, 'rb')
        gz_data = gzip.open(dfn+'.gz', 'wb')
        gz_data.writelines(data)
        gz_data.close()
        data.close()
        os.remove(dfn)

        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        self.mode = 'w'
        self.stream = self._open()
        current_time = int(time.time())
        new_rollover_time = self.computeRollover(current_time)
        while new_rollover_time <= current_time:
            new_rollover_time = new_rollover_time + self.interval
            # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_now = time.localtime(current_time)[-1]
            dst_at_rollover = time.localtime(new_rollover_time)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    new_rollover_time -= 3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    new_rollover_time += 3600
        self.rolloverAt = new_rollover_time


def remove_handler_if_existing(hdlr, logging_root=''):
    logger_instance = logging.getLogger(logging_root)
    found = False
    for h in logger_instance.handlers:
        if h.get_name() == hdlr.get_name():
            logger_instance.removeHandler(h)
            found = True
    return found


def add_file_logger(dir_name, file_name, log_level, logging_root='', backup_count=90):
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    fh = TimedCompressedRotatingFileHandler("{dir}{sep}{file}".format(dir=dir_name, sep=os.sep,
                                                                      file=file_name),
                                            when='midnight', backupCount=backup_count)
    formatter = ColoredFormatter(LOG_FORMAT)
    fh.setFormatter(formatter)
    fh.setLevel(log_level)
    fh.set_name('TimedCompressedRotatingFileHandler')
    remove_handler_if_existing(fh, logging_root)
    logging.getLogger(logging_root).addHandler(fh)


class AuthenticatedHTTPSHandler(logging.handlers.HTTPHandler):
    """
    A class which sends records to a Web server, using either GET or
    POST semantics, with an authentication header.
    """
    # There's no easy way to extend logging.handlers.HTTPHandler.emit(),
    # so this is a modified copy.  Yuck.
    # AuthenticatedHTTPHandler(proxy_servers, o.netloc, o.path, method='POST')
    def __init__(self, host, url, method="GET", *args, **kwargs):
        import requests
        super(AuthenticatedHTTPSHandler, self).__init__(*args, **kwargs)
        # TODO Make surer verify cert is supported; self.session.verify = verify_cert
        self.full_url = "https://" + self.host + self.url
        self.session = requests.session()
        self.formatter = logging.Formatter()

    def emit(self, record):
        """
        Emit a record.

        Send the record to the Web server as a percent-encoded dictionary
        """
        try:
            record_map = self.mapLogRecord(record)
            notification = None
            if 'notification' in record_map:
                notification = record_map.pop('notification')  # This causes
                # issues, so I'm removing it.
            if notification:
                record_map['notification'] = notification
            if 'exc_info' in record_map and record_map['exc_info']:
                record_map['exc_text'] = self.formatter.formatException(
                    record_map['exc_info']) + '\n'
            try:
                if self.method == "GET":
                    self.session.get(self.full_url, params=record_map, timeout=5)
                elif self.method == "PUT":
                    self.session.put(self.full_url, params=record_map, timeout=5)
                elif self.method == "POST":
                    rep = self.session.post(self.full_url, record_map, timeout=5)
                    rep.raise_for_status()

            except Exception as e:
                pass

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def mapLogRecord(self, record):
        """
        Default implementation of mapping the log record into a dict
        that is sent as the CGI data. Overwrite in your class.
        Contributed by Franz Glasner.
        """
        return record.__dict__


class PUBHandler(logging.Handler):
    """
    Use this handler to send raw records to the logging process over ZMQ
    """
    def __init__(self, port):
        super(PUBHandler, self).__init__()
        ctx = zmq.Context()
        self.pub = ctx.socket(zmq.PUB)
        self.pub.setsockopt(zmq.LINGER, 0)
        self.pub.connect('tcp://127.0.0.1:{}'.format(port))

    def emit(self, record):
        rec = self.make_pickle(record)
        self.pub.send(rec)

    @staticmethod
    def make_pickle(record):
        """
        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        Stolen from SocketHandler and modified to work for our purposes.
        """
        ei = record.exc_info
        if ei:
            # just to get traceback text into record.exc_text ...
            record.exc_info = None  # to avoid Unpickleable error
        # See issue #14436: If msg or args are objects, they may not be
        # available on the receiving end. So we convert the msg % args
        # to a string, save it as msg and zap the args.
        d = dict(record.__dict__)
        d['msg'] = record.getMessage()
        d['args'] = None
        s = pickle.dumps(d, 1)
        if ei:
            record.exc_info = ei  # for next handler
        return s


def add_http_logger(host, url, method, logging_level=logging.INFO, logging_root=''):
    the_logger = logging.getLogger(logging_root)
    try:
        # dont allow the requests library to propagate down
        requests_log = logging.getLogger("requests")
        requests_log.propagate = False

        # TODO: try to open the url to see if we have a connection
        the_logger.info("Initializing http logging")
        http_handler = AuthenticatedHTTPSHandler(host, url, method)
        http_handler.setLevel(logging_level)
        formatter = logging.Formatter(LOG_FORMAT)
        formatter.formatTime = epoch_time
        http_handler.setFormatter(formatter)

        # http_handler must be prepended, or else asctime gets added to record
        http_handler.set_name('HttpHandler')
        remove_handler_if_existing(http_handler)
        the_logger.handlers.insert(0, http_handler)
    except URLError as e:
        the_logger.exception("Unable to initialize http logger")
    except Exception as e:
        the_logger.exception("Unable to initialize http logger")


def initialize_console_logging(logging_root=''):
    try:
        logging.getLogger(logging_root).removeHandler(logging.getLogger(logging_root).handlers[0])
    except IndexError:
        pass
    logging.getLogger(logging_root).setLevel(logging.DEBUG)
    is_win = sys.platform == 'win32'
    console = logging.StreamHandler(stream_logger)
    console.setLevel(logging.DEBUG)
    console.setFormatter(ColoredFormatter(LOG_FORMAT, date_fmt="%m/%d %H:%M:%S"))
    console.set_name("console")
    logging.getLogger(logging_root).addHandler(console)


def initialize_zmq_logging(port, logging_root=''):
    logging.addLevelName(STATISTICS, 'STATISTICS')
    logging.addLevelName(NOTIFICATION, 'NOTIFICATION')
    thelogger = logging.getLogger(logging_root)
    thelogger.setLevel(logging.DEBUG)

    handler = PUBHandler(port)
    handler.set_name("Motive-ZMQHandler")
    thelogger.addHandler(handler)


def initialize_sentry_logging(sentry_credentials, logging_level, logging_root=''):

    the_logger = logging.getLogger(logging_root)
    client = Client('http://{s.username}:{s.password}@{s.url}/{s.project}'.format(
        s=sentry_credentials))
    sentry_handler = SentryHandler(client)
    sentry_handler.setLevel(logging_level)
    sentry_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    sentry_handler.set_name('SentryHandler')
    remove_handler_if_existing(sentry_handler, logging_root)
    the_logger.handlers.append(sentry_handler)


def get_default_log_directory():
    default_log_dir = "/var/log/motive"
    if sys.platform == 'darwin':
        default_log_dir = "{0}/Library/Logs/motive".format(os.getenv("HOME"))
    elif os.name == 'nt':
        default_log_dir = "{base}{sep}motive{sep}logs".format(
            base=os.environ['ALLUSERSPROFILE'], sep=os.sep)
    try:
        os.makedirs(default_log_dir)
    except OSError as e:
        if e.errno == 17:
            pass
    if not os.access(default_log_dir, os.W_OK):
        default_log_dir = "{home}{sep}motive{sep}logs".format(home=os.getenv("HOME"),
                                                              sep=os.sep)
        try:
            os.makedirs(default_log_dir)
        except OSError as e:
            if e.errno == 17:
                pass

    return default_log_dir


def set_process_name(name, use_pid=True):
    if use_pid:
        current_process().name = "{0}-{1}".format(name, os.getpid())
    else:
        current_process().name = "{0}".format(name)


def initialize_additional_logging(file_log_directory,
                                  file_log_level=logging.INFO,
                                  sentry_log_level=logging.ERROR,
                                  sentry_credentials=None,
                                  http_log_info=None,
                                  logging_root=''):

    logging.addLevelName(STATISTICS, 'STATISTICS')
    logging.addLevelName(NOTIFICATION, 'NOTIFICATION')
    thelogger = logging.getLogger(logging_root)

    if file_log_level is not None:
        try:
            if not os.path.exists(file_log_directory):
                os.makedirs(file_log_directory)
            add_file_logger(dir_name=file_log_directory, file_name="motive.log",
                            logging_root=logging_root,
                            log_level=file_log_level)
        except Exception as e:
            logging.warn('Unable to initialize logger in %s: %s', file_log_directory, e.message)
            log_directory = "{home}{sep}MotiveLogs{sep}".format(home=os.getenv("HOME"), sep=os.sep)
            try:
                if not os.path.exists(log_directory):
                    os.makedirs(log_directory)
                add_file_logger(dir_name=log_directory,
                                file_name="motive.log",
                                log_level=file_log_level,
                                logging_root=logging_root)
                thelogger.warn('Logging to %s instead', log_directory)
            except Exception:
                thelogger.exception("Could not instantiate file logging")
    else:
        logging.info('File logging not enabled')

    if sentry_log_level is not None and sentry_credentials is not None and raven_available:
        try:
            initialize_sentry_logging(sentry_credentials, sentry_log_level, logging_root)
        except Exception:
            thelogger.exception("Could not initialize Sentry logger")
    else:
        thelogger.info("Sentry logger not enabled")

    if http_log_info is not None:
        try:
            add_http_logger(http_log_info.host, http_log_info.url, http_log_info.method,
                            http_log_info.logging_level, logging_root)
        except Exception:
            thelogger.exception("Could not initialize cloud logging")
    else:
        thelogger.info("Cloud logging not enabled")


class ClassInstanceLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        labels = ''
        for key, label in self.extra.items():
            labels += label + '.'
        return '[%s] %s' % (labels.rstrip('.'), msg), kwargs
