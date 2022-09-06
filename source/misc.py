import glob 
from datetime import date 
import pandas as pd 
import glob 
#import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import json 
import geopandas as gp 

###########################################################################################################################################################################
#Set global variables

# Read the keys to maps and data access
try:
    f = open('source/keys.json','r')
except:
    f = open('keys.json','r')
keys = json.load(f)
f.close()

# Read the json containing the information for each project
f = open('/mnt/c/Users/nicolas/Documents/2021_IWA/iwa-web/data/projects.json','r')
watersheds = json.load(f)
f.close()

#Get the access tocken to mapbox
mapbox_access_token = keys['mapbox']['token']

#Paths to things that the code uses 
path_maps = '/mnt/c/Users/nicolas/Documents/2021_IWA/iwa-web/data/'

###########################################################################################################################################################################
#Define the class that will perform all
class misc:
    def __init__(self):
        #Define the watershed to present
        self.wat_name = 'clearcreek'
        self.watershed = watersheds[self.wat_name]        
        self.usgs = pd.read_csv('%s%s/usgs.csv' % (path_maps,self.wat_name))
        self.projects = pd.read_csv('%s%s/projects.csv' % (path_maps,self.wat_name))
        self.network = pd.read_csv('%s%s/net.csv' % (path_maps,self.wat_name), index_col = 0)

        projects = []
        for k in watersheds.keys():
            projects.append({'value':k, 'label':watersheds[k]['name']})
        self.proj_names = projects

    def plot_map(self):
                
        #Reads the watershed divisory lines
        f = open('%s%s/divisory.json' % (path_maps, self.wat_name))
        geoJSON_div = json.load(f)
        f.close()
        color_wat = 'rgba(0,0,50,0.1)'

        #Reads the watershed network for plot purposes
        f = open('%s%s/net.geojson' % (path_maps, self.wat_name))
        geoJSON_net = json.load(f)
        f.close()
        color_net = '#045a8d'


        #Adds the USGS gauges in the region
        t = ['id:0%d' % self.usgs.loc[i,'USGS_ID'] for i in self.usgs.index]
        fig = go.Figure(go.Scattermapbox(
            mode = "markers",
            lon = self.usgs.x,
            lat = self.usgs.y,
            marker = go.scattermapbox.Marker(
                    size=15,
                    color = 1),
            text = t))

        #Adds the USGS gauges in the region
        t = ['%s' % self.projects.loc[i,'ID'] for i in self.projects.index]
        fig = fig.add_trace(go.Scattermapbox(
            mode = "markers",
            lon = self.projects.x,
            lat = self.projects.y,
            marker = {'size': 20},
            text = t))

        #Adds the centroids of the network
        t = ['%s' % i for i in self.network.index]
        fig = fig.add_trace(go.Scattermapbox(
            mode = "markers",
            lon = self.network.x,
            lat = self.network.y,
            marker = {'size': 3, 'color':color_net},
            text = t))

        fig.update_layout(
            hovermode='closest',
            showlegend=False,
            margin ={'l':0,'t':0,'b':0,'r':0},
            mapbox=dict(
                layers=[
                    dict(
                        sourcetype = 'geojson',
                        source = geoJSON_div,
                        type = 'fill',
                        color = color_wat
                    ),
                    dict(
                        sourcetype = 'geojson',
                        source = geoJSON_net,
                        type = 'line',
                        color = color_net
                    )
                ],
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(                    
                    lat=self.watershed['coord'][1],
                    lon=self.watershed['coord'][0]
                ),
                pitch=0,
                zoom=10,                  
                #style='mapbox://styles/nicolas998/cl12cdq1n000n15mfyfgq8eoi',
                style = 'mapbox://styles/nicolas998/cl7q76nvn000815ohwwz5evh0'                
            )
        )
        return fig