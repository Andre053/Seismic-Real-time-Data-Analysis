-- Command for checking if the seismic event is new
SELECT source_id FROM seismic_events WHERE source_id = {id}

-- Commands for adding a new seismic event
INSERT INTO seismic_events (
  magnitude, 
  region, 
  latitude, 
  longitude, 
  depth, 
  event_time, 
  last_updated, 
  source_id
) VALUES (
  {mag},
  '{reg}',
  {lat},
  {lon},
  {dep},
  '{evt}',
  '{upd}',
  {sid}
);

INSERT INTO seismic_event_updates (
  magnitude,
  depth,
  last_updated,
  source_id
) VALUES (
  {mag},
  {dep},
  '{upd}',
  {sid}
);

-- Commands for updating a seismic event
INSERT INTO seismic_event_updates (
  source_id,
  magnitude,
  depth,
  last_updated
) VALUES (
  {sid},
  {mag},
  {dep},
  '{upd}'
);

UPDATE seismic_events
SET
  magnitude = {mag},
  depth = {dep},
  last_updated = '{upd}'
WHERE source_id = {sid};
