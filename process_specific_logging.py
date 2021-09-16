import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Generator, Set
from datetime import datetime
from sys import argv
from time import time, sleep
from io import FileIO
from psutil import Process
from helpers import str_is_yes, str_is_no, str_is_yes_or_no, print_identifiable_characteristics_of_processes
import psutil
import igpu


# ARG SYNTAX:
#  --ppid (or --pid) v1
#  --ppids (or --pids) v1,v2,v3,v4
#  --fout str
#  --interval float > 0


class InvalidArg(Exception):
    GENERIC_DESCRIPTION = "Invalid flag or value."

    INVALID_FLAG_DESC = "Invalid flag."
    UNKNOWN_FLAG_DESC = "Unknown flag."

    INVALID_ARG_DESC = "Invalid arg."
    INVALID_VAL_TYPE_DESC = "Invalid value type."

    MISSING_VALUE_DESC = "Missing value."

    def __init__(self, flag, value, error_description=GENERIC_DESCRIPTION):
        super(InvalidArg, self).__init__()
        self.description = error_description
        self.flag = flag
        self.value = value

    def __str__(self):
        return f"{self.description} Flag {self.flag} & value {self.value}."


class CMDHandler:
    PARENT_ARG = "--PPID"
    PARENTS_ARG = "--PPIDS"
    PROCESS_ARG = "--PID"
    PROCESSES_ARG = "--PIDS"
    FOUT_PREFIX_ARG = "--FOUT"
    DT_INTERVAL_ARG = "--INTERVAL"

    VALID_FLAGS = [PARENT_ARG, PARENTS_ARG, PROCESS_ARG, PROCESSES_ARG, FOUT_PREFIX_ARG, DT_INTERVAL_ARG]

    def __init__(self):
        self.arg_index = 0
        self.parents_pids = []
        self.processes_pids = []
        self.fout_prefix = ""
        self.dt_interval = 0.5

    def parse(self):
        args = self.get_next_arg()
        for arg in args:
            arg = arg.upper()

            if arg not in CMDHandler.VALID_FLAGS:
                raise InvalidArg(arg, None, InvalidArg.UNKNOWN_FLAG_DESC)

            self.handle_parent(arg, args)
            self.handle_parents(arg, args)
            self.handle_process(arg, args)
            self.handle_processes(arg, args)
            self.handle_fout_name(arg, args)
            self.handle_dt_interval(arg, args)

    def handle_parent(self, arg, gen: Generator):
        if arg != self.PARENT_ARG:
            return False

        # next arg will be 1 arg
        tvalue = gen.__next__()
        try:
            val = int(tvalue)
        except ValueError:
            raise InvalidArg(arg, tvalue, InvalidArg.INVALID_VAL_TYPE_DESC)
        except StopIteration:
            raise InvalidArg(arg, None, InvalidArg.MISSING_VALUE_DESC)

        self.parents_pids.append(val)

        return True

    def handle_parents(self, arg, gen: Generator):
        if arg != self.PARENTS_ARG:
            return False

        # next arg will be N count args separated by comma
        tvalues = gen.__next__().split(",")
        try:
            val = [int(v) for v in tvalues]
        except ValueError:
            raise InvalidArg(arg, tvalues, InvalidArg.INVALID_VAL_TYPE_DESC)
        except StopIteration:
            raise InvalidArg(arg, None, InvalidArg.MISSING_VALUE_DESC)

        self.parents_pids.extend(val)

        return True

    def handle_process(self, arg, gen: Generator):
        if arg != self.PROCESS_ARG:
            return False

        # next arg will be 1 arg
        tvalue = gen.__next__()
        try:
            val = int(tvalue)
        except ValueError:
            raise InvalidArg(arg, tvalue, InvalidArg.INVALID_VAL_TYPE_DESC)
        except StopIteration:
            raise InvalidArg(arg, None, InvalidArg.MISSING_VALUE_DESC)

        self.processes_pids.append(val)

        return True

    def handle_processes(self, arg, gen: Generator):
        if arg != self.PROCESSES_ARG:
            return False

        # next arg will be N count args separated by comma
        tvalues = gen.__next__().split(",")
        try:
            val = [int(v) for v in tvalues]
        except ValueError:
            raise InvalidArg(arg, tvalues, InvalidArg.INVALID_VAL_TYPE_DESC)
        except StopIteration:
            raise InvalidArg(arg, None, InvalidArg.MISSING_VALUE_DESC)

        self.processes_pids.extend(val)

        return True

    def handle_fout_name(self, arg, gen: Generator):
        if arg != self.FOUT_PREFIX_ARG:
            return False

        # next arg will be 1 arg
        try:
            self.fout_prefix = gen.__next__()
        except StopIteration:
            raise InvalidArg(arg, None, InvalidArg.MISSING_VALUE_DESC)

        return True

    def handle_dt_interval(self, arg, gen: Generator):
        if arg != self.DT_INTERVAL_ARG:
            return False

        # next arg will be 1 arg
        val = gen.__next__()
        try:
            self.dt_interval = float(val)
            if self.dt_interval < 0.:
                raise InvalidArg(arg, val, "Expected float with value > 0.")
        except ValueError:
            raise InvalidArg(arg, next, InvalidArg.INVALID_VAL_TYPE_DESC)
        except StopIteration:
            raise InvalidArg(arg, None, InvalidArg.MISSING_VALUE_DESC)

        return True

    def get_next_arg(self):
        for arg in argv[1:]:
            self.arg_index += 1
            yield arg

        return


