#!/usr/bin/env python3.5
# coding: utf-8

'''Show streaming graph of database.'''


import io
import os
import datetime
import logging
from dbinfo import dsn
import pandas
import psycopg2
from flask import Flask, jsonify, render_template, request, send_file
from threading import Thread
import time


log = logging.getLogger()
log.info("Starting application")

root = os.path.dirname(__file__)

sleep = 2  # timestep for reading database

app = Flask(__name__)
values = [[], [], []]  # data, last values (with coords), coords


# Open database
class Database():
    def __init__(self, dsn):
        self.dsn = dsn

    def __enter__(self):
        self._connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._disconnect()

    def _connect(self):
        self.conn = psycopg2.connect(self.dsn)
        self.curs = self.conn.cursor()
        log.debug("connection database ok")

    def _disconnect(self):
        self.curs.close()
        self.conn.close()
        log.debug("connection database closed")

    def execute(self, sql):
        self._connect()
        log.debug("running SQL: %s" % sql)
        self.curs.execute(sql)
        self.conn.commit()
        self._disconnect()

    def execute_and_fetch_all(self, sql):
        self._connect()
        log.debug("running SQL: %s" % sql)
        self.curs.execute(sql)
        res = self.curs.fetchall()
        self._disconnect()
        return res


db = Database(dsn)


def dt2jst(dt):
    """ Convert python 'datetime' object to javascript 'time' object.
    :param dt: datetime object.
    :return dt: javascript time as int.
    """
    # with x 1000 to convert to javascript time
    return int(
        time.mktime(
            time.strptime(
                dt.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')))


def prettydt(dt):
    """ Convert datetime string.
    :param dt: datetime stdring (%Y-%m-%d %H:%M:%S format).
    :return: datetime string (%d/%m/%Y %H:%M:%S format).
    """
    pydt = datetime.datetime.strptime(
        dt.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    return pydt.strftime('%d/%m/%Y %H:%M:%S')


def poll_data():
    """ Read data from the database and save them into list.
    """
    while True:
        # Read the last 100 rows
        try:
            res = db.execute_and_fetch_all("""
                SELECT dt, value1, value2, value3, lon, lat
                FROM qa.data
                ORDER BY dt DESC LIMIT 100
            """)
            res = res[::-1]
        except psycopg2.OperationalError:
            log.error("error: cannot read database !")
            time.sleep(sleep)
            continue

        if not res:
            time.sleep(sleep)
            continue

        # list of (time, value) for the chart
        data1 = [(dt2jst(dt) * 1000, float(value1))
                 for dt, value1, value2, value3, lon, lat in res]
        data2 = [(dt2jst(dt) * 1000, float(value2))
                 for dt, value1, value2, value3, lon, lat in res]
        data3 = [(dt2jst(dt) * 1000, float(value3))
                 for dt, value1, value2, value3, lon, lat in res]

        # last record (and convert datetime in a pretty format)
        # it will be use to add a marker inside map and show last value in a
        # tooltip.
        last = list(res[-1])
        last[0] = prettydt(last[0])
        last[1:] = [float(e) for e in last[1:]]

        # list of coords (lat, lon) for polyline
        coords = [(float(lat), float(lon))
                  for dt, value1, value2, value3, lon, lat in res]

        # save data
        values[0], values[1], values[2] = [data1, data2, data3], last, coords

        # wait
        time.sleep(sleep)


@app.route('/')
def home():
    """ Homepage. """
    return render_template('index.html', sleepms=sleep * 1000)


@app.route('/data')
def data():
    """ Export data in JSON format. """
    return jsonify(values=values[0], last=values[1], coords=values[2])


@app.route('/import')
def import_data():
    """ Import data into database. """
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    value1 = request.args.get('value1', 'NULL')
    value2 = request.args.get('value2', 'NULL')
    value3 = request.args.get('value3', 'NULL')
    now = datetime.datetime.utcnow()

    if lon is None:
        return jsonify(status='error', message='pas de données lon'), 400

    if lat is None:
        return jsonify(status='error', message='pas de données lat'), 400

    sql = ("INSERT INTO qa.data (dt, value1, value2, value3, lon, lat) "
           "VALUES ('{now:%Y-%m-%d %H:%M:%S}', {value1}, {value2}, {value3}, "
           "{lon}, {lat})").format(**locals())
    db.execute(sql)

    return jsonify(status='ok')


@app.route('/export.csv')
def export_data():
    """ Export data. """
    sql = "SELECT dt, value1, value2, value3, lon, lat FROM qa.data ORDER BY dt"
    with Database(dsn) as db:
        df = pandas.read_sql(sql, db.conn)

    f = io.BytesIO()
    writer = pandas.ExcelWriter(f, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='data')
    writer.close()

    f.seek(0)

    return send_file(f, attachment_filename="data.xlsx",
                     as_attachment=True)


@app.route('/clean')
def clean():
    """ Clean database. """
    sql = "DELETE FROM qa.data"
    db.execute(sql)

    return jsonify(status='ok')


@app.route('/doc')
def doc():
    with open(os.path.join(root, 'HOWTO.md'), 'rb') as f:
        txt = f.read().decode('utf-8')
    return "<pre>" + txt + "</pre>"


# Run a thread to read data
thr = Thread(target=poll_data)
thr.daemon = True
thr.start()


if __name__ == '__main__':
    # Start application
    app.run(host='0.0.0.0', port=9877, debug=True)
