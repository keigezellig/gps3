#!/usr/bin/env python3.5
# coding=utf-8
"""Threaded gps client"""
from __future__ import print_function

from threading import Thread
from time import sleep

try:  # This kludge to get around imports with files and directories the same name.
    import agps3  # Python 3
except ImportError:
    from . import agps3  # Python 2

__author__ = 'Moe'
__copyright__ = 'Copyright 2016  Moe'
__license__ = 'MIT'
__version__ = '0.2.3'

HOST = '127.0.0.1'  # gpsd
GPSD_PORT = 2947  # defaults
PROTOCOL = 'json'  # "


class AGPS3mechanism(object):
    """Create threaded data stream as updated object attributes
    """

    def __init__(self):
        self.socket = agps3.GPSDSocket()
        self.data_stream = agps3.DataStream()

    def stream_data(self, host=HOST, port=GPSD_PORT, enable=True, gpsd_protocol=PROTOCOL, devicepath=None, on_datareceived=None):
        """ Connect and command, point and shoot, flail and bail. on_datareceived is callback which is fired when data is received
        """
        self.socket.connect(host, port)
        self.socket.watch(enable, gpsd_protocol, devicepath)
        self.on_datareceived = on_datareceived

    def unpack_data(self, usnap=.2):  # 2/10th second sleep between empty requests
        """ Iterates over socket response and unpacks values of object attributes.
        Sleeping here has the greatest response to cpu cycles short of blocking sockets
        """
        for new_data in self.socket:
            if new_data:
                self.data_stream.unpack(new_data)
                if self.on_datareceived is not None:
                    self.on_datareceived(self.data_stream)
            else:
                sleep(usnap)  # Sleep in seconds after an empty look up.

    def run_thread(self, usnap=.2, daemon=True):
        """run thread with data
        """
        # self.stream_data() # Unless other changes are made this would limit to localhost only.
        try:
            gps3_data_thread = Thread(target=self.unpack_data, args={usnap: usnap}, daemon=daemon)
        except TypeError:
            # threading.Thread() only accepts daemon argument in Python 3.3
            gps3_data_thread = Thread(target=self.unpack_data, args={usnap: usnap})
            gps3_data_thread.setDaemon(daemon)
        gps3_data_thread.start()

    def stop(self):
        """ Stop as much as possible, as gracefully as possible, if possible.
        """
        self.stream_data(enable=False)  # Stop data stream, thread is on its own so far.
        print('Process stopped by user')
        print('Good bye.')  # You haven't gone anywhere, re-start it all with 'self.stream_data()'


if __name__ == '__main__':

    def callback(data):
        print ("******* Hello from callback...")
        print('\nTime {}'.format(data.time))
        print('Lat:{}  Lon:{}  Speed:{}  Course:{}\n'.format(data.lat,
                                                             data.lon,
                                                             data.speed,
                                                             data.track))
    from misc import add_args
    try:

        args = add_args()

        agps3_thread = AGPS3mechanism()  # The thread triumvirate
        if args.use_callback:
            agps3_thread.stream_data(host=args.host, port=args.port, gpsd_protocol=args.gpsd_protocol, on_datareceived=callback)
        else:
            agps3_thread.stream_data(host=args.host, port=args.port, gpsd_protocol=args.gpsd_protocol, on_datareceived=None)

        agps3_thread.run_thread(usnap=.2)  # Throttle sleep between empty lookups in seconds defaults = 0.2 of a second.

        while True:
            if not args.use_callback:
                seconds_nap = int(args.seconds_nap)  # Threaded Demo loop 'seconds_nap' is not the same as 'usnap'
                for nod in range(0, seconds_nap):
                    print('{:.0%} wait period of {} seconds'.format(nod / seconds_nap, seconds_nap), end='\r')
                    sleep(1)

                print('\nGPS3 Thread still functioning at {}'.format(agps3_thread.data_stream.time))
                print('Lat:{}  Lon:{}  Speed:{}  Course:{}\n'.format(agps3_thread.data_stream.lat,
                                                                     agps3_thread.data_stream.lon,
                                                                     agps3_thread.data_stream.speed,
                                                                     agps3_thread.data_stream.track))            
    except KeyboardInterrupt:
        agps3_thread.stop()
    #
######
# END
