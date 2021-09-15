from datetime import datetime
from sys import argv
from time import time

from helpers import *


def getfname():
    fprefix = "" if len(argv) < 2 else argv[1]
    fname = fprefix + __name__ + str(datetime.fromtimestamp(time())) + ".csv"
    return fname


def get_info_from_processes(keys=PROC_KEYS):
    timestamp = time()

    processes = {}
    # Iterate over all running process
    for proc in psutil.process_iter():
        try:
            key = str(proc.pid) + str(proc.name())
            # proc.
            # Get process name & pid from process object.
            process_info: Dict = proc.as_dict(attrs=PROC_KEYS, ad_value="null")
            process_info["timestamp"] = timestamp
            processes[key] = process_info
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print("nonfatal " + e)

    return processes


if __name__ == "__main__":

    with open(getfname(), "w") as out:
        print(get_sys_info(), file=out)  # first line is system info
        print(csv_join(*PROC_KEYS), file=out)  # second line is column names

        iterations = 1

        history: List[Dict] = []
        while True:
            history.append(get_info_from_processes())
            print("Iteration done...")
            if iterations % 500 == 0:
                print("Dumping list to file...")
                dump_list_to_file(out, history)
                history.clear()  # free memory occupied
                print("Cleaned up & continuing as usual!")

            iterations += 1

        # noinspection PyUnreachableCode
        print("Done!")
