""" player using flask """

import collections
import os
import re
import signal
import sqlite3
from random import shuffle

from flask import Flask, render_template, redirect, request
import psutil

from config import PATH, PATHS, OMXPLAYER, DB


APP = Flask(__name__)
FIFO = " < /tmp/myfifo "


def get_queue() -> list:
    """ get next commands list """
    with open(DB, 'r') as my_file:
        return my_file.readlines()


def reset_queue():
    """ remove all commands from queue """
    with open(DB, 'w') as my_file:
        my_file.write('')


def kill_player():
    """ kill all process with omplayer in the name """
    for proc in psutil.process_iter(attrs=['pid', 'name', 'username']):
        if 'omxplayer.bin' in proc.name():
            os.kill(int(proc.pid), signal.SIGTERM)


def extensions_white_list(my_str_file: str) -> bool:
    """ send only whitelist files to omxplayer """
    white_list = ['mp4', 'avi', 'mkv', 'mp3', 'flac', 'wav']
    return my_str_file.lower() in white_list


def get_last_histories(limit=10) -> list:
    """ get historic """
    conn = sqlite3.connect('/run/omxplayer-flask/sqlite3.db')
    my_c = conn.cursor()
    my_c.execute(
        "CREATE TABLE IF NOT EXISTS history (date text, filename text)"
    )
    conn.commit()
    result = []
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    for row in my_c.execute(
            (
                "SELECT filename FROM history order by date DESC  limit {}"
            ).format(limit)):
        result.append(row[0])
    conn.close()

    return result


@APP.route("/")
def homepage():
    """ homepage """
    onlyfiles = [
        f for f in os.listdir(PATH)
        if os.path.isfile(os.path.join(PATH, f))
    ]
    onlyfiles.sort()
    return render_template(
        'homepage.html',
        paths=collections.OrderedDict(sorted(PATHS.items())),
        files=onlyfiles,
        queue=get_queue(),
        history=get_last_histories(request.args.get('limit', 10))
    )


@APP.route("/read/<filename>/<extension>")
def read_omxplayer(filename, extension):
    """ add to DB """
    if extensions_white_list(extension):
        with open(DB, 'a+') as my_file:
            my_file.write(
                '{omxplayer} {path}{file}.{extension} {fifo} \n'.format(
                    omxplayer=OMXPLAYER,
                    path=PATH,
                    fifo=FIFO,
                    file=filename,
                    extension=extension
                )
            )
    return redirect("/")


@APP.route("/<custom_path>")
def homepage_custom(custom_path):
    """ list files from custom_path """
    try:
        path = PATHS[custom_path]
    except KeyError:
        return redirect("/")
    onlyfiles = [
        f for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
    ]
    onlyfiles.sort()
    return render_template(
        'homepage.html',
        paths=collections.OrderedDict(sorted(PATHS.items())),
        files=onlyfiles,
        custom_path=custom_path,
        queue=get_queue(),
        history=get_last_histories(request.args.get('limit', 10))
    )


@APP.route("/<custom_path>/read/<filename>/<extension>")
def read_omxplayer_custom(custom_path, filename, extension):
    """ add to dB """
    if extensions_white_list(extension):
        with open(DB, 'a+') as my_file:
            my_file.write(
                '{omxplayer} {custom_path}{file}.{extension} {fifo} \n'.format(
                    omxplayer=OMXPLAYER,
                    fifo=FIFO,
                    file=filename,
                    custom_path=PATHS[custom_path],
                    extension=extension
                )
            )

    return redirect("/{}".format(custom_path))


@APP.route("/remove-from-queue/<filename_complete>")
def remove_from_queue(filename_complete):
    """ remove from queue """
    with open(DB, 'r') as my_file:
        commands = my_file.readlines()
    with open(DB, 'w') as my_file:
        for command in commands:
            if filename_complete not in command:
                my_file.write(command)
    return redirect("/")


@APP.route("/play-all/<custom_path>")
def playall_custom(custom_path):
    """ play all files from this custom_path """
    path = PATHS[custom_path]
    onlyfiles = [
        f for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
        and extensions_white_list(f.split('.')[-1])
    ]
    onlyfiles.sort()

    with open(DB, 'a+') as my_file:
        for filename in onlyfiles:
            my_file.write('{omxplayer} {path}{file} {fifo} \n'.format(
                omxplayer=OMXPLAYER,
                path=path,
                fifo=FIFO,
                file=filename))

    return redirect("/{}".format(custom_path))


@APP.route("/play-random/<custom_path>")
def playrandom_custom(custom_path):
    """ random play for all files from this custom_path """
    path = PATHS[custom_path]
    onlyfiles = [
        f for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
        and extensions_white_list(f.split('.')[-1])
    ]
    shuffle(onlyfiles)

    with open(DB, 'a+') as my_file:
        for filename in onlyfiles:
            my_file.write('{omxplayer} {path}{file} {fifo} \n'.format(
                omxplayer=OMXPLAYER,
                fifo=FIFO,
                path=path,
                file=filename))

    return redirect("/{}".format(custom_path))


@APP.route("/play-pattern", methods=['POST'])
def playpattern():
    """ play files matching labelPattern """
    custom_path = request.form['custom_path'] or 'songs'
    label_pattern = request.form['labelPattern']
    path = PATHS[custom_path]
    onlyfiles = [
        f for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
        and re.search(label_pattern, f)
        and extensions_white_list(f.split('.')[-1])
    ]
    onlyfiles.sort()
    with open(DB, 'a+') as my_file:
        for filename in onlyfiles:
            my_file.write('{omxplayer} {path}{file} {fifo} \n'.format(
                omxplayer=OMXPLAYER,
                path=path,
                fifo=FIFO,
                file=filename))

    return redirect("/{}".format(custom_path))


@APP.route('/clear-all')
def clear_all():
    """ erase all files in queue and stop any player running """
    reset_queue()
    kill_player()
    return redirect("/")


@APP.route("/command/<my_command>")
def command_to_omxplayer(my_command):
    """ send my_command to fifo """
    my_f = open('/tmp/myfifo', 'w')
    my_f.write(my_command)
    my_f.close()
    return redirect('/')
