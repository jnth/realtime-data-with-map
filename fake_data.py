#!/usr/bin/env python3.5
# coding: utf-8

""" Create SQLite3 database and add fake data (value, lon, lat). """


import requests
import datetime
import time
import random


# Configuration
url = "http://0.0.0.0:9876"
initvalue, initlon, initlat = 50, 5., 45.
dvalue, dlon, dlat = (-20, 20), (-.001, .001), (0., .001)
minvalue, maxvalue = 0, 200
sleep = 2


def rand(init, mn, mx):
    """ Add a random value.
    :param init: initial value (int or float).
    :param mn: minimal limit for the random value to add (int or float).
    :param mx: maximal limit for the random value to add (int or float).
    :return: initial value + random value (float).
    """
    value = init + random.uniform(mn, mx)
    if value > maxvalue:
        value = maxvalue
    if value < minvalue:
        value = minvalue
    return value


def main():
    # Infinite loop and add data into database
    oldvalue1, oldvalue2, oldvalue3, oldlon, oldlat = initvalue, initvalue, initvalue, initlon, initlat
    while True:
        try:
            # Date and time and generate random data
            dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            v1 = rand(oldvalue1, *dvalue)
            v2 = rand(oldvalue2, *dvalue)
            v3 = rand(oldvalue3, *dvalue)
            lon = rand(oldlon, *dlon)
            lat = rand(oldlat, *dlat)

            # Show data and insert into the database
            print("{dt}  {v1:8.3f}, {v2:8.3f}, {v3:8.3f}, {lon:10.6f}, {lat:10.6f}".format(
                **locals()))

            # Send data by http
            r = requests.get("{}/import?lon={}&lat={}&value1={}&value2={}&value3={}".format(url, lon, lat, v1, v2, v3))
            if r.status_code == 200:
                print("-> ok")
            else:
                print("-> erreur {}".format(r.status_code))

            oldvalue1, oldvalue2, oldvalue3, oldlon, oldlat = v1, v2, v3, lon, lat
            time.sleep(sleep)

        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
