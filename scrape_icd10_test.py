from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import time

# Configuration - Test with ONE chapter
TEST_CHAPTER = 'F01-F99'  # Mental, Behavioral and Neurodevelopmental disorders
BASE_URL = 'https://www.icd10data.com'
OUTPUT_FILE = f'icd10_test_{TEST_CHAPTER}.csv'

def extract_codes_from_page(driver):
    """Extract all codes visible on the current page"""
    codes = []
    
    try:
        # Find all code links
        code_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ICD10CM/Codes/"]')
        
        for elem in code_elements:
            try:
                code_text = elem.text.strip()
                href = elem.get_attribute('href')
                
                # Skip if it's a range (contains dash) or navigation element
                if code_text and '-' not in code_text and '/' not in code_text:
                    # Try to get description from parent element
                    parent = elem.find_element(By.XPATH, '..')
                    full_text = parent.text.strip()
                    
                    # Extract code (first part before space)
                    code = code_text.split()[0] if ' ' in code_text else code_text
                    
                    # Extract description (everything after code)
                    description = full_text.replace(code, '').strip()
                    
                    # Basic validation
                    if len(code) >= 3 and code[0].isalpha():
                        codes.append({
                            'Code': code,
                            'Description': description
                        })
            except:
                continue
    except Exception as e:
        print(f"    Error extracting: {e}")
    
    return codes

def scrape_test_chapter():
    """Scrape a single chapter for testing"""
    driver = None
    
    try:
        # Set up Chrome options
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        print('='*70)
        print(f'ICD-10-CM Test Scraper - Chapter {TEST_CHAPTER}')
        print('='*70)
        print('\nStarting browser...')
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to test chapter
        chapter_url = f'{BASE_URL}/ICD10CM/Codes/{TEST_CHAPTER}'
        print(f'Navigating to {chapter_url}...')
        driver.get(chapter_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        print('Page loaded successfully!')
        print('\nExtracting codes from main chapter page...')
        
        # Extract codes from main page
        main_codes = extract_codes_from_page(driver)
        print(f'Found {len(main_codes)} codes on main page')
        
        # Find all sub-range links (e.g., F01-F09, F10-F19, etc.)
        print('\nFinding sub-ranges...')
        range_links = []
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ICD10CM/Codes/"]')
        
        for link in links:
            href = link.get_attribute('href')
            text = link.text.strip()
            # Look for range patterns like "F01-F09"
            if href and '-' in text and TEST_CHAPTER in href:
                range_links.append(href)
        
        # Remove duplicates
        range_links = list(set(range_links))
        print(f'Found {len(range_links)} sub-ranges')
        
        all_codes = main_codes.copy()
        
        # Visit each sub-range
        for i, range_url in enumerate(range_links[:10], 1):  # Limit to first 10 for testing
            print(f'\nProcessing sub-range {i}/{min(len(range_links), 10)}...')
            driver.get(range_url)
            time.sleep(0.5)
            
            range_codes = extract_codes_from_page(driver)
            all_codes.extend(range_codes)
            print(f'  Extracted {len(range_codes)} codes')
        
        # Remove duplicates based on code
        seen = set()
        unique_codes = []
        for code in all_codes:
            code_id = code['Code']
            if code_id not in seen:
                seen.add(code_id)
                unique_codes.append(code)
        
        print('\n' + '='*70)
        print(f'Total unique codes extracted: {len(unique_codes)}')
        print('='*70)
        
        if not unique_codes:
            print('\n⚠ Warning: No codes were extracted!')
            print('The website structure may have changed.')
            return
        
        # Save to CSV
        print(f'\nSaving to {OUTPUT_FILE}...')
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Code', 'Description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_codes)
        
        print(f'✓ Data saved successfully!')
        
        # Show sample
        print('\n' + '='*70)
        print('Sample codes (first 10):')
        print('='*70)
        for i, row in enumerate(unique_codes[:10], 1):
            desc = row['Description'][:50] + '...' if len(row['Description']) > 50 else row['Description']
            print(f"{i}. {row['Code']}: {desc}")
        
        print('\n' + '='*70)
        print('✅ Test scraping completed successfully!')
        print(f'📄 Check {OUTPUT_FILE} for results')
        print('='*70)
        
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            print('\n✓ Browser closed.')

if __name__ == '__main__':
    print('\n📋 This is a TEST scraper for one chapter only')
    print(f'📑 Testing with chapter: {TEST_CHAPTER}')
    print('⏱️  Estimated time: 2-5 minutes')
    print('\n💡 To scrape all chapters, use:')
    print('   - scrape_icd10_complete.py (10-20 hours)')
    print('   - scrape_icd10_fast.py (1-2 hours)')
    print('\nStarting in 2 seconds...\n')
    
    time.sleep(2)
    scrape_test_chapter()
