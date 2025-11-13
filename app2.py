#!/usr/bin/env python3
"""
ICD-10 Batch Web Scraper
Reads URLs from a file and scrapes all of them, appending results to a single CSV file
"""

import asyncio
import csv
import re
import json
import sys
import os
from datetime import datetime

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
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set to True for faster processing
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for content
            await asyncio.sleep(3)
            
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
                        codes.append({'code': code, 'description': description, 'url': url})
                
                # Extract from href
                elif href and '#/' in href:
                    code_match = re.search(r'#/([A-Z]\d{2}[\.-]?\d*)', href)
                    if code_match:
                        code = code_match.group(1)
                        desc = re.sub(r'^' + re.escape(code) + r'[\s\-]*', '', text).strip()
                        if desc and len(desc) > 5:
                            codes.append({'code': code, 'description': desc, 'url': url})
            
            await browser.close()
            return remove_duplicates(codes)
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            await browser.close()
            return []

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
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(3)
        
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
                        codes.append({'code': code, 'description': description, 'url': url})
                
                # Extract from href
                elif href and '#/' in href:
                    code_match = re.search(r'#/([A-Z]\d{2}[\.-]?\d*)', href)
                    if code_match:
                        code = code_match.group(1)
                        desc = re.sub(r'^' + re.escape(code) + r'[\s\-]*', '', text).strip()
                        if desc and len(desc) > 5:
                            codes.append({'code': code, 'description': desc, 'url': url})
            except:
                continue
        
        return remove_duplicates(codes)
    
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return []
    
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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
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
                    codes.append({'code': code, 'description': description, 'url': url})
            
            # Extract from href
            elif href and '#/' in href:
                code_match = re.search(r'#/([A-Z]\d{2}[\.-]?\d*)', href)
                if code_match:
                    code = code_match.group(1)
                    desc = re.sub(r'^' + re.escape(code) + r'[\s\-]*', '', text).strip()
                    if desc and len(desc) > 5:
                        codes.append({'code': code, 'description': desc, 'url': url})
        
        return remove_duplicates(codes)
    
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return []

