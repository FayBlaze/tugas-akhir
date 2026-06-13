import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Hotel Booking BI Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema dan Judul
st.title("🏨 Hotel Booking Business Intelligence Dashboard")
st.markdown("Dashboard interaktif untuk menganalisis demand, revenue, dan cancellation pada pemesanan hotel.")
st.markdown("---")

# ==========================================
# DATA PREPROCESSING
# ==========================================
@st.cache_data
def load_data():
    # Membaca data
    try:
        df = pd.read_csv('hotel_bookings.csv')
    except FileNotFoundError:
        st.error("File 'hotel_bookings.csv' tidak ditemukan. Pastikan file berada di direktori yang sama dengan app.py.")
        st.stop()
        
    # Membersihkan data yang kosong (Null handling)
    df.fillna({'children': 0, 'country': 'Unknown', 'agent': 0, 'company': 0}, inplace=True)
    
    # Mapping nama bulan ke angka untuk membuat datetime
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 
        'May': 5, 'June': 6, 'July': 7, 'August': 8, 
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['arrival_month_num'] = df['arrival_date_month'].map(month_map)
    
    # Membuat kolom arrival_date
    df['arrival_date'] = pd.to_datetime(
        df['arrival_date_year'].astype(str) + '-' + 
        df['arrival_month_num'].astype(str) + '-' + 
        df['arrival_date_day_of_month'].astype(str), 
        errors='coerce'
    )
    
    # Membuat kolom Revenue
    df['Revenue'] = df['adr'] * (df['stays_in_week_nights'] + df['stays_in_weekend_nights'])
    
    # Menghapus revenue negatif atau tidak masuk akal jika ada
    df = df[df['Revenue'] >= 0]
    
    return df

df = load_data()

# ==========================================
# SIDEBAR FILTERS
# ==========================================
st.sidebar.header("🎯 Filter Data")

# Filter Hotel
hotel_list = df['hotel'].unique()
selected_hotels = st.sidebar.multiselect("Pilih Hotel", hotel_list, default=hotel_list)

# Filter Tahun
year_list = sorted(df['arrival_date_year'].unique())
selected_years = st.sidebar.multiselect("Pilih Tahun", year_list, default=year_list)

# Filter Market Segment
segment_list = df['market_segment'].unique()
selected_segments = st.sidebar.multiselect("Pilih Market Segment", segment_list, default=segment_list)

# Terapkan filter ke dataframe
filtered_df = df[
    (df['hotel'].isin(selected_hotels)) &
    (df['arrival_date_year'].isin(selected_years)) &
    (df['market_segment'].isin(selected_segments))
]

if filtered_df.empty:
    st.warning("⚠️ Data tidak ditemukan berdasarkan filter yang dipilih.")
    st.stop()

# ==========================================
# SECTION 1 - EXECUTIVE SUMMARY
# ==========================================
st.subheader("📊 Executive Summary")

total_booking = len(filtered_df)
total_revenue = filtered_df['Revenue'].sum()
average_adr = filtered_df['adr'].mean()
cancellation_rate = (filtered_df['is_canceled'].sum() / total_booking) * 100 if total_booking > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Booking", value=f"{total_booking:,.0f}")
with col2:
    st.metric(label="Total Revenue", value=f"${total_revenue:,.2f}")
with col3:
    st.metric(label="Average ADR", value=f"${average_adr:,.2f}")
with col4:
    st.metric(label="Cancellation Rate", value=f"{cancellation_rate:.2f}%")

st.markdown("---")

# Menggunakan Tabs untuk struktur Dashboard
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 Customer Analysis", 
    "💰 Revenue Analysis", 
    "🚫 Cancellation Analysis", 
    "💡 Business Insights & Recs", 
    "🤖 Predictive Analytics"
])

