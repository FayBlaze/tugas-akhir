import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Dashboard",
    page_icon="😎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. CONSTANTS
MONTH_ORDER = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]

# 3. DATA LOADING & FEATURE ENGINEERING
@st.cache_data # 1
def load():
    try:
        df = pd.read_csv("hotel_bookings.csv")
    except FileNotFoundError:
        st.error("File tidak ditemukan.")
        return pd.DataFrame() 

    # — Bersihkan —
    df["children"] = pd.to_numeric(df["children"], errors="coerce").fillna(0).astype(int)
    df["agent"]    = df["agent"].fillna("None").astype(str)
    df["company"]  = df["company"].fillna("None").astype(str)
    df["country"]  = df["country"].fillna("Unknown")
    df["adr"]      = pd.to_numeric(df["adr"], errors="coerce").fillna(0)

    # — Fitur turunan —
    df["total_nights"]  = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["total_guests"]  = df["adults"] + df["children"] + df["babies"]
    df["revenue_est"]   = (df["adr"] * df["total_nights"]).clip(lower=0)
    df["room_match"]    = (df["reserved_room_type"] == df["assigned_room_type"]).astype(int)
    df["is_family"]     = ((df["children"] > 0) | (df["babies"] > 0)).astype(int)
    df["month_cat"]     = pd.Categorical(
        df["arrival_date_month"], categories=MONTH_ORDER, ordered=True
    )

    # — Bucket lead time —
    df["lead_bucket"] = pd.cut(
        df["lead_time"],
        bins=[-1, 7, 30, 90, 180, 365, 9_999],
        labels=["0-7d", "8-30d", "31-90d", "91-180d", "181-365d", "365d+"],
    )

    # — Bucket lama menginap —
    df["stay_bucket"] = pd.cut(
        df["total_nights"],
        bins=[-1, 1, 3, 7, 14, 9_999],
        labels=["1 malam", "2-3 malam", "4-7 malam", "8-14 malam", "15+ malam"],
    )

    return df

# ──────────────────────────────────────────────────────────────────────────────
# 4. LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
df_raw = load()


# 5. SIDEBAR
with st.sidebar:
    st.title("🏨 HotelIQ")
    st.write("**Business Intelligence Dashboard**")
    
    st.divider()
    
    st.subheader("Filters")
    hotels   = st.multiselect("Tipe Hotel", df_raw["hotel"].unique(), default=list(df_raw["hotel"].unique()))
    years    = st.multiselect("Tahun", sorted(df_raw["arrival_date_year"].unique()), default=list(df_raw["arrival_date_year"].unique()))
    segments = st.multiselect("Market Segment", df_raw["market_segment"].unique(), default=list(df_raw["market_segment"].unique()))

    df = df_raw[
        df_raw["hotel"].isin(hotels) &
        df_raw["arrival_date_year"].isin(years) &
        df_raw["market_segment"].isin(segments)
    ].copy()

    st.divider()
    st.write(f"**{len(df):,}** rekaman")
    st.write(f"**{df['hotel'].nunique()}** tipe hotel")
    st.write(f"**{df['country'].nunique()}** negara asal")
    st.write(f"**{df['arrival_date_year'].nunique()}** tahun data")

# ──────────────────────────────────────────────────────────────────────────────
# 6. HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.title("HOTEL BOOKING ANALYTICS")
st.caption("📊 Business Intelligence · HotelIQ Platform")

# ──────────────────────────────────────────────────────────────────────────────
# 7. KPI ROW
st.subheader("KEY PERFORMANCE INDICATORS")

df_ok = df[df["is_canceled"] == 0]

total_bkg   = len(df)
cancel_rate = df["is_canceled"].mean() * 100 if total_bkg > 0 else 0
avg_adr     = df_ok["adr"].mean() if len(df_ok) > 0 else 0
tot_rev     = df_ok["revenue_est"].sum()
avg_los     = df_ok["total_nights"].mean() if len(df_ok) > 0 else 0
avg_lead    = df["lead_time"].mean() if total_bkg > 0 else 0

