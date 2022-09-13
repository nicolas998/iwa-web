import dash
from dash import dcc
#import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
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

###########################################################################################################################################################################
# Define the server 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,)
server = app.server

###########################################################################################################################################################################
#Web page layout 

app.layout = html.Div([

    ###################################################################################################################################
    #First Column contains the watershed selector and the map with its information

    html.Div(children=[        
        # Map control panel
        html.Div(children=[ 
            dcc.Dropdown(
                id = 'drop-project-selector',
                options = mi.proj_names,
                value = mi.proj_names[0]['value'],
                multi = False, 
                style={
                    'width':'140px'
                }
            )            
        ]),

        # Map
        dcc.Graph(
            id = 'plot-map',
            clickData = {'points': [{'text': 'CC:None'}]},
            figure = fig_map,
            style={'width': '100vh', 'height': '60vh'},
            config={"toImageButtonOptions": {"scale":4, "filename": 'event_streamflow'}}
        ),
        html.Div(children=[
            html.Div(children = [
                html.H6(id = 'project-id'),
                html.Div('Practice: '),
                html.Div(id = 'project-practice'),
            ]), #style={'display': 'flex', 'flex-direction': 'row'}),            
            html.Img(id = 'practice-image', src=mi.img_source)            
        ])
    ]),

    ###################################################################################################################################
    #Second column has: Clicked project description, project impact plot, GHOST validation
    html.Div(children=[
        html.Div(
            children = [
                html.Div('Network segment:'),
                html.Div(id = 'network-segment'),
            ], style={'display': 'flex', 'flex-direction': 'row'}),
        html.Div(children=[
            dcc.Graph(
                id = 'plot-link-streamflow',
                figure = fig_proj_noproj_streamflow,
                style = {'width': '45vh', 'height': '45vh'},            
            ),
            dcc.Graph(
                id = 'plot-link-totalvol',
                figure = fig_proj_noproj_totalvol,
                style = {'width': '45vh', 'height': '45vh'},            
            )
        ], style = {'display':'flex','flex-direction':'row'})
        
    ])
   

], style={'display': 'flex', 'flex-direction': 'row'})



###########################################################################################################################################################################
#Call back functions

#Get the info of the clicked dot in the map 
@app.callback(
    Output('project-id','children'),
    Output('project-practice','children'),
    Output('practice-image','src'),
    Output('plot-link-streamflow','figure'),
    Output('plot-link-totalvol','figure'),
    Output('network-segment','children'),
    Input('plot-map','clickData')
)
def get_info_from_map(clickData):
    #Updates the selected project, link, usgs gauge
    mi.update_click_selection(clickData['points'][0]['text'])    
    #Make the project / no project figure
    fig_proj_noproj_st = mi.plot_selected_link_streamflow()
    fig_proj_noproj_vol = mi.plot_selected_link_totalvol()
    #Returns: the selected project name, practice type, and practice image
    return mi.selected_project, mi.proj_practice,mi.img_source, fig_proj_noproj_st, fig_proj_noproj_vol, str(mi.selected_link)

###########################################################################################################################################################################
#Excecution

if __name__ == '__main__':
    app.run_server(debug=True, port = 8890,)
