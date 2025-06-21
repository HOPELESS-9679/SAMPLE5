import streamlit as st
import pandas as pd
import folium
import json
from geopy.distance import geodesic
from folium.plugins import LocateControl
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Nursery Locator", layout="wide")
st.title("🌱 Nursery Locator with Distance & Live Location")

# 🔹 Load nursery data
df = pd.read_excel("NURSARY.xlsx")
required_cols = ['Name', 'Latitude', 'Longitude', 'Capacity', 'PlantsAvailable', 'Contact']
if not all(col in df.columns for col in required_cols):
    st.error("❌ Excel must include: " + ", ".join(required_cols))
    st.stop()

# 🔹 Load Khariar division boundary (optional)
try:
    with open("khariar_boundary.geojson", "r") as f:
        khariar_geojson = json.load(f)
except:
    khariar_geojson = None

# 🧭 Try to get user location from browser
st.subheader("📍 Detecting your location...")
loc = streamlit_js_eval(
    js_expressions="navigator.geolocation.getCurrentPosition((pos) => pos.coords)",
    key="get_user_location"
)

# If allowed, use it — else fallback
if loc and "latitude" in loc and "longitude" in loc:
    user_location = (loc["latitude"], loc["longitude"])
    st.success(f"✅ Your location: {user_location}")
else:
    user_location = (20.5600, 84.1400)
    st.warning("⚠️ Location not shared. Using fallback: Khariar")

# 🗺️ Initialize map
m = folium.Map(location=user_location, zoom_start=12)
LocateControl(auto_start=True).add_to(m)

# Draw boundary (optional)
if khariar_geojson:
    folium.GeoJson(
        khariar_geojson,
        name="Khariar Boundary",
        style_function=lambda x: {
            "fillColor": "yellow",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(m)

# 📍 Add user marker
folium.Marker(
    location=user_location,
    tooltip="Your Location",
    icon=folium.Icon(color="blue", icon="user")
).add_to(m)

# 🟢 Add nursery markers with tooltip = Name
for _, row in df.iterrows():
    popup = f"""
    <b>{row['Name']}</b><br>
    Capacity: {row['Capacity']}<br>
    Plants Available: {row['PlantsAvailable']}<br>
    Contact: {row['Contact']}
    """
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        tooltip=row['Name'],
        popup=popup,
        icon=folium.Icon(color="green", icon="leaf")
    ).add_to(m)

# 🔁 Draw lines and distances to each nursery
df['Distance_km'] = df.apply(
    lambda row: geodesic(user_location, (row['Latitude'], row['Longitude'])).km,
    axis=1
)
for _, row in df.iterrows():
    dist = row['Distance_km']
    loc = (row['Latitude'], row['Longitude'])
    folium.PolyLine([user_location, loc], color="gray", weight=1).add_to(m)
    folium.Marker(
        location=loc,
        icon=folium.DivIcon(html=f"""<div style="font-size: 10pt; color: black;">{dist:.2f} km</div>""")
    ).add_to(m)

# 🔍 Detect which marker is clicked
st.subheader("🗺️ Click a nursery to view details and distance")
map_data = st_folium(m, width=1000, height=600)

# 🎯 Show clicked nursery details
if map_data and map_data.get("last_object_clicked_tooltip"):
    clicked_name = map_data["last_object_clicked_tooltip"]
    clicked_row = df[df['Name'] == clicked_name].iloc[0]
    distance_km = geodesic(user_location, (clicked_row['Latitude'], clicked_row['Longitude'])).km

    st.success(f"📍 {clicked_name} – {distance_km:.2f} km away")
    st.markdown(f"""
    **Capacity:** {clicked_row['Capacity']}  
    **Plants Available:** {clicked_row['PlantsAvailable']}  
    **Contact:** {clicked_row['Contact']}
    """)
else:
    st.info("Click on a nursery marker to see distance and details.")
