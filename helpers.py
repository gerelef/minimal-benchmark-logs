import logging
import platform
import psutil
import socket
from typing import List, Dict, Set

PROC_KEYS = ["pid", "name", "cpu_num", "cpu_percent", "cpu_times",
             "num_threads", "threads", "memory_full_info",
             "memory_info", "memory_percent", "open_files", "nice",
             "status"]

_YES_SHORT_ANS = "Y"
_NO_SHORT_ANS = "N"
_YES_ANS = "YES"
_NO_ANS = "NO"


def str_is_yes_or_no(s):
    return str_is_yes(s) or str_is_no(s)


def str_is_yes(s):
    s = s.upper()
    return s == _YES_ANS or s == _YES_SHORT_ANS


def str_is_no(s):
    s = s.upper()
    return s == _NO_ANS or s == _NO_SHORT_ANS


def print_identifiable_characteristics_of_processes(proc_set: Set[psutil.Process]):
    for process in proc_set:
        print(f"PID: {process.pid} PPID: {process.ppid()} NAME: {process.name()} STATUS: {process.status()}")


def get_sys_info():
    try:
        sys = f"{platform.system()},{platform.release()},{platform.version()},{platform.machine()}," \
              f"{socket.gethostname()},{platform.processor()}," \
              f"{str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + ' GB'}"
        # noinspection PyBroadException
        try:
            import wmi
            sys += f",{wmi.WMI().Win32_VideoController()[0].name}"
        except Exception:
            pass
        return sys
    except Exception as ex:
        logging.exception(ex)


def csv_join(*args):
    csv_separated_str = ""
    for arg in args:
        csv_separated_str += str(arg) + ","
    return csv_separated_str[0:-1]


def dump_list_to_file(fhandle, node_list: List[Dict]):
    for data_node in node_list:
        for k in data_node.keys():
            data = data_node[k]
            print(f"{data['timestamp']},{data['pid']},{data['name']},{data['cpu_num']},{data['cpu_percent']},"
                  f"{data['cpu_times']},{data['num_threads']},{data['threads']},"
                  f"{data['memory_full_info']},{data['memory_info']},{data['memory_percent']},"
                  f"{data['open_files']},{data['nice']},{data['status']}",
                  file=fhandle)
