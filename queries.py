import time
from DbConnector import DbConnector
from tabulate import tabulate
from haversine import haversine, haversine_vector, Unit


class Queries:

    def __init__(self):
        self.connection = DbConnector()
        self.db_connection = self.connection.db_connection
        self.cursor = self.connection.cursor

    def run_query(self, query):
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        print(tabulate(rows, headers=self.cursor.column_names))
        return rows

    def task_1_counts(self):
        query = """SELECT
                (SELECT COUNT(*) FROM taxi) AS total_taxis,
                (SELECT COUNT(*) FROM trip) AS total_trips,
                (SELECT COUNT(*) FROM gps_point) AS total_gps_points;
        """
        self.run_query(query)

    def task_2_avg_trips_per_taxi(self):

        query = """
            SELECT AVG(trip_count) AS avg_trips_per_taxi
            FROM (
                SELECT taxi_id, COUNT(*) AS trip_count
                FROM trip
                GROUP BY taxi_id
            ) AS taxi_trips;
        """

        self.run_query(query)

    def task_3_top_20_taxis(self):
        query = """SELECT
                taxi_id,
                COUNT(*) AS trip_count
            FROM trip
            GROUP BY taxi_id
            ORDER BY trip_count DESC
            LIMIT 20;
        """
        self.run_query(query)

    def task_4a_most_used_call_type(self):
        query = """WITH call_type_counts AS (
                SELECT
                    taxi_id,
                    call_type,
                    COUNT(*) AS trip_count
                FROM trip
                GROUP BY taxi_id, call_type
            ),
            ranked AS (
                SELECT
                    taxi_id, call_type, trip_count,
                    RANK() OVER (
                        PARTITION BY taxi_id
                        ORDER BY trip_count DESC
                    ) AS rank_num
                FROM call_type_counts
            )
            SELECT taxi_id, call_type, trip_count
            FROM ranked
            WHERE rank_num = 1
            ORDER BY trip_count DESC
        """
        self.run_query(query)

    def task_4b_call_type_stats(self):
        query = """SELECT
                call_type,
                COUNT(*) AS trip_count,
                AVG(TIMESTAMPDIFF(SECOND, start_time, end_time)) / 60 AS avg_duration_min,
                AVG(distance_km) AS avg_distance_km,
                AVG(HOUR(start_time) < 6) AS fraction_00_06,
                AVG(HOUR(start_time) BETWEEN 6 AND 11) AS fraction_06_12,
                AVG(HOUR(start_time) BETWEEN 12 AND 17) AS fraction_12_18,
                AVG(HOUR(start_time) >= 18) AS fraction_18_24
            FROM trip
            GROUP BY call_type
            ORDER BY call_type;
        """
        self.run_query(query)

    def task_5_hours_and_distance(self):
        query = """SELECT
                taxi_id,
                SUM(TIMESTAMPDIFF(SECOND, start_time, end_time)) / 3600 AS total_hours,
                SUM(distance_km) AS total_distance_km
            FROM trip
            GROUP BY taxi_id
            ORDER BY total_hours DESC
            LIMIT 20;
        """
        self.run_query(query)

    def task_6_city_hall(self, chunk_size=5000):
        city_hall_lat = 41.15794
        city_hall_lon = -8.62911
        max_distance_m = 100

        query = """SELECT
                g.trip_pk,
                t.trip_id,
                t.taxi_id,
                g.latitude,
                g.longitude
            FROM gps_point g
            JOIN trip t ON t.trip_pk = g.trip_pk;
        """
        self.cursor.execute(query)

        found_trips = {}

        while True:
            points = self.cursor.fetchmany(chunk_size)
            if not points:
                break

            for point in points:
                trip_pk = point[0]
                trip_id = point[1]
                taxi_id = point[2]
                latitude = point[3]
                longitude = point[4]

                if trip_pk in found_trips:
                    continue

                distance_m = haversine(
                    (latitude, longitude),
                    (city_hall_lat, city_hall_lon),
                    Unit.METERS
                )

                if distance_m <= max_distance_m:
                    found_trips[trip_pk] = (trip_id, taxi_id)

        rows = []
        for trip_pk in sorted(found_trips):
            trip_id, taxi_id = found_trips[trip_pk]
            rows.append((trip_id, taxi_id))

        print(tabulate(rows, headers=["trip_id", "taxi_id"]))

    def task_7_invalid_trips(self):
        query = """WITH points_per_trip AS (
                SELECT
                    t.trip_pk,
                    COUNT(g.trip_pk) AS n_points
                FROM trip t
                LEFT JOIN gps_point g ON g.trip_pk = t.trip_pk
                GROUP BY t.trip_pk
            )
            SELECT COUNT(*) AS invalid_trips
            FROM points_per_trip
            WHERE n_points < 3;
        """
        self.run_query(query)

    def task_8_midnight_crossers(self):
        query = """SELECT trip_id, taxi_id, start_time, end_time
            FROM trip
            WHERE DATEDIFF(end_time, start_time) = 1
            ORDER BY start_time;
        """
        self.run_query(query)

    def task_9_circular_trips(self, chunk_size=5000):
        max_distance_m = 50

        query = """WITH first_last AS (
                SELECT
                    trip_pk,
                    MIN(seq_num) AS first_seq,
                    MAX(seq_num) AS last_seq
                FROM gps_point
                GROUP BY trip_pk
            )
            SELECT
                t.trip_id,
                t.taxi_id,
                start_point.latitude,
                start_point.longitude,
                end_point.latitude,
                end_point.longitude
            FROM first_last fl
            JOIN trip t ON t.trip_pk = fl.trip_pk
            JOIN gps_point start_point
                ON start_point.trip_pk = fl.trip_pk AND start_point.seq_num = fl.first_seq
            JOIN gps_point end_point
                ON end_point.trip_pk = fl.trip_pk AND end_point.seq_num = fl.last_seq
            WHERE fl.last_seq > fl.first_seq;
        """
        self.cursor.execute(query)

        rows = []

        while True:
            trips = self.cursor.fetchmany(chunk_size)
            if not trips:
                break

            start_coords = []
            end_coords = []
            for trip in trips:
                start_lat = trip[2]
                start_lon = trip[3]
                end_lat = trip[4]
                end_lon = trip[5]
                start_coords.append((start_lat, start_lon))
                end_coords.append((end_lat, end_lon))

            distances = haversine_vector(start_coords, end_coords, Unit.METERS, check=False)

            for i in range(len(trips)):
                trip_id = trips[i][0]
                taxi_id = trips[i][1]
                distance_m = distances[i]

                if distance_m <= max_distance_m:
                    rows.append((trip_id, taxi_id, round(distance_m, 1)))

        print(tabulate(rows, headers=["trip_id", "taxi_id", "start_end_distance_m"]))

    def task_10_idle_time(self):
        query = """WITH idle_periods AS (
                SELECT
                    taxi_id,
                    end_time,
                    LEAD(start_time) OVER (
                        PARTITION BY taxi_id
                        ORDER BY start_time, trip_pk
                    ) AS next_start_time
                FROM trip
            )
            SELECT
                taxi_id,
                AVG(TIMESTAMPDIFF(SECOND, end_time, next_start_time)) / 3600 AS avg_idle_hours
            FROM idle_periods
            WHERE next_start_time IS NOT NULL
            GROUP BY taxi_id
            ORDER BY avg_idle_hours DESC
            LIMIT 20;
        """
        self.run_query(query)


def main():
    program = Queries()

    #program.task_1_counts()
    program.task_2_avg_trips_per_taxi()
    #program.task_3_top_20_taxis()
    #program.task_4a_most_used_call_type()
    #program.task_4b_call_type_stats()
    #program.task_5_hours_and_distance()
    #program.task_6_city_hall()
    #program.task_7_invalid_trips()
    #program.task_8_midnight_crossers()
    #program.task_9_circular_trips()
    #program.task_10_idle_time()
    # program.debug_db_health()

    program.connection.close_connection()


if __name__ == "__main__":
    main()