# ==========================================
# SECTION 2 - CUSTOMER ANALYSIS
# ==========================================
with tab1:
    st.subheader("👥 Customer Analysis")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        # Top 10 Country
        top_countries = filtered_df['country'].value_counts().head(10).reset_index()
        top_countries.columns = ['Country', 'Total Booking']
        fig_country = px.bar(top_countries, x='Country', y='Total Booking', title="Top 10 Countries by Booking", color='Total Booking', color_continuous_scale='Blues')
        st.plotly_chart(fig_country, use_container_width=True)
        
    with col_c2:
        # Customer Type Distribution
        if 'customer_type' in filtered_df.columns:
            cust_type = filtered_df['customer_type'].value_counts().reset_index()
            cust_type.columns = ['Customer Type', 'Count']
            fig_cust = px.pie(cust_type, names='Customer Type', values='Count', title="Customer Type Distribution", hole=0.4)
            st.plotly_chart(fig_cust, use_container_width=True)
        else:
            st.info("Kolom 'customer_type' tidak tersedia di dataset.")

    # Repeat Guest Analysis
    if 'is_repeated_guest' in filtered_df.columns:
        repeat_guest = filtered_df['is_repeated_guest'].replace({0: 'New Guest', 1: 'Repeated Guest'}).value_counts().reset_index()
        repeat_guest.columns = ['Guest Type', 'Count']
        fig_repeat = px.pie(repeat_guest, names='Guest Type', values='Count', title="Repeat Guest Analysis", hole=0.4, color_discrete_sequence=['#ff9999','#66b3ff'])
        st.plotly_chart(fig_repeat, use_container_width=True)

# ==========================================
# SECTION 3 - REVENUE ANALYSIS
# ==========================================
with tab2:
    st.subheader("💰 Revenue Analysis")
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        # Revenue by Hotel
        rev_hotel = filtered_df.groupby('hotel')['Revenue'].sum().reset_index()
        fig_rev_hotel = px.bar(rev_hotel, x='hotel', y='Revenue', title="Revenue by Hotel", color='hotel')
        st.plotly_chart(fig_rev_hotel, use_container_width=True)
        
    with col_r2:
        # Revenue by Market Segment
        rev_segment = filtered_df.groupby('market_segment')['Revenue'].sum().reset_index().sort_values(by='Revenue', ascending=False)
        fig_rev_segment = px.bar(rev_segment, x='market_segment', y='Revenue', title="Revenue by Market Segment", color='market_segment')
        st.plotly_chart(fig_rev_segment, use_container_width=True)
        
    # Revenue Trend per Month
    rev_trend = filtered_df.groupby(['arrival_date_year', 'arrival_date_month', 'arrival_month_num'])['Revenue'].sum().reset_index()
    rev_trend = rev_trend.sort_values(by=['arrival_date_year', 'arrival_month_num'])
    rev_trend['Year-Month'] = rev_trend['arrival_date_year'].astype(str) + " - " + rev_trend['arrival_date_month']
    
    fig_rev_trend = px.line(rev_trend, x='Year-Month', y='Revenue', title="Revenue Trend per Month", markers=True)
    st.plotly_chart(fig_rev_trend, use_container_width=True)

# ==========================================
# SECTION 4 - CANCELLATION ANALYSIS
# ==========================================
with tab3:
    st.subheader("🚫 Cancellation Analysis")
    
    col_ca1, col_ca2 = st.columns(2)
    
    with col_ca1:
        # Cancellation Rate per Hotel
        cancel_hotel = filtered_df.groupby('hotel')['is_canceled'].mean().reset_index()
        cancel_hotel['is_canceled'] = cancel_hotel['is_canceled'] * 100 # ubah ke persen
        fig_cancel_hotel = px.bar(cancel_hotel, x='hotel', y='is_canceled', title="Cancellation Rate per Hotel (%)", color='hotel', text_auto='.2f')
        fig_cancel_hotel.update_traces(textposition="outside")
        st.plotly_chart(fig_cancel_hotel, use_container_width=True)
        
    with col_ca2:
        # Market Segment vs Cancellation
        cancel_segment = filtered_df.groupby(['market_segment', 'is_canceled']).size().reset_index(name='count')
        cancel_segment['is_canceled'] = cancel_segment['is_canceled'].replace({0: 'Not Canceled', 1: 'Canceled'})
        fig_cancel_segment = px.bar(cancel_segment, x='market_segment', y='count', color='is_canceled', title="Market Segment vs Cancellation", barmode='group')
        st.plotly_chart(fig_cancel_segment, use_container_width=True)
        
    # Lead Time vs Cancellation
    fig_lead_time = px.histogram(filtered_df, x="lead_time", color="is_canceled", title="Lead Time Distribution vs Cancellation", nbins=50, barmode="overlay")
    st.plotly_chart(fig_lead_time, use_container_width=True)

