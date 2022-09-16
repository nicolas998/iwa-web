import dash
from dash import dcc
#import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
#import dash_html_components as html
from dash import html
from datetime import date
import numpy as np
from misc import misc, proj_images
#Local packages
import plotly.express as px
import plotly.graph_objects as go
import base64

###########################################################################################################################################################################
# Initialize variables 

mi = misc()
fig_map = mi.plot_map()
fig_proj_noproj_streamflow = mi.plot_selected_link_streamflow()
fig_proj_noproj_totalvol = mi.plot_selected_link_totalvol()
fig_ghost_sim = mi.plot_selected_usgs_gauge()

###########################################################################################################################################################################
# Define the server 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

###########################################################################################################################################################################
#Tabs content

tab1_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row([
                dcc.Graph(
                    id = 'plot-link-streamflow',
                    figure = fig_proj_noproj_streamflow,
                    style = {'width': '40vh', 'height': '40vh'},            
                ),
                dcc.Graph(
                    id = 'plot-link-totalvol',
                    figure = fig_proj_noproj_totalvol,
                    style = {'width': '40vh', 'height': '40vh'},            
                ),
                mi.table                        
            ])
        ]
    ),color="secondary", outline=True
)

tab2_content = dbc.Card(
    dbc.CardBody(
        [            
            dbc.Row([
                dbc.Col([
                    html.H6(id = 'project-identifier'),
                    html.Div('Practice: '),
                    html.Div(id = 'project-practice')
                ], width=6),
                dbc.Col([
                    html.Img(id = 'practice-image', src=mi.img_source)
                ], width = 6)
            ])            
        ]
    ),color="secondary", outline=True, className="w-75 h-50",)

tab3_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label(id = "selected-usgs"),
            dcc.Graph(
                id = 'plot-usgs-streamflow',
                figure = fig_ghost_sim,
                style = {'width': '90vh', 'height': '40vh'},            
            ),            
        ]
    ),color="secondary", outline=True
)

###########################################################################################################################################################################
#Web page layout 
app.layout = dbc.Container([
    html.H1("Iowa Watershed Approach"),
    html.H3("Projects flood reduction analysis"),
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dbc.Label("Watershed"),
            dcc.Dropdown(
                id = 'drop-project-selector',
                options = mi.proj_names,
                value = mi.proj_names[0]['value'],
                multi = False, 
                style={
                    'width':'140px'
                }
            ),
            dcc.Graph(
                id = 'plot-map',
                clickData = {'points': [{'text': 'CC:None'}]},
                figure = fig_map,
                style={'width': '100vh', 'height': '60vh'},
                config={"toImageButtonOptions": {"scale":4, "filename": 'event_streamflow'}}
            ),
        ], width = 6),
        dbc.Col([                        
            dbc.Tabs([
                dbc.Tab(tab1_content, tab_id = "tab_flood_reduction", label="Flood Reduction"),
                dbc.Tab(tab2_content, tab_id = "tab_project_info", label="Project description"),
                dbc.Tab(tab3_content, tab_id = "tab_GHOST_performance", label="GHOST performance"),                
            ], active_tab = mi.active_tab, id = "tabs",)
                        
        ], width = 6)
    ],align="center"),

    

], fluid = True)

# ###########################################################################################################################################################################
# #Call back functions

# #Get the info of the clicked dot in the map 
@app.callback(
    Output('project-identifier','children'),
    Output('project-practice','children'),
    Output('practice-image','src'),
    Output('plot-link-streamflow','figure'),
    Output('plot-link-totalvol','figure'),
    Output('plot-usgs-streamflow','figure'),
    Output('selected-usgs','children'),
    Output('tabs','active_tab'),
    Input('plot-map','clickData')
)
def get_info_from_map(clickData):
    #Updates the selected project, link, usgs gauge
    mi.update_click_selection(clickData['points'][0]['text'])    
    #Make the project / no project figure
    fig_proj_noproj_st = mi.plot_selected_link_streamflow()
    fig_proj_noproj_vol = mi.plot_selected_link_totalvol()
    fig_ghost_sim = mi.plot_selected_usgs_gauge()
    #Returns: the selected project name, practice type, and practice image
    usgs = 'USGS gauge: %s, %s' % (mi.selected_usgs, mi.selected_usgs_descriptor)
    return mi.selected_project, mi.proj_practice,mi.img_source, fig_proj_noproj_st, fig_proj_noproj_vol, fig_ghost_sim, usgs, mi.active_tab#, str(mi.selected_link)

###########################################################################################################################################################################
#Excecution

if __name__ == '__main__':
    app.run_server(debug=True, port = 8890,)
