"""
Kamap Property Management PDF Parser
Extracts listings with all metadata
"""

import re
import pandas as pd
from datetime import datetime
import pdfplumber

class KamapParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.current_year = 2026
        self.listings = []
        
    def extract_text(self):
        """Extract text from PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    
    def parse_unit_numbers(self, unit_text):
        """Extract unit numbers and dates"""
        pattern = r'(\w+)\s*\((\d{1,2}/\d{1,2})\)'
        matches = re.findall(pattern, unit_text)
        
        units = []
        for unit_num, date_str in matches:
            try:
                month, day = map(int, date_str.split('/'))
                available_date = datetime(self.current_year, month, day)
                units.append({
                    'unit_number': unit_num,
                    'available_date': available_date
                })
            except ValueError:
                continue
        
        return units
    
    def parse_price(self, price_str):
        """Extract numeric price"""
        match = re.search(r'\$?([\d,]+)', price_str)
        if match:
            return float(match.group(1).replace(',', ''))
        return None
    
    def parse_room_type(self, room_str):
        """Parse bedroom/bathroom configuration"""
        bed_match = re.search(r'(\d+)\s*(Bed|Singles?|Person)', room_str)
        bath_match = re.search(r'(\d+(?:\.\d+)?)\s*Bath', room_str)
        
        beds = int(bed_match.group(1)) if bed_match else None
        baths = float(bath_match.group(1)) if bath_match else None
        room_type = bed_match.group(2) if bed_match else "Unknown"
        
        return {
            'bedrooms': beds,
            'bathrooms': baths,
            'room_type': room_type,
            'person_capacity': beds
        }
    
    def extract_features(self, description):
        """Extract amenities and boolean features"""
        features = {
            'is_remodeled': bool(re.search(r'Remodeled', description, re.I)),
            'has_balcony': bool(re.search(r'Balcony', description, re.I)),
            'has_patio': bool(re.search(r'Patio', description, re.I)),
            'has_parking': bool(re.search(r'Parking Available', description, re.I)),
            'split_floor_plan': bool(re.search(r'Split Floor Plan', description, re.I)),
        }
        
        # Parking cost
        parking_cost_match = re.search(r'\$(\d+)\s*per year', description)
        features['parking_cost_yearly'] = float(parking_cost_match.group(1)) if parking_cost_match else 0
        
        # Amenities
        amenities = []
        if re.search(r'Free.*Internet', description, re.I):
            amenities.append('Free Internet')
        if re.search(r'Water.*Trash|Trash.*Water', description, re.I):
            amenities.append('Water/Trash Included')
        if re.search(r'Washer.*Dryer', description, re.I):
            amenities.append('In-Unit Washer/Dryer')
        if re.search(r'Gas', description, re.I):
            amenities.append('Gas Included')
            
        features['amenities'] = ', '.join(amenities) if amenities else 'None listed'
        
        return features
    
    def parse_all(self):
        """Main parsing logic"""
        text = self.extract_text()
        
        # Common IV street names for Kamap
        address_pattern = r'(\d{4,5}\s+(?:Cordoba|Abrego|El Nido|Segovia|Sabado Tarde|Trigo|Picasso|Pasado|Camino Corto|Embarcadero del Norte)(?:\s+(?:Rd|St|Ave|Dr|Ln))?)'
        
        current_address = None
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Check for address
            addr_match = re.search(address_pattern, line, re.I)
            if addr_match:
                current_address = addr_match.group(1)
                continue
            
            # Parse listing lines
            if line.startswith('$') and current_address:
                self._parse_listing_line(line, current_address)
        
        return self.listings
    
    def _parse_listing_line(self, line, address):
        """Parse individual listing line"""
        parts = line.split(' ', 1)
        if len(parts) < 2:
            return
            
        price = self.parse_price(parts[0])
        rest = parts[1]
        
        # Find unit section
        unit_match = re.search(r'Unit[s]?\s*#', rest)
        if not unit_match:
            return
        
        room_part = rest[:unit_match.start()].strip()
        unit_part = rest[unit_match.end():].strip()
        
        room_info = self.parse_room_type(room_part)
        units = self.parse_unit_numbers(unit_part)
        features = self.extract_features(line + ' ' + unit_part)
        
        # Create listing for each unit
        for unit_info in units:
            listing = {
                'listing_id': f"kamap_{address.replace(' ', '_')}_{unit_info['unit_number']}".lower(),
                'property_management': 'Kamap Property Management',
                'address': f"{address}, Isla Vista, CA 93117",
                'unit_number': unit_info['unit_number'],
                'price_monthly': price,
                'available_date': unit_info['available_date'],
                'source_url': 'https://www.kamap.net/',
                'scraped_date': datetime.now(),
                **room_info,
                **features,
                'description': line.strip()
            }
            
            self.listings.append(listing)
    
    def to_dataframe(self):
        """Convert to DataFrame"""
        return pd.DataFrame(self.listings)
    
    def save_to_csv(self, output_path):
        """Save to CSV"""
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
        print(f"✅ Saved {len(df)} listings to {output_path}")
        return df
