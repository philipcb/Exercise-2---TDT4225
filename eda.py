import pandas as pd
import json
from tabulate import tabulate

DATA_PATH = "porto/porto.csv"


def inspect_structure(df):
    print(tabulate([["Rows", df.shape[0]], ["Columns", df.shape[1]]], headers=["", "Count"]))

    dtypes = df.dtypes
    missing = df.isna().sum()
    column_rows = []
    for column in df.columns:
        column_rows.append((column, str(dtypes[column]), missing[column]))
    print()
    print(tabulate(column_rows, headers=["Column", "Type", "Missing values"]))

    print()
    print(tabulate(df.drop(columns="POLYLINE").head(), headers="keys", showindex=False, floatfmt=".0f"))


def analyze_trip_ids(df):
    duplicates = df[df.duplicated("TRIP_ID", keep=False)]
    exact_duplicates = df[df.duplicated(keep=False)]

    summary = [
        ["Unique TRIP_IDs", df["TRIP_ID"].nunique()],
        ["Duplicate TRIP_IDs", duplicates["TRIP_ID"].nunique()],
        ["Rows with duplicate TRIP_ID", len(duplicates)],
        ["Exact duplicate rows", len(exact_duplicates)],
    ]
    print(tabulate(summary, headers=["", "Count"]))

    print("\nTRIP_IDs with exact duplicates:")
    counts = exact_duplicates["TRIP_ID"].value_counts()
    print(tabulate(counts.items(), headers=["TRIP_ID", "Occurrences"]))

    print("\nExact duplicate rows:")
    print(tabulate(
        exact_duplicates[["TRIP_ID", "CALL_TYPE", "TAXI_ID", "TIMESTAMP", "n_points"]],
        headers="keys",
        showindex=False,
    ))

def analyze_call_types(df):
    counts = df["CALL_TYPE"].value_counts()

    rows = []
    for call_type in ["A", "B", "C"]:
        subset = df[df["CALL_TYPE"] == call_type]
        rows.append((
            call_type,
            counts[call_type],
            subset["ORIGIN_CALL"].notna().sum(),
            subset["ORIGIN_STAND"].notna().sum(),
        ))

    print(tabulate(rows, headers=["CALL_TYPE", "Trips", "With ORIGIN_CALL", "With ORIGIN_STAND"]))


def analyze_day_types(df):
    counts = df["DAY_TYPE"].value_counts()
    print(tabulate(counts.items(), headers=["DAY_TYPE", "Trips"]))

def analyze_polyline(df):
    points_stats = df["n_points"].describe()

    trips = df[df["n_points"] >= 2]
    duration_min = (trips["n_points"] - 1) * 15 / 60
    duration_stats = duration_min.describe()

    rows = []
    for statistic in points_stats.index:
        rows.append((statistic, points_stats[statistic], duration_stats[statistic]))
    print(tabulate(
        rows,
        headers=["Statistic", "n_points (all trips)", "duration_min (trips with >= 2 points)"],
        floatfmt=".2f",
    ))

    print()
    print(tabulate([["Trips over 3 hours", (duration_min > 180).sum()]], headers=["", "Count"]))


def analyze_missing_data(df):
    missing_counts = df["MISSING_DATA"].value_counts()
    print(tabulate(missing_counts.items(), headers=["MISSING_DATA", "Trips"]))

    short_trips = df[df["n_points"] < 2]

    summary = [
        ["Trips with 0 points", (df["n_points"] == 0).sum()],
        ["Trips with 1 point", (df["n_points"] == 1).sum()],
        ["Trips with < 2 points flagged as MISSING_DATA", short_trips["MISSING_DATA"].sum()],
    ]
    print()
    print(tabulate(summary, headers=["", "Count"]))

    print("\nCALL_TYPE of trips with < 2 points:")
    call_type_counts = short_trips["CALL_TYPE"].value_counts()
    print(tabulate(call_type_counts.items(), headers=["CALL_TYPE", "Trips"]))


def main():
    df = pd.read_csv(DATA_PATH)
    #inspect_structure(df)

    n_points = []
    for polyline in df["POLYLINE"]:
        points = json.loads(polyline)
        n_points.append(len(points))
    df["n_points"] = n_points

    analyze_trip_ids(df)
    #analyze_call_types(df)
    #analyze_day_types(df)
    #analyze_polyline(df)
    #analyze_missing_data(df)


if __name__ == '__main__':
    main()