# ==========================================
# SECTION 5 & 6 - BUSINESS INSIGHTS & RECS
# ==========================================
with tab4:
    col_ins1, col_ins2 = st.columns(2)
    
    with col_ins1:
        st.subheader("💡 Automated Business Insights")
        
        # Cari Hotel dengan cancel tertinggi
        if total_booking > 0:
            highest_cancel_hotel = filtered_df.groupby('hotel')['is_canceled'].mean().idxmax()
            highest_cancel_rate = filtered_df.groupby('hotel')['is_canceled'].mean().max() * 100
            st.warning(f"**Hotel dengan Cancellation Tertinggi:** {highest_cancel_hotel} ({highest_cancel_rate:.2f}%)")
            
            # Segment dengan revenue terbesar
            top_revenue_segment = filtered_df.groupby('market_segment')['Revenue'].sum().idxmax()
            top_revenue_value = filtered_df.groupby('market_segment')['Revenue'].sum().max()
            st.success(f"**Segment Revenue Terbesar:** {top_revenue_segment} (${top_revenue_value:,.2f})")
            
            # Negara dengan booking terbanyak
            top_country = filtered_df['country'].value_counts().idxmax()
            top_country_bookings = filtered_df['country'].value_counts().max()
            st.info(f"**Negara Booking Terbanyak:** {top_country} ({top_country_bookings:,} bookings)")
        else:
            st.write("Belum ada data untuk dianalisis.")

    with col_ins2:
        st.subheader("📈 Business Recommendations")
        st.markdown("""
        Berdasarkan analisis tren dan data historis, berikut rekomendasi strategis:
        
        * **Terapkan Kebijakan Deposit Fleksibel:** Mengingat tingginya angka pembatalan pada reservasi dengan *lead time* yang lama, terapkan sistem deposit progresif untuk mengunci komitmen tamu.
        * **Tingkatkan Kampanye Direct Booking:** Kurangi ketergantungan pada Online Travel Agents (OTA) dengan memberikan insentif (seperti diskon atau welcome drink) bagi tamu yang memesan langsung via website hotel.
        * **Program Loyalitas untuk Repeat Guests:** Tamu yang kembali (*repeated guests*) terbukti memiliki *cancellation rate* yang rendah. Buat program member/loyalitas khusus.
        * **Promosi Agresif di Low Season:** Analisis revenue bulanan menunjukkan adanya celah (*drop*) di beberapa bulan tertentu. Fokuskan budget marketing pada periode tersebut.
        """)

# ==========================================
# SECTION 7 - PREDICTIVE ANALYTICS
# ==========================================
with tab5:
    st.subheader("🤖 Predictive Analytics: Cancellation Predictor")
    st.markdown("Menggunakan Machine Learning (Random Forest) untuk memprediksi probabilitas pembatalan berdasarkan pola booking historis.")
    
    features = ['lead_time', 'adr', 'adults', 'children']
    target = 'is_canceled'
    
    # Periksa ketersediaan fitur
    if all(col in filtered_df.columns for col in features + [target]):
        ml_data = filtered_df[features + [target]].dropna()
        
        if len(ml_data) > 100: # Cukup data untuk training
            X = ml_data[features]
            y = ml_data[target]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train Model
            rf_model = RandomForestClassifier(n_estimators=50, random_state=42)
            rf_model.fit(X_train, y_train)
            
            # Prediksi dan Akurasi
            y_pred = rf_model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                st.metric(label="🤖 Model Accuracy Score", value=f"{acc*100:.2f}%")
                st.write("Model berhasil dilatih menggunakan algoritma Random Forest Classifier.")
                
            with col_m2:
                # Feature Importance
                importances = rf_model.feature_importances_
                feat_df = pd.DataFrame({'Feature': features, 'Importance': importances}).sort_values(by='Importance', ascending=False)
                fig_feat = px.bar(feat_df, x='Importance', y='Feature', orientation='h', title="Feature Importance")
                st.plotly_chart(fig_feat, use_container_width=True)
                
        else:
            st.warning("⚠️ Data setelah difilter terlalu sedikit untuk melatih model Machine Learning.")
    else:
        st.error("Kolom fitur yang dibutuhkan untuk Prediksi tidak ditemukan.")