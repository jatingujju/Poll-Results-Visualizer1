
"""Generate realistic synthetic survey data for the Poll Results Visualizer."""

from pathlib import Path

import numpy as np
import pandas as pd


# Reproducible results: the same seed produces the same dataset.
RANDOM_SEED = 42
NUMBER_OF_RESPONSES = 1000

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "poll_responses.csv"


def generate_survey_data(
    number_of_responses: int = NUMBER_OF_RESPONSES,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Create synthetic survey responses with realistic group patterns."""

    if number_of_responses < 1:
        raise ValueError("number_of_responses must be at least 1.")

    rng = np.random.default_rng(seed)

    # Generate timestamps over a 30-day survey period.
    start_date = pd.Timestamp("2026-09-01")
    timestamps = start_date + pd.to_timedelta(
        rng.integers(0, 30 * 24 * 60, number_of_responses),
        unit="m",
    )

    regions = rng.choice(
        ["North", "South", "East", "West", "Central"],
        size=number_of_responses,
        p=[0.20, 0.22, 0.16, 0.24, 0.18],
    )

    age_groups = rng.choice(
        ["18-24", "25-34", "35-44", "45-54", "55+"],
        size=number_of_responses,
        p=[0.32, 0.30, 0.18, 0.12, 0.08],
    )

    # Preferences vary by age group to enable demographic comparisons.
    preferred_tools = []
    satisfaction_ratings = []

    tool_options = ["Python", "Excel", "Power BI", "Tableau", "Other"]

    for age_group in age_groups:
        if age_group == "18-24":
            probabilities = [0.34, 0.18, 0.24, 0.16, 0.08]
        elif age_group == "25-34":
            probabilities = [0.27, 0.18, 0.27, 0.20, 0.08]
        elif age_group == "35-44":
            probabilities = [0.18, 0.25, 0.29, 0.20, 0.08]
        else:
            probabilities = [0.12, 0.34, 0.25, 0.20, 0.09]

        preferred_tools.append(
            rng.choice(tool_options, p=probabilities)
        )

    # Ratings are associated with the selected tool, with random variation.
    tool_rating_means = {
        "Python": 4.2,
        "Excel": 3.8,
        "Power BI": 4.3,
        "Tableau": 4.1,
        "Other": 3.5,
    }

    for tool in preferred_tools:
        rating = int(np.rint(rng.normal(tool_rating_means[tool], 0.9)))
        satisfaction_ratings.append(np.clip(rating, 1, 5))

    feedback_options = {
        "Python": [
            "Flexible and useful for data analysis",
            "Great for automation and visualization",
            "Powerful but takes time to learn",
        ],
        "Excel": [
            "Easy to use for everyday tasks",
            "Useful for quick reports",
            "Works well for smaller datasets",
        ],
        "Power BI": [
            "Interactive dashboards are very useful",
            "Great for business reporting",
            "Helpful for sharing insights with teams",
        ],
        "Tableau": [
            "Beautiful and interactive visualizations",
            "Useful for exploring business trends",
            "Charts are clear and engaging",
        ],
        "Other": [
            "Could use more learning resources",
            "Works for my specific requirements",
            "Some features could be improved",
        ],
    }

    feedback = [
        rng.choice(feedback_options[tool])
        for tool in preferred_tools
    ]

    df = pd.DataFrame(
        {
            "Response_ID": range(1, number_of_responses + 1),
            "Timestamp": timestamps,
            "Region": regions,
            "Age_Group": age_groups,
            "Preferred_Tool": preferred_tools,
            "Satisfaction": satisfaction_ratings,
            "Feedback": feedback,
        }
    )

    # Introduce a small number of missing values to test cleaning later.
    if number_of_responses >= 20:
        missing_count = max(1, int(number_of_responses * 0.02))
        missing_rows = rng.choice(
            df.index, size=missing_count, replace=False
        )
        df.loc[missing_rows, "Feedback"] = None

    return df


def main() -> None:
    """Generate and save the survey CSV."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = generate_survey_data()
    df.to_csv(OUTPUT_FILE, index=False)

    print("=" * 55)
    print("POLL RESULTS VISUALIZER - DATA GENERATOR")
    print("=" * 55)
    print(f"Generated responses : {len(df):,}")
    print(f"Unique regions      : {df['Region'].nunique()}")
    print(f"Unique age groups   : {df['Age_Group'].nunique()}")
    print(f"Available tools     : {df['Preferred_Tool'].nunique()}")
    print(f"Missing feedback    : {df['Feedback'].isna().sum()}")
    print(f"Output file         : {OUTPUT_FILE}")
    print("\nDataset preview:")
    print(df.head(10).to_string(index=False))
    print("\nDataset information:")
    print(df.info())
    print("\nSynthetic data generated successfully.")


if __name__ == "__main__":
    main()
