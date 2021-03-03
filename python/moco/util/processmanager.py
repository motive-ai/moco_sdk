import threading
import shlex
import os
import logging
import sys
from distutils import spawn
from subprocess import PIPE

import psutil
from moco.util.threads import TimedTaskProcessor

logger = logging.getLogger(__name__)


class ProcessManager(object):
    def __init__(self, callback=None):
        self._counter = 0
        logger.debug("CURRENT PROCESS ID = %d", os.getpid())

        self._lock = threading.RLock()
        self._processes = {}
        if os.name == 'nt':
            self.posix = False
        else:
            self.posix = True
        if callback and callable(callback):
            self.callback = callback
        self.bin_extension = ''
        if sys.platform == 'win32':
            self.bin_extension = '.exe'

    def start(self, cmd_line, cmd_dir='', use_bin_extension=True, use_stdout=False):
        if len(cmd_dir) > 0 and cmd_dir[-1] != os.sep:
            cmd_dir += os.sep
        cmd_dir = os.path.expandvars(os.path.expanduser(cmd_dir))
        args = shlex.split(cmd_line, posix=self.posix)
        program_name = os.path.expandvars(os.path.expanduser(args[0]))
        if use_bin_extension and not program_name.endswith(self.bin_extension):
            program_name += self.bin_extension
        full_line = "{} {}".format(os.path.join(cmd_dir, program_name), " ".join(args[1:]))
        full_path = spawn.find_executable(os.path.join(cmd_dir, program_name))
        # if the executable does not exist, complain:
        if not full_path or not os.path.isfile(full_path):
            msg = "{0} is not a valid file. " \
                  "Cannot start it as a process".format(os.path.join(cmd_dir, program_name))
            raise IOError(msg)
        try:
            process = self._start(full_path, args[1:], use_stdout)
        except Exception as e:
            logger.exception("Unable to start Process %s", cmd_line)
            raise e
        else:
            logger.debug("Process: %s was successfully started. Pid = %d", full_line, process.pid)
            with self._lock:
                self._processes[process.pid] = process
                self._counter += 1
            return process

    @staticmethod
    def _start(full_path, arguments=None, use_stdout=False):
        if arguments is None:
            arguments = []
        en = dict(os.environ)
        exe_path = os.path.split(os.path.abspath(sys.executable))[0]
        if en['PATH'].split(':')[0] != exe_path:
            en['PATH'] = exe_path + os.pathsep + en['PATH']
        std_out = open(os.devnull, 'w+')
        if use_stdout:
            std_out = PIPE
        close_fds = True
        if os.name == 'nt':
            close_fds = False
        proc = psutil.Popen([full_path] + arguments, shell=False, env=en, universal_newlines=True,
                            close_fds=close_fds, stdout=std_out, stderr=std_out)
        return proc

    def stopped_processes(self):
        stopped_procs = list()
        for proc in self._processes.values():
            if not self.is_running(proc):
                stopped_procs.append(proc)
        return stopped_procs

    def process_ended(self, proc):
        if proc in self._processes:
            self._processes.pop(proc.pid)
        self.callback(proc)

    def get_processes(self):
        return self._processes

    def get_process_by_pid(self, pid):
        with self._lock:
            try:
                return self._processes[pid]
            except KeyError:
                logger.info("Could not find '{}' in ProcessManager. "
                            "Looking across all processes".format(pid))
                # This will raise a "NoSuchProcess" exception if not found
                return psutil.Process(pid)

    def stop_proc(self, proc, stop_children=True, timeout=10):
        return_value = False
        with self._lock:
            # if process already dead, say so:
            try:
                returncode = proc.poll()
            except AttributeError:
                returncode = 0
            proc_pid = proc.pid
            try:
                if proc.is_running() is False:
                    logger.info("Trying to stop \"{0}\", but it is not running. Has returncode:"
                                " {1}".format(proc.pid, returncode))
                    if proc.pid in self._processes:
                        self._processes.pop(proc_pid)
                    return True
                child_procs = proc.children(recursive=True)
                proc_cmdline = proc.cmdline()
                proc.terminate()
                (gone, alive) = psutil.wait_procs([proc], timeout)
                if gone:
                    logger.info("Terminated command {}".format(proc_cmdline))
                    if proc in self._processes:
                        self._processes.pop(proc_pid)
                    return_value = True
                for p in alive:
                    logger.info("Process did not terminate, killing '{}'".format(proc.cmdline()))
                    p.kill()
                    if proc.is_running():
                        return_value = False
            except psutil.AccessDenied:
                logger.warning("Could not access process {}".format(proc.pid))
                return return_value
            except psutil.NoSuchProcess:
                logger.info("Process {} no longer exists".format(proc.pid))
                return return_value

            # Stop Child Processes:
            if stop_children:
                for proc in child_procs:
                    logger.warning("Stopping Child Process {}".format(proc.pid))
                    try:
                        self.stop_proc(proc, stop_children=False, timeout=timeout)
                    except psutil.NoSuchProcess:
                        logger.info("Child process {} already stopped".format(proc.pid))
                    except psutil.AccessDenied:
                        logger.warning("Child process {} could not be accessed".format(proc.pid))
                    except Exception as e:
                        logger.exception("Unknown error stopping process")
                        raise e
            return return_value

    def stop_by_pid(self, pid, stop_children=True, timeout=10):
        # if the process id doesn't exist, complain loudly
        proc = self.get_process_by_pid(pid)
        success = self.stop_proc(proc, stop_children, timeout)
        if success:
            try:
                del self._processes[pid]
            except KeyError:
                pass

    def stop_all(self, timeout=10):
        for pid, process in self._processes.items():
            try:
                self.stop_proc(process, True, timeout)
            except psutil.NoSuchProcess:
                logger.info("Process {} already stopped".format(pid))

    @staticmethod
    def get_processes_from_name(process_name):
        """
        Note: this method is depreciated in favor of find_process_by_name
        """
        process_list = list()
        try:
            for process in psutil.process_iter():
                try:
                    if process_name in process.cmdline():
                        process_list.append(process)
                        continue
                    if process.name() == process_name:
                        process_list.append(process)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
        except Exception as e:
            logger.error("Unable to get process '{}'".format(process_name))
            raise e
        return process_list

    @staticmethod
    def find_process_by_name(name):
        found_processes = list()
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['name'])
                if pinfo['name'] == name:
                    found_processes.append(proc)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        return found_processes

    @staticmethod
    def get_pids_from_name(process_name):
        procs = ProcessManager.find_process_by_name(process_name)
        pids = [p.pid for p in procs]
        return pids

    @staticmethod
    def kill_pid(pid):
        if not pid:
            return False
        psutil.Process(pid).kill()

    @staticmethod
    def is_running(process):
        try:
            if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                return True
        except psutil.NoSuchProcess:
            return False
        return False

    def shutdown(self, timeout=10):
        with self._lock:
            if self._processes:
                for pid, process in self._processes.items():
                    try:
                        if process.is_running():
                            if process.status() == psutil.STATUS_ZOMBIE:
                                logger.info("Killing process {}: '{}'".format(pid, process.name()))
                                process.kill()
                                continue
                            try:
                                proc_text = "'{}'".format(' '.join(process.cmdline()))
                            except psutil.AccessDenied:
                                proc_text = "'{}' ({})".format(process.name(), pid)
                            logger.warning("Stopping process: %s", proc_text)
                            self.stop_proc(process, True, timeout)
                    except psutil.NoSuchProcess:
                        pass
        return


class ProcessWatcher(object):
    def __init__(self, process_manager, callback_fn):
        self.process_manager = process_manager
        self.callback_fn = callback_fn
        self.ttp = TimedTaskProcessor(self.check_processes, 'ProcessWatcher', 2)
        self.ttp.start()

    def check_processes(self):
        stopped_processes = self.process_manager.stopped_processes()
        if stopped_processes:
            self.callback_fn(stopped_processes)

    def shutdown(self):
        self.ttp.shutdown()
