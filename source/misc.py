import glob 
from datetime import date 
import pandas as pd 
import glob 
#import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import json 
import geopandas as gp 
import dash_bootstrap_components as dbc
from dash import html
from hydroeval import evaluator, kge, nse, pbias
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
        self.network = pd.read_csv('%s%s/net_linked.csv' % (path_maps,self.wat_name), index_col = 0)
        #Define watersheds with projects
        projects = []
        for k in watersheds.keys():
            projects.append({'value':k, 'label':watersheds[k]['name']})
        self.proj_names = projects
        #Define selected items
        self.selected_project = self.projects.loc[0,'Project']
        print(self.selected_project)
        self.selected_usgs = '0%d' % self.usgs.loc[0,'USGS_ID']
        self.selected_usgs_descriptor = '%s, Area: %.1f km2' % tuple(self.usgs.loc[0,['SITE_NAME','DRAIN_AREA']].values.tolist())
        self.selected_link = 1
        self.selected_link_peak_red = 0
        self.selected_link_vol_red = 0
        self.selected_link_area = 0
        self.active_tab = "tab_flood_reduction"
        self.performance={'kge':0,'nse':0,'pbias':0,'nse_year':0}
        #Image 
        self.img_png = '../assets/grade_stabilizations.jpg'
        self.img_base64 = base64.b64encode(open(self.img_png, 'rb').read()).decode('ascii')
        self.img_source = 'data:image/png;base64,{}'.format(self.img_base64)
        #Create tables 
        self.table_segment_reduction()
        self.table_project_description()
        self.table_ghost_performance()
        #Read the flows for the segments
        self.segment_flows = {
            'control': pd.read_parquet('%s%s/control.gzip' % (path_maps,self.wat_name)),
            'project': pd.read_parquet('%s%s/project.gzip' % (path_maps,self.wat_name))
        }

    def table_ghost_performance(self):
        table_header = [
            html.Thead(html.Tr([html.Th("Index"), html.Th("Value")]))
        ]
        val = '%.2f' % self.performance['nse']
        row1 = html.Tr([html.Td("Nash Sutcliffe [-inf - 1]"), html.Td(val)])        
        val = '%.2f' % self.performance['kge']
        row2 = html.Tr([html.Td("Kling Gupta [-inf - 1]"), html.Td(val)])        
        val = '%.2f' % self.performance['pbias']
        row3 = html.Tr([html.Td("Volume bias [-100 - 100]"), html.Td(val)]) 
        table_body = [html.Tbody([row1, row2, row3])]
        self.table_ghost_perf = table_header + table_body             

    def table_segment_reduction(self):        
        table_header = [
            html.Thead(html.Tr([html.Th("Item"), html.Th("Value")]))
        ]        
        area = '%.1f' % self.selected_link_area
        if self.selected_link_peak_red < 0: self.selected_link_peak_red = 0
        if self.selected_link_vol_red < 0: self.selected_link_vol_red = 0
        peak_reduction = '%.1f' % self.selected_link_peak_red
        volume_reduction = '%.1f' % self.selected_link_vol_red
        row1 = html.Tr([html.Td("Segment upstream area [km2]"), html.Td(area)])
        row2 = html.Tr([html.Td("Peak reduction [%]"), html.Td(peak_reduction)])
        row3 = html.Tr([html.Td("Volume reduction [%]"), html.Td(volume_reduction)])        
        table_body = [html.Tbody([row1, row2, row3])]
        self.table_link_reduction = table_header + table_body        

    def table_project_description(self):
        table_header = [
            html.Thead(html.Tr([html.Th("Name"), html.Th(self.selected_project)]))
        ]
        print(self.selected_project)
        project_data = self.projects.loc[self.projects['Project'] == self.selected_project,['PRACTICE','County','NAME','BID PACK']]
        print(project_data)
        row1 = html.Tr([html.Td("Practice"), html.Td(project_data.PRACTICE)])
        row2 = html.Tr([html.Td("County"), html.Td(project_data.County)])
        row3 = html.Tr([html.Td("Owner"), html.Td(project_data.NAME)])
        row4 = html.Tr([html.Td("Bid Pack"), html.Td(project_data['BID PACK'])])
        table_body = [html.Tbody([row1, row2, row3,row4])]
        self.table_project_desc = table_header + table_body

    def get_performance(self, qo, qs):
        for name, metric in zip(['kge','nse','pbias'], [kge, nse, pbias]):
            self.performance[name] = evaluator(metric, qo, qs)[0]
        self.performance['nse_year'] = pd.DataFrame([evaluator(nse, qo.loc[str(i)], qs.loc[str(i)])[0] for i in range(2002,2021)], index = range(2002,2021), columns = ['nse'])
        



    def update_click_selection(self, text):
        if text.startswith('CC'):
            self.selected_project = text
            self.__projects_update_image__()
            self.active_tab = "tab_project_info"
        elif text.startswith('US'):
            self.selected_usgs = text[5:]
            number = int(self.selected_usgs)            
            self.selected_usgs_descriptor = '%s, Area: %.1f km2' % tuple(self.usgs.loc[self.usgs['USGS_ID'] == number,['SITE_NAME','DRAIN_AREA']].values.tolist()[0])
            self.active_tab = "tab_GHOST_performance"
            #self.get_performance(self.selected_usgs)
        else:
            self.selected_link = int(text)
            self.get_segment_area()            
            self.active_tab = "tab_flood_reduction"

    def plot_selected_usgs_gauge(self):
        #Read the data 
        q = pd.read_pickle('%s%s/%s.gzip' % (path_maps,self.wat_name, self.selected_usgs))        
        #Get the performance for that gauge
        self.get_performance(q['usgs_dis [cms]'], q['ghost_dis [cms]'])
        #Make the figure
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=list(q.index), 
                    y=list(q['usgs_dis [cms]']), 
                    name = 'Observed', line=dict(width=4.5)))
        fig.add_trace(
            go.Scatter(x=list(q.index), 
                    y=list(q['ghost_dis [cms]']), 
                    name = 'Simulated', line=dict(width=3)))
        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = True,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "Streamflow [cms]",
            xaxis_title = 'Time [days]',            
        )
        return fig

    def get_segment_area(self):
        link = int(self.selected_link)
        self.selected_link_area = self.network.loc[link,'USContArea']/1e6

    def plot_selected_link_streamflow(self):    
        #Read the data of the selected link (This has to be changed)
        #path2simulations = '../../web_testing_ClearCreek/segment_analysis/CC_output/outflow '+str(self.selected_link)+'/timeseries_seg_'+str(self.selected_link)+'_US.csv'
        #q = pd.read_csv(path2simulations, index_col=0)
        #q = q.loc[300:600]
        #q.loc[q['Qcontrol']<0,'Qcontrol'] = np.nan
        column = 'outflow %d' % self.selected_link
        qc = self.segment_flows['control']
        qc = qc.loc[0:250,column]
        qp = self.segment_flows['project']
        qp = qp.loc[0:250,column]
        
        self.selected_link_peak_red = 100-100*(qp.max()/qc.max())
        #Make the plot 
        print(self.selected_link)
        fig = go.Figure()
        fig.add_trace(
                go.Scatter(x=list(qc.index), 
                    y=list(qc), 
                    name = 'Control', line=dict(width=4)))
        fig.add_trace(
                go.Scatter(x=list(qp.index), y=list(qp), 
                    name = 'Project', line=dict(width=4)))
        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = False,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "Streamflow [cms]",
            xaxis_title = 'Time [seconds]',
        )
        return fig

    def plot_selected_link_totalvol(self):
        #Read the data of the selected link (This has to be changed)
        # path2simulations = '../../web_testing_ClearCreek/segment_analysis/CC_output/outflow '+str(self.selected_link)+'/timeseries_seg_'+str(self.selected_link)+'_US.csv'
        # q = pd.read_csv(path2simulations, index_col=0)        
        #q = q.loc[300:600]
        #q.loc[q['Qcontrol']<0,'Qcontrol'] = np.nan
        column = 'outflow %d' % self.selected_link
        qc = self.segment_flows['control']
        qc = qc[column].cumsum()*(300/1e6)
        qp = self.segment_flows['project']
        qp = qp[column].cumsum()*(300/1e6)
        
        self.selected_link_vol_red = 100-100*(qp.values[-1]/qc.values[-1])
        
        #Make the plot 
        fig = go.Figure()
        fig.add_trace(
                go.Scatter(x=list(qc.index), 
                    y=list(qc), 
                    name = 'Control', line=dict(width=4)))
        fig.add_trace(
                go.Scatter(x=list(qp.index), y=list(qp), 
                    name = 'Project', line=dict(width=4)))
        fig.update_layout(
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01),
            showlegend = True,
            margin=dict(t=0, b=0, l=0, r=0),
            yaxis_title = "Total volume [Mm3]",
            xaxis_title = 'Time [seconds]',
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

        f = open('%s%s/boundaries/%d.json' % (path_maps,self.wat_name, self.selected_link))
        geoJSON_subWat = json.load(f)
        f.close()
        color_swat = 'rgba(0,0,50,0.3)'

        #Beauty layout
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
                        source = geoJSON_subWat,
                        type = 'fill',
                        color = color_swat
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
