from DbConnector import DbConnector

DROP_TABLES = [
    "DROP TABLE IF EXISTS gps_point",
    "DROP TABLE IF EXISTS trip",
    "DROP TABLE IF EXISTS taxi",
]

CREATE_TABLES = [
    """CREATE TABLE taxi (
        taxi_id INT NOT NULL PRIMARY KEY
    )""",
    """CREATE TABLE trip (
        trip_pk BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        trip_id BIGINT NOT NULL,
        call_type CHAR(1) NOT NULL,
        origin_call INT,
        origin_stand INT,
        taxi_id INT NOT NULL,
        start_time DATETIME NOT NULL,
        day_type CHAR(1),
        missing_data BOOLEAN NOT NULL,
        FOREIGN KEY (taxi_id) REFERENCES taxi (taxi_id)
    )""",
    """CREATE TABLE gps_point (
        trip_pk BIGINT NOT NULL,
        seq_num INT NOT NULL,
        longitude DOUBLE NOT NULL,
        latitude DOUBLE NOT NULL,
        PRIMARY KEY (trip_pk, seq_num),
        FOREIGN KEY (trip_pk) REFERENCES trip (trip_pk)
    )""",
]


def main():
    connection = DbConnector()

    for query in DROP_TABLES + CREATE_TABLES:
        connection.cursor.execute(query)
    connection.db_connection.commit()

    connection.cursor.execute("SHOW TABLES")
    print(connection.cursor.fetchall())

    connection.close_connection()


if __name__ == '__main__':
    main()
