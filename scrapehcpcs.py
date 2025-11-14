from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import time

# Configuration
BASE_URL = 'https://www.hcpcsdata.com/Codes'
OUTPUT_FILE = 'all_hcpcs_codes.csv'

def scrape_category(driver, category_url, category_name):
    """Scrape all codes from a specific category page"""
    print(f'\n  Navigating to {category_name} codes...')
    driver.get(category_url)
    
    try:
        # Wait for the table to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table')))
        
        # Find all rows in the table
        rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        print(f'  Found {len(rows)} codes in category {category_name}')
        
        # Extract data
        category_data = []
        for row in rows:
            try:
                code_element = row.find_element(By.CSS_SELECTOR, 'td:first-child a')
                description_element = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2)')
                
                code = code_element.text.strip()
                description = description_element.text.strip()
                
                if code and description:
                    category_data.append({
                        'Code': code,
                        'Description': description
                    })
                    
            except Exception as e:
                continue
        
        print(f'  ✓ Extracted {len(category_data)} codes from category {category_name}')
        return category_data
        
    except Exception as e:
        print(f'  ✗ Error scraping category {category_name}: {e}')
        return []

def scrape_all_hcpcs_codes():
    driver = None
    
    try:
        # Set up Chrome options
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Create driver
        print('Starting browser...')
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to the main codes page
        print(f'Navigating to {BASE_URL}...')
        driver.get(BASE_URL)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table')))
        print('Main page loaded successfully!')
        
        # Find all category links
        category_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        categories = []
        
        for row in category_rows:
            try:
                link_element = row.find_element(By.CSS_SELECTOR, 'td:first-child a')
                category_name = link_element.text.strip().replace("'", "").replace(" Codes", "")
                category_url = link_element.get_attribute('href')
                
                if category_name and category_url:
                    categories.append({
                        'name': category_name,
                        'url': category_url
                    })
            except Exception as e:
                continue
        
        print(f'\nFound {len(categories)} code categories to scrape:')
        for cat in categories:
            print(f'  - {cat["name"]}')
        
        # Scrape all categories
        all_data = []
        total_codes = 0
        
        print('\n' + '='*60)
        print('Starting to scrape all categories...')
        print('='*60)
        
        for i, category in enumerate(categories, 1):
            print(f'\n[{i}/{len(categories)}] Processing {category["name"]} category...')
            category_data = scrape_category(driver, category['url'], category['name'])
            all_data.extend(category_data)
            total_codes += len(category_data)
            
            # Small delay to avoid overwhelming the server
            time.sleep(1)
        
        print('\n' + '='*60)
        print(f'Scraping complete! Total codes extracted: {total_codes}')
        print('='*60)
        
        if not all_data:
            print('\n⚠ Warning: No data was extracted!')
            return
        
        # Save to CSV
        print(f'\nSaving data to {OUTPUT_FILE}...')
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Code', 'Description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(all_data)
        
        print(f'✓ Data saved successfully to {OUTPUT_FILE}')
        
        # Display first few rows
        print('\n' + '='*60)
        print('Sample data (first 10 rows):')
        print('='*60)
        for i, row in enumerate(all_data[:10], 1):
            print(f"{i}. {row['Code']}: {row['Description'][:80]}...")
        
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            print('\n✓ Browser closed.')

if __name__ == '__main__':
    print('='*60)
    print('HCPCS Code Scraper - All Categories')
    print('='*60)
    scrape_all_hcpcs_codes()