class Plotter(ABC):

    @abstractmethod
    def plot(self, data: List[Dict]):
        pass


class _MockPlotter(Plotter):

    def plot(self, data: List[Dict]):
        pass


# https://stackoverflow.com/questions/3774328/implementing-use-of-with-object-as-f-in-custom-class-in-python
class ProcessLogger:
    """Use with 'with obj as m' statement"""

    _process_fname_infix = "_processes_"
    _system_fname_infix = "_system_"

    # noinspection PyTypeChecker
    def __init__(self, fname=""):
        self.fout_process: FileIO = None
        self.fout_system: FileIO = None
        self.fout_errors: FileIO = None
        self.fname_process = fname + self._process_fname_infix
        self.fname_system = fname + self._system_fname_infix
        self.processes_to_keep_track: Set = set()
        self.iterations = 1

        self.conv_1d_list_to_str_list = lambda l: [str(v) for v in l]

    def __enter__(self):
        self.fname_process += str(datetime.fromtimestamp(time())) + ".csv"
        self.fname_system += str(datetime.fromtimestamp(time())) + ".csv"
        self.fout_process = open(self.fname_process, "w")
        self.fout_system = open(self.fname_system, "w")
        self.fout_errors = open("errors.log", "w+")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fout_process.close()
        self.fout_system.close()
        self.fout_errors.close()

        if exc_type is not None:
            sys.stderr.write(f"For file {self.fname_process}\n\tgot exc_type {exc_type} val {exc_val} exc_tb {exc_tb}\n")

    def pre_init(self, pids: List[int], ppids: List[int]) -> Set[Process]:
        processes: Set[Process] = set()
        # Iterate over all running process
        for proc in psutil.process_iter():
            try:
                pid_found = proc.pid in pids
                ppid_found = proc.pid in pids
                ppid_found_ppid = proc.ppid in ppids
                pid_found_ppid = proc.pid in ppids

                found_any_related_proc = pid_found or ppid_found or ppid_found_ppid or pid_found_ppid
                if found_any_related_proc:
                    processes.add(proc)

                if ppid_found_ppid or pid_found_ppid:
                    children = proc.children(recursive=True)
                    for child_process in children:
                        processes.add(child_process)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.error(f"Got nonfatal {e} on proccess {proc}")

        return processes

    def init(self, pids: List[int], ppids: List[int], process_set: Set[Process] = None):
        if process_set is not None:
            self.processes_to_keep_track = process_set
            return

        self.processes_to_keep_track = self.pre_init(pids, ppids)

    def loop(self):
        # loop (data point) ts
        timestamp = time()
        # #############SYSTEM###############
        system_info = self.get_system_info()
        system_info.insert(0, timestamp)
        self.log_system_info(system_info)
        # #############SYSTEM###############

        # #############PROCESS###############
        for p in self.processes_to_keep_track:
            proc_info = self.get_process_info(p)
            proc_info.insert(0, timestamp)
            self.log_process_info(proc_info)
        # #############PROCESS###############

        self.iterations += 1

    def log_process_info(self, info):
        print(",".join(self.conv_1d_list_to_str_list(info)), file=self.fout_process)

    def log_system_info(self, info):
        print(",".join(self.conv_1d_list_to_str_list(info)), file=self.fout_system)

    def get_process_info(self, p: Process) -> List:
        identifiers = self.get_process_identifiers(p)
        performance = self.get_process_performance(p)
        memory = self.get_process_memory_used(p)
        return identifiers + performance + memory

    def get_system_info(self) -> List:
        vm_info = self.get_virtual_memory_info()
        sp_info = self.get_swap_info()
        gpu_info = self.get_gpu_info()
        return vm_info + sp_info + gpu_info

    @staticmethod
    def get_process_identifiers(p: Process):
        return [p.pid, p.ppid(), p.name()]

    @staticmethod
    def get_process_performance(p: Process):
        return [p.cpu_num(), p.cpu_percent(interval=0.01)]

    @staticmethod
    def get_process_memory_used(p: Process):
        return [p.memory_info().rss]

    @staticmethod
    def get_virtual_memory_info() -> List:
        vm_info = psutil.virtual_memory()
        metrics = [vm_info.used, vm_info.total]
        return metrics

    @staticmethod
    def get_swap_info() -> List:
        swap_info = psutil.swap_memory()
        metrics = [swap_info.used, swap_info.total]
        return metrics

    # https://openbase.com/python/igpu#examples
    @staticmethod
    def get_gpu_info() -> List:
        metrics = [-1, -1, -1]
        # noinspection PyBroadException
        try:
            # TODO make it work w/ more than 1 device (igpu from what i've read only works with nvidia gpus)
            if igpu.count_devices() > 0:
                gpu = igpu.get_device(0)
                metrics = [gpu.utilization.gpu, gpu.memory.used, gpu.memory.total]
        except Exception:
            # silently ignore, we probably do not have nvidia gpu...
            pass

        return metrics

    @staticmethod
    def error(msg):
        print(msg)

    def redirect_stdout(self):
        sys.stdout = self.fout_errors


