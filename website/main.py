from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import numpy as np
from sklearn.cluster import KMeans, DBSCAN

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
    html.H1(children='Real-time Seismic Data Analysis'),
    html.Div(id='sql-data'),
    dcc.Interval(
        id='sql-update-interval',
        interval=3600000,
        n_intervals=0
    ),
    html.Div([
        html.P("Dashboard for visualization and analysis of seismic data. Collection of data started April 7th, 2024. Ingestion dropped on April 11th and was restarted. Ingestion paused April 14th to strategize lowering RDS usage."),
        html.A('Overview and source code', href='https://github.com/Andre053/Seismic-Real-time-Data-Analysis', target='_blank')
    ]),
    html.H4("Choose Timeframe"),
    dcc.DatePickerRange(
        id='date-picker-range',
        initial_visible_month=datetime.date.today(),
        start_date=datetime.date(2000, 1, 1),
        end_date=None
    ),
    html.H4('Overview'),
    html.Div(
        id='metrics',
        style={'width': '250px'}
    ),
    html.H4('Event Counts over Time', style={'margin-bottom': '5px'}),
    dcc.Graph(id='events-over-time', style={'margin-top': '5px'}),
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
    html.H3('K-Means Clustering'),
    html.H6('Choose number of clusters', style={'margin-bottom': '10px'}),
    dcc.Input(id='input-clusters', type='number', value=3),
    html.Div(id='cluster-info', style={'margin-top': '25px'}),
    dcc.Graph(id='cluster-plot'),
    html.H3('DBSCAN'),
    html.H6('Choose eps value', style={'margin-bottom': '10px'}),
    dcc.Input(id='input-eps', type='number', value=5),
    html.Div(id='dbscan-info', style={'margin-top': '25px'}),
    dcc.Graph(id='dbscan-plot')
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
    Output('events-over-time', 'figure'),
    [Input('sql-data', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')]  # You can add an input if needed
)
def update_line_graph(c, start, end):
    # Create line graph trace

    global sql_data
    data = sql_data
    
    if data is None:
        return None

    df = pd.DataFrame(data, columns=[
                                "event_time"
                            ])

    event_counts = df.groupby(pd.Grouper(key='event_time', freq='3h')).size()

    trace = go.Scatter(
        x=event_counts.index,
        y=event_counts.values,
        mode='lines+markers',
        marker=dict(color='blue'),  # Adjust color if needed
        name='Counts by Day'
    )

    # Create layout
    layout = go.Layout(
        xaxis=dict(title='Date'),
        yaxis=dict(title='Events'),
        hovermode='closest'
    )

    # Combine trace and layout
    fig = go.Figure(data=[trace], layout=layout)

    return fig


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



# MACHINE LEARNING
@app.callback(
    Output("cluster-plot", "figure"),
    Output("cluster-info", "children"),
    [Input('sql-data', 'children'),
    Input('input-clusters', 'value')])
def update_cluster(c, n_clusters):
    global sql_data
    data = sql_data
    if data is None:
        return None

    if n_clusters > len(data):
        n_clusters = len(data)
    elif n_clusters < 1:
        n_clusters = 1
    # Use dropdown to choose K clusters
    df = pd.DataFrame(data, columns=[
                                "magnitude",
                                "depth"
                            ])
    
    nums = df.to_numpy()
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(nums)
    labels = kmeans.predict(nums)
    centroids = np.round(kmeans.cluster_centers_, 2)

    cluster_counts = pd.Series(labels).value_counts()

    cluster_info = html.Div([
        html.Table([
            html.Tr([html.Th("Cluster"), html.Th("Centroid"), html.Th("Count")]),
            *[html.Tr([
                html.Td(f"{i+1}"),
                html.Td(f"{centroid[0]}, {centroid[1]}"),
                html.Td(str(count))
            ], style={'textAlign': 'center'}) for i, (centroid, count) in enumerate(zip(centroids, cluster_counts))]
        ],
        style={'border': '1px solid black'})
    ])

    trace1 = go.Scatter(
                    x=df["magnitude"], # maybe these should be numpy arrays?
                    y=df["depth"], 
                    mode="markers",
                    marker=dict(
                        color=labels,
                        colorscale='viridis',
                        size=10,
                        line=dict(width=1, color='black')
                    ),
                    name="Clusters"
    )
    trace2 = go.Scatter(
                    x=centroids[:, 0],
                    y=centroids[:, 1],
                    mode='markers',
                    marker=dict(symbol='x', size=10, color='black'),
                    name='Centroids'
    )

    layout = go.Layout(
        title='Clusters and Centroids',
        xaxis=dict(title='Magnitude'),
        yaxis=dict(title='Depth'),
        showlegend=True
    )
    fig = go.Figure(data=[trace1, trace2], layout=layout)
    return fig, cluster_info


@app.callback(
    Output("dbscan-plot", "figure"),
    Output("dbscan-info", "children"),
    [Input('sql-data', 'children'),
    Input('input-eps', 'value')])
def update_dbscan(c, eps_value):
    global sql_data
    data = sql_data
    if data is None:
        return None

    # Use dropdown to choose K clusters
    df = pd.DataFrame(data, columns=[
                                "magnitude",
                                "depth"
                            ])
    
    nums = df.to_numpy()

    if eps_value == 0 or eps_value < 0:
        eps_value = 0.1
    dbscan = DBSCAN(eps=eps_value, min_samples=5)
    labels = dbscan.fit_predict(nums)
    noise_labels = np.where(labels == -1)[0]
    non_noise_labels = np.where(labels != -1)[0]

    trace1 = go.Scatter(
                    x=df["magnitude"][noise_labels], # maybe these should be numpy arrays?
                    y=df["depth"][noise_labels], 
                    mode="markers",
                    marker=dict(
                        color='red',
                        size=10,
                        line=dict(width=1, color='black')
                    ),
                    name="Noise"
    )
    trace2 = go.Scatter(
                    x=df["magnitude"][non_noise_labels], # maybe these should be numpy arrays?
                    y=df["depth"][non_noise_labels], 
                    mode="markers",
                    marker=dict(
                        color='blue',
                        size=10,
                        line=dict(width=1, color='black')
                    ),
                    name="Non-Noise"
    )

    layout = go.Layout(
        title='Noise and Non-Noise',
        xaxis=dict(title='Magnitude'),
        yaxis=dict(title='Depth'),
        showlegend=True
    )
    cluster_info = html.Div("")
    fig = go.Figure(data=[trace1, trace2], layout=layout)
    return fig, cluster_info

# RUN IT
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
