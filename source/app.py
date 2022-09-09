import dash
from dash import dcc
#import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
#import dash_html_components as html
from dash import html
from datetime import date
import numpy as np
from misc import misc
#Local packages
import plotly.express as px
import plotly.graph_objects as go

###########################################################################################################################################################################
# Initialize variables 

mi = misc()
fig_map = mi.plot_map()


###########################################################################################################################################################################
# Define the server 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,)
server = app.server

###########################################################################################################################################################################
#Web page layout 

app.layout = html.Div([

    #First Column with stuff
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
            ),
            html.H5(id = 'for-display'),
        ]),

        # Map
        dcc.Graph(
            id = 'plot-map',
            clickData = {'points': [{'text': 'CC:None'}]},
            figure = fig_map,
            style={'width': '100vh', 'height': '57vh'},
            config={"toImageButtonOptions": {"scale":4, "filename": 'event_streamflow'}}
        )
    ])

])



###########################################################################################################################################################################
#Call back functions

#Get the info of the clicked dot in the map 
@app.callback(
    Output('for-display','children'),
    Input('plot-map','clickData')
)
def get_info_from_map(clickData):
    mi.update_click_selection(clickData['points'][0]['text'])
    print(mi.selected_link)
    print(mi.selected_usgs)
    print(mi.selected_project)
    print('---------')
    #print(clickData['points'][0]['text'])
    return clickData['points'][0]['text']

###########################################################################################################################################################################
#Excecution

if __name__ == '__main__':
    app.run_server(debug=True, port = 8890,)
