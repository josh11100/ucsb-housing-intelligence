"""
UCSB Housing Intelligence - Streamlit App
Interactive housing map with student-focused insights
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="UCSB Housing Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #003660 0%, #0055a2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Load data function with caching
@st.cache_data
def load_data():
    """Load enriched listings data"""
    try:
        df = pd.read_csv('data/geocoded/all_listings_geocoded.csv')
        df['available_date'] = pd.to_datetime(df['available_date'])
        df = df.dropna(subset=['latitude', 'longitude'])
        return df
    except FileNotFoundError:
        st.error("⚠️ No data found. Please run the data pipeline first!")
        st.stop()

def get_price_color(price):
    """Color code by price range"""
    if price < 2800:
        return 'green'
    elif price < 3500:
        return 'orange'
    else:
        return 'red'

def create_map(filtered_df):
    """Create interactive Folium map"""
    # Center on Isla Vista
    m = folium.Map(
        location=[34.4133, -119.8550],
        zoom_start=15,
        tiles='OpenStreetMap'
    )
    
    # Add UCSB campus marker
    folium.Marker(
        [34.4140, -119.8489],
        popup='UCSB Campus',
        icon=folium.Icon(color='blue', icon='university', prefix='fa'),
        tooltip='UCSB Main Campus'
    ).add_to(m)
    
    # Add Del Playa marker
    folium.Marker(
        [34.4133, -119.8610],
        popup='Del Playa (Party Zone)',
        icon=folium.Icon(color='red', icon='volume-up', prefix='fa'),
        tooltip='Del Playa - High Noise Area'
    ).add_to(m)
    
    # Add listing markers
    for idx, row in filtered_df.iterrows():
        # Create detailed popup
        popup_html = f"""
        <div style='width: 280px; font-family: Arial;'>
            <h4 style='color: #003660; margin-bottom: 10px;'>{row['address']}</h4>
            <hr style='margin: 10px 0;'>
            <p style='font-size: 18px; color: #d9534f;'><b>💰 ${row['price_monthly']:.0f}/month</b></p>
            <p><b>🛏️ Bedrooms:</b> {row['bedrooms']} | <b>🚿 Bathrooms:</b> {row['bathrooms']}</p>
            <p><b>👥 Capacity:</b> {row['person_capacity']} people</p>
            <hr style='margin: 10px 0;'>
            <p><b>📍 Walk to Campus:</b> {row['walk_time_to_campus_min']:.1f} minutes</p>
            <p><b>📏 Distance:</b> {row['distance_to_ucsb_meters']:.0f}m from UCSB</p>
            <p><b>🔊 Noise Level:</b> {row['noise_score']:.1f}/10</p>
            <p><b>📅 Available:</b> {row['available_date'].strftime('%B %d, %Y')}</p>
            <hr style='margin: 10px 0;'>
            <p><b>✨ Amenities:</b><br>{row['amenities']}</p>
            {'<p><b>🅿️ Parking:</b> $' + str(int(row['parking_cost_yearly'])) + '/year</p>' if row['parking_cost_yearly'] > 0 else ''}
            {'<p style="color: green;">✓ Remodeled</p>' if row['is_remodeled'] else ''}
            {'<p style="color: green;">✓ Balcony/Patio</p>' if row['has_balcony'] or row['has_patio'] else ''}
            <hr style='margin: 10px 0;'>
            <a href='{row['source_url']}' target='_blank' style='color: #0055a2;'>
                <b>View Original Listing →</b>
            </a>
        </div>
        """
        
        # Marker with color coding
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=10,
            popup=folium.Popup(popup_html, max_width=320),
            color=get_price_color(row['price_monthly']),
            fill=True,
            fillColor=get_price_color(row['price_monthly']),
            fillOpacity=0.7,
            weight=2,
            tooltip=f"${row['price_monthly']:.0f} - {row['bedrooms']}bed - Unit {row['unit_number']}"
        ).add_to(m)
    
    return m

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏠 UCSB Housing Intelligence</h1>
        <p style='font-size: 1.2rem; margin: 0;'>
            Student-focused housing insights for Isla Vista & Campus
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filter Listings")
    
    # Price range filter
    price_range = st.sidebar.slider(
        "Monthly Rent Range",
        int(df['price_monthly'].min()),
        int(df['price_monthly'].max()),
        (int(df['price_monthly'].min()), int(df['price_monthly'].max())),
        step=50
    )
    
    # Bedroom filter
    bedrooms = st.sidebar.multiselect(
        "Bedrooms",
        options=sorted(df['bedrooms'].dropna().unique()),
        default=sorted(df['bedrooms'].dropna().unique())
    )
    
    # Bathroom filter
    bathrooms = st.sidebar.multiselect(
        "Bathrooms",
        options=sorted(df['bathrooms'].dropna().unique()),
        default=sorted(df['bathrooms'].dropna().unique())
    )
    
    # Distance filter
    max_distance = st.sidebar.slider(
        "Max Walk Time to Campus (minutes)",
        0,
        int(df['walk_time_to_campus_min'].max()),
        int(df['walk_time_to_campus_min'].max()),
        step=1
    )
    
    # Noise tolerance
    max_noise = st.sidebar.slider(
        "Max Noise Level (0=Quiet, 10=Party Zone)",
        0.0,
        10.0,
        10.0,
        step=0.5
    )
    
    # Feature filters
    st.sidebar.subheader("🎯 Features")
    remodeled_only = st.sidebar.checkbox("Remodeled Only")
    parking_only = st.sidebar.checkbox("Parking Available")
    balcony_only = st.sidebar.checkbox("Balcony/Patio Only")
    
    # Availability filter
    st.sidebar.subheader("📅 Availability")
    date_range = st.sidebar.date_input(
        "Available Between",
        value=(df['available_date'].min().date(), df['available_date'].max().date()),
        min_value=df['available_date'].min().date(),
        max_value=df['available_date'].max().date()
    )
    
    # Apply filters
    filtered_df = df[
        (df['price_monthly'] >= price_range[0]) &
        (df['price_monthly'] <= price_range[1]) &
        (df['bedrooms'].isin(bedrooms)) &
        (df['bathrooms'].isin(bathrooms)) &
        (df['walk_time_to_campus_min'] <= max_distance) &
        (df['noise_score'] <= max_noise)
    ]
    
    if remodeled_only:
        filtered_df = filtered_df[filtered_df['is_remodeled'] == True]
    if parking_only:
        filtered_df = filtered_df[filtered_df['has_parking'] == True]
    if balcony_only:
        filtered_df = filtered_df[(filtered_df['has_balcony'] == True) | (filtered_df['has_patio'] == True)]
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['available_date'].dt.date >= date_range[0]) &
            (filtered_df['available_date'].dt.date <= date_range[1])
        ]
    
    # Main content area
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Listings Found", len(filtered_df))
    with col2:
        st.metric("💵 Avg Price", f"${filtered_df['price_monthly'].mean():.0f}")
    with col3:
        st.metric("🚶 Avg Walk Time", f"{filtered_df['walk_time_to_campus_min'].mean():.1f} min")
    with col4:
        st.metric("🔊 Avg Noise", f"{filtered_df['noise_score'].mean():.1f}/10")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map View", "📊 Analytics", "📋 Listings Table", "ℹ️ About"])
    
    with tab1:
        st.subheader("Interactive Housing Map")
        
        if len(filtered_df) > 0:
            # Create and display map
            m = create_map(filtered_df)
            st_folium(m, width=1200, height=600)
            
            # Legend
            st.markdown("""
            **Map Legend:**
            - 🟢 **Green**: Under $2,800/month (Budget-friendly)
            - 🟠 **Orange**: $2,800-$3,500/month (Mid-range)
            - 🔴 **Red**: Over $3,500/month (Premium)
            - 🔵 **Blue Pin**: UCSB Campus
            - 🔴 **Red Pin**: Del Playa (High noise area)
            """)
        else:
            st.warning("No listings match your filters. Try adjusting the criteria.")
    
    with tab2:
        st.subheader("📊 Housing Market Analytics")
        
        if len(filtered_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # Price distribution
                fig_price = px.histogram(
                    filtered_df,
                    x='price_monthly',
                    nbins=30,
                    title="Price Distribution",
                    labels={'price_monthly': 'Monthly Rent ($)'},
                    color_discrete_sequence=['#003660']
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
                # Noise vs Price scatter
                fig_noise = px.scatter(
                    filtered_df,
                    x='noise_score',
                    y='price_monthly',
                    size='bedrooms',
                    color='bedrooms',
                    title="Noise Level vs Price",
                    labels={'noise_score': 'Noise Score', 'price_monthly': 'Price ($)'},
                    hover_data=['address', 'bedrooms']
                )
                st.plotly_chart(fig_noise, use_container_width=True)
            
            with col2:
                # Bedrooms breakdown
                bedroom_counts = filtered_df['bedrooms'].value_counts().sort_index()
                fig_beds = px.pie(
                    values=bedroom_counts.values,
                    names=bedroom_counts.index,
                    title="Listings by Bedroom Count",
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                st.plotly_chart(fig_beds, use_container_width=True)
                
                # Distance vs Price
                fig_distance = px.scatter(
                    filtered_df,
                    x='distance_to_ucsb_meters',
                    y='price_monthly',
                    color='noise_score',
                    size='bedrooms',
                    title="Distance to Campus vs Price",
                    labels={'distance_to_ucsb_meters': 'Distance to UCSB (m)', 'price_monthly': 'Price ($)'},
                    hover_data=['address', 'walk_time_to_campus_min']
                )
                st.plotly_chart(fig_distance, use_container_width=True)
            
            # Availability timeline
            st.subheader("📅 Availability Timeline")
            avail_counts = filtered_df.groupby(filtered_df['available_date'].dt.to_period('M')).size()
            fig_timeline = px.bar(
                x=avail_counts.index.astype(str),
                y=avail_counts.values,
                title="Listings Available by Month",
                labels={'x': 'Month', 'y': 'Number of Listings'},
                color_discrete_sequence=['#0055a2']
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
    
    with tab3:
        st.subheader("📋 All Listings")
        
        if len(filtered_df) > 0:
            # Display options
            show_columns = st.multiselect(
                "Select columns to display:",
                options=filtered_df.columns.tolist(),
                default=['address', 'unit_number', 'price_monthly', 'bedrooms', 'bathrooms', 
                        'walk_time_to_campus_min', 'noise_score', 'available_date', 'amenities']
            )
            
            # Sort options
            sort_by = st.selectbox("Sort by:", options=['price_monthly', 'walk_time_to_campus_min', 
                                                        'noise_score', 'available_date', 'bedrooms'])
            sort_order = st.radio("Order:", ['Ascending', 'Descending'], horizontal=True)
            
            # Apply sorting
            display_df = filtered_df[show_columns].sort_values(
                by=sort_by,
                ascending=(sort_order == 'Ascending')
            )
            
            # Display table
            st.dataframe(
                display_df,
                use_container_width=True,
                height=600,
                hide_index=True
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"ucsb_housing_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No listings to display with current filters.")
    
    with tab4:
        st.subheader("ℹ️ About This Project")
        
        st.markdown("""
        ### UCSB Housing Intelligence Platform
        
        This is a **student-focused housing intelligence layer** for UCSB and Isla Vista. 
        Unlike generic rental sites, this platform provides insights that matter to students:
        
        #### 🎯 Key Features:
        - **Distance Intelligence**: Actual walking times to campus, not just "close to UCSB"
        - **Noise Scoring**: Proximity to Del Playa and party zones (0=quiet, 10=loud)
        - **Student Context**: Parking availability, amenities, remodel status
        - **Availability Tracking**: See when units become available
        - **Price Analytics**: Compare pricing across different areas
        
        #### 📊 Data Sources:
        - Kamap Property Management (current)
        - More sources coming soon!
        
        #### 🔗 Important Notes:
        - This platform **never replaces** the original listings
        - All listings link directly to the property management site to apply
        - Data is updated regularly (last update: {})
        
        #### 🛠️ Built With:
        - Python, Streamlit, Folium, Plotly
        - Geospatial analysis with GeoPy
        - PDF parsing and NLP for amenity extraction
        
        ---
        
        **Questions or feedback?** This is a student project for UCSB housing data science.
        """.format(datetime.now().strftime('%B %d, %Y')))
        
        # Fun stats
        st.subheader("📈 Platform Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Units Tracked", len(df))
        with col2:
            st.metric("Buildings Covered", df['address'].nunique())
        with col3:
            st.metric("Avg Monthly Rent", f"${df['price_monthly'].mean():.0f}")

if __name__ == "__main__":
    main()
