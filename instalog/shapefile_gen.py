import pandas as pd
from shapely.geometry import Point, LineString
import geopandas as gpd
from datetime import datetime
import os
from .path_utils import new_path

class ShapefileGenerator:
    def __init__(self, output_dir, callback):
        self.output_dir = output_dir
        self.callback = callback

        self.date = None
        self.counter = None
    
    def continue_data(self, data):
        '''Updates attributes for when old data is being added on to'''
        if not data.get('status'):
            self.date = None
            self.counter = None
        else:
            self.date = data['date']
            self.counter = data['counter']

    def generate(self):
        '''Starts shapefile generation'''
        obs_csv_path = self.callback('get obs csv path')
        track_csv_path = self.callback('get track csv path')

        # If nothing has been saved, csv_path will be "None", so terminate program
        if not obs_csv_path:
            return
        
        obs_df = pd.read_csv(obs_csv_path)
        track_df = pd.read_csv(track_csv_path)

        self.add_obs_geometry(obs_df)
        self.add_track_geometry(track_df)

        self.write_shapefile('track', track_df)
        self.write_shapefile('obs', obs_df)

    def add_obs_geometry(self, df):
        '''Adds geometry column of "Point" objects to provided dataframe'''
        points = []
        for i in range(len(df)):
            point = Point(df.iloc[i]['Longitude'], df.iloc[i]['Latitude'])
            points.append(point)

        df['Geometry'] = points
    
    def add_track_geometry(self, df):
        '''Adds geometry column of "LineString" objects to provided dataframe'''
        linestrings = []
        for i in range(len(df) - 1):
            start = (df.iloc[i]['Longitude'], df.iloc[i]['Latitude'])
            end = (df.iloc[i + 1]['Longitude'], df.iloc[i + 1]['Latitude'])
            ls = LineString([start, end])
            linestrings.append(ls)

        # Add last element twice since entries can't be empty
        if linestrings:
            linestrings.append(linestrings[-1])

        df['Geometry'] = linestrings

    def write_shapefile(self, type, df):
        '''Writes shapefile of given type to output directory'''
        gdf = gpd.GeoDataFrame(df, geometry='Geometry')
        gdf.set_crs(epsg=4326, inplace=True)

        if self.date:
            dir_name = f'{self.date}_{type}' if self.counter == '0' else f'{self.date}_{type}_{self.counter}'
            filename = dir_name + '.shp'
            output_path = os.path.join(self.output_dir, dir_name, filename)
        else:
            date = datetime.today().strftime('%d%b%Y')
            name = f'{date}_{type}'
            dir = f'{self.output_dir}/{name}'
            if os.path.exists(dir):
                dir = new_path(dir)
            output_path = os.path.join(dir, name + '.shp')

            os.makedirs(dir, exist_ok=True) # Need to make directory before writing

        gdf.to_file(output_path)