import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    page_title="Zurich Traffic Accident Dashboard",
    page_icon="🚦",
    layout="wide"
)


st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0B1020;
        color: #CBD5E1;
    }

    [data-testid="stHeader"] {
        background-color: #0B1020;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    [data-testid="stSidebar"] * {
        color: #CBD5E1;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        color: #F8FAFC;
    }

    p, li, label, span {
        color: #CBD5E1;
    }

    .intro-box {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 18px;
        padding: 18px 22px;
        margin-bottom: 20px;
    }

    .section-label {
        color: #edf19c;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }

    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 14px 16px;
    }

    div[role="radiogroup"] {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 10px 14px;
    }

    div[role="radiogroup"] label {
        background-color: #1E293B;
        border-radius: 999px;
        padding: 6px 10px;
        margin-right: 4px;
    }

    div[role="radiogroup"] label:has(input:checked) {
        background-color: #9A2F7A;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
    "staticPlot": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d",
        "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"
    ],
}

SPATIAL_CONFIG = {
    "displayModeBar": True,
    "scrollZoom": True,
    "doubleClick": "reset",
    "modeBarButtonsToRemove": ["select2d", "lasso2d"],
}


@st.cache_data
def load_data():
    data_path = (
        Path(__file__).resolve().parents[1]
        / "data_acquisition"
        / "Processed"
        / "traffic_accidents_zh_clean.csv"
    )
    return pd.read_csv(data_path)


def format_ch_number(value):
    if pd.isna(value):
        return ""
    return f"{float(value):,.0f}".replace(",", "’")


def clean_severity_label(label):
    label = str(label)
    label = label.replace("Accident with ", "")
    label = label.replace("accident with ", "")
    label = label.replace("property damage", "Property damage")
    label = label.replace("light injuries", "Light")
    label = label.replace("severe injuries", "Severe")
    label = label.replace("fatalities", "Fatal")
    return label.strip()


def clean_accident_type_label(label):
    label = str(label)

    replacements = [
        "Accident involving ",
        "accident involving ",
        "Accident with ",
        "accident with ",
        "Accident when ",
        "accident when ",
        "Other accident",
        "other accident",
    ]

    for text in replacements:
        label = label.replace(text, "")

    label = label.strip()

    if not label:
        return "Other"

    return label[:1].upper() + label[1:]


def apply_dark_layout(fig, height=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B1020",
        plot_bgcolor="#0B1020",
        font=dict(color="#CBD5E1"),
        hoverlabel=dict(
            bgcolor="#111827",
            bordercolor="#334155",
            font=dict(color="#F8FAFC")
        ),
        dragmode=False,
        margin=dict(l=70, r=35, t=30, b=70)
    )

    if height:
        fig.update_layout(height=height)

    return fig


df = load_data()


st.markdown('<div class="section-label">Interactive dashboard</div>', unsafe_allow_html=True)
st.title("Traffic Accident Patterns in the Canton of Zurich")
st.markdown(
    """
    <div class="intro-box">
    Explore police-recorded traffic accidents by time, accident type, road user involvement,
    severity and location. Use the filters on the left to focus the dashboard on specific
    years, road types, severities or participant groups.
    </div>
    """,
    unsafe_allow_html=True
)


st.sidebar.header("Filters")

year_min = int(df["AccidentYear"].min())
year_max = int(df["AccidentYear"].max())

selected_years = st.sidebar.slider(
    "Year range",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max)
)

severity_options_original = sorted(df["AccidentSeverityCategory_en"].dropna().unique())
severity_label_map = {
    clean_severity_label(value): value
    for value in severity_options_original
}

selected_severity_clean = st.sidebar.multiselect(
    "Severity category",
    options=list(severity_label_map.keys()),
    default=list(severity_label_map.keys())
)

selected_severity = [
    severity_label_map[label]
    for label in selected_severity_clean
]

road_options = sorted(df["RoadType_en"].dropna().unique())

selected_roads = st.sidebar.multiselect(
    "Road type",
    options=road_options,
    default=road_options
)

type_options_original = sorted(df["AccidentType_en"].dropna().unique())
type_label_map = {
    clean_accident_type_label(value): value
    for value in type_options_original
}

selected_types_clean = st.sidebar.multiselect(
    "Accident type",
    options=list(type_label_map.keys()),
    default=list(type_label_map.keys())
)

selected_types = [
    type_label_map[label]
    for label in selected_types_clean
]

