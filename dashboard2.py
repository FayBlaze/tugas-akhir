import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# PAGE CONFIG  (must be first Streamlit call)
st.set_page_config(
    page_title="Power BI",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CONSTANTS / HELPERS
PALETTE      = ["#38bdf8", "#818cf8", "#34d399", "#fb923c", "#f472b6", "#facc15", "#a78bfa"]
PAPER_BG     = "#0c1220"
PLOT_BG      = "#131f35"
GRID_COLOR   = "#1e3050"
FONT_COLOR   = "#cbd5e1"

MONTH_ORDER  = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]

def apply_theme(fig, height: int = 400, rotate_x: int = 0, show_legend: bool = True) -> go.Figure:
    """Apply dark-mode theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        height=height,
        font=dict(color=FONT_COLOR, family="Inter, Segoe UI, sans-serif", size=12),
        title_font=dict(color="#38bdf8", size=14, family="Inter, Segoe UI, sans-serif"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
        ) if show_legend else dict(visible=False),
        margin=dict(l=44, r=20, t=52, b=44),
    )
    fig.update_xaxes(
        gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
        tickangle=rotate_x, tickfont_color=FONT_COLOR
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
        tickfont_color=FONT_COLOR
    )
    return fig

def divider():
    st.divider()

def section(title: str, icon: str = ""):
    st.subheader(f"{icon} {title}")

# ─────────────────────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading and processing data …")
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv("hotel_bookings.csv")
    except FileNotFoundError:
        st.error(
            "❌ **hotel_bookings.csv not found.**  \n"
            "Place the dataset in the same directory as `app.py` and restart."
        )
        st.stop()

    month_num = {m: str(i).zfill(2) for i, m in enumerate(MONTH_ORDER, 1)}
    df["arrival_date_month_num"] = df["arrival_date_month"].map(month_num)
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date_year"].astype(str) + "-"
        + df["arrival_date_month_num"] + "-"
        + df["arrival_date_day_of_month"].astype(str).str.zfill(2),
        errors="coerce",
    )

    df["total_nights"] = df["stays_in_week_nights"] + df["stays_in_weekend_nights"]
    df["Revenue"] = df["adr"] * df["total_nights"]

    df = df.dropna(subset=["arrival_date"])
    df["children"]  = df["children"].fillna(0).astype(int)
    df["country"]   = df["country"].fillna("Unknown")
    df["agent"]     = df["agent"].fillna(0)
    df["company"]   = df["company"].fillna(0)

    df = df[df["total_nights"] > 0].copy()

    df["YearMonth"] = df["arrival_date"].dt.to_period("M").dt.to_timestamp()
    df["Month"]     = df["arrival_date"].dt.strftime("%b")
    df["Year"]      = df["arrival_date_year"].astype(str)

    return df.reset_index(drop=True)


df_raw = load_data()

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏨 Hotel BI")
    st.caption("Business Intelligence Dashboard")
    st.divider()

    st.markdown("#### 🔍 Filters")

    hotels    = ["All"] + sorted(df_raw["hotel"].unique().tolist())
    sel_hotel = st.selectbox("🏩 Hotel Type", hotels)

    years    = ["All"] + sorted(df_raw["arrival_date_year"].unique().tolist())
    sel_year = st.selectbox("📅 Arrival Year", years)

    segments  = ["All"] + sorted(df_raw["market_segment"].unique().tolist())
    sel_seg   = st.selectbox("🎯 Market Segment", segments)

    st.divider()

    df = df_raw.copy()
    if sel_hotel != "All": df = df[df["hotel"] == sel_hotel]
    if sel_year  != "All": df = df[df["arrival_date_year"] == int(sel_year)]
    if sel_seg   != "All": df = df[df["market_segment"] == sel_seg]

    st.markdown("#### 📊 Filtered Data")
    st.metric("Records", f"{len(df):,}")
    if len(df):
        st.metric("Date range",
                  f"{df['arrival_date'].min().strftime('%b %Y')} → "
                  f"{df['arrival_date'].max().strftime('%b %Y')}")
    st.divider()
    st.caption("Dataset · Hotel Booking Demand\nSource · Kaggle")

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.title("🏨 Hotel Booking Intelligence")
st.caption("Business Intelligence Dashboard — Hotel Booking Demand Dataset")

active = []
if sel_hotel != "All": active.append(f"Hotel: {sel_hotel}")
if sel_year  != "All": active.append(f"Year: {sel_year}")
if sel_seg   != "All": active.append(f"Segment: {sel_seg}")
if active:
    st.info("🔍 Active Filters: " + " | ".join(active))

divider()

if len(df) == 0:
    st.warning("⚠️ No data matches the selected filters. Adjust the sidebar filters to continue.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# SECTION 1 — EXECUTIVE SUMMARY
# ─────────────────────────────────────────────────────────────
section("Executive Summary", "📋")

total_bookings  = len(df)
confirmed       = int((df["is_canceled"] == 0).sum())
total_revenue   = df["Revenue"].sum()
avg_adr         = df["adr"].mean()
cancel_rate     = df["is_canceled"].mean() * 100
avg_rev_booking = df.loc[df["is_canceled"] == 0, "Revenue"].mean()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("📊 Total Bookings", f"{total_bookings:,}",
              delta=f"{confirmed:,} confirmed")
with c2:
    st.metric("💰 Total Revenue", f"${total_revenue:,.0f}",
              delta=f"Avg ${avg_rev_booking:,.0f} / booking")
with c3:
    st.metric("💵 Average ADR", f"${avg_adr:.2f}",
              delta=f"Max ${df['adr'].max():.2f}")
with c4:
    st.metric("❌ Cancellation Rate", f"{cancel_rate:.1f}%",
              delta=f"{df['is_canceled'].sum():,} cancellations",
              delta_color="inverse")

divider()

# ─────────────────────────────────────────────────────────────
# SECTION 2 — CUSTOMER ANALYSIS
# ─────────────────────────────────────────────────────────────
section("Customer Analysis", "👥")

tab_c1, tab_c2, tab_c3 = st.tabs(["🌍 By Country", "📋 Customer Type", "🔁 Repeat Guests"])

with tab_c1:
    top_countries = (
        df.groupby("country").size()
        .reset_index(name="Bookings")
        .sort_values("Bookings", ascending=False)
        .head(10)
    )

    col_a, col_b = st.columns([3, 2])
    with col_a:
        fig = px.bar(
            top_countries, x="country", y="Bookings",
            title="Top 10 Countries by Booking Volume",
            color="Bookings",
            color_continuous_scale=["#1e3a5f", "#38bdf8"],
            text="Bookings",
        )
        fig.update_traces(textposition="outside", textfont_color=FONT_COLOR)
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(apply_theme(fig, show_legend=False), use_container_width=True)

    with col_b:
        fig2 = px.pie(
            top_countries, values="Bookings", names="country",
            title="Country Share — Top 10",
            color_discrete_sequence=PALETTE, hole=0.45,
        )
        fig2.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(apply_theme(fig2, show_legend=True), use_container_width=True)

with tab_c2:
    ct_size = df.groupby("customer_type").size().reset_index(name="Count")
    ct_agg  = df.groupby("customer_type").agg(
        Total=("is_canceled", "count"),
        Canceled=("is_canceled", "sum"),
    ).reset_index()
    ct_agg["Confirmed"]   = ct_agg["Total"] - ct_agg["Canceled"]
    ct_agg["Cancel_Rate"] = (ct_agg["Canceled"] / ct_agg["Total"] * 100).round(1)

    col_a, col_b = st.columns([2, 3])
    with col_a:
        fig = px.pie(
            ct_size, values="Count", names="customer_type",
            title="Customer Type Distribution",
            color_discrete_sequence=PALETTE, hole=0.5,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    with col_b:
        fig = px.bar(
            ct_agg, x="customer_type", y=["Confirmed", "Canceled"],
            title="Confirmed vs Canceled by Customer Type",
            color_discrete_sequence=["#34d399", "#f87171"],
            barmode="stack", text_auto=True,
        )
        fig.update_traces(textfont_color=FONT_COLOR)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    st.markdown("##### Cancel Rate by Customer Type")
    disp = ct_agg[["customer_type", "Total", "Confirmed", "Canceled", "Cancel_Rate"]].rename(
        columns={"customer_type": "Type", "Cancel_Rate": "Cancel Rate (%)"}
    )
    st.dataframe(disp.style.format({"Cancel Rate (%)": "{:.1f}%"}), use_container_width=True, hide_index=True)

with tab_c3:
    rg = df.groupby("is_repeated_guest").agg(
        Count=("is_repeated_guest", "count"),
        Revenue=("Revenue", "mean"),
        ADR=("adr", "mean"),
        CancelRate=("is_canceled", "mean"),
    ).reset_index()
    rg["Guest Type"] = rg["is_repeated_guest"].map({0: "New Guest", 1: "Repeat Guest"})
    rg["CancelRate"] = (rg["CancelRate"] * 100).round(1)

    col_a, col_b = st.columns([2, 3])
    with col_a:
        fig = px.pie(
            rg, values="Count", names="Guest Type",
            title="New vs Repeat Guests",
            color_discrete_sequence=["#38bdf8", "#818cf8"], hole=0.5,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    with col_b:
        fig = px.bar(
            rg, x="Guest Type", y=["Revenue", "ADR"],
            title="Avg Revenue & ADR: New vs Repeat Guests",
            color_discrete_sequence=["#38bdf8", "#818cf8"],
            barmode="group", text_auto=".2f",
        )
        fig.update_traces(textfont_color=FONT_COLOR)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    repeat_pct = df["is_repeated_guest"].mean() * 100
    new_cr     = df.loc[df["is_repeated_guest"] == 0, "is_canceled"].mean() * 100
    rep_cr     = df.loc[df["is_repeated_guest"] == 1, "is_canceled"].mean() * 100
    st.info(
        f"🔁 Repeat guests account for **{repeat_pct:.1f}%** of total bookings.  \n"
        f"Their cancellation rate is **{rep_cr:.1f}%** vs **{new_cr:.1f}%** for new guests — "
        f"a **{new_cr - rep_cr:.1f} pp** lower risk, underscoring the value of loyalty investment."
    )

divider()

# ─────────────────────────────────────────────────────────────
# SECTION 3 — REVENUE ANALYSIS
# ─────────────────────────────────────────────────────────────
section("Revenue Analysis", "💰")

rev_hotel = df.groupby("hotel").agg(
    Revenue=("Revenue", "sum"),
    AvgADR=("adr", "mean"),
).reset_index().sort_values("Revenue", ascending=False)

rev_seg = (
    df.groupby("market_segment")["Revenue"].sum()
    .reset_index().sort_values("Revenue", ascending=False)
)

col_a, col_b = st.columns(2)
with col_a:
    fig = px.bar(
        rev_hotel, x="hotel", y="Revenue",
        title="Total Revenue by Hotel Type",
        color="hotel", color_discrete_sequence=PALETTE,
        text="Revenue",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside",
                      textfont_color=FONT_COLOR)
    st.plotly_chart(apply_theme(fig, show_legend=False), use_container_width=True)

with col_b:
    fig = px.bar(
        rev_seg, x="market_segment", y="Revenue",
        title="Revenue by Market Segment",
        color="Revenue",
        color_continuous_scale=["#1e3a5f", "#38bdf8"],
        text="Revenue",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside",
                      textfont_color=FONT_COLOR)
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(apply_theme(fig, rotate_x=-30, show_legend=False), use_container_width=True)

rev_trend = (
    df.groupby("YearMonth").agg(
        Revenue=("Revenue", "sum"),
        Bookings=("hotel", "count"),
        AvgADR=("adr", "mean"),
    ).reset_index().sort_values("YearMonth")
)
rev_trend["YearMonth_str"] = rev_trend["YearMonth"].dt.strftime("%Y-%m")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=rev_trend["YearMonth_str"], y=rev_trend["Revenue"],
    mode="lines+markers", name="Revenue",
    line=dict(color="#38bdf8", width=2.5),
    marker=dict(size=6, color="#38bdf8"),
    fill="tozeroy", fillcolor="rgba(56,189,248,0.08)",
))
fig.add_trace(go.Scatter(
    x=rev_trend["YearMonth_str"], y=rev_trend["AvgADR"],
    mode="lines+markers", name="Avg ADR",
    line=dict(color="#818cf8", width=2, dash="dash"),
    marker=dict(size=5, color="#818cf8"),
    yaxis="y2",
))
fig.update_layout(
    title="Monthly Revenue Trend with Avg ADR Overlay",
    yaxis=dict(title="Revenue ($)", gridcolor=GRID_COLOR),
    yaxis2=dict(
        title="Avg ADR ($)", overlaying="y", side="right",
        color="#818cf8", gridcolor="rgba(0,0,0,0)"
    ),
    hovermode="x unified",
)
st.plotly_chart(apply_theme(fig, height=440, rotate_x=-45), use_container_width=True)

divider()

# ─────────────────────────────────────────────────────────────
# SECTION 4 — CANCELLATION ANALYSIS
# ─────────────────────────────────────────────────────────────
section("Cancellation Analysis", "❌")

tab_x1, tab_x2, tab_x3 = st.tabs(["🏩 By Hotel", "⏱️ Lead Time", "🎯 By Segment"])

with tab_x1:
    cancel_hotel = df.groupby("hotel").agg(
        Total=("is_canceled", "count"),
        Canceled=("is_canceled", "sum"),
    ).reset_index()
    cancel_hotel["Confirmed"]   = cancel_hotel["Total"] - cancel_hotel["Canceled"]
    cancel_hotel["Cancel_Rate"] = (cancel_hotel["Canceled"] / cancel_hotel["Total"] * 100).round(1)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            cancel_hotel, x="hotel", y="Cancel_Rate",
            title="Cancellation Rate by Hotel (%)",
            color="Cancel_Rate",
            color_continuous_scale=["#34d399", "#f87171"],
            text="Cancel_Rate",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                          textfont_color=FONT_COLOR)
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(apply_theme(fig, show_legend=False), use_container_width=True)

    with col_b:
        fig = px.bar(
            cancel_hotel, x="hotel", y=["Confirmed", "Canceled"],
            title="Confirmed vs Canceled by Hotel",
            color_discrete_sequence=["#34d399", "#f87171"],
            barmode="group", text_auto=True,
        )
        fig.update_traces(textfont_color=FONT_COLOR)
        st.plotly_chart(apply_theme(fig), use_container_width=True)

with tab_x2:
    df_lt = df.copy()
    df_lt["LT Bucket"] = pd.cut(
        df_lt["lead_time"],
        bins=[0, 30, 60, 90, 180, 365, 9999],
        labels=["0–30", "31–60", "61–90", "91–180", "181–365", "365+"],
    )
    lt_agg = df_lt.groupby("LT Bucket").agg(
        Total=("is_canceled", "count"),
        Canceled=("is_canceled", "sum"),
    ).reset_index()
    lt_agg["Cancel_Rate"] = (lt_agg["Canceled"] / lt_agg["Total"] * 100).round(1)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            lt_agg, x="LT Bucket", y="Cancel_Rate",
            title="Cancellation Rate by Lead Time Bucket (%)",
            color="Cancel_Rate",
            color_continuous_scale=["#34d399", "#f87171"],
            text="Cancel_Rate",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                          textfont_color=FONT_COLOR)
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(apply_theme(fig, show_legend=False), use_container_width=True)

    with col_b:
        fig = px.histogram(
            df_lt.sample(min(8000, len(df_lt)), random_state=42),
            x="lead_time",
            color=df_lt.sample(min(8000, len(df_lt)), random_state=42)["is_canceled"].map(
                {0: "Not Canceled", 1: "Canceled"}
            ),
            title="Lead Time Distribution (Canceled vs Not)",
            color_discrete_map={"Not Canceled": "#34d399", "Canceled": "#f87171"},
            nbins=60, opacity=0.72, barmode="overlay",
            labels={"color": "Status"},
        )
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    sample = df.sample(min(6000, len(df)), random_state=42).copy()
    sample["Status"] = sample["is_canceled"].map({0: "Not Canceled", 1: "Canceled"})
    fig = px.scatter(
        sample, x="lead_time", y="adr",
        color="Status",
        title="Lead Time vs ADR — Cancellation Highlighted",
        color_discrete_map={"Not Canceled": "#34d399", "Canceled": "#f87171"},
        labels={"lead_time": "Lead Time (days)", "adr": "ADR ($)"},
        opacity=0.45,
    )
    st.plotly_chart(apply_theme(fig, height=440), use_container_width=True)

with tab_x3:
    ms_agg = df.groupby("market_segment").agg(
        Total=("is_canceled", "count"),
        Canceled=("is_canceled", "sum"),
    ).reset_index()
    ms_agg["Cancel_Rate"] = (ms_agg["Canceled"] / ms_agg["Total"] * 100).round(1)
    ms_agg["Confirmed"]   = ms_agg["Total"] - ms_agg["Canceled"]
    ms_agg_sorted = ms_agg.sort_values("Cancel_Rate", ascending=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            ms_agg_sorted, x="Cancel_Rate", y="market_segment",
            orientation="h",
            title="Cancellation Rate by Market Segment (%)",
            color="Cancel_Rate",
            color_continuous_scale=["#34d399", "#f87171"],
            text="Cancel_Rate",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                          textfont_color=FONT_COLOR)
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(apply_theme(fig, show_legend=False), use_container_width=True)

    with col_b:
        fig = px.bar(
            ms_agg.sort_values("Total", ascending=False),
            x="market_segment", y=["Confirmed", "Canceled"],
            title="Total vs Canceled by Segment",
            color_discrete_sequence=["#38bdf8", "#f87171"],
            barmode="group",
        )
        st.plotly_chart(apply_theme(fig, rotate_x=-30), use_container_width=True)

divider()

# ─────────────────────────────────────────────────────────────
# SECTION 5 — BUSINESS INSIGHTS
# ─────────────────────────────────────────────────────────────
section("Business Insights", "💡")

top_country     = df.groupby("country").size().idxmax()
top_country_n   = df.groupby("country").size().max()
top_country_pct = top_country_n / len(df) * 100

best_segment  = df.groupby("market_segment")["Revenue"].sum().idxmax()
best_seg_rev  = df.groupby("market_segment")["Revenue"].sum().max()

high_cr_hotel = cancel_hotel.loc[cancel_hotel["Cancel_Rate"].idxmax(), "hotel"]
high_cr_rate  = cancel_hotel["Cancel_Rate"].max()

best_month_idx   = rev_trend["Revenue"].idxmax()
best_month_label = rev_trend.loc[best_month_idx, "YearMonth_str"]
best_month_rev   = rev_trend.loc[best_month_idx, "Revenue"]

lt90_cr = df.loc[df["lead_time"] > 90, "is_canceled"].mean() * 100

col_a, col_b = st.columns(2)
with col_a:
    st.warning(
        f"⚠️ **High Cancellation Alert**  \n"
        f"**{high_cr_hotel}** records the highest cancellation rate at **{high_cr_rate:.1f}%**.  \n"
        "This erodes revenue predictability. Immediate intervention via deposit policy is recommended."
    )
    st.info(
        f"🌍 **Dominant Source Market**  \n"
        f"**{top_country}** is the #1 origin country with **{top_country_n:,} bookings** "
        f"(**{top_country_pct:.1f}%** of total). Localized marketing and pricing for this market "
        "offers the single highest ROI opportunity."
    )
    st.success(
        f"📈 **Revenue Peak**  \n"
        f"**{best_month_label}** was the strongest month, generating **${best_month_rev:,.0f}** in revenue.  \n"
        "Align staffing, pricing, and capacity planning around this seasonal peak."
    )

with col_b:
    st.success(
        f"💰 **Top Revenue Segment**  \n"
        f"**{best_segment}** is the most valuable market segment, contributing **${best_seg_rev:,.0f}** in revenue.  \n"
        "Dedicated account management and exclusive rate agreements for this segment are warranted."
    )
    st.warning(
        f"⏱️ **Long Lead-Time Cancellation Risk**  \n"
        f"Bookings made more than 90 days in advance cancel at a rate of **{lt90_cr:.1f}%**.  \n"
        "Deposit requirements and pre-arrival engagement campaigns can significantly reduce this loss."
    )
    st.info(
        f"🔁 **Repeat Guest Loyalty Value**  \n"
        f"Repeat guests cancel **{new_cr - rep_cr:.1f} percentage points** less than new guests.  \n"
        "Growing the loyal base from the current **{:.1f}%** is a low-cost, high-return strategy.".format(repeat_pct)
    )

divider()

# ─────────────────────────────────────────────────────────────
# SECTION 6 — BUSINESS RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────
section("Business Recommendations", "🎯")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("💳 **Risk-Based Deposit Policy**\n\nRequire non-refundable deposits for bookings with lead time > 90 days or from high-cancellation market segments. This can reduce revenue loss by 20–30%.")
with col2:
    st.info("📱 **Boost Direct Bookings**\n\nOffer exclusive perks — early check-in, room upgrades, loyalty points — for direct-channel bookings to reduce OTA commission costs of 15–25% per booking.")
with col3:
    st.info("🌟 **Loyalty Program**\n\nBuild a structured loyalty scheme targeting the top 20% of high-frequency new guests. Repeat guests cancel far less and spend more — improving both RevPAR and predictability.")

col4, col5, col6 = st.columns(3)
with col4:
    st.success("📅 **Low-Season Bundle Offers**\n\nActivate bundled packages (F&B, spa, local tours) during identified low-revenue months to sustain occupancy without deep rate discounting.")
with col5:
    st.success(f"🤝 **Corporate Contract Focus**\n\nNegotiate long-term rate agreements with top-spending segments ({best_segment}). Guaranteed-volume contracts provide revenue floor and reduce marketing costs.")
with col6:
    st.success("🤖 **Predictive Cancellation System**\n\nDeploy ML-based cancellation scoring to flag at-risk bookings 30/60/90 days before arrival — enabling targeted re-engagement and overbooking buffer optimisation.")

divider()

# ─────────────────────────────────────────────────────────────
# SECTION 7 — PREDICTIVE ANALYTICS (OPTIONAL)
# ─────────────────────────────────────────────────────────────
section("Predictive Analytics", "🤖")

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    ML_OK = True
except ImportError:
    ML_OK = False

if not ML_OK:
    st.info(
        "ℹ️ **scikit-learn not installed.**  \n"
        "Add `scikit-learn` to `requirements.txt` and reinstall to enable ML predictions.  \n"
        "The rest of the dashboard runs normally."
    )
else:
    FEATURES = ["lead_time", "adr", "adults", "children"]
    TARGET   = "is_canceled"

    ml_df = df[FEATURES + [TARGET]].dropna()

    if len(ml_df) < 200:
        st.warning("⚠️ Not enough filtered data to train a model. Broaden your filter selection.")
    else:
        X, y = ml_df[FEATURES], ml_df[TARGET]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        @st.cache_resource(show_spinner="Training Random Forest …")
        def train_model(train_hash: int):
            clf = RandomForestClassifier(n_estimators=150, random_state=42, n_jobs=-1)
            clf.fit(X_train, y_train)
            return clf

        clf = train_model(hash(len(X_train)))

        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1]
        acc    = accuracy_score(y_test, y_pred)

        m1, m2, m3 = st.columns(3)
        with m1: st.metric("🎯 Model Accuracy",   f"{acc * 100:.2f}%", "Random Forest (150 trees)")
        with m2: st.metric("📦 Training Samples", f"{len(X_train):,}")
        with m3: st.metric("🧪 Test Samples",     f"{len(X_test):,}")

        col_a, col_b = st.columns(2)

        with col_a:
            fi = pd.DataFrame(
                {"Feature": FEATURES, "Importance": clf.feature_importances_}
            ).sort_values("Importance", ascending=True)
            fig = px.bar(
                fi, x="Importance", y="Feature", orientation="h",
                title="Feature Importance — Cancellation Prediction",
                color="Importance",
                color_continuous_scale=["#1e3a5f", "#38bdf8"],
                text="Importance",
            )
            fig.update_traces(texttemplate="%{text:.3f}", textposition="outside",
                              textfont_color=FONT_COLOR)
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(apply_theme(fig, show_legend=False), use_container_width=True)

        with col_b:
            prob_df = pd.DataFrame({
                "Cancellation Probability": y_prob,
                "Actual": y_test.values,
            })
            prob_df["Status"] = prob_df["Actual"].map({0: "Not Canceled", 1: "Canceled"})
            fig = px.histogram(
                prob_df, x="Cancellation Probability", color="Status",
                title="Predicted Probability Distribution",
                color_discrete_map={"Not Canceled": "#34d399", "Canceled": "#f87171"},
                nbins=40, opacity=0.72, barmode="overlay",
            )
            st.plotly_chart(apply_theme(fig), use_container_width=True)

        st.markdown("---")
        st.markdown("### 🔮 Cancellation Risk Predictor")
        st.caption("Enter booking parameters to estimate cancellation risk in real time.")

        p1, p2, p3, p4 = st.columns(4)
        with p1: inp_lt  = st.number_input("Lead Time (days)", 0, 1000, 45)
        with p2: inp_adr = st.number_input("ADR ($)", 0.0, 2000.0, 100.0, step=5.0)
        with p3: inp_adu = st.number_input("Adults", 1, 10, 2)
        with p4: inp_chi = st.number_input("Children", 0, 10, 0)

        if st.button("🔮 Predict Risk", type="primary"):
            x_new = pd.DataFrame([[inp_lt, inp_adr, inp_adu, inp_chi]], columns=FEATURES)
            prob  = clf.predict_proba(x_new)[0][1]
            pct   = prob * 100

            if pct >= 65:
                st.error(
                    f"🚨 **HIGH RISK — {pct:.1f}% cancellation probability**  \n"
                    "Action: Collect a non-refundable deposit immediately and send a personalised "
                    "pre-arrival communication sequence."
                )
            elif pct >= 35:
                st.warning(
                    f"⚠️ **MEDIUM RISK — {pct:.1f}% cancellation probability**  \n"
                    "Action: Monitor the booking and trigger a check-in email 2 weeks prior to arrival."
                )
            else:
                st.success(
                    f"✅ **LOW RISK — {pct:.1f}% cancellation probability**  \n"
                    "This booking shows strong confirmation signals. Standard pre-arrival flow applies."
                )

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
divider()
st.caption("🏨 Hotel Booking BI Dashboard · Built with Streamlit & Plotly · Dataset: Hotel Booking Demand — Kaggle")