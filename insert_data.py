import json
from datetime import timedelta
import pandas as pd
from haversine import haversine_vector, Unit
from DbConnector import DbConnector

DATA_PATH = "porto/porto.csv"
BATCH_SIZE = 1000

INSERT_TRIP_QUERY = """INSERT INTO trip
    (trip_id, call_type, origin_call, origin_stand, taxi_id, start_time, end_time, distance_km, day_type, missing_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

INSERT_POINT_QUERY = """INSERT INTO gps_point
    (trip_pk, seq_num, latitude, longitude)
    VALUES (%s, %s, %s, %s)"""

INSERT_TAXI_QUERY = "INSERT INTO taxi (taxi_id) VALUES (%s)"


def load_data():
    df = pd.read_csv(DATA_PATH)
    print("Rows:", len(df))

    df = df.drop_duplicates()
    print("Rows after drop_duplicates:", len(df))

    utc_time = pd.to_datetime(df["TIMESTAMP"], unit="s", utc=True)
    df["start_time"] = utc_time.dt.tz_convert("Europe/Lisbon").dt.tz_localize(None)

    return df


def to_int_or_none(value):
    if pd.isna(value):
        return None
    return int(value)


def compute_distance_km(points):
    if len(points) < 2:
        return 0.0

    distances = haversine_vector(points[:-1], points[1:], Unit.KILOMETERS, check=False)
    return float(distances.sum())


def insert_taxis(connection, df):

    taxi_rows = []
    for taxi_id in df["TAXI_ID"].unique():
        taxi_rows.append((int(taxi_id),))

    connection.cursor.executemany(INSERT_TAXI_QUERY, taxi_rows)
    connection.db_connection.commit()
    print("Taxis:", len(taxi_rows))


def insert_batch(connection, trip_rows, point_lists):
    connection.cursor.executemany(INSERT_TRIP_QUERY, trip_rows)
    first_trip_pk = connection.cursor.lastrowid

    point_rows = []
    for i, points in enumerate(point_lists):
        trip_pk = first_trip_pk + i
        for seq_num, point in enumerate(points):
            latitude = point[0]
            longitude = point[1]
            point_rows.append((trip_pk, seq_num, latitude, longitude))

    connection.cursor.executemany(INSERT_POINT_QUERY, point_rows)
    connection.db_connection.commit()
    return len(point_rows)


def insert_trips_and_points(connection, df):
    trip_rows = []
    point_lists = []
    trip_count = 0
    point_count = 0

    for row in df.itertuples(index=False):
        polyline = json.loads(row.POLYLINE)

        # POLYLINE stores [longitude, latitude], so we convert to (latitude, longitude)
        points = []
        for longitude, latitude in polyline:
            points.append((latitude, longitude))

        start_time = row.start_time.to_pydatetime()
        duration_s = max(len(points) - 1, 0) * 15
        end_time = start_time + timedelta(seconds=duration_s)
        distance_km = compute_distance_km(points)

        trip_rows.append(
            (
                row.TRIP_ID,
                row.CALL_TYPE,
                to_int_or_none(row.ORIGIN_CALL),
                to_int_or_none(row.ORIGIN_STAND),
                row.TAXI_ID,
                start_time,
                end_time,
                distance_km,
                row.DAY_TYPE,
                row.MISSING_DATA,
            )
        )

        point_lists.append(points)

        if len(trip_rows) == BATCH_SIZE:
            point_count += insert_batch(connection, trip_rows, point_lists)
            trip_count += len(trip_rows)
            trip_rows = []
            point_lists = []

            if trip_count % 100000 == 0:
                print("Trips:", trip_count)

    point_count += insert_batch(connection, trip_rows, point_lists)
    trip_count += len(trip_rows)

    print("Trips:", trip_count)
    print("GPS points:", point_count)


def main():
    connection = DbConnector()

    df = load_data()
    insert_taxis(connection, df)
    insert_trips_and_points(connection, df)

    connection.close_connection()


if __name__ == "__main__":
    main()
