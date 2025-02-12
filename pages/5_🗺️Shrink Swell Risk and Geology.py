import streamlit as st
import folium
from folium.plugins import Geocoder
from streamlit_folium import folium_static
import json

# Set up the page configuration
st.set_page_config(page_title="Postcode Data", page_icon="🗺️", layout="wide")

@st.cache_resource
def add_logo(logo_url: str, width: int = 250, height: int = 300):
    """Add a logo (from logo_url) on the top of the navigation page of a multipage app."""
    logo_css = f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: url({logo_url});
                background-repeat: no-repeat;
                background-size: {width}px {height}px; /* Set the size of the logo */
                padding-top: {height + 20}px;
                background-position: 20px 0px;
            }}
        </style>
    """
    st.markdown(logo_css, unsafe_allow_html=True)

st.sidebar.markdown("""
     Data visualisation of Shrink Swell Risk Map and proximity of Jurassic Geology
""")

# URL of the logo image
logo_url = "https://grmdevelopment.wpengine.com/wp-content/uploads/2020/07/GRM-master-logo-02.png"

# Add the logo with a specified height and resize using CSS
add_logo(logo_url, height=100)

st.markdown("## Shrink Swell Risk Map and Jurassic Geology Proxmity")

# Paths to the GeoJSON files
shrink_swell_file = 'ShrinkSwell.geojson'
jurassic_file = 'jurassic.geojson'

# Function to load GeoJSON content from a file
def load_geojson(file_path):
    try:
        with open(file_path, 'r') as file:
            geojson_data = json.load(file)
        return geojson_data
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

# Function to create color based on 'Legend' property
def get_color_legend(legend_value):
    color_mapping = {
        'Low': 'yellow',
        'Moderate': 'orange',
        'Significant': 'red'
    }
    return color_mapping.get(legend_value, 'grey')

# Function to create map with multiple GeoJSON layers
def create_map(shrink_swell_data, jurassic_data):
    # Create base map centered on a default location
    m = folium.Map(location=[54.0, -2.0], zoom_start=6)

    # Add Shrink Swell GeoJSON layer
    if shrink_swell_data:
        folium.GeoJson(
            shrink_swell_data,
            name="Shrink Swell",
            style_function=lambda feature: {
                'fillColor': get_color_legend(feature['properties'].get('Legend')),
                'color': 'transparent',
                'weight': 0,
                'fillOpacity': 0.5,
            },
        ).add_to(m)

    # Add Jurassic GeoJSON layer
    if jurassic_data:
        folium.GeoJson(
            jurassic_data,
            name="Jurassic",
            style_function=lambda feature: {
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.3,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['LEX_D'],
                aliases=['<b>Geology:</b>'],
                localize=True,
                sticky=True,
                direction='top',
                style=(
                    "background-color: white; "
                    "color: black; "
                    "font-size: 14px; "
                    "padding: 5px; "
                    "border-radius: 3px; "
                    "border: 1px solid black; "
                    "max-width: 300px; "  # Set a max width to control when text wraps
                    "white-space: normal;"  # Allow text to wrap onto multiple lines
                )
            )
        ).add_to(m)

    # Add Geocoder plugin
    Geocoder().add_to(m)

    return m

# Function to display the map and legend
def show_map_and_legend():
    # Create two columns
    col1, col2 = st.columns([4, 1.5])  # Adjust the ratio as needed

    with col1:
        shrink_swell_data = load_geojson(shrink_swell_file)
        jurassic_data = load_geojson(jurassic_file)
        m = create_map(shrink_swell_data, jurassic_data)
        folium_static(m, width=1000, height=800)  # Adjust size as needed

    with col2:
        st.markdown("""
        <div style="background-color: black; padding: 10px; border-radius: 5px; border: 1px solid #ddd;">
            <h3>Shrink Swell Risk</h3>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="background: yellow; width: 20px; height: 20px; margin-right: 10px; border: 1px solid black;"></div>
                <span>Low</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="background: orange; width: 20px; height: 20px; margin-right: 10px; border: 1px solid black;"></div>
                <span>Moderate</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="background: red; width: 20px; height: 20px; margin-right: 10px; border: 1px solid black;"></div>
                <span>Significant</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Show the map and legend
show_map_and_legend()