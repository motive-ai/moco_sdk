import inspect
import logging
import sys
import threading
import traceback
try:
    from queue import Queue, Empty, Full
except ImportError:
    from Queue import Queue, Empty
from collections import Counter
from datetime import datetime
from time import time
from datetime import timedelta

logger = logging.getLogger(__name__)


class TaskProcessor(object):
    """
        Wraps the python threading class with statistics and error handling.

        This is not a drop-in replacement for threads, as
    """
    class Stats(object):
        def __init__(self):
            self.num_times_run = 0
            self.run_duration = timedelta(seconds=0)
            self.all_exceptions = Counter()

        def get_stats(self):
            return dict(calls=self.num_times_run, total_duration=self.run_duration,
                        exception_count=sum(self.all_exceptions.values()))

        def reset_stats(self):
            self.__init__()

    def __init__(self, target, name=None):
        """Initializes the TaskProcessor

        :param target: the function that gets run at specific intervals.
        :param name: name for the underlying thread for statistics and debugging."""
        self._function = None

        self.function_return_value = None
        self.function_exception = None
        self._function_args = None

        self.last_execution_time = datetime.utcnow()
        self.last_execution_duration = timedelta(seconds=0)
        self.stats = TaskProcessor.Stats()
        self._event = threading.Event()
        self._worker = threading.Thread(target=self._run, name=name)
        self._worker.setDaemon(True)
        self.set_function(target)
        if name:
            self.name = name
        else:
            try:
                self.name = target.func_name
            except AttributeError:
                self.name = str(target)

    def set_function(self, func):
        if not func:
            raise Exception("{} received a null function".format(self.__class__.__name__))
        if not callable(func):
            raise Exception("{} received a non-callable function: {}".format(
                self.__class__.__name__, func))
        self._function = func

    def _run(self):
        """Internal function that runs the user function"""
        self.last_execution_time = datetime.utcnow()
        try:
            if self._function_args:
                self.function_return_value = self._function(*self._function_args)
            else:
                self.function_return_value = self._function()
        except (BaseException, Exception) as e:
            logger.exception("%s caught exception during processing of task", self.name)
            self.function_exception = e
            self.stats.all_exceptions[type(e)] += 1
            self._event.clear()
            self._event.wait(timeout=.1)  # sleep for one tenth of second after an exception
        finally:
            self.stats.num_times_run += 1
            self.last_execution_duration = datetime.utcnow() - self.last_execution_time
            self.stats.run_duration += self.last_execution_duration

    def start(self, *function_args):
        """start() starts up the worker thread with specified arguments"""
        if function_args:
            self._function_args = function_args
        self._worker.start()

    def set_args(self, *function_args):
        """Allows to update the arguments of the user function"""
        self._function_args = function_args

    def join(self, join_time=1.0):
        """Joins the user function. Will wait for join_time before returning.

        :param join_time: time in seconds that shutdown should wait for function to end
        :return: Boolean, True if function is still alive, False otherwise"""
        try:
            self._event.set()
        except AttributeError:
            return True
        try:
            self._worker.join(join_time)
        except RuntimeError:
            return True

        return not self._worker.isAlive()

    def shutdown(self, join_time=1.0):
        self.join(join_time)
        if self._worker.isAlive():
            logger.error("%s shut down halted for longer than timeout", self.name)
        else:
            logger.debug("%s shut down correctly.", self.name)

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        is_alive = "stopped"
        try:
            if self._worker.is_alive():
                is_alive = "running"
            return "<{} \"{}\" {} ({})>".format(self.__class__.__name__, self.name,
                                                self._function.__name__, is_alive)
        except AttributeError:
            return "<{} Invalid>".format(self.__class__.__name__)

    def __del__(self):
        self.shutdown(.1)


class QueueTaskProcessor(TaskProcessor):
    """
    A task queue that runs functions in a thread. Will run functions in serial FIFO order as
    given to add_task.
    """

    def __init__(self, name, max_queue_length=0):
        self._queue = Queue(max_queue_length)
        self._keep_going = True
        super(self.__class__, self).__init__(self._loop, name)
        self.start()

    def null_task(self):
        return

    def add_task(self, func, *function_args, **kw_args):
        """Adds a task to the thread owned by QueueTaskProcessor that runs asynchronously.

         :param func: -- the function to run
         :param function_args: -- a list of arguments, can be None
         """
        task = [func, function_args, kw_args]
        try:
            self._queue.put(task, block=False)
        except Full:
            pass
        return

    def get_queue_length(self):
        return self._queue.qsize()

    def _loop(self):
        while self._keep_going:
            try:
                task = self._queue.get(block=True, timeout=1.0)
            except Empty:
                continue
            r = task[0](*task[1], **(task[2]))
            self._queue.task_done()

    def wait_for_empty_queue(self, timeout=1.0):
        """
        sleep until queue is empty
        :param timeout: seconds to wait
        :return:
        """
        # TODO: don't spin
        stop_time = datetime.utcnow() + timedelta(seconds=timeout)
        while datetime.utcnow() < stop_time:
            if self.get_queue_length() == 0:
                return True
        return False

    def join_queue(self):
        self._queue.join()

    def shutdown(self, join_time=1.0):
        self._keep_going = False
        super(self.__class__, self).shutdown(join_time)


