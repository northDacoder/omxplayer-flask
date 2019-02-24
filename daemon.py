""" daemon to process omxplayer commands """

import datetime
import os
import sqlite3
import subprocess
import time

from config import DB


def add_history(line):
    """ add history into DB """
    conn = sqlite3.connect('/run/omxplayer-flask/sqlite3.db')
    my_c = conn.cursor()
    filename = line.split('/')[-3].split(' ')[0]
    my_c.execute(
        "CREATE TABLE IF NOT EXISTS history (date text, filename text)"
    )
    my_c.execute(
        "INSERT INTO history VALUES ('{}', '{}')".format(
            datetime.datetime.now(),
            filename
        )
    )
    conn.commit()
    conn.close()


def main():
    """ main function for this daemon """
    current_command = False
    current_pid = False
    while True:
        if not current_pid:
            with open(DB, 'r') as my_file:
                commands = my_file.readlines()
                if commands:
                    command = commands[0].strip('\n')
                    current_command = command
                    try:
                        os.mkfifo("/tmp/myfifo")
                    except OSError:
                        pass
                    my_process = subprocess.Popen(
                        '{cmd}'.format(cmd=current_command),
                        shell=True
                    )
                    my_fifo = open("/tmp/myfifo", 'w')
                    my_fifo.write('.\n')
                    my_fifo.close()
                    current_pid = my_process.pid
        else:
            poll = my_process.poll()
            if poll is not None:
                current_pid = False
                current_command = False
                with open(DB, 'r') as my_file:
                    commands = my_file.readlines()
                with open(DB, 'w') as my_file:
                    first_line = True
                    for my_command in commands:
                        if first_line:
                            first_line = False
                            add_history(my_command)
                        else:
                            my_file.write(my_command)
        time.sleep(5)


if __name__ == '__main__':
    main()
