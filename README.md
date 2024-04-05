# Real-time Seismic Data Analysis
## Overview
EU Seismic Portal data analyses completed by consuming the real-time data using Python and ingesting into a MySQL database.   

## Software
- Python client listens for websocket posts, parses the JSON, and connects to the database to add the data
- Client hosted on AWS EC2 instance
- MySQL server running on AWS RDS ingests data from the Python client
- Dash-built website to display data analysis and visualizations, hosted on EC2

## Flow
1. JSON received from server
2. JSON parsed into data class
3. Data inserted into database based on logic (create vs. update)
4. Website connects to database, updates graphs and analytics accordingly

## Database
- Commands for table creation and data insert/update in the sql folder

## Website
- All files related to the Dash website are in the website folder