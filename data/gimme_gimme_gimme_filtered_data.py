from datetime import datetime
from typing import List, Dict, Set, Tuple
from sys import argv
import csv
import psutil

_TIMESTAMP_COLUMN = 0
_PID_COLUMN = 1
_PPID_COLUMN = 2
_PNAME_COLUMN = 3
_CPU_NUM_COLUMN = 4
_CPU_PERCENT_COLUMN = 5
_PROCESS_PHYSICAL_MEMORY_USED = 6


def filter_fragmented_process_data(fname: str, delimiter=",") -> List[List]:
    pid_filter = lambda r: r[_PID_COLUMN] == pid

    columns: List[List] = []
    pid_set: Set = set()
    index: int = 0
    with open(fname, "r") as f:
        for line in f:
            row = line.strip("\n").split(delimiter)
            columns.append(row)

            pid_set.add(row[_PID_COLUMN])

            index += 1

    for pid in pid_set:
        yield list(filter(pid_filter, columns))

    return


def write_csv_per_process(fname, data_list: List):
    with open(data_list[0][_PID_COLUMN] + fname, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data_list)


def process_data_per_process(data_list: List):
    true_cpu_usage = list(map(lambda r: float(r[_CPU_PERCENT_COLUMN]) / psutil.cpu_count(), data_list))
    [r.pop(_CPU_PERCENT_COLUMN) for r in data_list]
    [r.pop(_CPU_NUM_COLUMN) for r in data_list]

    for row, cpu_usage_per_core in zip(data_list, true_cpu_usage):
        row.insert(4, cpu_usage_per_core)


if __name__ == "__main__":
    for file in argv[1:]:
        for process_data in filter_fragmented_process_data(file):
            process_data_per_process(process_data)
            write_csv_per_process(file, process_data)
