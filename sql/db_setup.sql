CREATE DATABASE seismic;
USE seismic;

CREATE TABLE seismic_events (
  source_id BIGINT PRIMARY KEY,
  magnitude FLOAT,
  region VARCHAR(50),
  latitude FLOAT,
  longitude FLOAT,
  depth FLOAT,
  event_time DATETIME,
  last_updated DATETIME
);

CREATE TABLE seismic_event_updates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_id BIGINT,
  magnitude FLOAT,
  depth FLOAT,
  last_updated DATETIME,
  FOREIGN KEY (source_id) REFERENCES seismic_events(source_id)
);
