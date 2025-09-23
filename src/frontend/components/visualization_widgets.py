import folium
from streamlit_folium import st_folium

def plot_map(df):
    m = folium.Map(location=[0, 90], zoom_start=5)
    for _, row in df.iterrows():
        folium.Marker([row["latitude"], row["longitude"]], popup=row["float"]).add_to(m)
    return st_folium(m)