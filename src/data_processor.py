
"""Data loading, validation, cleaning, and quality reporting."""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "Response_ID",
    "Timestamp",
    "Region",
    "Age_Group",
    "Preferred_Tool",
    "Satisfaction",
    "Feedback",
]


def load_data(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV file and validate its required columns."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    return df


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean survey data and return it with a quality report."""
    if df.empty:
        raise ValueError("Cannot clean an empty dataset.")

    data = df.copy()
    original_rows = len(data)

    # Record missing values before cleaning.
    missing_before = int(data.isna().sum().sum())

    # Remove exact duplicate rows.
    duplicate_rows = int(data.duplicated().sum())
    data = data.drop_duplicates().copy()

    # Standardize text fields without converting missing values to "nan".
    text_columns = [
        "Region",
        "Age_Group",
        "Preferred_Tool",
        "Feedback",
    ]

    for column in text_columns:
        data[column] = data[column].astype("string").str.strip()
        data[column] = data[column].replace("", pd.NA)

    # Convert fields to the expected data types.
    data["Timestamp"] = pd.to_datetime(
        data["Timestamp"], errors="coerce"
    )
    data["Satisfaction"] = pd.to_numeric(
        data["Satisfaction"], errors="coerce"
    )

    # Invalid ratings become missing values.
    invalid_ratings = ~data["Satisfaction"].between(1, 5)
    invalid_rating_count = int(
        (data["Satisfaction"].notna() & invalid_ratings).sum()
    )
    data.loc[invalid_ratings, "Satisfaction"] = pd.NA

    # A response without a timestamp or rating cannot support
    # time-based or satisfaction analysis, so exclude it.
    essential_missing = data["Timestamp"].isna() | data["Satisfaction"].isna()
    excluded_rows = int(essential_missing.sum())
    data = data.loc[~essential_missing].copy()

    # Ratings should be whole numbers from 1 through 5.
    data["Satisfaction"] = data["Satisfaction"].round().astype("Int64")

    # Fill missing optional categorical values for consistent grouping.
    for column in ["Region", "Age_Group", "Preferred_Tool"]:
        data[column] = data[column].fillna("Unknown")

    # Feedback is optional. Preserve missing comments for quality reporting.
    data["Feedback"] = data["Feedback"].fillna("")

    missing_after = int(data.isna().sum().sum())

    report = {
        "original_rows": original_rows,
        "duplicate_rows_removed": duplicate_rows,
        "invalid_ratings_found": invalid_rating_count,
        "rows_excluded": excluded_rows,
        "cleaned_rows": len(data),
        "missing_values_before": missing_before,
        "missing_values_after": missing_after,
        "feedback_entries_missing": int((data["Feedback"] == "").sum()),
    }

    return data.reset_index(drop=True), report


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / "data" / "poll_responses.csv"
    output_file = project_root / "outputs" / "cleaned_poll_responses.csv"

    df = load_data(input_file)
    cleaned_df, report = clean_data(df)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_file, index=False)

    print("=" * 55)
    print("POLL RESULTS VISUALIZER - DATA QUALITY REPORT")
    print("=" * 55)

    for label, value in report.items():
        print(f"{label.replace('_', ' ').title():30}: {value}")

    print(f"\nCleaned dataset saved to:\n{output_file}")
    print("\nCleaned data preview:")
    print(cleaned_df.head().to_string(index=False))


if __name__ == "__main__":
    main()
