import serial
import serial.tools.list_ports
import threading
import time
from tkinter import messagebox
import sys
from datetime import datetime
import pandas as pd

class GpsManager:
    def __init__(self, baud_rate, callback):
        self.baud_rate = baud_rate
        self.callback = callback

        # self.find_gps_port()

        self.coords = (0.0, 0.0)
        self.track_df = pd.DataFrame(columns=['Time', 'Latitude', 'Longitude'])
    
    def get_track_df(self):
        return self.track_df
    
    def get_coords(self):
        return self.coords

    def find_gps_port(self):
        '''
        - Finds the GPS port by connecting to all ports and looking for specific
        NMEA sentences
        - Once valid sentences are found, collects the valid NMEA sentence types 
        and saves the port.
        '''
        self.sentence_types = [None, None, None]
        self.port = None

        ports = serial.tools.list_ports.comports()
        gps_sentences = ['$GPGGA', '$GPRMC', '$GPGLL']
        for port in ports:
            try:
                with serial.Serial(port.device, baudrate=self.baud_rate, timeout=1) as ser:
                    start_time = time.time()
                    while time.time() - start_time < 5:
                        data = ser.readline()
                        for i in range(len(gps_sentences)):
                            sentence_bytes = gps_sentences[i].encode('utf-8')
                            if sentence_bytes in data:
                                sentence_str = gps_sentences[i]
                                if sentence_str not in self.sentence_types:
                                    self.sentence_types[i] = sentence_str
                                    self.port = port.device
                        if self.sentence_types == gps_sentences:
                            return
            except Exception as e:
                messagebox.showerror('Error', f'Error accessing port {port.device}: {e}')
                sys.exit()

        if not self.port:
            messagebox.showerror('Error', 'Could not find a connected GPS')
            sys.exit()

    def init_gps_thread(self):
        '''Starts thread for regularly reading coordinates in the background'''
        self.gps_thread = threading.Thread(target=self.start_reading)
        self.gps_thread.daemon = True
        self.gps_thread.start()

    def start_reading(self):
        '''Retrieves coordinates every 3 seconds'''
        while True:
            self.coords = self.read_coords()
            row = [datetime.now().time().replace(microsecond=0),
                   self.coords[0],
                   self.coords[1]]
            self.track_df.loc[len(self.track_df)] = row
            time.sleep(1)

    def read_coords(self) -> tuple[float]:
        '''
        - Attempts to read and return coordinates from the GPS
        - Upon failure, displays an error message in the GUI and returns
        the last recorded coordinates instead
        '''
        lat, lon = 0.0, 0.0

        start_time = time.time()
        with serial.Serial(port=self.port, baudrate=self.baud_rate, timeout=1) as ser:
            # Read for right sentence with valid data for 5 seconds
            while time.time() - start_time < 5:
                num_types = sum(element != None for element in self.sentence_types)
                line = ser.readline().decode('utf-8', errors='replace')
                if line.startswith(self.sentence_types[0]):
                    # $GPGGA,123519.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
                    parts = line.split(',')
                    if parts[6] == '1' or parts[6] == '2':
                        lat, lon = self.ddm2dd(((parts[2], parts[3]), (parts[4], parts[5])))
                        self.coords = lat, lon
                        self.callback('clear errors')
                    break
                elif num_types >= 2 and line.startswith(self.sentence_types[1]):
                    # $GPRMC,123519.00,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
                    parts = line.split(',')
                    if parts[2] == 'A':
                        lat, lon = self.ddm2dd(((parts[3], parts[4]), (parts[5], parts[6])))
                        self.coords = lat, lon
                        self.callback('clear errors')
                    break
                elif num_types == 3 and line.startswith(self.sentence_types[2]):
                    # $GPGLL,4807.038,N,01131.000,E,013604,A,A*54
                    parts = line.split(',')
                    if parts[6] == 'A':
                        lat, lon = self.ddm2dd(((parts[1], parts[2]), (parts[3], parts[4])))
                        self.coords = lat, lon
                        self.callback('clear errors')
                    break

        if (lat, lon) == (0.0, 0.0) and not self.callback('has read error'):
            self.callback('show read error')

        return self.coords

    def ddm2dd(self, coordinates: tuple[tuple[str]]) -> tuple[float]:
        '''
        - Converts coordinates from degrees and decimal minutes to decimal degrees
        - Example input: (('3519.2344', 'N'), ('12059.9621', 'W'))
        '''
        ddm_lat, ddm_lon = coordinates
        lat_degrees = float(ddm_lat[0][:2])
        lat_mins = float(ddm_lat[0][2:])
        lon_degrees = float(ddm_lon[0][:3])
        lon_mins = float(ddm_lon[0][3:])

        lat = lat_degrees + (lat_mins / 60)
        lon = lon_degrees + (lon_mins / 60)

        lat = lat if ddm_lat[1] == 'N' else -lat
        lon = lon if ddm_lon[1] == 'E' else -lon

        return round(lat, 6), round(lon, 6)