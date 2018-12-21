import os
from flask import Flask
from flask import render_template, redirect, request
import subprocess
import datetime
import sqlite3
from config import path, paths, omxplayer, db
from random import shuffle
import re
import collections

app = Flask(__name__)


def get_queue():
    with open(db, 'r') as my_file:
        return my_file.readlines()

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
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
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
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
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
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and re.search(label_pattern ,f)]
    onlyfiles.sort()
    with open(db, 'a+') as my_file:
        for filename in onlyfiles:
            my_file.write('{omxplayer} {path}{file}\n'.format(
                omxplayer=omxplayer,
                path=path,
                file=filename))

    return redirect("/{}".format(custom_path))
