#!/usr/bin/env python3
"""
ICD-10 Web Scraper with Multiple Approaches
Choose different scraping methods based on what works best
"""

import asyncio
import csv
import re
import json
import sys

# ============================================================================
# METHOD 1: Playwright (Best for JavaScript-heavy sites)
# ============================================================================
async def method_playwright(url):
    """
    Use Playwright - best for dynamic content
    Install: pip install playwright && playwright install chromium
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright")
        return []
    
    print("🎭 Using Playwright method...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see browser
        page = await browser.new_page()
        
        print(f"📡 Navigating to {url}...")
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        # Wait for content
        print("⏳ Waiting for content to load...")
        await asyncio.sleep(5)
        
        # Extract data
        codes = []
        
        # Get all visible text and links
        data = await page.evaluate('''() => {
            const results = [];
            
            // Get all elements that might contain codes
            const elements = document.querySelectorAll('a, li, div, span, td');
            
            elements.forEach(el => {
                const text = el.textContent.trim();
                const href = el.getAttribute('href') || '';
                
                if (text.length > 3) {
                    results.push({text, href});
                }
            });
            
            return results;
        }''')
        
        for item in data:
            text = item['text']
            href = item['href']
            
            # Pattern: "CODE Description"
            match = re.match(r'^([A-Z]\d{2}[\.-]?\d*)\s+(.+)$', text, re.DOTALL)
            if match:
                code = match.group(1)
                description = match.group(2).strip()
                if len(description) > 5:
                    codes.append({'code': code, 'description': description})
            
            # Extract from href
            elif href and '#/' in href:
                code_match = re.search(r'#/([A-Z]\d{2}[\.-]?\d*)', href)
                if code_match:
                    code = code_match.group(1)
                    desc = re.sub(r'^' + re.escape(code) + r'[\s\-]*', '', text).strip()
                    if desc and len(desc) > 5:
                        codes.append({'code': code, 'description': desc})
        
        await browser.close()
        return remove_duplicates(codes)

# ============================================================================
# METHOD 2: Selenium (Good alternative to Playwright)
# ============================================================================
def method_selenium(url):
    """
    Use Selenium - widely supported
    Install: pip install selenium
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        import time
    except ImportError:
        print("❌ Selenium not installed. Run: pip install selenium")
        return []
    
    print("🔍 Using Selenium method...")
    
    options = Options()
    # options.add_argument('--headless')  # Comment out to see browser
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"📡 Navigating to {url}...")
        driver.get(url)
        
        print("⏳ Waiting for content to load...")
        time.sleep(5)
        
        codes = []
        
        # Find all elements
        elements = driver.find_elements(By.XPATH, "//*[text()]")
        
        for element in elements:
            try:
                text = element.text.strip()
                href = element.get_attribute('href') or ''
                
                if not text or len(text) < 5:
                    continue
                
                # Pattern: "CODE Description"
                match = re.match(r'^([A-Z]\d{2}[\.-]?\d*)\s+(.+)$', text)
                if match:
                    code = match.group(1)
                    description = match.group(2).strip()
                    if len(description) > 5:
                        codes.append({'code': code, 'description': description})
                
                # Extract from href
                elif href and '#/' in href:
                    code_match = re.search(r'#/([A-Z]\d{2}[\.-]?\d*)', href)
                    if code_match:
                        code = code_match.group(1)
                        desc = re.sub(r'^' + re.escape(code) + r'[\s\-]*', '', text).strip()
                        if desc and len(desc) > 5:
                            codes.append({'code': code, 'description': desc})
            except:
                continue
        
        return remove_duplicates(codes)
    
    finally:
        driver.quit()

