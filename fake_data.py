#!/usr/bin/env python3.5
# coding: utf-8

""" Create SQLite3 database and add fake data (value, lon, lat). """


# Configuration
initvalue, initlon, initlat = 0, 5., 45.
dvalue, dlon, dlat = (-20, 20), (-.001, .001), (0., .001)
sleep = 2


import os
import sys
import sqlite3
import datetime
import time
import random


def rand(init, mn, mx):
    """ Add a random value.
    :param init: initial value (int or float).
    :param mn: minimal limit for the random value to add (int or float).
    :param mx: maximal limit for the random value to add (int or float).
    :return: initial value + random value (float).
    """
    return init + random.uniform(mn, mx)


def read_args():
    """ Read arguments and return path of database.
    :return: path of database (string).
    """
    def usage():
        print("usage: python fake_data.py path/of/database.db")

    args = sys.argv[1:]
    if '-h' in args or '--help' in args or not args:
        usage()
        sys.exit()
    return args[0]


def main():
    # Read arguments
    fndb = read_args()

    # Create table query if the file does not exits
    createdb = not os.path.isfile(fndb)

    # Database connection (sqlite3)
    conn = sqlite3.connect(fndb)
    curs = conn.cursor()

    # Create table query
    if createdb:
        curs.execute(
            "CREATE TABLE data (dt datetime, value real, lon real, lat real)")
        conn.commit()
        print("sqlite3: create table ok")

    # Infinite loop and add data into database
    oldvalue, oldlon, oldlat = initvalue, initlon, initlat
    while True:
        try:
            # Date and time and generate random data
            dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            v = rand(oldvalue, *dvalue)
            lon = rand(oldlon, *dlon)
            lat = rand(oldlat, *dlat)

            # Show data and insert into the database
            print("{dt}  {v:8.3f}, {lon:10.6f}, {lat:10.6f}".format(
                **locals()))
            curs.execute("""
                INSERT INTO data (dt, value, lon, lat)
                VALUES (?, ?, ?, ?)
            """, (dt, v, lon, lat))
            conn.commit()

            oldvalue, oldlon, oldlat = v, lon, lat
            time.sleep(sleep)

        except KeyboardInterrupt:
            break

    # Close database connection
    curs.close()
    conn.close()


if __name__ == '__main__':
    main()
