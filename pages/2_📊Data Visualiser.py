from pygwalker.api.streamlit import StreamlitRenderer
import pandas as pd
import streamlit as st

# Adjust the width of the Streamlit page
st.set_page_config(
    page_title="Custom Data Visualisation by attributes",
    layout="wide",
    page_icon=":bar_chart:"
)

st.markdown("## Custom Data Visualisation by attributes")

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

     This app allows you to further explore the data by allowing you to manipulate the data in any way you want. 
     
     You can use this tool to compare any data fields and produce any desired output, such as bar charts, scatter plots 
     and custom tables, in order to personalise your analysis and discover trends in the data.
     
     There are options to export to CSV or image formats.
""")

# URL of the logo image
logo_url = "https://grmdevelopment.wpengine.com/wp-content/uploads/2020/07/GRM-master-logo-02.png"

# Add the logo with a specified height and resize using CSS
add_logo(logo_url, height=100)

# Import your data
df = pd.read_csv("Pointdate.csv")

df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values(by='Date')


pyg_app = StreamlitRenderer(df)

pyg_app.explorer()
