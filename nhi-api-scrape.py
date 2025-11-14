import requests
import csv
import time
import json

# Configuration
API_URL = 'https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search'
OUTPUT_FILE = 'icd10_codes_complete.csv'

def fetch_all_codes_paginated():
    """
    Fetch all ICD-10 codes using pagination
    The API returns codes in batches, we need to paginate through all results
    """
    all_codes = []
    max_list = 7000  # Max per request
    
    print('Fetching all ICD-10 codes from NIH API...')
    print('This may take a few minutes...\n')
    
    # Start with empty search to get all codes
    params = {
        'terms': '',           # Empty = get all
        'maxList': max_list,   # Max results
        'df': 'code,name'      # Display format: code and name
    }
    
    try:
        print('Making API request...')
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f'API Response structure: {len(data)} elements')
        
        # NIH API returns: [total_count, code_array, extra_field, display_array]
        # display_array contains [code, description] pairs
        
        total_count = data[0] if len(data) > 0 else 0
        print(f'Total codes available: {total_count}')
        
        if len(data) >= 4:
            display_data = data[3]
            print(f'Retrieved {len(display_data)} code entries')
            
            for item in display_data:
                if isinstance(item, list) and len(item) >= 2:
                    code = item[0]
                    description = item[1]
                    all_codes.append({
                        'Code': code,
                        'Description': description
                    })
        
        return all_codes
        
    except Exception as e:
        print(f'Error fetching codes: {e}')
        import traceback
        traceback.print_exc()
        return []

def fetch_by_chapter_ranges():
    """
    Alternative method: Fetch codes by ICD-10 chapter ranges
    """
    # ICD-10-CM chapter ranges
    ranges = [
        'A00-B99', 'C00-D49', 'D50-D89', 'E00-E89', 'F01-F99',
        'G00-G99', 'H00-H05', 'H60-H95', 'I00-I99', 'J00-J99',
        'K00-K95', 'L00-L99', 'M00-M99', 'N00-N99', 'O00-O9A',
        'P00-P96', 'Q00-Q99', 'R00-R99', 'S00-T88', 'V00-Y99', 'Z00-Z99'
    ]
    
    all_codes = []
    
    print('Fetching ICD-10 codes by chapter ranges...')
    print(f'Processing {len(ranges)} ranges...\n')
    
    for i, code_range in enumerate(ranges, 1):
        # Extract first letter
        start_code = code_range.split('-')[0][:1]
        
        print(f'[{i}/{len(ranges)}] Range {code_range} (codes starting with {start_code})...', end=' ')
        
        params = {
            'terms': start_code,
            'maxList': 7000,
            'df': 'code,name'
        }
        
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if len(data) >= 4 and isinstance(data[3], list):
                for item in data[3]:
                    if isinstance(item, list) and len(item) >= 2:
                        all_codes.append({
                            'Code': item[0],
                            'Description': item[1]
                        })
                
                print(f'✓ {len(data[3])} codes')
            else:
                print('⚠ No codes')
            
            time.sleep(0.5)  # Be nice to the API
            
        except Exception as e:
            print(f'✗ Error: {e}')
    
    return all_codes

def remove_duplicates(codes):
    """Remove duplicate codes"""
    seen = set()
    unique_codes = []
    
    for code in codes:
        code_id = code['Code']
        if code_id not in seen:
            seen.add(code_id)
            unique_codes.append(code)
    
    return unique_codes

def save_to_csv(codes, filename):
    """Save codes to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Code', 'Description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(codes)

def main():
    print('='*70)
    print('ICD-10-CM Code Fetcher - NIH Clinical Tables API')
    print('='*70)
    print()
    
    # Try the paginated approach first
    print('Attempting to fetch all codes at once...\n')
    all_codes = fetch_all_codes_paginated()
    
    # If that doesn't work well, try by ranges
    if not all_codes or len(all_codes) < 1000:
        print('\n⚠ Single request didn\'t return enough codes.')
        print('Trying alternative method: fetching by chapter ranges...\n')
        all_codes = fetch_by_chapter_ranges()
    
    if not all_codes:
        print('\n❌ Error: No codes were fetched!')
        print('\n💡 Alternative: Download directly from CMS')
        print('   URL: https://www.cob.cms.hhs.gov/Section111/assets/section111/icd10.dx.codes.htm')
        return
    
    print(f'\n{"="*70}')
    print(f'Total codes fetched: {len(all_codes)}')
    
    # Remove duplicates
    print('Removing duplicates...')
    unique_codes = remove_duplicates(all_codes)
    print(f'Unique codes: {len(unique_codes)}')
    
    # Save to CSV
    print(f'\nSaving to {OUTPUT_FILE}...')
    save_to_csv(unique_codes, OUTPUT_FILE)
    
    print('='*70)
    print(f'✅ Success! {len(unique_codes)} codes saved to {OUTPUT_FILE}')
    print('='*70)
    
    # Show sample
    print('\nSample codes (first 10):')
    print('-'*70)
    for i, code in enumerate(unique_codes[:10], 1):
        desc = code['Description'][:50] + '...' if len(code['Description']) > 50 else code['Description']
        print(f"{i}. {code['Code']}: {desc}")
    
    print('\nSample codes (last 10):')
    print('-'*70)
    for i, code in enumerate(unique_codes[-10:], len(unique_codes)-9):
        desc = code['Description'][:50] + '...' if len(code['Description']) > 50 else code['Description']
        print(f"{i}. {code['Code']}: {desc}")
    
    print('\n' + '='*70)
    print('📄 All codes are now in CSV format: Code, Description')
    print('='*70)

if __name__ == '__main__':
    print('\n⏱️  This will take approximately 2-5 minutes')
    print('🌐 Using NIH Clinical Tables API (free, no registration)')
    print('📊 Fetching ICD-10-CM codes')
    print('\n💡 If this doesn\'t work, you can download directly from CMS:')
    print('   https://www.cob.cms.hhs.gov/Section111/assets/section111/icd10.dx.codes.htm\n')
    
    time.sleep(2)
    main()