participant_filter = st.sidebar.selectbox(
    "Vulnerable road user involvement",
    [
        "All accidents",
        "Pedestrian involved",
        "Bicycle involved",
        "Motorcycle involved"
    ]
)


filtered_df = df[
    (df["AccidentYear"].between(selected_years[0], selected_years[1])) &
    (df["AccidentSeverityCategory_en"].isin(selected_severity)) &
    (df["RoadType_en"].isin(selected_roads)) &
    (df["AccidentType_en"].isin(selected_types))
].copy()

if participant_filter == "Pedestrian involved":
    filtered_df = filtered_df[filtered_df["AccidentInvolvingPedestrian"] == True]
elif participant_filter == "Bicycle involved":
    filtered_df = filtered_df[filtered_df["AccidentInvolvingBicycle"] == True]
elif participant_filter == "Motorcycle involved":
    filtered_df = filtered_df[filtered_df["AccidentInvolvingMotorcycle"] == True]

if filtered_df.empty:
    st.warning("No data available for the current filter selection.")
    st.stop()


fatal_count = filtered_df[
    filtered_df["AccidentSeverityCategory_en"].str.contains("fatal", case=False, na=False)
].shape[0]

severe_count = filtered_df[
    filtered_df["AccidentSeverityCategory_en"].str.contains("severe", case=False, na=False)
].shape[0]

top_road = filtered_df["RoadType_en"].value_counts().idxmax()
top_type = filtered_df["AccidentType_en"].value_counts().idxmax()

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Selected accidents", format_ch_number(len(filtered_df)))

with k2:
    st.metric("Fatal accidents", format_ch_number(fatal_count))

with k3:
    st.metric("Severe injury accidents", format_ch_number(severe_count))

with k4:
    st.metric("Most common road type", top_road)

st.caption(f"Most common accident type in the current selection: {top_type}")


st.markdown('<div class="section-label">01 · Scale over time</div>', unsafe_allow_html=True)
st.subheader("Accident trend over time")
st.markdown("Yearly totals show the long-term development. The monthly view highlights seasonal variation within a selected year.")

yearly_counts = (
    filtered_df
    .groupby("AccidentYear")
    .size()
    .reset_index(name="Accidents")
    .sort_values("AccidentYear")
)

yearly_counts["Accidents_label"] = yearly_counts["Accidents"].apply(format_ch_number)

fig_year = go.Figure()

fig_year.add_trace(
    go.Scatter(
        x=yearly_counts["AccidentYear"],
        y=yearly_counts["Accidents"],
        customdata=yearly_counts["Accidents_label"],
        mode="lines+markers",
        line=dict(color="#F28A63", width=3),
        marker=dict(
            size=10,
            color="#F28A63",
            line=dict(width=1.2, color="#FFD9C7")
        ),
        hovertemplate=(
            "<b>Accidents: %{customdata}</b><br>"
            "Year: %{x}"
            "<extra></extra>"
        )
    )
)

fig_year.update_layout(
    xaxis_title="Year",
    yaxis_title="Number of accidents",
    hovermode="closest",
    showlegend=False,
    yaxis=dict(
        tickformat=",",
        gridcolor="#1E293B",
        fixedrange=True
    ),
    xaxis=dict(
        dtick=1,
        fixedrange=True,
        showspikes=False
    )
)

fig_year = apply_dark_layout(fig_year, height=440)

st.plotly_chart(
    fig_year,
    use_container_width=True,
    config=PLOTLY_CONFIG
)

available_years = yearly_counts["AccidentYear"].astype(int).tolist()

if "monthly_drilldown_year" not in st.session_state:
    st.session_state.monthly_drilldown_year = available_years[-1]

if st.session_state.monthly_drilldown_year not in available_years:
    st.session_state.monthly_drilldown_year = available_years[-1]

selected_year = st.session_state.monthly_drilldown_year

month_order = list(range(1, 13))
month_names = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}

selected_year_df = filtered_df[
    filtered_df["AccidentYear"] == selected_year
].copy()

monthly_counts = (
    selected_year_df
    .groupby("AccidentMonth")
    .size()
    .reindex(month_order, fill_value=0)
    .reset_index(name="Accidents")
)

monthly_counts["Month"] = monthly_counts["AccidentMonth"].map(month_names)
monthly_counts["Accidents_label"] = monthly_counts["Accidents"].apply(format_ch_number)

st.markdown('<div class="section-label">Monthly drill-down</div>', unsafe_allow_html=True)
st.subheader(f"Monthly breakdown — {selected_year}")

