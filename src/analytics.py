
"""Calculate survey statistics and generate actionable insights."""

from pathlib import Path

import pandas as pd


def analyze_data(df: pd.DataFrame) -> dict:
    """Calculate summary metrics, distributions, and demographic patterns."""
    required = {
        "Timestamp",
        "Region",
        "Age_Group",
        "Preferred_Tool",
        "Satisfaction",
        "Feedback",
    }
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {', '.join(sorted(missing))}"
        )

    if df.empty:
        raise ValueError("Cannot analyze an empty dataset.")

    data = df.copy()
    data["Satisfaction"] = pd.to_numeric(
        data["Satisfaction"], errors="coerce"
    )
    data["Timestamp"] = pd.to_datetime(
        data["Timestamp"], errors="coerce"
    )
    data = data.dropna(subset=["Satisfaction", "Timestamp"])
    data = data[data["Satisfaction"].between(1, 5)]

    if data.empty:
        raise ValueError("No valid responses remain for analysis.")

    # Popularity and satisfaction summaries.
    tool_counts = (
        data["Preferred_Tool"]
        .value_counts()
        .rename_axis("Preferred_Tool")
        .reset_index(name="Responses")
    )
    tool_counts["Percentage"] = (
        tool_counts["Responses"] / len(data) * 100
    ).round(2)

    rating_counts = (
        data["Satisfaction"]
        .value_counts()
        .reindex([1, 2, 3, 4, 5], fill_value=0)
        .sort_index()
        .rename_axis("Rating")
        .reset_index(name="Responses")
    )

    age_tool_counts = pd.crosstab(
        data["Age_Group"], data["Preferred_Tool"]
    )
    region_tool_counts = pd.crosstab(
        data["Region"], data["Preferred_Tool"]
    )

    monthly_responses = (
        data.assign(Date=data["Timestamp"].dt.date)
        .groupby("Date")
        .size()
        .rename("Responses")
        .reset_index()
    )

    feedback = (
        data["Feedback"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    feedback = feedback[feedback.ne("")]

    top_tool = tool_counts.iloc[0]["Preferred_Tool"]
    top_tool_count = int(tool_counts.iloc[0]["Responses"])
    average_satisfaction = float(data["Satisfaction"].mean())
    high_ratings = int(data["Satisfaction"].ge(4).sum())
    high_rating_percentage = high_ratings / len(data) * 100

    insights = [
        f"{top_tool} is the most popular tool, with "
        f"{top_tool_count:,} responses ({top_tool_count / len(data) * 100:.1f}%).",
        f"The average satisfaction rating is "
        f"{average_satisfaction:.2f} out of 5.",
        f"{high_rating_percentage:.1f}% of valid responses have a rating of 4 or 5.",
        f"{len(feedback):,} responses contain written feedback.",
    ]

    return {
        "total_responses": int(len(data)),
        "average_satisfaction": round(average_satisfaction, 2),
        "top_tool": str(top_tool),
        "top_tool_count": top_tool_count,
        "high_rating_percentage": round(high_rating_percentage, 2),
        "tool_counts": tool_counts,
        "rating_counts": rating_counts,
        "age_tool_counts": age_tool_counts,
        "region_tool_counts": region_tool_counts,
        "daily_responses": monthly_responses,
        "feedback": feedback,
        "insights": insights,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_file = project_root / "outputs" / "cleaned_poll_responses.csv"

    if not data_file.exists():
        raise FileNotFoundError(
            "Cleaned dataset not found. Run "
            "'python src\\data_processor.py' first."
        )

    df = pd.read_csv(data_file)
    results = analyze_data(df)

    print("=" * 55)
    print("POLL RESULTS VISUALIZER - ANALYTICS REPORT")
    print("=" * 55)
    print(f"Total responses          : {results['total_responses']:,}")
    print(f"Most popular tool        : {results['top_tool']}")
    print(f"Average satisfaction     : {results['average_satisfaction']}/5")
    print(
        f"Ratings of 4 or 5        : "
        f"{results['high_rating_percentage']:.1f}%"
    )

    print("\nTool popularity:")
    print(results["tool_counts"].to_string(index=False))

    print("\nSatisfaction distribution:")
    print(results["rating_counts"].to_string(index=False))

    print("\nPreferred tools by age group:")
    print(results["age_tool_counts"].to_string())

    print("\nAutomated insights:")
    for number, insight in enumerate(results["insights"], start=1):
        print(f"{number}. {insight}")


if __name__ == "__main__":
    main()
