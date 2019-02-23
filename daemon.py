import os
import subprocess
import time
import sqlite3
import datetime
from config import db


current_command = False
current_pid = False
commands = []


def add_history(line):
    conn = sqlite3.connect('/run/omxplayer-flask/sqlite3.db')
    c = conn.cursor()
    filename = line.split('/')[-3].split(' ')[0]
    c.execute("""
    CREATE TABLE IF NOT EXISTS history (date text, filename text) """)
    c.execute(
        "INSERT INTO history VALUES ('{}', '{}')".format(
            datetime.datetime.now(),
            filename
        )
    )
    conn.commit()
    conn.close()


while True:
    if not current_pid:
        with open(db, 'r') as my_file:
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
                f = open("/tmp/myfifo", 'w')
                f.write('.\n')
                f.close()
                current_pid = my_process.pid
    else:
        poll = my_process.poll()
        if poll:
            current_pid = False
            current_command = False
            with open(db, 'r') as my_file:
                commands = my_file.readlines()
            with open(db, 'w') as my_file:
                firstLine = True
                for my_command in commands:
                    if firstLine:
                        firstLine = False
                        add_history(my_command)
                    else:
                        my_file.write(my_command)
    time.sleep(5)