fig_month = go.Figure()

fig_month.add_trace(
    go.Scatter(
        x=monthly_counts["Month"],
        y=monthly_counts["Accidents"],
        customdata=monthly_counts["Accidents_label"],
        mode="lines+markers",
        line=dict(color="#9A2F7A", width=3),
        marker=dict(
            size=9,
            color="#9A2F7A",
            line=dict(width=1.1, color="#F9A8D4")
        ),
        hovertemplate=(
            "<b>Accidents: %{customdata}</b><br>"
            "Month: %{x}"
            "<extra></extra>"
        )
    )
)

fig_month.update_layout(
    xaxis_title="Month",
    yaxis_title="Number of accidents",
    hovermode="closest",
    showlegend=False,
    yaxis=dict(
        tickformat=",",
        gridcolor="#1E293B",
        fixedrange=True
    ),
    xaxis=dict(
        fixedrange=True,
        showspikes=False
    )
)

fig_month = apply_dark_layout(fig_month, height=340)

st.plotly_chart(
    fig_month,
    use_container_width=True,
    config=PLOTLY_CONFIG
)

st.markdown('<div class="section-label">Select year for monthly drill-down</div>', unsafe_allow_html=True)

selected_year_new = st.radio(
    "Select year for monthly drill-down",
    options=available_years,
    index=available_years.index(selected_year),
    horizontal=True,
    label_visibility="collapsed"
)

if selected_year_new != st.session_state.monthly_drilldown_year:
    st.session_state.monthly_drilldown_year = selected_year_new
    st.rerun()


st.markdown('<div class="section-label">02 · When do accidents peak?</div>', unsafe_allow_html=True)
st.subheader("Accidents by weekday and hour")
st.markdown("The heatmap shows recurring time windows with higher accident frequency.")

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

weekday_hour = filtered_df.pivot_table(
    index="AccidentWeekDay_en",
    columns="AccidentHour",
    values="AccidentUID",
    aggfunc="count"
).fillna(0)

weekday_hour = weekday_hour.reindex(weekday_order)
weekday_hour = weekday_hour.reindex(columns=range(24), fill_value=0)

heatmap_hover = np.empty(weekday_hour.shape, dtype=object)

for i in range(weekday_hour.shape[0]):
    for j in range(weekday_hour.shape[1]):
        heatmap_hover[i, j] = format_ch_number(weekday_hour.iloc[i, j])

fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=weekday_hour.values,
        x=list(weekday_hour.columns),
        y=list(weekday_hour.index),
        customdata=heatmap_hover,
        colorscale="Viridis",
        hovertemplate=(
            "<b>Accidents: %{customdata}</b><br>"
            "Weekday: %{y}<br>"
            "Hour: %{x}:00<extra></extra>"
        ),
        colorbar=dict(title="Accidents")
    )
)

fig_heatmap.update_layout(
    xaxis=dict(title="Hour of day", dtick=1, fixedrange=True),
    yaxis=dict(title="Weekday", fixedrange=True),
    margin=dict(l=90, r=40, t=30, b=70)
)

fig_heatmap = apply_dark_layout(fig_heatmap, height=520)

st.plotly_chart(
    fig_heatmap,
    use_container_width=True,
    config=PLOTLY_CONFIG
)


st.markdown('<div class="section-label">03 · What happens most often?</div>', unsafe_allow_html=True)
st.subheader("Vulnerable road users and accident types")
st.markdown("The first view shows vulnerable road user involvement. The second breaks frequent accident types down by road user group.")

col_vulnerable, col_types = st.columns([0.75, 1.75])

vulnerable_colors = {
    "Pedestrian": "#EAD7A1",
    "Bicycle": "#6D28D9",
    "Motorcycle": "#DB2777"
}