# ============================================================================
# METHOD 3: Requests + BeautifulSoup (Fast but may miss dynamic content)
# ============================================================================
def method_requests(url):
    """
    Use requests + BeautifulSoup - fast but limited for JavaScript sites
    Install: pip install requests beautifulsoup4
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ Required libraries not installed. Run: pip install requests beautifulsoup4")
        return []
    
    print("🌐 Using Requests method...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"📡 Fetching {url}...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    codes = []
    
    # Find all text elements
    for element in soup.find_all(['a', 'li', 'div', 'span', 'td']):
        text = element.get_text(strip=True)
        href = element.get('href', '')
        
        if not text or len(text) < 5:
            continue
        
        # Pattern: "CODE Description"
        match = re.match(r'^([A-Z]\d{2}[\.-]?\d*)\s+(.+)$', text)
        if match:
            code = match.group(1)
            description = match.group(2).strip()
            if len(description) > 5:
                codes.append({'code': code, 'description': description})
        
        # Extract from href
        elif href and '#/' in href:
            code_match = re.search(r'#/([A-Z]\d{2}[\.-]?\d*)', href)
            if code_match:
                code = code_match.group(1)
                desc = re.sub(r'^' + re.escape(code) + r'[\s\-]*', '', text).strip()
                if desc and len(desc) > 5:
                    codes.append({'code': code, 'description': desc})
    
    return remove_duplicates(codes)

# ============================================================================
# METHOD 4: API Approach (if WHO provides one)
# ============================================================================
def method_api(code_range):
    """
    Try to use WHO ICD API if available
    """
    print("🔌 Checking for ICD API...")
    print("⚠️  WHO ICD API requires authentication - not implemented yet")
    return []

# ============================================================================
# Helper Functions
# ============================================================================
def remove_duplicates(codes):
    """Remove duplicate codes, keeping longest description"""
    seen = {}
    for item in codes:
        code = item['code']
        desc = item['description']
        if code not in seen or len(desc) > len(seen[code]):
            seen[code] = desc
    
    return [{'code': k, 'description': v} for k, v in seen.items()]

def save_to_csv(codes, filename='icd10_codes.csv'):
    """Save codes to CSV file"""
    if not codes:
        print("❌ No codes to save!")
        return False
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for item in codes:
            description = item['description'].replace('\n', ' ').replace('\r', ' ')
            description = re.sub(r'\s+', ' ', description).strip()
            writer.writerow([item['code'], description])
    
    print(f"✅ Saved {len(codes)} codes to {filename}")
    return True

def display_results(codes):
    """Display scraped results"""
    if not codes:
        print("❌ No codes found!")
        return
    
    print(f"\n✅ Found {len(codes)} codes\n")
    print("First 10 entries:")
    print("-" * 80)
    for i, item in enumerate(codes[:10], 1):
        desc = item['description'][:60] + '...' if len(item['description']) > 60 else item['description']
        print(f"{i:2d}. {item['code']:<10s} {desc}")
    
    if len(codes) > 10:
        print(f"\n... and {len(codes) - 10} more entries")

# ============================================================================
# Main Program
# ============================================================================
async def main():
    print("\n" + "="*80)
    print(" ICD-10 Web Scraper - Multiple Methods")
    print("="*80 + "\n")
    
    # Get URL
    url = input("Enter ICD-10 URL (or press Enter for default): ").strip()
    if not url:
        url = 'https://icd.who.int/browse10/2019/en#/P54.0'
    
    print(f"\n🎯 Target: {url}\n")
    
    # Choose method
    print("Select scraping method:")
    print("1. Playwright (recommended - best for JavaScript sites)")
    print("2. Selenium (good alternative)")
    print("3. Requests + BeautifulSoup (fast, may miss dynamic content)")
    print("4. Try all methods")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    codes = []
    
    if choice == '1':
        codes = await method_playwright(url)
    
    elif choice == '2':
        codes = method_selenium(url)
    
    elif choice == '3':
        codes = method_requests(url)
    
    elif choice == '4':
        print("\n🔄 Trying all methods...\n")
        
        # Try Playwright
        try:
            codes = await method_playwright(url)
            if codes:
                print(f"✅ Playwright found {len(codes)} codes")
        except Exception as e:
            print(f"❌ Playwright failed: {e}")
        
        # Try Selenium if Playwright didn't work
        if not codes:
            try:
                codes = method_selenium(url)
                if codes:
                    print(f"✅ Selenium found {len(codes)} codes")
            except Exception as e:
                print(f"❌ Selenium failed: {e}")
        
        # Try Requests as last resort
        if not codes:
            try:
                codes = method_requests(url)
                if codes:
                    print(f"✅ Requests found {len(codes)} codes")
            except Exception as e:
                print(f"❌ Requests failed: {e}")
    
    else:
        print("❌ Invalid choice!")
        return
    
    # Display and save results
    display_results(codes)
    
    if codes:
        save = input("\nSave to CSV? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("Enter filename (default: icd10_codes.csv): ").strip()
            if not filename:
                filename = 'icd10_codes.csv'
            save_to_csv(codes, filename)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
