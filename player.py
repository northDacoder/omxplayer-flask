import os
from flask import Flask
from flask import render_template, redirect, request
import subprocess
import datetime
import sqlite3
from config import path, paths, omxplayer, db, kill_player_cmd
from random import shuffle
import re
import collections
import psutil
import signal

app = Flask(__name__)


def get_queue():
    with open(db, 'r') as my_file:
        return my_file.readlines()

def reset_queue():
    with open(db, 'w') as my_file:
        my_file.write('')

def kill_player():
    for proc in psutil.process_iter(attrs=['pid', 'name', 'username']): 
        if 'omxplayer.bin' in proc.name():
            os.kill(int(proc.pid), signal.SIGTERM)

def extensions_white_list(my_str_file: str) -> bool:
    """ send only whitelist files to omxplayer """
    white_list = ['mp4', 'avi', 'mkv', 'mp3', 'flac', 'wav']
    return my_str_file.lower() in white_list

def get_last_histories(limit=10):
    conn = sqlite3.connect('/run/omxplayer-flask/sqlite3.db')
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS history (date text, filename text) """)
    conn.commit()
    result = []
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    for row in c.execute(""" SELECT filename FROM history order by date DESC  limit {}""".format(limit)):
        result.append(row[0])
    conn.close()

    return result

@app.route("/")
def homepage():
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    onlyfiles.sort()
    return render_template('homepage.html', paths=collections.OrderedDict(sorted(paths.items())), files=onlyfiles, queue=get_queue(), history=get_last_histories(request.args.get('limit', 10)))


@app.route("/read/<filename>/<extension>")
def read_omxplayer(filename, extension):
    if extensions_white_list(extension):
        with open(db, 'a+') as my_file:
            my_file.write('{omxplayer} {path}{file}.{extension}\n'.format(
                omxplayer=omxplayer,
                path=path,
                file=filename,
                extension=extension))
    return redirect("/")

@app.route("/<custom_path>")
def homepage_custom(custom_path):
    try:
        path = paths[custom_path]
    except KeyError:
        return redirect("/")
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    onlyfiles.sort()
    return render_template('homepage.html', paths=collections.OrderedDict(sorted(paths.items())), files=onlyfiles, custom_path=custom_path, queue=get_queue(), history=get_last_histories(request.args.get('limit', 10)))


@app.route("/<custom_path>/read/<filename>/<extension>")
def read_omxplayer_custom(custom_path, filename, extension):
    if extensions_white_list(extension):
        with open(db, 'a+') as my_file:
            my_file.write('{omxplayer} {custom_path}{file}.{extension}\n'.format(
                omxplayer=omxplayer,
                path=path,
                file=filename,
                custom_path=paths[custom_path],
                extension=extension))

    return redirect("/{}".format(custom_path))


@app.route("/remove-from-queue/<filename_complete>")
def remove_from_queue(filename_complete):
    with open(db, 'r') as my_file:
        commands = my_file.readlines()
    with open(db, 'w') as my_file:
        for command in commands:
            if filename_complete not in command:
                my_file.write(command)
    return redirect("/")

@app.route("/play-all/<custom_path>")
def playall_custom(custom_path):
    path = paths[custom_path]
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and extensions_white_list(f.split('.')[-1])]
    onlyfiles.sort()

    with open(db, 'a+') as my_file:
        for filename in onlyfiles:
            my_file.write('{omxplayer} {path}{file}\n'.format(
                omxplayer=omxplayer,
                path=path,
                file=filename))

    return redirect("/{}".format(custom_path))

@app.route("/play-random/<custom_path>")
def playrandom_custom(custom_path):
    path = paths[custom_path]
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and extensions_white_list(f.split('.')[-1])]
    shuffle(onlyfiles)

    with open(db, 'a+') as my_file:
        for filename in onlyfiles:
            my_file.write('{omxplayer} {path}{file}\n'.format(
                omxplayer=omxplayer,
                path=path,
                file=filename))

    return redirect("/{}".format(custom_path))

@app.route("/play-pattern", methods=['POST'])
def playpattern():
    custom_path = request.form['custom_path'] or 'songs'
    label_pattern =  request.form['labelPattern']
    path = paths[custom_path]
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and re.search(label_pattern ,f) and extensions_white_list(f.split('.')[-1])]
    onlyfiles.sort()
    with open(db, 'a+') as my_file:
        for filename in onlyfiles:
            my_file.write('{omxplayer} {path}{file}\n'.format(
                omxplayer=omxplayer,
                path=path,
                file=filename))

    return redirect("/{}".format(custom_path))

@app.route('/clear-all')
def clear_all():
    """ erase all files in queue and stop any player running """
    reset_queue()
    kill_player()
    return redirect("/")