with col_vulnerable:
    st.markdown("#### Vulnerable road users")

    vulnerable_counts = pd.DataFrame({
        "Participant group": [
            "Pedestrian",
            "Bicycle",
            "Motorcycle"
        ],
        "Accidents": [
            int(filtered_df["AccidentInvolvingPedestrian"].sum()),
            int(filtered_df["AccidentInvolvingBicycle"].sum()),
            int(filtered_df["AccidentInvolvingMotorcycle"].sum())
        ]
    })

    vulnerable_counts["Accidents_label"] = vulnerable_counts["Accidents"].apply(format_ch_number)

    fig_vulnerable = px.bar(
        vulnerable_counts,
        x="Participant group",
        y="Accidents",
        template="plotly_dark",
        color="Participant group",
        color_discrete_map=vulnerable_colors,
        text="Accidents_label"
    )

    fig_vulnerable.update_traces(
        textposition="outside",
        hoverinfo="skip",
        hovertemplate=None
    )

    fig_vulnerable.update_layout(
        xaxis=dict(title="", fixedrange=True),
        yaxis=dict(
            title="Number of accidents",
            tickformat=",",
            gridcolor="#1E293B",
            fixedrange=True
        ),
        showlegend=False,
        margin=dict(l=60, r=20, t=25, b=60)
    )

    fig_vulnerable = apply_dark_layout(fig_vulnerable, height=470)

    st.plotly_chart(
        fig_vulnerable,
        use_container_width=True,
        config=PLOTLY_CONFIG
    )

with col_types:
    st.markdown("#### Accident types by vulnerable road user")

    vulnerable_type_frames = []

    vulnerable_mapping = {
        "Pedestrian": "AccidentInvolvingPedestrian",
        "Bicycle": "AccidentInvolvingBicycle",
        "Motorcycle": "AccidentInvolvingMotorcycle"
    }

    for group_name, column_name in vulnerable_mapping.items():
        temp = filtered_df[filtered_df[column_name] == True].copy()
        temp["Participant group"] = group_name
        vulnerable_type_frames.append(temp)

    vulnerable_type_long = pd.concat(vulnerable_type_frames, ignore_index=True)

    top_types = (
        vulnerable_type_long["AccidentType_en"]
        .value_counts()
        .head(8)
        .index
        .tolist()
    )

    vulnerable_type_long = vulnerable_type_long[
        vulnerable_type_long["AccidentType_en"].isin(top_types)
    ].copy()

    vulnerable_type_counts = (
        vulnerable_type_long
        .groupby(["AccidentType_en", "Participant group"])
        .size()
        .reset_index(name="Accidents")
    )

    type_totals = (
        vulnerable_type_counts
        .groupby("AccidentType_en")["Accidents"]
        .sum()
        .reset_index(name="Type total")
    )

    vulnerable_type_counts = vulnerable_type_counts.merge(
        type_totals,
        on="AccidentType_en",
        how="left"
    )

    vulnerable_type_counts["Share"] = (
        vulnerable_type_counts["Accidents"]
        / vulnerable_type_counts["Type total"]
        * 100
    )

    vulnerable_type_counts["Accidents_label"] = vulnerable_type_counts["Accidents"].apply(format_ch_number)

    fig_types = px.bar(
        vulnerable_type_counts,
        x="Accidents",
        y="AccidentType_en",
        color="Participant group",
        orientation="h",
        template="plotly_dark",
        color_discrete_map=vulnerable_colors,
        category_orders={
            "AccidentType_en": top_types,
            "Participant group": ["Pedestrian", "Bicycle", "Motorcycle"]
        },
        custom_data=["Participant group", "Share", "Accidents_label"]
    )

    fig_types.update_layout(
        barmode="stack",
        yaxis=dict(
            autorange="reversed",
            title="",
            fixedrange=True
        ),
        xaxis=dict(
            title="Number of accidents",
            tickformat=",",
            gridcolor="#1E293B",
            fixedrange=True
        ),
        legend=dict(
            title="Road user group",
            orientation="h",
            yanchor="bottom",
            y=-0.32,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=210, r=20, t=25, b=140)
    )

    fig_types.update_traces(
        hovertemplate=(
            "<b>Accidents: %{customdata[2]}</b><br>"
            "%{customdata[0]}<br>"
            "Share: %{customdata[1]:.1f}%"
            "<extra></extra>"
        )
    )

    fig_types = apply_dark_layout(fig_types, height=470)

    st.plotly_chart(
        fig_types,
        use_container_width=True,
        config=PLOTLY_CONFIG
    )


st.markdown('<div class="section-label">04 · How severe are accidents by road type?</div>', unsafe_allow_html=True)
st.subheader("Accident severity by road type")
st.markdown("The stacked bars compare total accident volume and severity mix across road types.")

road_severity_abs = pd.crosstab(
    filtered_df["RoadType_en"],
    filtered_df["AccidentSeverityCategory_en"]
)

