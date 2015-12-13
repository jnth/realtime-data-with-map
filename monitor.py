#!/usr/bin/env python3.5
# coding: utf-8

'''Show streaming graph of database.'''

sleep = 2  # timestep for reading database

import sys
import datetime
import sqlite3
from flask import Flask, jsonify, render_template
from threading import Thread
import time


app = Flask(__name__)
values = [[], [], []]  # data, last values (with coords), coords


def read_args():
    """ Read arguments and return path of database.
    :return: path of database (string).
    """
    def usage():
        print("usage: python monitor.py path/of/database.db")

    args = sys.argv[1:]
    if '-h' in args or '--help' in args or not args:
        usage()
        sys.exit()
    return args[0]


def dt2jst(dt):
    """ Convert python 'datetime' object to javascript 'time' object.
    :param dt: datetime object.
    :return dt: javascript time as int.
    """
    # with x 1000 to convert to javascript time
    return int(time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S')))


def prettydt(dt):
    """ Convert datetime string.
    :param dt: datetime string (%Y-%m-%d %H:%M:%S format).
    :return: datetime string (%d/%m/%Y %H:%M:%S format).
    """
    pydt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    return pydt.strftime('%d/%m/%Y %H:%M:%S')


def poll_data(fndb):
    """ Read data from the database and save it.
    :param fndb: path of SQLite database (string).
    """
    while True:
        # Open database and read the last 100 rows
        conn = sqlite3.connect(fndb)
        curs = conn.cursor()
        try:
            curs.execute("""
                SELECT dt, value, lon, lat
                FROM data
                LIMIT 100 OFFSET (SELECT count(*) FROM data) - 100
            """)
            db = curs.fetchall()
        except sqlite3.OperationalError:
            print("sqlite3 error: cannot read database !")
            time.sleep(sleep)
            continue

        # list of (time, value) for the chart
        data = [(dt2jst(dt) * 1000, value)
                for dt, value, lon, lat in db]

        # last record (and convert datetime in a pretty format)
        # it will be use to add a marker inside map and show last value in a
        # tooltip.
        last = list(db[-1])
        last[0] = prettydt(last[0])

        # list of coords (lat, lon) for polyline
        coords = [(lat, lon) for dt, value, lon, lat in db]

        # save data
        values[0], values[1], values[2] = data, last, coords

        # clone database connection
        curs.close()
        conn.close()
        time.sleep(sleep)


@app.route('/')
def home():
    """ Homepage. """
    return render_template('index.html', sleepms=sleep * 1000)


@app.route('/data')
def data():
    """ Export data in JSON format. """
    return jsonify(values=values[0], last=values[1], coords=values[2])


def main():

    # Read path of database from arguments
    fndb = read_args()

    # Run a thread to read data
    thr = Thread(target=poll_data, args=(fndb, ))
    thr.daemon = True
    thr.start()

    # Start application
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