cols = st.columns(6)
cols[0].metric("Total Booking", f"{total_bkg:,}")
cols[1].metric("Tingkat Pembatalan", f"{cancel_rate:.1f}%")
cols[2].metric("Rata-rata ADR", f"${avg_adr:,.0f}")
cols[3].metric("Est. Total Revenue", f"${tot_rev/1_000_000:.1f}M")
cols[4].metric("Rata-rata Menginap", f"{avg_los:.1f} malam")
cols[5].metric("Rata-rata Lead Time", f"{avg_lead:.0f} hari")

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# 8. TABS
# ──────────────────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs([
    "📈 TREN BOOKING",
    "💰 REVENUE & HARGA",
    "👥 SEGMENTASI TAMU",
    "⚙️ OPERASIONAL",
    "❌ ANALISIS PEMBATALAN",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — TREN BOOKING
# ══════════════════════════════════════════════════════════════════════════════
with t1:
    st.subheader("Volume Booking Bulanan")

    left, right = st.columns([2, 1])

    with left:
        monthly = (
            df.groupby(["arrival_date_year", "month_cat"], observed=True)
            .size()
            .reset_index(name="bookings")
        )
        monthly["arrival_date_year"] = monthly["arrival_date_year"].astype(str)

        fig = px.line(
            monthly, x="month_cat", y="bookings", color="arrival_date_year",
            title="Jumlah Booking per Bulan & Tahun",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        hs = df.groupby(["hotel", "is_canceled"]).size().reset_index(name="count")
        hs["status"] = hs["is_canceled"].map({0: "Confirmed", 1: "Canceled"})
        fig2 = px.bar(
            hs, x="hotel", y="count", color="status",
            title="Booking per Tipe Hotel",
            barmode="stack",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.info("💡 **Pola Musiman:** Juli–Agustus biasanya puncak occupancy Resort Hotel, sementara City Hotel lebih stabil sepanjang tahun. Identifikasi shoulder season untuk strategi promosi tepat sasaran.")
    
    st.divider()

    st.subheader("Saluran Distribusi & Segmen Pasar")
    c3, c4 = st.columns(2)

    with c3:
        seg = (
            df.groupby("market_segment").size()
            .reset_index(name="count")
            .sort_values("count")
        )
        fig3 = px.bar(
            seg, y="market_segment", x="count", orientation="h",
            title="Booking per Market Segment",
            color="count",
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        dist = df.groupby("distribution_channel").size().reset_index(name="count")
        fig4 = px.pie(
            dist, names="distribution_channel", values="count",
            title="Komposisi Distribution Channel",
            hole=0.45,
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.info("💡 **Strategi Channel:** OTA mendominasi volume tetapi membawa biaya komisi tinggi. Bandingkan tingkat pembatalan antar channel untuk menilai nilai bersih tiap saluran.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — REVENUE & PRICING
# ══════════════════════════════════════════════════════════════════════════════
with t2:
    st.subheader("Tren Average Daily Rate (ADR)")

    c1, c2 = st.columns(2)

    with c1:
        adr_m = (
            df_ok.groupby(["arrival_date_year", "month_cat"], observed=True)["adr"]
            .mean()
            .reset_index()
        )
        adr_m["arrival_date_year"] = adr_m["arrival_date_year"].astype(str)
        fig = px.line(
            adr_m, x="month_cat", y="adr", color="arrival_date_year",
            title="Rata-rata ADR per Bulan & Tahun (Booking Terkonfirmasi)",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        clip99 = df_ok["adr"].quantile(0.99) if len(df_ok) > 0 else 9999
        fig2 = px.violin(
            df_ok[df_ok["adr"] < clip99], x="hotel", y="adr", color="hotel",
            title="Distribusi ADR per Tipe Hotel",
            box=True,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Revenue per Segmen & Tipe Pelanggan")

    c3, c4 = st.columns(2)

    with c3:
        rev_seg = (
            df_ok.groupby("market_segment")
            .agg(total_rev=("revenue_est", "sum"), n=("adr", "count"))
            .reset_index()
            .sort_values("total_rev")
        )
        rev_seg["avg_rev"] = np.where(rev_seg["n"] > 0, rev_seg["total_rev"] / rev_seg["n"], 0)
        fig3 = px.bar(
            rev_seg, y="market_segment", x="total_rev", orientation="h",
            title="Estimasi Total Revenue per Market Segment",
            color="avg_rev",
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        adr_ct = (
            df_ok.groupby("customer_type")["adr"]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        adr_ct.columns = ["customer_type", "mean_adr", "median_adr", "count"]
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=adr_ct["customer_type"], y=adr_ct["mean_adr"],
            name="Mean ADR"
        ))
        fig4.add_trace(go.Bar(
            x=adr_ct["customer_type"], y=adr_ct["median_adr"],
            name="Median ADR"
        ))
        fig4.update_layout(
            title="Mean vs Median ADR per Customer Type",
            barmode="group",
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.info("💡 **Kesenjangan Mean–Median:** Celah besar antara mean dan median ADR menandakan outlier premium yang menarik rata-rata ke atas. Fokuskan upsell pada segmen dengan median ADR tinggi untuk pertumbuhan revenue yang lebih stabil.")

    st.divider()
    st.subheader("Dampak Deposit terhadap ADR & Volume")

    dep_adr = (
        df.groupby(["deposit_type", "is_canceled"])
        .agg(avg_adr=("adr", "mean"), count=("adr", "count"))
        .reset_index()
    )
    dep_adr["Status"] = dep_adr["is_canceled"].map({0: "Confirmed", 1: "Canceled"})

    fig5 = px.scatter(
        dep_adr, x="deposit_type", y="avg_adr", color="Status",
        size="count", title="ADR Rata-rata per Deposit Type (ukuran bubble = volume)",
        size_max=60,
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.info("💡 **Kebijakan Deposit:** Non-refundable deposit hampir menjamin nol pembatalan. Pertimbangkan insentif harga (diskon 5–10%) untuk mendorong tamu memilih tarif non-refundable.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SEGMENTASI TAMU
# ══════════════════════════════════════════════════════════════════════════════
with t3:
    st.subheader("Distribusi Geografis Tamu")

    country_df = (
        df_ok.groupby("country")
        .agg(bookings=("hotel", "count"), avg_adr=("adr", "mean"))
        .reset_index()
        .sort_values("bookings", ascending=False)
    )

    map_col, bar_col = st.columns([2, 1])

    with map_col:
        fig = px.choropleth(
            country_df.head(60), locations="country",
            color="bookings", locationmode="ISO-3",
            title="Top Negara Asal Tamu (Booking Terkonfirmasi)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with bar_col:
        top10 = country_df.head(10).iloc[::-1]
        fig2 = px.bar(
            top10, y="country", x="bookings", orientation="h",
            title="Top 10 Negara Asal",
            color="avg_adr",
            text="bookings",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Profil Pelanggan & Preferensi")
    c3, c4, c5 = st.columns(3)

    with c3:
        ctype = df_ok.groupby("customer_type").size().reset_index(name="count")
        fig3 = px.pie(
            ctype, names="customer_type", values="count",
            title="Komposisi Tipe Pelanggan",
            hole=0.42,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        meal = df_ok.groupby("meal").size().reset_index(name="count").sort_values("count", ascending=False)
        fig4 = px.bar(
            meal, x="meal", y="count",
            title="Popularitas Paket Makan",
            color="meal",
            text="count",
        )
        fig4.update_layout(showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    with c5:
        fam = (
            df_ok.groupby("is_family")
            .agg(count=("hotel", "count"), avg_adr=("adr", "mean"))
            .reset_index()
        )
        fam["Tipe"] = fam["is_family"].map({0: "Tanpa Anak", 1: "Dengan Anak"})
        fig5 = px.bar(
            fam, x="Tipe", y="count",
            title="Tamu Keluarga vs Non-Keluarga",
            color="Tipe",
            text="count",
        )
        fig5.update_layout(showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)

    st.info("💡 **Peluang Upsell Meal:** BB (Bed & Breakfast) mendominasi, namun HB/FB memiliki ADR lebih tinggi. Program upsell paket makan saat check-in dapat meningkatkan revenue ancillary secara signifikan.")

    st.divider()
    st.subheader("Analisis Tamu Berulang")

    repeat = (
        df.groupby("is_repeated_guest")
        .agg(n=("is_canceled", "count"), cancel=("is_canceled", "sum"), avg_adr=("adr", "mean"))
        .reset_index()
    )
    repeat["cancel_rate"] = np.where(repeat["n"] > 0, repeat["cancel"] / repeat["n"] * 100, 0)
    repeat["avg_spend"]   = repeat["avg_adr"]
    repeat["label"]       = repeat["is_repeated_guest"].map({0: "Tamu Baru", 1: "Tamu Kembali"})

    r1, r2 = st.columns(2)
    with r1:
        fig6 = px.bar(
            repeat, x="label", y="cancel_rate",
            title="Tingkat Pembatalan: Tamu Baru vs Kembali",
            color="label",
            text=repeat["cancel_rate"].apply(lambda x: f"{x:.1f}%"),
        )
        fig6.update_layout(showlegend=False)
        st.plotly_chart(fig6, use_container_width=True)

    with r2:
        fig7 = px.bar(
            repeat, x="label", y="avg_adr",
            title="ADR Rata-rata: Tamu Baru vs Kembali",
            color="label",
            text=repeat["avg_adr"].apply(lambda x: f"${x:.0f}"),
        )
        fig7.update_layout(showlegend=False)
        st.plotly_chart(fig7, use_container_width=True)

    st.info("💡 **Nilai Loyalitas:** Tamu yang kembali membatalkan jauh lebih sedikit dan sering memiliki ADR lebih tinggi. Setiap investasi dalam program loyalitas langsung mengurangi eksposur pembatalan.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — OPERASIONAL
# ══════════════════════════════════════════════════════════════════════════════
with t4:
    st.subheader("Efisiensi Alokasi Kamar")

    match_rate = df["room_match"].mean() * 100 if len(df) > 0 else 0
    o1, o2 = st.columns(2)

    with o1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=match_rate,
            title={"text": "Room Assignment Match Rate"},
            number={"suffix": "%"}
        ))
        st.plotly_chart(fig, use_container_width=True)

        st.info(f"💡 **Akurasi Kamar:** Match rate {match_rate:.1f}%: tamu menerima tipe kamar berbeda dari yang dipesan. Di bawah 85% berdampak signifikan pada kepuasan — cek prosedur overbook.")

    with o2:
        los = (
            df_ok.groupby("stay_bucket", observed=True)
            .size()
            .reset_index(name="count")
        )
        fig2 = px.bar(
            los, x="stay_bucket", y="count",
            title="Distribusi Lama Menginap",
            color="stay_bucket",
            text="count",
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Special Requests & Parkir")
    c3, c4 = st.columns(2)

    with c3:
        sr = (
            df_ok.groupby("total_of_special_requests").size()
            .reset_index(name="count")
        )
        fig3 = px.bar(
            sr, x="total_of_special_requests", y="count",
            title="Distribusi Jumlah Special Request per Booking",
            color="total_of_special_requests",
            text="count",
        )
        fig3.update_layout(xaxis=dict(tickmode="linear"))
        st.plotly_chart(fig3, use_container_width=True)

        st.info("💡 **Sinyal Komitmen:** Booking dengan lebih banyak special request memiliki tingkat pembatalan lebih rendah — menandakan komitmen tamu yang lebih kuat. Prioritaskan layanan untuk grup ini.")

    with c4:
        park = (
            df_ok.groupby("required_car_parking_spaces").size()
            .reset_index(name="count")
        )
        fig4 = px.bar(
            park, x="required_car_parking_spaces", y="count",
            title="Permintaan Tempat Parkir",
            color="count",
            text="count",
        )
        fig4.update_layout(xaxis=dict(tickmode="linear"))
        st.plotly_chart(fig4, use_container_width=True)

        st.info("💡 **Revenue Parkir:** Permintaan parkir berkorelasi dengan tamu keluarga & long-stay. Dynamic pricing parkir bisa menjadi sumber pendapatan ancillary yang signifikan.")

    st.divider()
    st.subheader("Lead Time & Perubahan Booking")
    c5, c6 = st.columns(2)

    with c5:
        ld = (
            df.groupby("lead_bucket", observed=True)
            .agg(count=("is_canceled", "count"), cancel_rate=("is_canceled", "mean"))
            .reset_index()
        )
        ld["cancel_rate"] = ld["cancel_rate"] * 100

        fig5 = go.Figure()
        fig5.add_trace(go.Bar(
            x=ld["lead_bucket"], y=ld["count"],
            name="Volume", yaxis="y",
        ))
        fig5.add_trace(go.Scatter(
            x=ld["lead_bucket"], y=ld["cancel_rate"],
            name="Tingkat Pembatalan", mode="lines+markers", yaxis="y2",
        ))
        fig5.update_layout(
            title="Lead Time: Volume vs Tingkat Pembatalan",
            yaxis=dict(title="Booking", side="left"),
            yaxis2=dict(title="Pembatalan %", overlaying="y", side="right", ticksuffix="%"),
        )
        st.plotly_chart(fig5, use_container_width=True)

    with c6:
        ch = (
            df.groupby("booking_changes")
            .agg(count=("is_canceled", "count"), cancel_rate=("is_canceled", "mean"))
            .reset_index()
        )
        ch["cancel_rate"] = ch["cancel_rate"] * 100
        ch = ch[ch["booking_changes"] <= 10]

        fig6 = go.Figure()
        fig6.add_trace(go.Bar(
            x=ch["booking_changes"], y=ch["count"],
            name="Volume", yaxis="y",
        ))
        fig6.add_trace(go.Scatter(
            x=ch["booking_changes"], y=ch["cancel_rate"],
            name="Tingkat Pembatalan", mode="lines+markers", yaxis="y2",
        ))
        fig6.update_layout(
            title="Perubahan Booking vs Tingkat Pembatalan",
            xaxis_title="Jumlah Perubahan",
            yaxis=dict(title="Booking", side="left"),
            yaxis2=dict(title="Pembatalan %", overlaying="y", side="right", ticksuffix="%"),
        )
        st.plotly_chart(fig6, use_container_width=True)

    st.info("💡 **Strategi Lead Time:** Lead time panjang (90+ hari) berkorelasi dengan tingkat pembatalan lebih tinggi. Tawarkan diskon 5–10% untuk tarif non-refundable pada pemesanan jauh hari — mengunci revenue lebih awal sekaligus mengurangi exposure pembatalan.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ANALISIS PEMBATALAN
# ══════════════════════════════════════════════════════════════════════════════
with t5:
    st.subheader("Peta Pembatalan per Dimensi Bisnis")

    a1, a2 = st.columns(2)

    with a1:
        ch = (
            df.groupby("hotel")
            .agg(total=("is_canceled", "count"), canceled=("is_canceled", "sum"))
            .reset_index()
        )
        ch["confirmed"] = ch["total"] - ch["canceled"]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=ch["hotel"], y=ch["confirmed"],
            name="Confirmed"
        ))
        fig.add_trace(go.Bar(
            x=ch["hotel"], y=ch["canceled"],
            name="Canceled"
        ))
        fig.update_layout(title="Pembatalan per Tipe Hotel", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

    with a2:
        dep = (
            df.groupby("deposit_type")
            .agg(total=("is_canceled", "count"), canceled=("is_canceled", "sum"))
            .reset_index()
        )
        dep["rate"] = np.where(dep["total"] > 0, dep["canceled"] / dep["total"] * 100, 0)
        fig2 = px.bar(
            dep, x="deposit_type", y="rate",
            title="Tingkat Pembatalan per Deposit Type",
            color="deposit_type",
            text=dep["rate"].apply(lambda x: f"{x:.1f}%"),
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Pembatalan per Segmen & Riwayat Tamu")
    a3, a4 = st.columns(2)

    with a3:
        seg_c = (
            df.groupby("market_segment")
            .agg(total=("is_canceled", "count"), canceled=("is_canceled", "sum"))
            .reset_index()
        )
        seg_c["rate"] = np.where(seg_c["total"] > 0, seg_c["canceled"] / seg_c["total"] * 100, 0)
        seg_c = seg_c.sort_values("rate")
        fig3 = px.bar(
            seg_c, y="market_segment", x="rate", orientation="h",
            title="Tingkat Pembatalan per Market Segment",
            color="rate",
            text=seg_c["rate"].apply(lambda x: f"{x:.1f}%"),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with a4:
        prev = (
            df.groupby("previous_cancellations")
            .agg(count=("is_canceled", "count"), rate=("is_canceled", "mean"))
            .reset_index()
        )
        prev["rate"] = prev["rate"] * 100
        prev = prev[prev["previous_cancellations"] <= 12]
        
        fig4 = px.bar(
            prev, x="previous_cancellations", y="rate",
            title="Tingkat Pembatalan Saat Ini vs Riwayat Pembatalan",
            color="rate",
            text=prev["rate"].apply(lambda x: f"{x:.0f}%"),
        )
        fig4.update_layout(
            xaxis_title="Jumlah Pembatalan Sebelumnya",
            yaxis_title="Tingkat Pembatalan Saat Ini",
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.info("💡 **Pembobotan Risiko:** Tamu dengan 3+ pembatalan sebelumnya memiliki risiko jauh lebih tinggi. Pertimbangkan syarat deposit wajib atau pra-otorisasi untuk profil risiko tinggi.")

    st.divider()
    st.subheader("Korelasi Special Requests dengan Pembatalan")

    sr_cancel = (
        df.groupby("total_of_special_requests")
        .agg(cancel_rate=("is_canceled", "mean"), count=("is_canceled", "count"))
        .reset_index()
    )
    sr_cancel["cancel_rate"] = sr_cancel["cancel_rate"] * 100

    fig5 = go.Figure()
    fig5.add_trace(go.Bar(
        x=sr_cancel["total_of_special_requests"],
        y=sr_cancel["cancel_rate"],
        name="Tingkat Pembatalan",
        yaxis="y",
    ))
    fig5.add_trace(go.Scatter(
        x=sr_cancel["total_of_special_requests"],
        y=sr_cancel["count"],
        mode="lines+markers",
        name="Volume Booking",
        yaxis="y2",
    ))
    fig5.update_layout(
        title="Special Requests: Dampak terhadap Tingkat Pembatalan",
        xaxis_title="Jumlah Special Request",
        xaxis=dict(tickmode="linear"),
        yaxis=dict(title="Tingkat Pembatalan %", ticksuffix="%", side="left"),
        yaxis2=dict(title="Volume Booking", overlaying="y", side="right"),
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.info("💡 **Strategi Retensi Tamu:** Tamu dengan 2+ special request mencerminkan keterlibatan dan niat tinggal yang lebih kuat. Encourage permintaan khusus di halaman booking sebagai sinyal komitmen sekaligus data ops.")

# 9. FOOTER
st.divider()
st.caption("HotelIQ BI Dashboard · Streamlit + Plotly Default Styling")