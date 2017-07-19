#!/usr/bin/env python3.5
# coding: utf-8

'''Show streaming graph of database.'''


import io
import datetime
import pandas
import pymysql
from flask import Flask, jsonify, render_template, request, send_file
from threading import Thread
import time


mysqlinfo = {
    'host': 'vmli-bdd',
    'user': 'jv',
    'passwd': 'jv',
    'db': 'afficheurqa'
}


sleep = 2  # timestep for reading database

app = Flask(__name__)
values = [[], [], []]  # data, last values (with coords), coords

# Open database
conn = pymysql.connect(**mysqlinfo)
curs = conn.cursor()


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
            curs.execute("""
                SELECT dt, value1, value2, value3, lon, lat
                FROM data
                ORDER BY dt DESC LIMIT 100
            """)
            db = curs.fetchall()[::-1]
        except pymysql.Error:
            print("mysql error: cannot read database !")
            time.sleep(sleep)
            continue

        # list of (time, value) for the chart
        data1 = [(dt2jst(dt) * 1000, value1)
                 for dt, value1, value2, value3, lon, lat in db]
        data2 = [(dt2jst(dt) * 1000, value2)
                 for dt, value1, value2, value3, lon, lat in db]
        data3 = [(dt2jst(dt) * 1000, value3)
                 for dt, value1, value2, value3, lon, lat in db]

        # last record (and convert datetime in a pretty format)
        # it will be use to add a marker inside map and show last value in a
        # tooltip.
        last = list(db[-1])
        last[0] = prettydt(last[0])

        # list of coords (lat, lon) for polyline
        coords = [(lat, lon) for dt, value1, value2, value3, lon, lat in db]

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

    sql = ("INSERT INTO data (dt, value1, value2, value3, lon, lat) "
           "VALUES ('{now:%Y-%m-%d %H:%M:%S}', {value1}, {value2}, {value3}, "
           "{lon}, {lat})").format(**locals())
    curs.execute(sql)
    conn.commit()

    return jsonify(status='ok')


@app.route('/export.csv')
def export_data():
    """ Export data. """
    sql = "SELECT dt, value1, value2, value3, lon, lat FROM data ORDER BY dt"
    df = pandas.read_sql(sql, conn)

    f = io.BytesIO()
    writer = pandas.ExcelWriter(f, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='data')
    writer.close()

    f.seek(0)

    return send_file(f, attachment_filename="data.xlsx",
                     as_attachment=True)


def main():

    # Run a thread to read data
    thr = Thread(target=poll_data)
    thr.daemon = True
    thr.start()

    # Start application
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
