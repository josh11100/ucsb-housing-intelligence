# UCSB Housing Intelligence Platform

Student-focused housing search tool for UCSB and Isla Vista.

## Features
- Interactive map with all available housing
- Distance to campus calculations
- Noise level scoring (Del Playa proximity)
- Price analytics and filtering
- Direct links to property management sites

## Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Place PDF in data/raw/
# Copy kamap_availability.pdf to data/raw/

# Process data
python pipeline.py

# Launch app
streamlit run app.py
```

## Data Sources
- Kamap Property Management
- More coming soon!

## Tech Stack
- Python, Streamlit
- Folium (maps), Plotly (charts)
- GeoPy (geocoding), Pandas (data)
