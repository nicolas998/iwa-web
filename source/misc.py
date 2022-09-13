import glob 
from datetime import date 
import pandas as pd 
import glob 
#import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import json 
import geopandas as gp 
import base64
###########################################################################################################################################################################
#Set global variables

# Read the keys to maps and data access
try:
    f = open('source/keys.json','r')
except:
    f = open('keys.json','r')
keys = json.load(f)
f.close()

#Paths to things that the code uses 
path_maps = '../data/'

# Read the json containing the information for each project
#f = open('/mnt/c/Users/nicolas/Documents/2021_IWA/iwa-web/data/projects.json','r')
f = open(path_maps+'/projects.json','r')
watersheds = json.load(f)
f.close()

#Get the access tocken to mapbox
mapbox_access_token = keys['mapbox']['token']

#Project images 
proj_images = {"GRADE STABILIZATION": "grade_stabilizations.jpg",
     "POND": "ponds.jpg", 
     "POND & FRINGE WETLAND": "ponds.jpg",
     "WASCOB":"wascobs.jpg",     
    "GRASSED WATERWAY":"grass_waterways.png",
     "WETLAND RESTORATION":"wetlands.png",     
    "FLOODPLAIN RESTORATION":"terraces.jpg",
     "PERENNIAL COVER":"perennial_cover.jpg"}

###########################################################################################################################################################################
#Define the class that will perform all
class misc:
    def __init__(self):
        #Define the watershed to present
        self.wat_name = 'clearcreek'
        self.watershed = watersheds[self.wat_name]        
        self.usgs = pd.read_csv('%s%s/usgs.csv' % (path_maps,self.wat_name))
        self.projects = pd.read_csv('%s%s/project_locations.csv' % (path_maps,self.wat_name))
        self.__projects_assign_id__()
        self.network = pd.read_csv('%s%s/net.csv' % (path_maps,self.wat_name), index_col = 0)
        #Define watersheds with projects
        projects = []
        for k in watersheds.keys():
            projects.append({'value':k, 'label':watersheds[k]['name']})
        self.proj_names = projects
        #Define selected items
        self.selected_project = None
        self.selected_usgs = None
        self.selected_link = 1
        #Image 
        self.img_png = '../assets/grade_stabilizations.jpg'
        self.img_base64 = base64.b64encode(open(self.img_png, 'rb').read()).decode('ascii')
        self.img_source = 'data:image/png;base64,{}'.format(self.img_base64)

    def update_click_selection(self, text):
        if text.startswith('CC'):
            self.selected_project = text
            self.__projects_update_image__()
        elif text.startswith('US'):
            self.selected_usgs = text
        else:
            self.selected_link = int(text)
            #self.plot_selected_link()

    def plot_selected_link_streamflow(self):
        #Read the data of the selected link (This has to be changed)
        path2simulations = '../../web_testing_ClearCreek/segment_analysis/CC_output/outflow '+str(self.selected_link)+'/timeseries_seg_'+str(self.selected_link)+'_US.csv'
        q = pd.read_csv(path2simulations, index_col=0)
        q = q.loc[300:600]
        q.loc[q['Qcontrol']<0,'Qcontrol'] = np.nan
        #Make the plot 
        fig = go.Figure()
        fig.add_trace(
                go.Scatter(x=list(q.index), 
                    y=list(q.Qcontrol), 
                    name = 'Control', line=dict(width=4)))
        fig.add_trace(
                go.Scatter(x=list(q.index), y=list(q.Qproject), 
                    name = 'Project', line=dict(width=4)))
        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = False,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "Streamflow [m3/s]",
        )
        return fig

    def plot_selected_link_totalvol(self):
        #Read the data of the selected link (This has to be changed)
        path2simulations = '../../web_testing_ClearCreek/segment_analysis/CC_output/outflow '+str(self.selected_link)+'/timeseries_seg_'+str(self.selected_link)+'_US.csv'
        q = pd.read_csv(path2simulations, index_col=0)
        #q = q.loc[300:600]
        #q.loc[q['Qcontrol']<0,'Qcontrol'] = np.nan
        #Make the plot 
        fig = go.Figure()
        fig.add_trace(
                go.Scatter(x=list(q.index), 
                    y=list(q.Vcum_control), 
                    name = 'Control', line=dict(width=4)))
        fig.add_trace(
                go.Scatter(x=list(q.index), y=list(q.Vcum_project), 
                    name = 'Project', line=dict(width=4)))
        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = True,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "Total volume [m3]",
        )
        return fig

    def __projects_update_image__(self):
        self.proj_practice = self.projects.loc[self.projects['Project'] == self.selected_project,'PRACTICE']
        if self.proj_practice.size > 0:
            self.proj_practice = self.projects.loc[self.projects['Project'] == self.selected_project,'PRACTICE'].values[0]
            #Get the practice image
            self.img_png = '../assets/%s' % proj_images[self.proj_practice]
            #print(practice_png)
            self.img_base64 = base64.b64encode(open(self.img_png, 'rb').read()).decode('ascii')
            self.img_source = 'data:image/png;base64,{}'.format(self.img_base64)

    def __projects_assign_id__(self):
        self.projects['prac_id'] = 0
        ids = np.arange(1,self.projects.PRACTICE.unique().size+1)
        for id, name in zip(ids, self.projects.PRACTICE.unique()):
            self.projects.loc[self.projects['PRACTICE'] == name,'prac_id'] = id


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

        #Adds the projects in the region
        fig = go.Figure(go.Scattermapbox(
                mode = 'markers',
                lon = self.projects.Long,
                lat = self.projects.Lat,
                marker=go.scattermapbox.Marker(
                    size=17.5,
                    color='black',                    
                ),                
                text=None,  
            ))
        t = ['%s' % self.projects.loc[i,'Project'] for i in self.projects.index]
        fig.add_trace(go.Scattermapbox(
            mode = 'markers',
            lon = self.projects.Long,
            lat = self.projects.Lat,
            marker=go.scattermapbox.Marker(
                    size=15,
                    #symbol = 'circle-stroked',
                    color = 'green'),
            text = t,
            hoverinfo = 'text'
        ))

        #Adds the USGS gauges in the region
        t = ['USGS:0%d' % self.usgs.loc[i,'USGS_ID'] for i in self.usgs.index]
        fig.add_trace(go.Scattermapbox(
            mode = "markers",
            lon = self.usgs.x,
            lat = self.usgs.y,
            marker = go.scattermapbox.Marker(
                    size=17.5,
                    color = 'black'),
            text = None))
        fig.add_trace(go.Scattermapbox(
            mode = "markers",
            lon = self.usgs.x,
            lat = self.usgs.y,
            marker = go.scattermapbox.Marker(
                    size=15,
                    color = 'blue'),
            text = t))

        #Adds the centroids of the network
        t = ['%s' % i for i in self.network.index]
        fig = fig.add_trace(go.Scattermapbox(
            mode = "markers",
            lon = self.network.x,
            lat = self.network.y,
            marker = {'size': 3, 'color':color_net},
            text = t,
            hoverinfo='none'))

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