if not road_severity_abs.empty:
    road_severity_abs = road_severity_abs.loc[
        road_severity_abs.sum(axis=1).sort_values(ascending=False).index
    ]

    severity_order = road_severity_abs.sum(axis=0).sort_values(ascending=False).index.tolist()
    road_severity_abs = road_severity_abs[severity_order]

    road_totals = road_severity_abs.sum(axis=1)

    road_severity_share = road_severity_abs.div(
        road_totals,
        axis=0
    ) * 100

    severity_colors = {
        "Accident with property damage": "#450b65",
        "Accident with light injuries": "#922760",
        "Accident with severe injuries": "#eb8709",
        "Accident with fatalities": "#edf19c"
    }

    abs_long = (
        road_severity_abs
        .reset_index()
        .melt(
            id_vars="RoadType_en",
            var_name="Severity category",
            value_name="Accidents"
        )
    )

    share_long = (
        road_severity_share
        .reset_index()
        .melt(
            id_vars="RoadType_en",
            var_name="Severity category",
            value_name="Share"
        )
    )

    severity_long = abs_long.merge(
        share_long,
        on=["RoadType_en", "Severity category"],
        how="left"
    )

    severity_long["Accidents_label"] = severity_long["Accidents"].apply(format_ch_number)

    fig_severity = px.bar(
        severity_long,
        x="RoadType_en",
        y="Accidents",
        color="Severity category",
        color_discrete_map=severity_colors,
        template="plotly_dark",
        custom_data=["Share", "Accidents_label"]
    )

    fig_severity.update_layout(
        barmode="stack",
        xaxis=dict(title="", fixedrange=True),
        yaxis=dict(
            title="Number of accidents",
            tickformat=",",
            gridcolor="#1E293B",
            fixedrange=True
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.32,
            xanchor="center",
            x=0.5,
            title="Severity category"
        ),
        margin=dict(l=70, r=40, t=30, b=150)
    )

    fig_severity.update_traces(
        hovertemplate=(
            "<b>Accidents: %{customdata[1]}</b><br>"
            "Share: %{customdata[0]:.1f}%<br>"
            "%{fullData.name}"
            "<extra></extra>"
        )
    )

    fig_severity = apply_dark_layout(fig_severity, height=560)

    st.plotly_chart(
        fig_severity,
        use_container_width=True,
        config=PLOTLY_CONFIG
    )

st.markdown('<div class="section-label">05 · Where do accidents concentrate?</div>', unsafe_allow_html=True)
st.subheader("Spatial accident hotspots")
st.markdown(
    "The hotspot view aggregates accident coordinates into spatial density cells. "
    "Zooming is enabled for this map-like view."
)

hotspot_focus_options = [
    "All accidents",
    "Severe injuries",
    "Fatal accidents",
    "Pedestrian involved",
    "Bicycle involved",
    "Motorcycle involved"
]

selected_hotspot_focus = st.multiselect(
    "Hotspot focus",
    options=hotspot_focus_options,
    default=["All accidents"]
)

if not selected_hotspot_focus:
    selected_hotspot_focus = ["All accidents"]

if "All accidents" in selected_hotspot_focus and len(selected_hotspot_focus) > 1:
    selected_hotspot_focus = [
        focus for focus in selected_hotspot_focus
        if focus != "All accidents"
    ]

focus_frames = []

for focus in selected_hotspot_focus:
    focus_df = filtered_df.copy()

    if focus == "Severe injuries":
        focus_df = focus_df[
            focus_df["AccidentSeverityCategory_en"].str.contains("severe", case=False, na=False)
        ]
    elif focus == "Fatal accidents":
        focus_df = focus_df[
            focus_df["AccidentSeverityCategory_en"].str.contains("fatal", case=False, na=False)
        ]
    elif focus == "Pedestrian involved":
        focus_df = focus_df[
            focus_df["AccidentInvolvingPedestrian"] == True
        ]
    elif focus == "Bicycle involved":
        focus_df = focus_df[
            focus_df["AccidentInvolvingBicycle"] == True
        ]
    elif focus == "Motorcycle involved":
        focus_df = focus_df[
            focus_df["AccidentInvolvingMotorcycle"] == True
        ]

    focus_df = focus_df[
        ["AccidentLocation_CHLV95_E", "AccidentLocation_CHLV95_N"]
    ].dropna().copy()

    focus_df["Focus"] = focus
    focus_frames.append(focus_df)

if not focus_frames:
    st.info("No accident locations available for the selected hotspot focus.")
