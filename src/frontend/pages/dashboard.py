import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.utils.logging import get_logger
from src.frontend.components.visualization_widgets import plot_map

logger = get_logger(__name__)

def load_argo_data():
    """Load ARGO data from processed files"""
    try:
        # Use absolute path from project root
        import os
        # Go up from pages/ to frontend/ to src/ to project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        data_path = os.path.join(project_root, "data", "processed")
        
        logger.info(f"Looking for data in: {data_path}")
        logger.info(f"Files in data directory: {os.listdir(data_path) if os.path.exists(data_path) else 'Directory not found'}")
        
        df = pd.read_parquet(os.path.join(data_path, "argo_data.parquet"))
        metadata = pd.read_csv(os.path.join(data_path, "metadata.csv"))
        
        logger.info(f"Successfully loaded data: {df.shape} records, {metadata.shape} metadata entries")
        return df, metadata
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        st.error(f"Error loading data: {e}")
        return None, None

def plot_argo_trajectories(metadata):
    """Plot ARGO float trajectories on map"""
    fig = px.scatter_mapbox(
        metadata,
        lat="LATITUDE_min",
        lon="LONGITUDE_min",
        hover_name="PLATFORM_NUMBER",
        hover_data=["TIME_min", "TIME_max"],
        color_discrete_sequence=["red"],
        zoom=2,
        height=600
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        title="ARGO Float Locations (Indian Ocean Region)",
        margin={"r": 0, "t": 30, "l": 0, "b": 0}
    )
    return fig

def plot_depth_time_profile(df, float_id=None):
    """Plot depth-time profiles for temperature/salinity"""
    if float_id:
        df_filtered = df[df["PLATFORM_NUMBER"] == float_id]
    else:
        df_filtered = df
    
    fig = go.Figure()
    
    # Temperature profile
    fig.add_trace(go.Scatter(
        x=df_filtered["TIME"],
        y=df_filtered["PRES"],  # Pressure as depth proxy
        mode='markers',
        marker=dict(
            color=df_filtered["TEMP"],
            colorscale='Viridis',
            size=6,
            colorbar=dict(title="Temperature (°C)")
        ),
        name="Temperature",
        hovertemplate="Time: %{x}<br>Depth: %{y}<br>Temp: %{marker.color}<extra></extra>"
    ))
    
    fig.update_layout(
        title=f"Temperature-Depth-Time Profile {'for Float ' + str(float_id) if float_id else ''}",
        xaxis_title="Time",
        yaxis_title="Pressure (dbar)",
        yaxis=dict(autorange="reversed"),  # Depth increases downward
        height=500
    )
    
    return fig

def plot_salinity_comparison(df):
    """Compare salinity profiles across different floats"""
    # Sample a few floats for comparison
    unique_floats = df["PLATFORM_NUMBER"].unique()[:5]
    
    fig = go.Figure()
    
    for float_id in unique_floats:
        float_data = df[df["PLATFORM_NUMBER"] == float_id]
        fig.add_trace(go.Scatter(
            x=float_data["TIME"],
            y=float_data["PSAL"],
            mode='lines+markers',
            name=f"Float {float_id}",
            hovertemplate=f"Float {float_id}<br>Time: %{{x}}<br>Salinity: %{{y}}<extra></extra>"
        ))
    
    fig.update_layout(
        title="Salinity Profile Comparison Across ARGO Floats",
        xaxis_title="Time",
        yaxis_title="Salinity (PSU)",
        height=500
    )
    
    return fig

def display_data_summary(metadata):
    """Display summary statistics"""
    st.subheader("📊 Data Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Floats", len(metadata))
    
    with col2:
        st.metric("Date Range", f"{metadata['TIME_min'].min()} to {metadata['TIME_max'].max()}")
    
    with col3:
        lat_range = f"{metadata['LATITUDE_min'].min():.1f}° to {metadata['LATITUDE_max'].max():.1f}°"
        st.metric("Latitude Range", lat_range)
    
    with col4:
        lon_range = f"{metadata['LONGITUDE_min'].min():.1f}° to {metadata['LONGITUDE_max'].max():.1f}°"
        st.metric("Longitude Range", lon_range)

# Main Dashboard
st.set_page_config(
    page_title="FloatChat Dashboard",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 FloatChat - ARGO Ocean Data Dashboard")
st.markdown("**AI-Powered Conversational Interface for ARGO Ocean Data Discovery**")

# Navigation back to chat
if st.button("💬 Back to Chat Interface"):
    st.switch_page("chat_interface.py")

# Load data
df, metadata = load_argo_data()

if df is not None and metadata is not None:
    # Data Summary
    display_data_summary(metadata)
    
    st.divider()
    
    # Visualization Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map View", "📈 Depth Profiles", "🔬 Salinity Comparison", "📊 Data Export"])
    
    with tab1:
        st.subheader("ARGO Float Locations")
        fig_map = plot_argo_trajectories(metadata)
        st.plotly_chart(fig_map, use_container_width=True)
    
    with tab2:
        st.subheader("Temperature-Depth-Time Profiles")
        
        # Float selection
        float_options = ["All Floats"] + sorted(metadata["PLATFORM_NUMBER"].unique().tolist())
        selected_float = st.selectbox("Select Float ID:", float_options)
        
        if selected_float == "All Floats":
            fig_profile = plot_depth_time_profile(df)
        else:
            fig_profile = plot_depth_time_profile(df, selected_float)
        
        st.plotly_chart(fig_profile, use_container_width=True)
    
    with tab3:
        st.subheader("Salinity Profile Comparison")
        fig_salinity = plot_salinity_comparison(df)
        st.plotly_chart(fig_salinity, use_container_width=True)
    
    with tab4:
        st.subheader("📥 Data Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Export Metadata**")
            csv_data = metadata.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="argo_metadata.csv",
                mime="text/csv"
            )
        
        with col2:
            st.markdown("**Export Profile Data**")
            parquet_data = df.to_parquet()
            st.download_button(
                label="Download Parquet",
                data=parquet_data,
                file_name="argo_profiles.parquet",
                mime="application/octet-stream"
            )
        
        st.markdown("**Future Enhancement**: NetCDF export will be added for full compatibility with oceanographic standards.")

else:
    st.error("❌ Unable to load ARGO data. Please ensure data ingestion has been completed.")
    st.markdown("Run: `python src/data_ingestion/ingest_argo.py`")