
"""Poll Results Visualizer — professional survey analytics dashboard."""

from collections import Counter
from pathlib import Path
import html
import re

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from wordcloud import STOPWORDS, WordCloud

from src.analytics import analyze_data
from src.data_processor import clean_data, load_data


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = PROJECT_ROOT / "data" / "poll_responses.csv"

st.set_page_config(
    page_title="Poll Results Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM UI THEME
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7ff 0%, #edf4ff 100%);
    }

    .block-container {
        max-width: 1600px;
        padding: 1.5rem 2rem 2.5rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111a30 0%, #202c47 100%);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #f8fafc !important;
        opacity: 1 !important;
        text-shadow: none !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #e2e8f0 !important;
    }

    /* Main headings */
    [data-testid="stAppViewContainer"] .main h1,
    [data-testid="stAppViewContainer"] .main h2,
    [data-testid="stAppViewContainer"] .main h3,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: #172554 !important;
        font-weight: 750 !important;
        opacity: 1 !important;
        text-shadow: none !important;
    }

    [data-testid="stMarkdownContainer"] p {
        color: #475569;
    }

    /* KPI cards */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.97);
        border: 1px solid #dce6f8;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 5px 18px rgba(31, 55, 100, 0.06);
        min-height: 122px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 9px 22px rgba(31, 55, 100, 0.10);
    }

    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #172554 !important;
        font-weight: 800;
    }

    /* Charts */
    [data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #dce6f8;
        border-radius: 16px;
        padding: 8px;
        box-shadow: 0 5px 18px rgba(31, 55, 100, 0.045);
    }

    [data-testid="stImage"] img {
        border-radius: 12px;
    }

    /* Expanders and tables */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #dce6f8;
        border-radius: 12px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #dce6f8;
        border-radius: 12px;
        overflow: hidden;
    }

    /* Buttons */
    .stButton button,
    .stDownloadButton button {
        border-radius: 10px;
        font-weight: 650;
        min-height: 42px;
        transition: all 0.2s ease;
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        border-color: #6366f1;
        color: #4f46e5;
    }

    .section-note {
        color: #64748b !important;
        font-size: 0.9rem;
        margin-top: -8px;
        margin-bottom: 14px;
    }

    .insight-card {
        background: linear-gradient(120deg, #eef2ff, #f0fdfa);
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 13px 16px;
        margin-bottom: 9px;
        color: #1e3a5f;
        line-height: 1.55;
    }

    .insight-number {
        color: #4f46e5;
        font-weight: 800;
    }

    hr {
        border-color: #dce6f8;
        margin: 1.4rem 0;
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.8rem 2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def make_chart(fig, height=350):
    """Apply consistent styling and readable text to Plotly charts."""

    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font={
            "family": "Arial, sans-serif",
            "color": "#334155",
            "size": 12,
        },
        margin={"l": 24, "r": 35, "t": 30, "b": 25},
        hoverlabel={
            "bgcolor": "#172554",
            "font_color": "#ffffff",
        },
        legend={
            "font": {"color": "#334155", "size": 11},
            "title_font": {"color": "#334155"},
        },
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#e2e8f0",
        zeroline=False,
        color="#475569",
        title_font_color="#334155",
        tickfont_color="#475569",
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#e2e8f0",
        zeroline=False,
        color="#475569",
        title_font_color="#334155",
        tickfont_color="#475569",
    )

    st.plotly_chart(fig, use_container_width=True)


def build_feedback_counts(feedback_series):
    """Count common feedback words after removing filler words."""

    stop_words = set(STOPWORDS) | {
        "useful", "could", "would", "really", "much",
        "also", "using", "used", "works", "work",
        "time", "takes", "great", "well", "easy",
        "helpful", "everyday", "specific", "requirements",
    }

    text = " ".join(
        feedback_series.fillna("").astype(str).tolist()
    ).lower()

    words = re.findall(r"\b[a-z]{3,}\b", text)
    counts = Counter(
        word for word in words if word not in stop_words
    )

    return pd.DataFrame(
        counts.most_common(12),
        columns=["Word", "Frequency"],
    )


def load_and_clean_data(source, uploaded_file=None):
    """Load sample or uploaded data and clean it."""

    if source == "Sample dataset":
        if not DEFAULT_DATA.exists():
            raise FileNotFoundError(
                "Sample data not found. Run "
                "'python src\\data_generator.py' first."
            )
        raw_df = load_data(DEFAULT_DATA)
    else:
        if uploaded_file is None:
            raise ValueError("Upload a CSV file to continue.")
        raw_df = pd.read_csv(uploaded_file)

    cleaned_df, quality_report = clean_data(raw_df)
    return cleaned_df, quality_report


# ============================================================
# DASHBOARD
# ============================================================

def main():
    # Header
    st.markdown(
        """
        <div style="
            background: linear-gradient(120deg, #4338ca, #2563eb, #0d9488);
            padding: 27px 30px;
            border-radius: 20px;
            margin-bottom: 22px;
            box-shadow: 0 12px 30px rgba(37, 99, 235, 0.18);
        ">
            <div style="
                color: #ffffff;
                font-size: clamp(1.7rem, 3vw, 2.45rem);
                font-weight: 800;
                letter-spacing: -1px;
            ">
                📊 Poll Results Visualizer
            </div>
            <div style="
                color: #e0eaff;
                font-size: 1rem;
                margin-top: 8px;
            ">
                Transform survey responses into clear,
                actionable insights.
            </div>
            <div style="
                color: #dbeafe;
                font-size: 0.82rem;
                margin-top: 14px;
            ">
                AIpreneur Portfolio Project
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar: data source
    with st.sidebar:
        st.markdown("## 📊 Poll Insights")
        st.caption("Survey analytics workspace")
        st.divider()

        st.markdown("### Data source")

        source = st.radio(
            "Select a data source",
            ["Sample dataset", "Upload CSV"],
            label_visibility="collapsed",
        )

        uploaded_file = None

        if source == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload survey CSV",
                type=["csv"],
                help=(
                    "Expected columns: Response_ID, Timestamp, "
                    "Region, Age_Group, Preferred_Tool, "
                    "Satisfaction, Feedback."
                ),
            )

        st.divider()
        st.markdown("### Filters")

    # Load data
    try:
        df, quality_report = load_and_clean_data(
            source, uploaded_file
        )
    except (
        ValueError,
        FileNotFoundError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as exc:
        if source == "Upload CSV" and uploaded_file is None:
            st.info(
                "Upload a compatible CSV from the sidebar "
                "to start analyzing your survey responses."
            )
        else:
            st.error(f"Unable to load this dataset: {exc}")
        st.stop()

    if df.empty:
        st.warning("No valid responses are available.")
        st.stop()

    required_columns = {
        "Timestamp", "Region", "Age_Group",
        "Preferred_Tool", "Satisfaction", "Feedback",
    }
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        st.error(
            "The dataset is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
        st.stop()

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"], errors="coerce"
    )
    df["Satisfaction"] = pd.to_numeric(
        df["Satisfaction"], errors="coerce"
    )

    # Sidebar filters
    with st.sidebar:
        regions = sorted(
            df["Region"].fillna("Unknown").unique().tolist()
        )
        age_groups = sorted(
            df["Age_Group"].fillna("Unknown").unique().tolist()
        )
        tools = sorted(
            df["Preferred_Tool"].fillna("Unknown").unique().tolist()
        )

        selected_regions = st.multiselect(
            "Region", regions, default=regions
        )
        selected_ages = st.multiselect(
            "Age group", age_groups, default=age_groups
        )
        selected_tools = st.multiselect(
            "Preferred tool", tools, default=tools
        )

        valid_dates = df["Timestamp"].dropna()
        date_range = None

        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

            date_range = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

        st.divider()
        st.caption("Poll Results Visualizer")
        st.caption("Sample data is synthetic.")

    # Apply filters
    filtered = df[
        df["Region"].fillna("Unknown").isin(selected_regions)
        & df["Age_Group"].fillna("Unknown").isin(selected_ages)
        & df["Preferred_Tool"].fillna("Unknown").isin(selected_tools)
    ].copy()

    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            filtered["Timestamp"].dt.date.between(
                start_date, end_date
            )
        ]

    if filtered.empty:
        st.warning("No responses match your selected filters.")
        st.stop()

    try:
        results = analyze_data(filtered)
    except (ValueError, KeyError) as exc:
        st.error(f"Unable to analyze this selection: {exc}")
        st.stop()

    # KPI cards
    st.markdown("## Survey overview")
    st.markdown(
        '<p class="section-note">'
        "A quick summary of the selected responses"
        "</p>",
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Total responses",
        f"{results['total_responses']:,}",
        help="Responses included after applying filters.",
    )
    k2.metric(
        "Average satisfaction",
        f"{results['average_satisfaction']:.2f} / 5",
        help="Average satisfaction rating.",
    )
    k3.metric(
        "Most popular tool",
        results["top_tool"],
        f"{results['top_tool_count']:,} responses",
    )
    k4.metric(
        "Positive ratings",
        f"{results['high_rating_percentage']:.1f}%",
        help="Percentage of responses rated 4 or 5.",
    )

    st.divider()

    # Tool popularity and satisfaction
    st.markdown("## Response analytics")
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### Preferred tools")
        st.markdown(
            '<p class="section-note">'
            "Which tools respondents prefer"
            "</p>",
            unsafe_allow_html=True,
        )

        tool_data = results["tool_counts"].sort_values("Responses")

        fig = px.bar(
            tool_data,
            x="Responses",
            y="Preferred_Tool",
            orientation="h",
            text="Responses",
            color="Preferred_Tool",
            color_discrete_sequence=px.colors.qualitative.Bold,
            hover_data={"Percentage": ":.1f"},
            labels={
                "Preferred_Tool": "Tool",
                "Responses": "Responses",
                "Percentage": "Share (%)",
            },
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="Number of responses",
            yaxis_title="",
        )
        make_chart(fig, 360)

    with right:
        st.markdown("### Satisfaction distribution")
        st.markdown(
            '<p class="section-note">'
            "How respondents rated their experience"
            "</p>",
            unsafe_allow_html=True,
        )

        rating_data = results["rating_counts"]

        fig = px.bar(
            rating_data,
            x="Rating",
            y="Responses",
            text="Responses",
            color="Rating",
            color_continuous_scale=[
                "#fda4af", "#fdba74", "#facc15",
                "#60a5fa", "#34d399",
            ],
            labels={"Rating": "Satisfaction rating (1–5)"},
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
        )
        fig.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            xaxis={"dtick": 1},
            xaxis_title="Rating (1–5)",
            yaxis_title="Number of responses",
        )
        make_chart(fig, 360)

    # Demographics and trends
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### Tool preferences by age")
        st.markdown(
            '<p class="section-note">'
            "Compare choices across age groups"
            "</p>",
            unsafe_allow_html=True,
        )

        age_data = results["age_tool_counts"].reset_index().melt(
            id_vars="Age_Group",
            var_name="Preferred_Tool",
            value_name="Responses",
        )

        fig = px.bar(
            age_data,
            x="Age_Group",
            y="Responses",
            color="Preferred_Tool",
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Bold,
            labels={"Age_Group": "Age group"},
        )
        fig.update_layout(
            xaxis_title="Age group",
            yaxis_title="Responses",
            legend_title="Preferred tool",
        )
        make_chart(fig, 380)

    with right:
        st.markdown("### Response trends")
        st.markdown(
            '<p class="section-note">'
            "Daily survey response volume"
            "</p>",
            unsafe_allow_html=True,
        )

        daily_data = (
            filtered.dropna(subset=["Timestamp"])
            .assign(
                Response_Date=lambda data: data["Timestamp"].dt.date
            )
            .groupby("Response_Date")
            .size()
            .reset_index(name="Responses")
        )

        fig = px.line(
            daily_data,
            x="Response_Date",
            y="Responses",
            markers=True,
            labels={"Response_Date": "Date"},
        )
        fig.update_traces(
            line={"color": "#4f46e5", "width": 3},
            marker={"size": 7, "color": "#2563eb"},
            fill="tozeroy",
            fillcolor="rgba(79,70,229,0.09)",
        )
        fig.update_layout(
            xaxis_title="Response date",
            yaxis_title="Responses",
        )
        make_chart(fig, 380)

    # Feedback analysis
    st.divider()
    st.markdown("## Feedback analysis")
    st.markdown(
        '<p class="section-note">'
        "Discover recurring themes in respondents’ written comments"
        "</p>",
        unsafe_allow_html=True,
    )

    feedback = (
        filtered["Feedback"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    feedback = feedback[feedback.ne("")]

    if feedback.empty:
        st.info("No written feedback is available for these filters.")
    else:
        feedback_text = " ".join(feedback.tolist())
        word_col, comments_col = st.columns([3, 2], gap="large")

        with word_col:
            st.markdown("### Feedback word cloud")

            # Corrected caption: dark text on the light background.
            st.markdown(
                '<p style="color:#64748b; font-size:14px; '
                'margin-top:-8px; margin-bottom:14px;">'
                'Larger words appear more frequently in the comments.'
                '</p>',
                unsafe_allow_html=True,
            )

            custom_stopwords = set(STOPWORDS) | {
                "useful", "could", "would", "really", "also",
                "using", "used", "works", "work", "takes", "time",
            }

            try:
                cloud = WordCloud(
                    width=1000,
                    height=500,
                    background_color="white",
                    colormap="viridis",
                    stopwords=custom_stopwords,
                    collocations=False,
                    max_words=100,
                    prefer_horizontal=0.9,
                    random_state=42,
                    margin=8,
                ).generate(feedback_text)

                fig, ax = plt.subplots(figsize=(12, 6))
                ax.imshow(cloud, interpolation="bilinear")
                ax.axis("off")
                fig.patch.set_facecolor("white")
                fig.tight_layout(pad=0)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

            except ValueError:
                st.info(
                    "There are not enough usable words to create "
                    "a word cloud for this selection."
                )

        with comments_col:
            st.markdown("### Common feedback words")
            word_data = build_feedback_counts(feedback)

            if not word_data.empty:
                fig = px.bar(
                    word_data.sort_values("Frequency"),
                    x="Frequency",
                    y="Word",
                    orientation="h",
                    text="Frequency",
                    color="Frequency",
                    color_continuous_scale="Purples",
                    labels={
                        "Word": "Word",
                        "Frequency": "Occurrences",
                    },
                )
                fig.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                )
                fig.update_layout(
                    coloraxis_showscale=False,
                    xaxis_title="Occurrences",
                    yaxis_title="",
                )
                make_chart(fig, 350)
            else:
                st.info("No frequent terms were found.")

        with st.expander(f"View written comments ({len(feedback):,})"):
            st.dataframe(
                feedback.rename("Feedback").to_frame(),
                use_container_width=True,
                hide_index=True,
            )

    # Insights and data quality
    st.divider()
    insight_col, quality_col = st.columns([3, 2], gap="large")

    with insight_col:
        st.markdown("## Key insights")
        for index, insight in enumerate(results["insights"], start=1):
            safe_insight = html.escape(str(insight))
            st.markdown(
                f"""
                <div class="insight-card">
                    <span class="insight-number">{index:02d}</span>
                    &nbsp;&nbsp;{safe_insight}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with quality_col:
        st.markdown("## Data quality")
        st.metric("Rows analyzed", f"{len(filtered):,}")

        missing_feedback = int(
            (
                filtered["Feedback"]
                .fillna("")
                .astype(str)
                .str.strip()
                == ""
            ).sum()
        )
        st.metric("Missing feedback", f"{missing_feedback:,}")

        with st.expander("View cleaning report"):
            st.json(quality_report)

    # Data preview and downloads
    st.divider()
    st.markdown("## Explore and export data")

    with st.expander("Preview filtered responses"):
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

    download_col1, download_col2 = st.columns(2)

    with download_col1:
        st.download_button(
            "⬇ Download filtered data",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="filtered_poll_responses.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with download_col2:
        summary = pd.DataFrame(
            {
                "Metric": [
                    "Total responses",
                    "Average satisfaction",
                    "Most popular tool",
                    "Positive ratings percentage",
                ],
                "Value": [
                    results["total_responses"],
                    results["average_satisfaction"],
                    results["top_tool"],
                    results["high_rating_percentage"],
                ],
            }
        )

        st.download_button(
            "⬇ Download summary",
            data=summary.to_csv(index=False).encode("utf-8"),
            file_name="poll_analysis_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Footer
    st.markdown("---")
    st.caption(
        "Poll Results Visualizer | AIpreneur Portfolio Project | "
        "Sample responses are synthetic demonstration data."
    )


if __name__ == "__main__":
    main()
