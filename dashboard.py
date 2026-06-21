import streamlit as st          
import pandas as pd             
import plotly.express as px     
import plotly.graph_objects as go

st.set_page_config(
    page_title="Video Game Sales — BI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Membaca dan membersihkan dataset vgsales.csv.
    """
    try:
        df = pd.read_csv("vgsales.csv")
    except FileNotFoundError:
        st.error("File vgsales.csv tidak ditemukan. Pastikan file berada di folder yang sama.")
        return pd.DataFrame()

    # — Pembersihan data —
    df = df.dropna(subset=["Year"])            # hapus baris tanpa tahun
    df["Year"]      = df["Year"].astype(int)   # float → int
    df["Publisher"] = df["Publisher"].fillna("Unknown")  # isi NaN publisher

    return df

#  LOAD DATA
df = load_data()   # df = DataFrame lengkap, belum difilter

if df.empty:
    st.stop()

#  JUDUL DASHBOARD
st.title("🎮 Video Game Sales — Business Intelligence Dashboard")
st.caption(
    "Analisis penjualan video game global · Data: VGChartz via Kaggle · "
    f"{len(df):,} judul · {df['Year'].min()}–{df['Year'].max()}"
)

#  SIDEBAR — FILTER INTERAKTIF
with st.sidebar:
    st.header("⚙️ Filter Data")

    #Filter tahun
    min_year = int(df["Year"].min())   # 1980
    max_year = int(df["Year"].max())   # 2020

    tahun_range = st.slider(
        "Pilih Rentang Tahun",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),    # default: semua tahun
        step=1
    )

    #Filter genre
    genre_unik = sorted(df["Genre"].unique())   # list genre unik, urut abjad
    pilihan_genre = st.multiselect(
        "Pilih Genre:",
        options=genre_unik,
        default=genre_unik             # default: semua genre terpilih
    )

    #Filter platform
    top_platforms = (
        df.groupby("Platform")["Global_Sales"]
          .sum()
          .sort_values(ascending=False)
          .head(15)
          .index.tolist()
    )
    
    # Urutkan nama platform secara alfabetis
    top_platforms_abjad = sorted(top_platforms)
    
    pilihan_platform = st.multiselect(
        "Pilih Platform (Top 15):",
        options=top_platforms_abjad,
        default=top_platforms_abjad
    )

    st.divider()
    st.caption("ℹ️ Filter berlaku pada semua grafik di bawah.")


#  FUNGSI: apply_filters()
def apply_filters(data: pd.DataFrame, year_range: tuple, genres: list, platforms: list) -> pd.DataFrame:
    mask = (
        (data["Year"]     >= year_range[0]) &
        (data["Year"]     <= year_range[1]) &
        (data["Genre"].isin(genres))        &
        (data["Platform"].isin(platforms))
    )
    return data[mask]

# df_filtered = subset data sesuai semua filter yang aktif
df_filtered = apply_filters(df, tahun_range, pilihan_genre, pilihan_platform)

#  BARIS KPI — INDIKATOR UTAMA
total_sales   = df_filtered["Global_Sales"].sum()   # total penjualan (juta unit)
total_games   = df_filtered.shape[0]                # jumlah judul game
avg_sales     = df_filtered["Global_Sales"].mean()  # rata-rata penjualan per judul

if not df_filtered.empty:
    top_publisher = df_filtered.groupby("Publisher")["Global_Sales"].sum().idxmax()
else:
    top_publisher = "-"

cols = st.columns(4)
cols[0].metric("🌍 Total Penjualan Global",  f"{total_sales:,.2f}M unit")
cols[1].metric("🎮 Jumlah Judul Game",        f"{total_games:,}")
cols[2].metric("📊 Rata-rata per Judul",      f"{avg_sales:.3f}M unit")
cols[3].metric("🏆 Publisher Teratas",        top_publisher)

st.divider()

#  FUNGSI: make_bar()
def make_bar(data: pd.DataFrame, x: str, y: str, title: str, color: str = None, horizontal: bool = False, top_n: int = None) -> go.Figure:
    if top_n:
        data = data.nlargest(top_n, y)
    orientation = "h" if horizontal else "v"
    if horizontal:
        x, y = y, x   # swap agar bar horizontal
    fig = px.bar(
        data, x=x, y=y,
        title=title,
        color=color if color else y,
        color_continuous_scale="Blues",
        orientation=orientation,
        text_auto=".1f"
    )
    fig.update_layout(showlegend=False, margin=dict(t=40, b=10))
    return fig


# ═══════════════════════════════════════════════════════════════
#  PEMBUATAN TABS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Tren", 
    "🕹️ Genre", 
    "🖥️ Platform", 
    "🏢 Publisher", 
    "🌏 Regional", 
    "🏆 Top 20", 
    "💡 Insight", 
    "📖 Docs"
])

# ───────────────────────────────────────────────────────────────
# TAB 1 — TREN PENJUALAN PER TAHUN
# ───────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Tren Penjualan per Tahun")
    st.markdown(
        """
        **Apa yang dianalisis:**
        Total penjualan global (juta unit) dijumlahkan per tahun untuk
        mengidentifikasi fase pertumbuhan, puncak, dan penurunan industri.

        **Temuan utama:**
        Industri mencapai puncaknya pada **2006–2009** (era Wii, DS, PS3, X360).
        Tren menurun setelah 2009 mencerminkan fragmentasi pasar ke mobile/digital
        yang tidak tercakup dataset ini (VGChartz hanya rekam penjualan fisik).
        """
    )
    if not df_filtered.empty:
        year_sales = (
            df_filtered.groupby("Year")["Global_Sales"]
                       .sum()
                       .reset_index()
                       .rename(columns={"Global_Sales": "Total_Sales"})
        )
        fig_trend = px.area(
            year_sales, x="Year", y="Total_Sales",
            title="Total Penjualan Global per Tahun (juta unit)",
            markers=True,
            color_discrete_sequence=["#1f77b4"]
        )
        fig_trend.update_layout(xaxis_title="Tahun", yaxis_title="Penjualan (juta unit)", margin=dict(t=40, b=10))
        st.plotly_chart(fig_trend, width="stretch")

# ───────────────────────────────────────────────────────────────
# TAB 2 — ANALISIS GENRE
# ───────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Analisis Genre")
    st.markdown(
        """
        **Apa yang dianalisis:**
        Total penjualan per genre dan jumlah judul per genre.
        Dua dimensi ini penting: genre bisa populer karena banyak judul
        (volume) *atau* karena tiap judulnya terjual banyak (kualitas).
        """
    )
    if not df_filtered.empty:
        genre_sales = (
            df_filtered.groupby("Genre")
                       .agg(Total_Sales=("Global_Sales", "sum"),
                            Total_Games=("Name", "count"),
                            Avg_Sales=("Global_Sales", "mean"))
                       .reset_index()
                       .sort_values("Total_Sales", ascending=False)
        )
        col1, col2 = st.columns(2)
        with col1:
            fig_genre_sales = make_bar(genre_sales, x="Genre", y="Total_Sales", title="Total Penjualan per Genre (juta unit)")
            st.plotly_chart(fig_genre_sales, width="stretch")
        with col2:
            fig_genre_count = make_bar(genre_sales.sort_values("Total_Games", ascending=False), x="Genre", y="Total_Games", title="Jumlah Judul Game per Genre")
            st.plotly_chart(fig_genre_count, width="stretch")

        st.caption("**Rata-rata Penjualan per Judul berdasarkan Genre** (mengindikasikan efisiensi/dampak per game)")
        avg_genre = genre_sales.sort_values("Avg_Sales", ascending=True)
        fig_avg = px.bar(
            avg_genre, x="Avg_Sales", y="Genre", orientation="h",
            title="Rata-rata Penjualan per Judul (juta unit)",
            color="Avg_Sales", color_continuous_scale="Greens", text_auto=".2f"
        )
        fig_avg.update_layout(showlegend=False, margin=dict(t=40, b=10))
        st.plotly_chart(fig_avg, width="stretch")

# ───────────────────────────────────────────────────────────────
# TAB 3 — ANALISIS PLATFORM
# ───────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Analisis Platform")
    st.markdown(
        """
        **Apa yang dianalisis:**
        Platform (konsol) mana yang menghasilkan penjualan terbesar
        dan berapa banyak judul yang tersedia di masing-masing platform.
        """
    )
    if not df_filtered.empty:
        platform_sales = (
            df_filtered.groupby("Platform")
                       .agg(Total_Sales=("Global_Sales", "sum"),
                            Total_Games=("Name", "count"))
                       .reset_index()
                       .sort_values("Total_Sales", ascending=False)
                       .head(15)
        )
        col3, col4 = st.columns(2)
        with col3:
            fig_plat_sales = px.bar(
                platform_sales, x="Platform", y="Total_Sales",
                title="Top 15 Platform — Total Penjualan",
                color="Total_Sales", color_continuous_scale="Oranges", text_auto=".0f"
            )
            fig_plat_sales.update_layout(showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(fig_plat_sales, width="stretch")
        with col4:
            fig_plat_games = px.bar(
                platform_sales.sort_values("Total_Games", ascending=False),
                x="Platform", y="Total_Games",
                title="Top 15 Platform — Jumlah Judul",
                color="Total_Games", color_continuous_scale="Purples", text_auto=".0f"
            )
            fig_plat_games.update_layout(showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(fig_plat_games, width="stretch")

# ───────────────────────────────────────────────────────────────
# TAB 4 — ANALISIS PUBLISHER
# ───────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Analisis Publisher")
    st.markdown(
        """
        **Apa yang dianalisis:**
        Top 10 publisher berdasarkan total penjualan global dan
        rata-rata penjualan per judul (mengukur efisiensi portofolio).
        """
    )
    if not df_filtered.empty:
        pub_sales = (
            df_filtered.groupby("Publisher")
                       .agg(Total_Sales=("Global_Sales", "sum"),
                            Total_Games=("Name", "count"),
                            Avg_Sales=("Global_Sales", "mean"))
                       .reset_index()
                       .sort_values("Total_Sales", ascending=False)
                       .head(10)
        )
        col5, col6 = st.columns(2)
        with col5:
            fig_pub = px.bar(
                pub_sales.sort_values("Total_Sales"), x="Total_Sales", y="Publisher",
                orientation="h", title="Top 10 Publisher — Total Penjualan",
                color="Total_Sales", color_continuous_scale="Reds", text_auto=".0f"
            )
            fig_pub.update_layout(showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(fig_pub, width="stretch")
        with col6:
            fig_pub_avg = px.bar(
                pub_sales.sort_values("Avg_Sales"), x="Avg_Sales", y="Publisher",
                orientation="h", title="Top 10 Publisher — Rata-rata per Judul",
                color="Avg_Sales", color_continuous_scale="YlOrRd", text_auto=".2f"
            )
            fig_pub_avg.update_layout(showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(fig_pub_avg, width="stretch")

# ───────────────────────────────────────────────────────────────
# TAB 5 — DISTRIBUSI REGIONAL (Sudah Terurut)
# ───────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Distribusi Penjualan Regional")
    st.markdown(
        """
        **Apa yang dianalisis:**
        Proporsi penjualan dari empat wilayah (NA, EU, JP, Other)
        dan perbandingan preferensi genre antar wilayah.
        """
    )
    if not df_filtered.empty:
        region_totals = pd.DataFrame({
            "Region": ["NA", "EU", "JP", "Other"],
            "Sales": [
                df_filtered["NA_Sales"].sum(),
                df_filtered["EU_Sales"].sum(),
                df_filtered["JP_Sales"].sum(),
                df_filtered["Other_Sales"].sum()
            ]
        })
        col7, col8 = st.columns([1, 2])
        with col7:
            fig_pie = px.pie(
                region_totals, values="Sales", names="Region",
                title="Proporsi Penjualan per Wilayah",
                hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_layout(margin=dict(t=40, b=10))
            st.plotly_chart(fig_pie, width="stretch")
            
        with col8:
            # 1. Hitung total penjualan per genre untuk dasar pengurutan
            region_genre = (
                df_filtered.groupby("Genre")[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]]
                           .sum().reset_index()
            )
            # 2. Tambahkan kolom Total dan urutkan dari terbesar ke terkecil
            region_genre["Total_Global"] = region_genre[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum(axis=1)
            region_genre = region_genre.sort_values("Total_Global", ascending=False)
            
            # 3. Lakukan melt untuk plotting Plotly
            region_genre_melt = region_genre.melt(
                id_vars=["Genre", "Total_Global"], 
                value_vars=["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"],
                var_name="Region", value_name="Sales"
            )
            region_genre_melt["Region"] = region_genre_melt["Region"].str.replace("_Sales", "")
            
            fig_stacked = px.bar(
                region_genre_melt, x="Genre", y="Sales", color="Region",
                barmode="stack", title="Penjualan Genre berdasarkan Wilayah (Urut Terbesar)",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            # Memastikan urutan sumbu X mengikuti urutan DataFrame yang sudah disortir
            fig_stacked.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(t=40, b=10))
            st.plotly_chart(fig_stacked, width="stretch")

# ───────────────────────────────────────────────────────────────
# TAB 6 — TOP 20 GAME TERLARIS
# ───────────────────────────────────────────────────────────────
with tab6:
    st.subheader("Top 20 Game Terlaris")
    if not df_filtered.empty:
        # 1. Ambil top 20 data mentah (terurut menurun)
        top20 = (
            df_filtered[["Name", "Platform", "Year", "Genre", "Publisher", "Global_Sales"]]
            .sort_values("Global_Sales", ascending=False)
            .head(20)
            .reset_index(drop=True)
        )
        top20.index += 1
        
        # 2. Pembuatan plot
        fig_top20 = px.bar(
            top20, x="Global_Sales", y="Name",
            orientation="h", color="Genre", hover_data=["Platform", "Year", "Publisher"],
            title="Top 20 Game Terlaris (Peringkat #1 di Atas)",
            color_discrete_sequence=px.colors.qualitative.Plotly, text_auto=".1f"
        )
        
        # 3. Kunci urutan sumbu Y agar mengabaikan pengelompokan warna (Genre)
        # 'total ascending' memastikan nilai terbesar berada paling atas di grafik horizontal
        fig_top20.update_layout(
            showlegend=True, 
            yaxis_title="", 
            margin=dict(t=50, b=10),
            yaxis={'categoryorder': 'total ascending'} 
        )
        
        st.plotly_chart(fig_top20, width="stretch")
        
        with st.expander("📋 Lihat Tabel Top 20"):
            st.dataframe(top20)

# ───────────────────────────────────────────────────────────────
# TAB 7 — INSIGHT BISNIS
# ───────────────────────────────────────────────────────────────
with tab7:
    st.subheader("Ringkasan Insight Bisnis")
    st.info(
        """
        **1. Dominasi Pasar Amerika Utara (49%)**\n
        NA adalah pasar tunggal paling menguntungkan. Publisher yang ingin
        sukses global harus mengutamakan pelokalan dan pemasaran di NA.\n\n
        **2. Pasar Jepang Berbeda**\n
        Jepang memiliki preferensi kuat pada RPG dan kurang tertarik pada
        Shooter — berlawanan dengan NA/EU. Strategi dual-market diperlukan.\n\n
        **3. Genre Action adalah Raja — Tapi Bukan yang Paling Efisien**\n
        Action memimpin total penjualan tapi karena volume judul banyak.
        Platform dan Sports memiliki rata-rata per judul yang lebih tinggi.\n\n
        **4. PS2 adalah Platform Terbesar Sepanjang Sejarah**\n
        Dengan library terbesar dan harga terjangkau, PS2 melampaui semua
        platform lain.\n\n
        **5. Puncak Industri 2006–2009 (Era Motion Control)**\n
        Peluncuran Wii oleh Nintendo menciptakan gelombang baru pengguna kasual.\n\n
        **6. Nintendo = Publisher Paling Efisien**\n
        Nintendo menghasilkan penjualan tertinggi dengan strategi first-party
        quality-over-quantity.
        """
    )

# ───────────────────────────────────────────────────────────────
# TAB 8 — DOKUMENTASI
# ───────────────────────────────────────────────────────────────
with tab8:
    st.subheader("Dokumentasi Variabel & Fungsi")
    
    with st.expander("📌 Variabel Dataset (Kolom vgsales.csv)", expanded=False):
        var_doc = pd.DataFrame({
            "Variabel":    ["Rank", "Name", "Platform", "Year", "Genre",
                            "Publisher", "NA_Sales", "EU_Sales", "JP_Sales",
                            "Other_Sales", "Global_Sales"],
            "Tipe":        ["int", "str", "str", "int", "str",
                            "str", "float", "float", "float", "float", "float"],
            "Deskripsi":   [
                "Peringkat berdasarkan Global_Sales", "Judul game",
                "Platform / konsol", "Tahun rilis", "Genre permainan",
                "Penerbit / developer", "Penjualan di NA", "Penjualan di EU",
                "Penjualan di JP", "Penjualan di wilayah lain", "Total penjualan global"
            ]
        })
        st.dataframe(var_doc, width="stretch", hide_index=True)

    with st.expander("⚙️ Variabel Turunan (dibuat di kode)", expanded=False):
        derived_doc = pd.DataFrame({
            "Variabel":      ["df", "df_filtered", "year_sales", "genre_sales",
                              "platform_sales", "pub_sales", "region_totals",
                              "region_genre", "region_genre_melt", "top20"],
            "Deskripsi": [
                "DataFrame lengkap setelah cleaning",
                "Subset df setelah filter diterapkan",
                "Aggregasi penjualan per tahun",
                "Aggregasi genre: sales, games, avg",
                "Top 15 platform by sales",
                "Top 10 publisher by sales",
                "Total penjualan 4 wilayah",
                "Penjualan genre × wilayah (wide)",
                "Penjualan genre × wilayah (long)",
                "Top 20 game terlaris"
            ]
        })
        st.dataframe(derived_doc, width="stretch", hide_index=True)

    with st.expander("🔧 Fungsi dalam Kode", expanded=False):
        func_doc = pd.DataFrame({
            "Fungsi":       ["load_data()", "apply_filters()", "make_bar()"],
            "Return":       ["pd.DataFrame", "pd.DataFrame", "plotly.Figure"],
            "Deskripsi": [
                "Membaca & membersihkan data (di-cache).",
                "Menerapkan filter pada DataFrame.",
                "Helper membuat bar chart dengan Plotly."
            ]
        })
        st.dataframe(func_doc, width="stretch", hide_index=True)


#  FOOTER
st.divider()
st.caption(
    "📊 Dashboard dibuat dengan Streamlit + Plotly · "
    "Data: VGChartz via Kaggle · "
    "Analisis mencakup penjualan fisik; penjualan digital tidak termasuk."
)