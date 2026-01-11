"""
Complete data pipeline
Run this to process new data before launching the app
"""

import os
import sys
from src.parsers.kamap_parser import KamapParser
from src.enrichment.geocoder import AddressGeocoder
from src.enrichment.features import FeatureEngineer

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        'data/raw',
        'data/processed',
        'data/geocoded'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_pipeline():
    """Execute complete pipeline"""
    print("🚀 UCSB Housing Intelligence - Data Pipeline\n")
    
    ensure_directories()
    
    # Step 1: Parse
    print("📄 Step 1: Parsing Kamap PDF...")
    parser = KamapParser('data/raw/kamap_availability.pdf')
    parser.parse_all()
    df = parser.save_to_csv('data/processed/kamap_processed.csv')
    print(f"   ✅ Parsed {len(df)} listings\n")
    
    # Step 2: Geocode
    print("🗺️  Step 2: Geocoding addresses...")
    geocoder = AddressGeocoder()
    df_geo = geocoder.geocode_dataframe(df)
    df_geo.to_csv('data/geocoded/kamap_geocoded.csv', index=False)
    
    # Step 3: Enrich
    print("🔧 Step 3: Engineering features...")
    engineer = FeatureEngineer()
    df_final = engineer.enrich_dataframe(df_geo)
    df_final.to_csv('data/geocoded/all_listings_geocoded.csv', index=False)
    
    print("\n✨ Pipeline complete! Data ready for Streamlit app.")
    print("   Run: streamlit run app.py")

if __name__ == "__main__":
    run_pipeline()
