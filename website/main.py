from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import numpy as np
from sklearn.cluster import KMeans

import datetime 
import pymysql

host = os.environ["DB_HOSTNAME"]
db_name = os.environ["DB_NAME"]
user = os.environ["DB_USER"]
pw = os.environ["DB_PASSWORD"]

class Database:
    def __init__(self):
        self.host = host
        self.user = user
        self.password = pw
        self.database = db_name
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.Error as e:
            print(f"Error connecting to the database: {e}")

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def query(self, query):
        if not self.connection:
            print("Not connected to the database")
            return None

        try:
            self.cursor = self.connection.cursor()
            self.cursor.execute(query)
            self.connection.commit()
            data = self.cursor.fetchall()
            self.cursor.close()
            return data
        except pymysql.Error as e:
            print(f"Error executing query: {e}")
            return None

app = Dash(__name__)
sql_data = None

np.random.seed(0)

# LAYOUT
app.layout = html.Div(children=[
    html.H1(children='Real-time Seismic Date'),
    html.Div(id='sql-data'),
    dcc.Interval(
        id='sql-update-interval',
        interval=30000,
        n_intervals=0
    ),
    html.Div(children='''
        This Dash app connects displays real-time seismic data.
    '''),
    html.H4("Choose Timeframe"),
    dcc.DatePickerRange(
        id='date-picker-range',
        min_date_allowed=datetime.date(2024, 4, 1),
        max_date_allowed=datetime.date.today(),
        initial_visible_month=datetime.date.today(),
        start_date=datetime.date(2024, 4, 1),
        end_date=datetime.date.today()
    ),
    html.H4('Overview'),
    html.Div(
        id='metrics',
        style={'width': '250px'}
    ),
    html.H2('Explore the Data'),
    dcc.Graph(
        id='world-map',
        figure={'layout': {'title': 'Seismic Events'}},
        style={'height': '800px', 'width': '80%'}
    ),
    html.Div(id='clicked-data'),
    dcc.Graph(
        id='line1',
        figure={'layout': {'title': 'Magnitude x Depth'}}),

    html.Div(id='clicked-data-line1'),
    html.H2('Analysis'),
    dcc.Graph(id='cluster-plot')
])

@app.callback(
    Output('sql-data', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('sql-update-interval', 'n_intervals')]
)
def update_sql_data(start_date, end_date, n):
    global sql_data

    db = Database()
    db.connect()
    sql_data = db.query(f"SELECT * FROM seismic_events WHERE DATE_FORMAT(event_time, '%Y-%m-%d') BETWEEN '{start_date}' AND '{end_date}';")
    db.disconnect()
    
    # Return a dummy output to trigger the callback
    return ''

@app.callback(
    Output('metrics', 'children'),
    [Input('sql-data', 'children')]
)
def update_metrics(c):
    global sql_data
    data = sql_data
    
    if data is None:
        return None

    df = pd.DataFrame(data, columns=[
                                "magnitude",
                                "depth"
                            ])
    metrics = {
        'Unique Events': df.shape[0],
        'Maximum Magnitude': df['magnitude'].max().round(2),
        'Average Magnitude': df['magnitude'].mean().round(2),
        'Maximum Depth': df['depth'].max().round(2),
        'Average Depth': df['depth'].mean().round(2),
        'Minimum Depth': df['depth'].min().round(2)
    }
    
    table_data = [{'Metric': metric, 'Value': value} for metric, value in metrics.items()]

    table = dash_table.DataTable(
        id='metrics-table',
        columns=[{'name': col, 'id': col} for col in ['Metric', 'Value']],
        data=table_data
    )
    return table

@app.callback(
    Output('world-map', 'figure'),
    [Input('sql-data', 'children'),
     Input('world-map', 'figure')])
def update_figure(c, figure):
    global sql_data
    data = sql_data
    if data is None:
        return None
    df = pd.DataFrame(data, columns=[
                                "latitude",
                                "longitude",
                                "magnitude",
                                "depth",
                                "region",
                                "source_id"
                            ])
    fig = go.Figure(data=go.Scattergeo(
        lon=df['longitude'],
        lat=df['latitude'],
        mode='markers',
        marker=dict(
            size=df['magnitude']*3,
            color='red',
            opacity=0.3
        ),
        text=df['region'],
        hovertemplate='Location: %{text}<br>Magnitude: %{customdata[0]:.2f}<br>Depth: %{customdata[1]}<extra></extra>',
        customdata=np.stack((df['magnitude'], df['depth'], df['source_id']), axis=-1)
    ))
    fig.update_layout(
        title='World Map of Seismic Events',
        geo_scope='world',
    )
    return fig

@app.callback(
    Output('clicked-data', 'children'),
    Input('world-map', 'clickData'))
def display_click_data(clickData):
    if clickData:
        point = clickData['points'][0]
        data = point['customdata']
        return f"Activity in {point['text']} with a magnitude of {data[0]} and depth of {data[1]}"
    else:
        return "Click on a point to see the related record."


@app.callback(
    Output("line1", "figure"),
    [Input('sql-data', 'children')])
def update_line1(c):
    global sql_data
    data = sql_data
    if data is None:
        return None

    df = pd.DataFrame(data, columns=[
                                "magnitude",
                                "depth",
                                "source_id",
                                "region",
                                "event_time",
                            ])
            
    y = df['depth']
    x = df['magnitude']

    points = go.Scatter(
                    x=x, 
                    y=y, 
                    mode="markers",
                    customdata=df.to_dict('records'))
    layout = go.Layout(title="Magnitude x Depth", xaxis_title="Magnitude", yaxis_title="Depth")
    figure = {"data": [points], "layout": layout}
    return figure

@app.callback(
    Output('clicked-data-line1', 'children'),
    Input('line1', 'clickData'))
def display_click_data(clickData):
    if clickData:
        point = clickData['points'][0]
        data = point['customdata']
        return f"Activity in {data['region']} with a magnitude of {data['magnitude']} and depth of {data['depth']}"
    else:
        return "Click on a point to see the related record."

@app.callback(
    Output("cluster-plot", "figure"),
    [Input('sql-data', 'children')])
def update_cluster(c):
    global sql_data
    data = sql_data
    if data is None:
        return None

    df = pd.DataFrame(data, columns=[
                                "magnitude",
                                "depth"
                            ])
    
    nums = df.to_numpy()
    kmeans = KMeans(n_clusters=3, random_state=0).fit(nums)
    labels = kmeans.labels

    scatt = go.Scatter(
                    x=df["magnitude"], # maybe these should be numpy arrays?
                    y=df["depth"], 
                    mode="markers",
                    marker=dict(
                        color=labels,
                        size=10,
                        lane=dict(width=1, color='black')
                    ),
                    name="Clusters"
    )

    layout = go.Layout(
        title='Clustering of Magnitude and Depth',
        xaxis=dict(title='Depth'),
        yaxis=dict(title='Magnitude'),
        showlegend=False
    )
    fig = go.Figure(data=[scatt], layout=layout)
    return fig

# RUN IT
if __name__ == '__main__':
    app.run(debug=True)
