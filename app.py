import pandas as pd
import json
from datetime import datetime
import folium
import streamlit as st
from streamlit_folium import st_folium
import plotly.express as px

# Load the JSON data
@st.cache_data
def load_data():
    try:
        with open('jdata/somalia.json') as f:
            data = json.load(f)
        return pd.json_normalize(data['data'])
    except FileNotFoundError:
        st.error("File not found. Please check the path.")
        return pd.DataFrame()
    except json.JSONDecodeError:
        st.error("Error decoding JSON. Please check the file format.")
        return pd.DataFrame()

df = load_data()

# Convert relevant fields and handle missing data
def preprocess_data(df):
    # Convert dates
    df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
    
    # Convert numerical fields
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['fatalities'] = pd.to_numeric(df['fatalities'], errors='coerce')
    
    # Fill missing or empty strings
    df.fillna('', inplace=True)
    
    return df

df = preprocess_data(df)

# Example function: Get event count by type
def get_event_count_by_type(df):
    return df.groupby('event_type').size().reset_index(name='count')

# Example function: Get total fatalities
def get_total_fatalities(df):
    return df['fatalities'].sum()

# Example function: Get events over time
def get_event_trend_over_time(df):
    df['event_month'] = df['event_date'].dt.to_period('M').dt.to_timestamp()  # Convert Period to Timestamp
    df_trend = df.groupby('event_month').size().reset_index(name='event_count')
    return df_trend

def create_map(df):
    if df['latitude'].isnull().all() or df['longitude'].isnull().all():
        st.error("No valid geospatial data available.")
        return folium.Map(location=[0, 0], zoom_start=2)  # Default location
    
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=6)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color='blue' if row['event_type'] == 'Violence against civilians' else 'red',
            fill=True,
            fill_color='blue' if row['event_type'] == 'Violence against civilians' else 'red',
            fill_opacity=0.6
        ).add_to(m)
    return m

def plot_event_trend(df):
    df_trend = get_event_trend_over_time(df)
    fig = px.line(df_trend, x='event_month', y='event_count', title='Event Trend Over Time')
    return fig

def analyze_actors(df):
    actor1_counts = df['actor1'].value_counts()
    actor2_counts = df['actor2'].value_counts()
    return actor1_counts, actor2_counts

def disorder_event_correlation(df):
    correlation = pd.crosstab(df['disorder_type'], df['event_type'])
    return correlation

def plot_fatality_distribution(df):
    fig = px.bar(df, x='event_type', y='fatalities', title='Fatality Distribution by Event Type')
    return fig

# Streamlit app
st.title('Conflict Event Dashboard')

# Geospatial Map
st.subheader('Event Location Map')
map_ = create_map(df)
st_folium(map_)

# Event Trend Over Time
st.subheader('Event Trend Over Time')
event_trend_fig = plot_event_trend(df)
st.plotly_chart(event_trend_fig)

# Actor Analysis
st.subheader('Actor Involvement Analysis')
actor1_counts, actor2_counts = analyze_actors(df)
st.write('Actor1 Counts:', actor1_counts)
st.write('Actor2 Counts:', actor2_counts)

# Disorder vs Event Types
st.subheader('Disorder vs Event Types')
correlation = disorder_event_correlation(df)
st.write(correlation)

# Fatality Distribution
st.subheader('Fatality Distribution by Event Type')
fatality_dist_fig = plot_fatality_distribution(df)
st.plotly_chart(fatality_dist_fig)
