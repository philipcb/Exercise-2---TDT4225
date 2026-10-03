import pandas as pd
import json

DATA_PATH = "porto/porto.csv"


def inspect_structure(df):
    print(df.shape)
    print(df.dtypes)
    print(df.drop(columns="POLYLINE").head())
    print(df.isna().sum())


def analyze_trip_ids(df):
    print("Unique TRIP_IDs:", df["TRIP_ID"].nunique())

    duplicates = df[df.duplicated("TRIP_ID", keep=False)]

    print("Duplicate TRIP_IDs:", duplicates["TRIP_ID"].nunique())
    print("Rows with duplicate TRIP_ID:", len(duplicates))

    exact_duplicates = df[df.duplicated(keep=False)]

    print("Exact duplicate rows:", len(exact_duplicates))
    print("TRIP_IDs with exact duplicates:")
    print(exact_duplicates["TRIP_ID"].value_counts())
    print(exact_duplicates[
    ["TRIP_ID", "CALL_TYPE", "TAXI_ID", "TIMESTAMP", "POLYLINE"]
    ].to_string(index=False))

def analyze_call_types(df):
    print(df["CALL_TYPE"].value_counts())

    for call_type in ["A", "B", "C"]:
        subset = df[df["CALL_TYPE"] == call_type]

        print(f"\nCALL_TYPE {call_type}:")
        print("  With ORIGIN_CALL:", subset["ORIGIN_CALL"].notna().sum())
        print("  With ORIGIN_STAND:", subset["ORIGIN_STAND"].notna().sum())


def analyze_day_types(df):
    print(df["DAY_TYPE"].value_counts())

def analyze_polyline(df):
    print(df["n_points"].describe())

    trips = df[df["n_points"] >= 2]
    duration_min = (trips["n_points"] - 1) * 15 / 60

    print(duration_min.describe())
    print("Trips over 3 hours:", (duration_min > 180).sum())


def analyze_missing_data(df):
    print(df["MISSING_DATA"].value_counts())

    print("Trips with 0 points:", (df["n_points"] == 0).sum())
    print("Trips with 1 point:", (df["n_points"] == 1).sum())

    short_trips = df[df["n_points"] < 2]

    print("Flagged as MISSING_DATA:", short_trips["MISSING_DATA"].sum())
    print(short_trips["CALL_TYPE"].value_counts())


def main():
    df = pd.read_csv(DATA_PATH)
    #inspect_structure(df)

    n_points = []
    for polyline in df["POLYLINE"]:
        points = json.loads(polyline)
        n_points.append(len(points))
    df["n_points"] = n_points

    #analyze_trip_ids(df)
    analyze_call_types(df)
    #analyze_day_types(df)
    #analyze_polyline(df)
    #analyze_missing_data(df)


if __name__ == '__main__':
    main()
