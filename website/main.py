from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.environ["DB_HOSTNAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.environ["DB_NAME"]
)


app = Dash(__name__)

# LAYOUT
app.layout = html.Div(children=[
    html.H1(children='Real-time Seismic Date'),
    html.Div(children='''
        This Dash app connects to a MySQL database on AWS RDS and displays the locations of unique seismic events.
    '''),
    dcc.Graph(
        id='world-map',
        figure={'layout': {'title': 'Seismic Events'}},
        style={'height': '800px', 'width': '80%'}
    )
    
])

# Callback to update the figure
@app.callback(
    Output('world-map', 'figure'),
    Input('world-map', 'figure'))
def update_figure(figure):
    # Execute a SQL query to fetch the data
    cur = conn.cursor()
    print("Getting lat,lon data from server")
    cur.execute("SELECT latitude, longitude FROM seismic_events")
    print("Got lat,lon data from server")
    data = cur.fetchall()
    cur.close()

    df = pd.DataFrame(data, columns=[
                                "latitude",
                                "longitude"
                            ])


    # Create the Plotly figure
    fig = go.Figure(data=go.Scattergeo(
        lon=df['longitude'],
        lat=df['latitude'],
        mode='markers',
        marker=dict(
            size=6,
            color='red',
            opacity=0.3
        )
    ))

    fig.update_layout(
        title='World Map with Latitude and Longitude Points',
        geo_scope='world',
    )

    return fig

# RUN IT
if __name__ == '__main__':
    app.run(debug=True)