# ============================================================================
# Helper Functions
# ============================================================================
def read_urls_from_file(filename):
    """Read URLs from a text file (one URL per line)"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        print(f"📂 Loaded {len(urls)} URLs from {filename}")
        return urls
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return []
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []

def remove_duplicates(codes):
    """Remove duplicate codes, keeping longest description"""
    seen = {}
    for item in codes:
        code = item['code']
        desc = item['description']
        url = item.get('url', '')
        key = code
        if key not in seen or len(desc) > len(seen[key]['description']):
            seen[key] = {'code': code, 'description': desc, 'url': url}
    
    return list(seen.values())

def append_to_csv(codes, filename='icd10_codes.csv'):
    """Append codes to CSV file"""
    if not codes:
        return False
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow(['Code', 'Description', 'Source URL'])
        
        for item in codes:
            description = item['description'].replace('\n', ' ').replace('\r', ' ')
            description = re.sub(r'\s+', ' ', description).strip()
            url = item.get('url', '')
            writer.writerow([item['code'], description, url])
    
    return True

def display_summary(all_codes, total_urls, successful_urls, failed_urls):
    """Display summary of scraped data"""
    print("\n" + "="*80)
    print(" SCRAPING SUMMARY")
    print("="*80)
    print(f"📊 Total URLs processed: {total_urls}")
    print(f"✅ Successful: {successful_urls}")
    print(f"❌ Failed: {len(failed_urls)}")
    print(f"📝 Total codes extracted: {len(all_codes)}")
    
    if failed_urls:
        print("\n⚠️  Failed URLs:")
        for url in failed_urls[:10]:
            print(f"   - {url}")
        if len(failed_urls) > 10:
            print(f"   ... and {len(failed_urls) - 10} more")
    
    if all_codes:
        print("\n" + "-"*80)
        print("Sample of extracted codes (first 10):")
        print("-"*80)
        for i, item in enumerate(all_codes[:10], 1):
            desc = item['description'][:50] + '...' if len(item['description']) > 50 else item['description']
            print(f"{i:2d}. {item['code']:<10s} {desc}")
        
        if len(all_codes) > 10:
            print(f"\n... and {len(all_codes) - 10} more codes")
    print("="*80 + "\n")

# ============================================================================
# Batch Processing Functions
# ============================================================================
async def scrape_url_async(url, method='playwright'):
    """Scrape a single URL using the specified method"""
    if method == 'playwright':
        return await method_playwright(url)
    else:
        return []

def scrape_url_sync(url, method='selenium'):
    """Scrape a single URL using synchronous methods"""
    if method == 'selenium':
        return method_selenium(url)
    elif method == 'requests':
        return method_requests(url)
    else:
        return []

async def batch_scrape_async(urls, output_file='icd10_codes.csv'):
    """Scrape multiple URLs asynchronously"""
    all_codes = []
    successful = 0
    failed_urls = []
    
    print(f"\n🚀 Starting batch scraping of {len(urls)} URLs...\n")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Processing: {url}")
        
        codes = await scrape_url_async(url, method='playwright')
        
        if codes:
            all_codes.extend(codes)
            successful += 1
            print(f"  ✅ Found {len(codes)} codes")
            
            # Append to file after each successful scrape
            append_to_csv(codes, output_file)
        else:
            print(f"  ⚠️  No codes found")
            failed_urls.append(url)
        
        print()
    
    return all_codes, successful, failed_urls

def batch_scrape_sync(urls, method='selenium', output_file='icd10_codes.csv'):
    """Scrape multiple URLs synchronously"""
    all_codes = []
    successful = 0
    failed_urls = []
    
    print(f"\n🚀 Starting batch scraping of {len(urls)} URLs...\n")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Processing: {url}")
        
        codes = scrape_url_sync(url, method=method)
        
        if codes:
            all_codes.extend(codes)
            successful += 1
            print(f"  ✅ Found {len(codes)} codes")
            
            # Append to file after each successful scrape
            append_to_csv(codes, output_file)
        else:
            print(f"  ⚠️  No codes found")
            failed_urls.append(url)
        
        print()
    
    return all_codes, successful, failed_urls

# ============================================================================
# Main Program
# ============================================================================
async def main():
    print("\n" + "="*80)
    print(" ICD-10 Batch Web Scraper")
    print("="*80 + "\n")
    
    # Get input file
    url_file = input("Enter path to URLs file: ").strip()
    if not url_file:
        print("❌ No file specified!")
        return
    
    urls = read_urls_from_file(url_file)
    if not urls:
        return
    
    # Choose scraping method
    print("\nSelect scraping method:")
    print("1. Playwright (recommended - best for JavaScript sites)")
    print("2. Selenium (good alternative)")
    print("3. Requests + BeautifulSoup (fast, may miss dynamic content)")
    
    method_choice = input("\nEnter choice (1-3): ").strip()
    
    # Get output filename
    output_file = input("\nEnter output filename (default: icd10_codes.csv): ").strip()
    if not output_file:
        output_file = 'icd10_codes.csv'
    
    # Clear existing file if it exists
    if os.path.exists(output_file):
        overwrite = input(f"\n⚠️  File '{output_file}' exists. Overwrite? (y/n): ").strip().lower()
        if overwrite == 'y':
            os.remove(output_file)
            print(f"✅ Removed existing file")
        else:
            print(f"✅ Will append to existing file")
    
    # Start scraping
    start_time = datetime.now()
    all_codes = []
    successful = 0
    failed_urls = []
    
    if method_choice == '1':
        all_codes, successful, failed_urls = await batch_scrape_async(urls, output_file)
    
    elif method_choice == '2':
        all_codes, successful, failed_urls = batch_scrape_sync(urls, method='selenium', output_file=output_file)
    
    elif method_choice == '3':
        all_codes, successful, failed_urls = batch_scrape_sync(urls, method='requests', output_file=output_file)
    
    else:
        print("❌ Invalid choice!")
        return
    
    # Calculate duration
    duration = datetime.now() - start_time
    
    # Display summary
    display_summary(all_codes, len(urls), successful, failed_urls)
    
    print(f"⏱️  Total time: {duration}")
    print(f"💾 Results saved to: {output_file}")
    print("\n✅ Batch scraping complete!\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