else:
    hotspot_source = pd.concat(focus_frames, ignore_index=True)

    if hotspot_source.empty:
        st.info("No accident locations available for the selected hotspot focus.")
    else:
        grid_size = 220

        x_min = hotspot_source["AccidentLocation_CHLV95_E"].min()
        x_max = hotspot_source["AccidentLocation_CHLV95_E"].max()
        y_min = hotspot_source["AccidentLocation_CHLV95_N"].min()
        y_max = hotspot_source["AccidentLocation_CHLV95_N"].max()

        if x_min == x_max:
            x_min -= 1
            x_max += 1

        if y_min == y_max:
            y_min -= 1
            y_max += 1

        hotspot_source["x_bin"] = pd.cut(
            hotspot_source["AccidentLocation_CHLV95_E"],
            bins=grid_size,
            labels=False
        )

        hotspot_source["y_bin"] = pd.cut(
            hotspot_source["AccidentLocation_CHLV95_N"],
            bins=grid_size,
            labels=False
        )

        cell_counts = (
            hotspot_source
            .dropna(subset=["x_bin", "y_bin"])
            .groupby(["Focus", "x_bin", "y_bin"])
            .size()
            .reset_index(name="Accidents")
        )

        cell_counts["x"] = (
            x_min
            + (cell_counts["x_bin"] + 0.5)
            * (x_max - x_min)
            / grid_size
        )

        cell_counts["y"] = (
            y_min
            + (cell_counts["y_bin"] + 0.5)
            * (y_max - y_min)
            / grid_size
        )

        cell_counts["Accidents_log"] = np.log10(cell_counts["Accidents"] + 1)
        cell_counts["Accidents_label"] = cell_counts["Accidents"].apply(format_ch_number)

        # Coordinate labels for tooltip
        cell_counts["East_label"] = (
            cell_counts["x"]
            .round(0)
            .astype(int)
            .apply(format_ch_number)
        )

        cell_counts["North_label"] = (
            cell_counts["y"]
            .round(0)
            .astype(int)
            .apply(format_ch_number)
        )

        hotspot_colorscale = [
            [0.00, "#140D2D"],
            [0.15, "#2B105C"],
            [0.35, "#5B1A82"],
            [0.55, "#9A2F7A"],
            [0.72, "#E45A3A"],
            [0.88, "#FFB000"],
            [1.00, "#FFF59D"],
        ]

        fig_hotspot = go.Figure()

        for focus in selected_hotspot_focus:
            focus_cells = cell_counts[cell_counts["Focus"] == focus].copy()

            if focus_cells.empty:
                continue

            fig_hotspot.add_trace(
                go.Scattergl(
                    x=focus_cells["x"],
                    y=focus_cells["y"],
                    mode="markers",
                    name=focus,
                    marker=dict(
                        size=4,
                        color=focus_cells["Accidents_log"],
                        colorscale=hotspot_colorscale,
                        opacity=0.82,
                        showscale=(focus == selected_hotspot_focus[0]),
                        colorbar=dict(
                            title="Accident density",
                            tickvals=[
                                np.log10(2),
                                np.log10(11),
                                np.log10(101),
                                np.log10(1001)
                            ],
                            ticktext=["1", "10", "100", "1’000"]
                        ),
                        line=dict(width=0)
                    ),
                    customdata=np.stack(
                        [
                            focus_cells["Accidents_label"],
                            focus_cells["Focus"],
                            focus_cells["East_label"],
                            focus_cells["North_label"]
                        ],
                        axis=-1
                    ),
                    hovertemplate=(
                        "<b>Accidents: %{customdata[0]}</b><br>"
                        "Focus: %{customdata[1]}<br>"
                        "East coordinate: %{customdata[2]}<br>"
                        "North coordinate: %{customdata[3]}"
                        "<extra></extra>"
                    )
                )
            )

        fig_hotspot.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0B1020",
            plot_bgcolor="#0B1020",
            font=dict(color="#CBD5E1"),
            hoverlabel=dict(
                bgcolor="#111827",
                bordercolor="#334155",
                font=dict(color="#F8FAFC")
            ),
            xaxis=dict(
                title="East coordinate CHLV95",
                showgrid=False,
                zeroline=False,
                fixedrange=False
            ),
            yaxis=dict(
                title="North coordinate CHLV95",
                showgrid=False,
                zeroline=False,
                scaleanchor="x",
                scaleratio=1,
                fixedrange=False
            ),
            legend=dict(
                title="Selected focus",
                orientation="h",
                yanchor="bottom",
                y=-0.18,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=70, r=30, t=30, b=110),
            height=760,
            dragmode="zoom"
        )

        st.plotly_chart(
            fig_hotspot,
            use_container_width=True,
            config=SPATIAL_CONFIG
        )
