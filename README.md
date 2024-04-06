# Real-time Seismic Data Analysis
## Summary
The objective of this project was to harness a real-time data source, ingest it, transform it, store it, then perform visualization and analysis of the data, ideally displaying on a public website. I found the SeismicPortal site when I stumbled upon awmatheson's GitHub project: https://github.com/bytewax/awesome-public-real-time-datasets. The possibilities of this data source were immediately interesting to me so I decided to move forward with it as the centre of this project. Ingestion and transformation are done with a Python script, which then connects to a MySQL database to insert the data. The MySQL database runs in AWS RDS, consisting of two tables, one for unique seismic events and the other for all updates associated with an event. The visualization and analysis happens in a separate Python script that utilizes the Dash framework to create an interactive site for displaying visualizations and performing real-time analysis of the data. Both Python scripts are hosted on an AWS EC2 instance (as long as my free tier eligibility continues).

## Introduction
A summary of the tools currently used by this project follows:
- Python
- MySQL
- AWS RDS
- AWS EC2

This project centres around the seismic data that is received from the websocket server graciously hosted by www.seismicportal.eu. The data received comes in JSON form, here is an example:
{"action":"update","data":{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [
      143.2849,
      -4.0270,
      -10.0
    ]
  },
  "id": "20240330_0000303",
  "properties": {
    "source_id": "1643105",
    "source_catalog": "EMSC-RTS",
    "lastupdate": "2024-04-06T03:28:24.385933Z",
    "time": "2024-03-30T04:09:58.597Z",
    "flynn_region": "NEW GUINEA, PAPUA NEW GUINEA",
    "lat": -4.0270,
    "lon": 143.2849,
    "depth": 10.0,
    "evtype": "ke",
    "auth": "NEIC",
    "mag": 4.6,
    "magtype": "mb",
    "unid": "20240330_0000303"
  }
}}

New messages are either of action 'update' or 'create' and come with the same list of properties. Of the available features, I chose to keep the following: ID, magnitude, region, latitude, longitude, depth, event time, updated time. With this set I can analyze interesting features like magnitude and depth alongside where they occur on the planet; region is useful for communication as it is much more interesting than latitude and lA summary of the tools currently used by this project follows:
- Python
- MySQL
- AWS RDS
- AWS EC2ngitude points for the average person; finally, keeping track of the time of the initial events and subsequent updates is important when keeping track of how an event changes through time. For the updates, I only chose to keep track of changes made to depth and magnitude as they are most interesting to me; upon further renditions I will be looking into what other data routinely changes with updates. 

Regarding software, I decided to focus on Python as it is prominent in the industry. For the ingestion script, a future update will likely have it developed in Go, a language I believe would be great for the engineering task. Nevertheless, the Python script does the job connecting to a websocket server and takes advantage of asynchonous programming to handle all data received. The choice of a relational database is mainly due to the relationship of the events and their updates, as well as the practicality of SQL databases in big data; MySQL as the database of choice is due to popularity and it being open-source. AWS as the cloud platform was chosen in part to previous experience I have with the platform, the free services available (for a time), and the share it holds of the cloud computing market. For data analytics and visualization, I started with the idea of using BI software, such as PowerBI or Tableau, but settled on a custom Python website dashboard as the free versions were not sufficient. To simplify the development of the dashboard I used the Dash framework which provided ample options for visualizations that are easily configured to be very dynamic.