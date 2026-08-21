"""Main file which imports and runs the main loop code from
config.py.
"""

from config import Main
import time


def run(time_input):
    # Instantiate and initialize hardware once outside the execution loop
    try:
        script = Main(time_input)
        script.initialise()
    except Exception as e:
        log_error(e)
        return

    # Run mainloop with error handling
    while True:
        try:
            script.mainloop()
        except Exception as e:
            log_error(e)
            time.sleep(1)  # Brief delay before retrying to prevent rapid loop lockup

def log_error(e):
    logs = ""
    # Safely read existing logs if the file exists
    try:
        with open("error_log.txt", "r") as file:
            logs = file.read()
    except OSError:
        pass  # File doesn't exist yet, start with empty string

    # Append new error log
    try:
        with open("error_log.txt", "w") as file:
            file.write(f"{logs}\n{e}".strip())
    except OSError:
        pass


if __name__ == "__main__":
    time_ = time.time()
    run(time_)

