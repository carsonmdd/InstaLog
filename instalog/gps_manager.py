import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
import pandas as pd
import os
import csv
from .path_utils import new_path

class GpsManager:
    def __init__(self, baud_rate, callback, output_dir, create_output=False):
        self.baud_rate = baud_rate
        self.callback = callback
        self.output_dir = output_dir
        self.create_output = create_output

        self.coords = (0.0, 0.0)
        self.track_df = pd.DataFrame(columns=['Time', 'Latitude', 'Longitude'])
        self.csv_path = None
        self.date = None
        self.counter = None
    
    def get_track_df(self):
        '''Returns track dataframe'''
        return self.track_df
    
    def get_coords(self):
        '''Returns last recorded coordinates'''
        return self.coords
    
    def set_create_output(self, create_output):
        '''Sets self.create_output'''
        self.create_output = create_output

    def continue_data(self, data):
        '''Updates attributes for when old data is being added on to'''
        if not data.get('status'):
            self.csv_path = None
            self.track_df = pd.DataFrame(columns=['Time', 'Latitude', 'Longitude'])
            self.create_output = False
        else:
            date = data['date']
            counter = data['counter']
            csv_name = f'{date}_track.csv' if counter == '0' else f'{date}_track_{counter}.csv'
            self.csv_path = os.path.join(self.output_dir, csv_name)
            # old_track_df = pd.read_csv(self.csv_path)
            # self.track_df = pd.concat([old_track_df, self.track_df], ignore_index=True)
            self.track_df = pd.read_csv(self.csv_path)

    def find_gps_port(self) -> str:
        '''
        - Finds the GPS port by connecting to all ports and looking for specific
        NMEA sentences
        - Once valid sentences are found, collects the valid NMEA sentence types 
        and saves the port
        - Returns error msg if error else empty string
        '''
        self.sentence_types = [None, None, None]
        self.port = None

        ports = serial.tools.list_ports.comports()
        gps_sentences = ['$GPGGA', '$GPRMC', '$GPGLL']
        for port in ports:
            try:
                with serial.Serial(port.device, baudrate=self.baud_rate, timeout=1) as ser:
                    start_time = time.time()
                    # CHANGE TO 5 SECONDS SEARCHING ##########################
                    while time.time() - start_time < 3: # Listening on each port for 5 seconds max
                        data = ser.readline()
                        for i in range(len(gps_sentences)): # Checking if the line read is a valid sentence type
                            sentence_bytes = gps_sentences[i].encode('utf-8')
                            if sentence_bytes in data:
                                sentence_str = gps_sentences[i]
                                if sentence_str not in self.sentence_types:
                                    self.sentence_types[i] = sentence_str
                                    self.port = port.device
                        if self.sentence_types == gps_sentences: # If all valid sentence types were already found, quit searching
                            self.init_gps_thread()
                            return ''
            except Exception as e:
                return f'Error accessing port {port.device}: {e}'
            
        if not self.port:
            return 'Could not find a connected GPS'
        else:
            self.init_gps_thread()
            return ''

    def init_gps_thread(self):
        '''Starts thread for regularly reading coordinates in the background'''
        # daemon=True ensures thread exits when mainloop terminates
        self.gps_thread = threading.Thread(target=self.start_reading, daemon=True)
        self.gps_thread.start()

    def start_reading(self):
        '''Tries to read coordinates every second'''
        while True:
            self.coords = self.read_coords()
            row = [datetime.now().time().replace(microsecond=0),
                   self.coords[0],
                   self.coords[1]]
            # print()
            # print(self.track_df.columns)
            # print()
            self.track_df.loc[len(self.track_df)] = row # Adding every coord read w/ timestamp to track dataframe
            self.save()
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
            # Read for valid sentence with valid data for 5 seconds
            while time.time() - start_time < 5:
                num_types = sum(element != None for element in self.sentence_types)
                line = ser.readline().decode('utf-8', errors='replace')
                if line.startswith(self.sentence_types[0]):
                    # Ex: $GPGGA,123519.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
                    parts = line.split(',')
                    try: # Use try-except for cases where sentence is incomplete
                        if parts[6] == '1' or parts[6] == '2':
                            lat, lon = self.ddm2dd(((parts[2], parts[3]), (parts[4], parts[5])))
                            self.coords = lat, lon
                            if self.callback('has read error'):
                                self.callback('clear errors')
                        break
                    except:
                        pass
                elif num_types >= 2 and line.startswith(self.sentence_types[1]):
                    # Ex: $GPRMC,123519.00,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
                    parts = line.split(',')
                    try:
                        if parts[2] == 'A':
                            lat, lon = self.ddm2dd(((parts[3], parts[4]), (parts[5], parts[6])))
                            self.coords = lat, lon
                            if self.callback('has read error'):
                                self.callback('clear errors')
                        break
                    except:
                        pass
                elif num_types == 3 and line.startswith(self.sentence_types[2]):
                    # Ex: $GPGLL,4807.038,N,01131.000,E,013604,A,A*54
                    parts = line.split(',')
                    try:
                        if parts[6] == 'A':
                            lat, lon = self.ddm2dd(((parts[1], parts[2]), (parts[3], parts[4])))
                            self.coords = lat, lon
                            if self.callback('has read error'):
                                self.callback('clear errors')
                        break
                    except:
                        pass
        # Shows read error if coords could not be updated and read error isn't already shown
        if (lat, lon) == (0.0, 0.0) and not self.callback('has read error'):
            self.callback('show read error')

        return self.coords

    def ddm2dd(self, coordinates: tuple[tuple[str]]) -> tuple[float]:
        '''
        - Converts coordinates from degrees and decimal minutes to decimal degrees
        - Example input: (('3519.2344', 'N'), ('12059.9621', 'W'))
        '''
        # Retrieving degrees and minutes
        ddm_lat, ddm_lon = coordinates
        lat_degrees = float(ddm_lat[0][:2])
        lat_mins = float(ddm_lat[0][2:])
        lon_degrees = float(ddm_lon[0][:3])
        lon_mins = float(ddm_lon[0][3:])

        # Calculating new coord absolute values
        lat = lat_degrees + (lat_mins / 60)
        lon = lon_degrees + (lon_mins / 60)

        # Handling signs based on input directions
        lat = lat if ddm_lat[1] == 'N' else -lat
        lon = lon if ddm_lon[1] == 'E' else -lon

        return round(lat, 6), round(lon, 6)
    
    def save(self):
        '''Writes the contents of the track dataframe to the track csv'''
        if not self.create_output:
            return

        # Creates a new CSV path if it does not exist
        if not self.csv_path:
            date = datetime.today().strftime('%d%b%Y')
            csv_name = f'{date}_track'
            self.csv_path = os.path.join(self.output_dir, csv_name + '.csv')
            if os.path.exists(self.csv_path):
                self.csv_path = new_path(self.csv_path)
        
        self.track_df.to_csv(self.csv_path, index=False)