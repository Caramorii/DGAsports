import sqlite3

conn = sqlite3.connect("weather_stations.db")
cur = conn.cursor()
cur.execute("INSERT INTO customer(COUSTOMER_ID, name, region, street_address, city, state, zip) VALUES(89, 'grosw', 'goili', 'gro', 'KP', 8974 )")
conn.commit()
conn.close()

if __name__ == "__main__":
    cur.execute("SELECT * FROM customer")