class TimedTaskProcessor(TaskProcessor):
    """Runs a function at intervals in a thread.
    """

    def __init__(self, func, name, sleep_interval, sleep_first_time=False, init_func=None, term_func=None):
        """Initializes the TimedTaskProcessor

        :param func: the function that gets run at specific intervals.
        :param name: name of the underlying thread for statistics and debugging.
        :param sleep_interval: a timedelta object that denotes the wait between successive starts
        :param sleep_first_time: Boolean, if True, will wait sleep_interval before initial run

        If the function takes longer than sleep_interval time to run, it will be run again
        immediately after finishing
        """
        super(self.__class__, self).__init__(func, name)
        self.init_func = init_func
        self.term_func = term_func
        self._keep_going = True
        self._sleep_time = 0
        self.q = Queue()
        self.update_sleep_interval(sleep_interval)
        self._sleep_first_time = sleep_first_time
        self._worker = threading.Thread(target=self._timed_loop, name=name, args=(self.q,))
        self._worker.setDaemon(True)

    def _timed_loop(self, q):
        """Internal function that runs the loop with an manual reset event"""
        if self._sleep_first_time:
            self._event.wait(timeout=self._sleep_time)
        if self.init_func and callable(self.init_func):
            self.init_func()
        last = time()
        keep_going = True
        while keep_going:
            self._run()
            next_time = last + self._sleep_time
            last = next_time
            sleep_time_left = next_time - time()
            # only go to sleep if you're still supposed to be running
            if keep_going and sleep_time_left > 0:
                self._event.clear()
                self._event.wait(timeout=sleep_time_left)
            keep_going = q.empty()
        q.get_nowait()

    def get_sleep_time_remaining(self):
        return timedelta(0, self._sleep_time) - (datetime.utcnow() - self.last_execution_time)

    def update_sleep_interval(self, sleep_interval):
        """Updates the amount of time the thread sleeps before running again

        :param sleep_interval: timedelta object or float seconds
        """
        try:
            self._sleep_time = sleep_interval.total_seconds()
        except AttributeError:
            self._sleep_time = sleep_interval

    def shutdown(self, join_time=1.0):
        self.q.put(False)
        super(self.__class__, self).shutdown(join_time)
        if self.term_func and callable(self.term_func):
            self.term_func()

    def __del__(self):
        if self._keep_going:
            self.shutdown()


class Singleton(type):
    def __init__(cls, name, bases, d):
        super(Singleton, cls).__init__(name, bases, d)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class ThreadWatcher(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.thread_list = []
        self._keep_running = True
        self._lock = threading.Lock()
        self._event = threading.Event()
        self.worker_thread = threading.Thread(target=self._watcher_worker)
        self.worker_thread.start()

    def add_thread(self, timed_processor):
        with self._lock:
            self.thread_list.append(timed_processor)
        if self.worker_thread.is_alive is False:
            self.worker_thread = threading.Thread(target=self._watcher_worker)
            self.worker_thread.start()

    def _watcher_worker(self):
        while self._keep_running:
            curr_time = datetime.utcnow()
            secs_dict = {}
            with self._lock:
                frames = None
                for t in self.thread_list:
                    secs_since_last_run = (curr_time - t.last_execution_time).total_seconds()
                    secs_dict["{}-{}".format(t.name, t._worker.ident)] = secs_since_last_run
                    if secs_since_last_run > 2*t._sleep_time and secs_since_last_run > 100:
                        logger.warn("Thread %s hasn't run in %s secs", t.name, secs_since_last_run)
                        if frames is None:
                            frames = sys._current_frames()
                        try:
                            info = inspect.getframeinfo(frames[t._worker.ident])
                            tb = traceback.format_stack(frames[t._worker.ident])
                            logger.warn("Thread %s State - %s:%s", t.name, info.function,
                                        info.lineno)
                            logger.warn("Traceback: %s", repr(tb))
                        except KeyError:
                            logger.warn("Could not find %s", t._worker.ident)

                logger.debug("Checked {} threads: {}".format(len(secs_dict), secs_dict))
            if not any([v._worker.is_alive() for v in self.thread_list]):
                return
            self._event.clear()
            self._event.wait(timeout=30)

    def shutdown(self):
        self._keep_running = False
        self._event.set()
        self.worker_thread.join(4)
        if not self.worker_thread.isAlive():
            logger.debug("%s shut down correctly.", "ThreadWatcher")
        else:
            logger.error("%s shut down halted for longer than timeout.", "ThreadWatcher")
        return not self.worker_thread.isAlive()