# TODO refactor someday, a little plague-stricken, input logic should be more fragmented...
# noinspection PyShadowingNames
def ask_for_confirmation(proc_set: Set[Process]) -> Set[Process]:
    processes_to_log = proc_set.copy()
    print("Found: ")
    print_identifiable_characteristics_of_processes(proc_set)

    while True:
        ans = input("Would you like to continue? (y/n) ")
        if str_is_yes(ans):
            return processes_to_log
        if not str_is_yes_or_no(ans):
            continue

        ans = input("Would you like to filter these processes instead of quitting? (n/give comma separated pids) ")
        if str_is_no(ans):
            return set()  # return empty process list to indicate no processes

        processes_to_log = set()

        ans = ans.split(",")
        try:
            pids = [int(v) for v in ans]
        except ValueError:
            print("Found possible typo, resetting...")
            continue

        for pid in pids:
            pid_match = False
            for process in proc_set:
                if process.pid == pid:
                    pid_match = True
                    processes_to_log.add(process)

            if not pid_match:
                print(f"Couldn't find process w/ pid {pid}, restarting!")

        return processes_to_log


if __name__ == "__main__":
    cmdhandle = CMDHandler()
    cmdhandle.parse()

    print("Looking for parents: ", cmdhandle.parents_pids, "\nand processes ", cmdhandle.processes_pids)

    with ProcessLogger(fname=cmdhandle.fout_prefix) as pl:
        proc_set = pl.pre_init(cmdhandle.processes_pids, cmdhandle.parents_pids)
        proc_set = ask_for_confirmation(proc_set)

        # if empty, bail
        if len(proc_set) == 0:
            exit(0)

        pl.init([], [], process_set=proc_set)
        pl.redirect_stdout()

        while True:
            sys.stderr.write("Looping...\n")
            start = time()
            pl.loop()
            end = time()

            sleep(cmdhandle.dt_interval - round(end - start, 2))

        # print_identifiable_characteristics_of_processes(pl.processes_to_keep_track)
