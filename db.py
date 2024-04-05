import mysql.connector
from mysql.connector import Error 
import os

class Database:
    def __init__(self):
        print("Initializing database...")
        self.conn = None
        self.conn = mysql.connector.connect(
                    host=host,
                    database=db_name,
                    user=user,
                    password=pw
        )
        print("Initialized database")

    def query(self, cmd, args=None):
        print("Query requested...")
        cur = self.conn.cursor()
        cur.execute(cmd, args)
        return cur

    def execute(self, cmd, args):
        row_count = None
        try:
            #print("Command requested:\n", cmd)
            cur = self.query(cmd, args)
            row_count = cur.rowcount
            self.conn.commit()
            cur.close()
        except Error as e:
            self.conn.rollback()
            print("Error executing command:", e)
        finally: 
            return row_count 
    
    def __del__(self):
        if self.conn is not None:
            self.conn.close()

# GLOBALS
host = os.environ["DB_HOSTNAME"]
db_name = os.environ["DB_NAME"]
user = os.environ["DB_USER"]
pw = os.environ["DB_PASSWORD"]
db = Database()

def check_id(id):
    print("Checking for ID")
    cmd = f"SELECT source_id FROM seismic_events WHERE source_id = {id}"
    cur = db.query(cmd)
    
    if cur.fetchone():
      print("ID in table, must update")
      cur.close()
      return False
    
    print("ID not in table, new event")
    cur.close()
    return True

def add_data(data):
    # check if id is in Earthquake
    # if so, update it accordingly, add the record into updates
    # if not, it is a create... or we missed the create (same)
    print("Data received with ID:", data.src_id)
    is_new = check_id(data.src_id)
    if is_new:
      insert_create(data.src_id, data.mag, data.reg, data.lat, data.lon, data.dep, data.time, data.updated)
    else: 
      insert_update(data.src_id, data.mag, data.dep, data.updated)
    print("Inserted data!")
    
if __name__ == '__main__':
    print("Attempting to connect to DB")
    connect()
    print("Done")


def insert_update(sid, mag, dep, upd): 
        cmd1 = f"""
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
"""
        cmd2 = f"""
UPDATE seismic_events
SET
  magnitude = {mag},
  depth = {dep},
  last_updated = '{upd}'
WHERE source_id = {sid};
"""
        rows1 = db.execute(cmd1, None)
        rows2 = db.execute(cmd2, None)
        print("Update ran, total rows affected:", rows1+rows2)



def insert_create(sid, mag, reg, lat, lon, dep, evt, upd):
        cmd1 = f"""
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
"""
        cmd2 = f"""
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
"""
        rows1 = db.execute(cmd1, None)
        rows2 = db.execute(cmd2, None)
        print("Update ran, total rows affected:", rows1+rows2)

