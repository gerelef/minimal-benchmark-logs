from abc import ABC, abstractmethod
from typing import Dict, List, Generator
from datetime import datetime
from sys import argv
from time import time


# ARG SYNTAX:
#  --ppid (or --pid) v1
#  --ppids (or --pids) v1,v2,v3,v4

class InvalidArg(Exception):
    GENERIC_DESCRIPTION = "Invalid flag or value. "

    INVALID_FLAG_DESC = "Invalid flag. "
    UNKNOWN_FLAG_DESC = "Unknown flag. "

    INVALID_ARG_DESC = "Invalid arg. "
    INVALID_VAL_TYPE_DESC = "Invalid value type. "

    def __init__(self, flag, value, error_description=GENERIC_DESCRIPTION):
        super(InvalidArg, self).__init__()
        self.description = error_description
        self.flag = flag
        self.value = value

    def __str__(self):
        return f"{self.description} with flag {self.flag} & value {self.value}."


class CMDHandler:
    PARENT_ARG = "--PPID"
    PARENTS_ARG = "--PPIDS"
    PROCESS_ARG = "--PID"
    PROCESSES_ARG = "--PIDS"

    VALID_FLAGS = [PARENT_ARG, PARENTS_ARG, PROCESS_ARG, PROCESSES_ARG]

    def __init__(self):
        self.arg_index = 0
        self.parent_pid = None
        self.parents_pids = None
        self.process_pid = None
        self.processes_pids = None

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

    def handle_parent(self, arg, gen: Generator):
        if arg != self.PARENT_ARG:
            return False

        # next arg will be 1 arg
        tvalue = gen.__next__()
        try:
            val = int(tvalue)
        except Exception:
            raise InvalidArg(arg, tvalue, InvalidArg.INVALID_VAL_TYPE_DESC)

        self.parent_pid = val

        return True

    def handle_parents(self, arg, gen: Generator):
        if arg != self.PARENTS_ARG:
            return False

        # next arg will be N count args separated by comma
        tvalues = gen.__next__().split(",")
        try:
            val = [int(v) for v in tvalues]
        except Exception:
            raise InvalidArg(arg, tvalues, InvalidArg.INVALID_VAL_TYPE_DESC)

        self.parents_pids = val

        return True

    def handle_process(self, arg, gen: Generator):
        if arg != self.PROCESS_ARG:
            return False

        # next arg will be 1 arg
        tvalue = gen.__next__()
        try:
            val = int(tvalue)
        except Exception:
            raise InvalidArg(arg, tvalue, InvalidArg.INVALID_VAL_TYPE_DESC)

        self.process_pid = val

        return True

    def handle_processes(self, arg, gen: Generator):
        if arg != self.PROCESSES_ARG:
            return False

        # next arg will be N count args separated by comma
        tvalues = gen.__next__().split(",")
        try:
            val = [int(v) for v in tvalues]
        except Exception:
            raise InvalidArg(arg, tvalues, InvalidArg.INVALID_VAL_TYPE_DESC)

        self.processes_pids = val

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


# https://stackoverflow.com/questions/3774328/implementing-use-of-with-object-as-f-in-custom-class-in-python
class ProcessLogger:
    """Use with 'with obj as m' statement"""

    def __init__(self, automatic_dumps=False, plot_at_eol=False, plotter: Plotter = None):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def init(self):
        pass

    def loop(self):
        pass

    def memory_dump(self):
        pass


if __name__ == "__main__":
    cmdhandle = CMDHandler()
    cmdhandle.parse()

    print("args ", cmdhandle.parent_pid, " ", cmdhandle.parents_pids, "\n",
          cmdhandle.process_pid, " ", cmdhandle.processes_pids)
