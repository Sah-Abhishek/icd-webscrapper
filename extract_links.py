
#!/usr/bin/env python3
"""
ICD-10 Category Range URL Extractor
Extracts all range-based URLs (like L20-L30, N00-N08) from the ICD-10 sidebar
"""

import asyncio
import re
from urllib.parse import urljoin

# ============================================================================
# METHOD 1: Playwright (Recommended)
# ============================================================================
async def extract_with_playwright(base_url='https://icd.who.int/browse10/2019/en'):
    """
    Use Playwright to click through sidebar and extract range URLs
    Install: pip install playwright && playwright install chromium
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright")
        return []
    
    print("🎭 Using Playwright to extract category URLs...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for background
        page = await browser.new_page()
        
        print(f"📡 Navigating to {base_url}...")
        await page.goto(base_url, wait_until='networkidle', timeout=60000)
        
        print("⏳ Waiting for sidebar to load...")
        await asyncio.sleep(3)
        
        # Find all expandable elements (arrows/triangles)
        print("🔍 Finding expandable categories...")
        
        # Click all expand buttons to reveal subcategories
        expand_buttons = await page.query_selector_all('span.expandable, .tree-node-toggle, .expand-icon, [class*="expand"], [class*="toggle"]')
        
        print(f"📂 Found {len(expand_buttons)} expandable elements")
        print("🖱️  Clicking to expand all categories...")
        
        # Click each expand button
        clicked = 0
        for button in expand_buttons:
            try:
                await button.click()
                clicked += 1
                await asyncio.sleep(0.2)  # Small delay to let content load
            except:
                pass
        
        print(f"✅ Clicked {clicked} expand buttons")
        
        # Wait for content to fully load
        await asyncio.sleep(2)
        
        # Extract all links from the page
        print("🔗 Extracting category range URLs...")
        
        links = await page.evaluate('''() => {
            const results = [];
            const linkElements = document.querySelectorAll('a[href*="#/"]');
            
            linkElements.forEach(link => {
                const href = link.getAttribute('href');
                const text = link.textContent.trim();
                
                if (href) {
                    results.push({
                        href: href,
                        text: text
                    });
                }
            });
            
            return results;
        }''')
        
        # Filter for range-based URLs (e.g., L20-L30, N00-N08)
        range_urls = []
        range_pattern = re.compile(r'#/([A-Z]\d{2,3}-[A-Z]\d{2,3})')
        
        seen = set()
        for link in links:
            href = link['href']
            text = link['text']
            
            match = range_pattern.search(href)
            if match:
                range_code = match.group(1)
                
                # Build full URL
                if href.startswith('#'):
                    full_url = base_url + href
                elif href.startswith('/'):
                    full_url = 'https://icd.who.int' + href
                else:
                    full_url = href
                
                if full_url not in seen:
                    seen.add(full_url)
                    range_urls.append({
                        'code': range_code,
                        'url': full_url,
                        'description': text
                    })
        
        await browser.close()
        
        # Sort by code
        range_urls.sort(key=lambda x: x['code'])
        
        return range_urls

# ============================================================================
# METHOD 2: Selenium (Alternative)
# ============================================================================
def extract_with_selenium(base_url='https://icd.who.int/browse10/2019/en'):
    """
    Use Selenium to click through sidebar and extract range URLs
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
    
    print("🔍 Using Selenium to extract category URLs...")
    
    options = Options()
    # options.add_argument('--headless')  # Uncomment for background mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"📡 Navigating to {base_url}...")
        driver.get(base_url)
        
        print("⏳ Waiting for sidebar to load...")
        time.sleep(3)
        
        # Find and click all expandable elements
        print("🔍 Finding expandable categories...")
        
        # Try different selectors for expand buttons
        selectors = [
            "span.expandable",
            ".tree-node-toggle",
            ".expand-icon",
            "[class*='expand']",
            "[class*='toggle']",
            "span[onclick]"
        ]
        
        expand_buttons = []
        for selector in selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                expand_buttons.extend(buttons)
            except:
                pass
        
        print(f"📂 Found {len(expand_buttons)} expandable elements")
        print("🖱️  Clicking to expand all categories...")
        
        # Click each expand button
        clicked = 0
        for button in expand_buttons:
            try:
                driver.execute_script("arguments[0].click();", button)
                clicked += 1
                time.sleep(0.1)
            except:
                pass
        
        print(f"✅ Clicked {clicked} expand buttons")
        
        # Wait for content to load
        time.sleep(2)
        
        # Extract all links
        print("🔗 Extracting category range URLs...")
        
        link_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="#/"]')
        
        # Filter for range-based URLs
        range_urls = []
        range_pattern = re.compile(r'#/([A-Z]\d{2,3}-[A-Z]\d{2,3})')
        
        seen = set()
        for link in link_elements:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                if href:
                    match = range_pattern.search(href)
                    if match:
                        range_code = match.group(1)
                        
                        if href not in seen:
                            seen.add(href)
                            range_urls.append({
                                'code': range_code,
                                'url': href,
                                'description': text
                            })
            except:
                continue
        
        # Sort by code
        range_urls.sort(key=lambda x: x['code'])
        
        return range_urls
    
    finally:
        driver.quit()

# ============================================================================
# Helper Functions
# ============================================================================
def save_to_file(urls, filename='icd10_range_urls.txt'):
    """Save URLs to a text file"""
    if not urls:
        print("❌ No URLs to save!")
        return False
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# ICD-10 Category Range URLs\n")
        f.write("# Extracted from WHO ICD-10 Browser\n")
        f.write("# Format: URL (Code - Description)\n\n")
        
        for item in urls:
            f.write(f"{item['url']}\n")
    
    print(f"✅ Saved {len(urls)} URLs to {filename}")
    return True

def save_detailed_csv(urls, filename='icd10_ranges_detailed.csv'):
    """Save detailed information to CSV"""
    if not urls:
        return False
    
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Code', 'Description', 'URL'])
        
        for item in urls:
            desc = item['description'].replace('\n', ' ').strip()
            desc = re.sub(r'\s+', ' ', desc)
            writer.writerow([item['code'], desc, item['url']])
    
    print(f"✅ Saved detailed information to {filename}")
    return True

def display_results(urls):
    """Display extracted URLs"""
    if not urls:
        print("❌ No range URLs found!")
        return
    
    print(f"\n✅ Found {len(urls)} category range URLs\n")
    print("="*80)
    
    for i, item in enumerate(urls, 1):
        desc = item['description'][:50] + '...' if len(item['description']) > 50 else item['description']
        print(f"{i:3d}. {item['code']:<15s} - {desc}")
        print(f"     {item['url']}")
        print()
    
    print("="*80)

# ============================================================================
# Main Program
# ============================================================================
async def main():
    print("\n" + "="*80)
    print(" ICD-10 Category Range URL Extractor")
    print("="*80 + "\n")
    
    # Get base URL
    base_url = input("Enter ICD-10 base URL (or press Enter for default): ").strip()
    if not base_url:
        base_url = 'https://icd.who.int/browse10/2019/en'
    
    print(f"\n🎯 Target: {base_url}\n")
    
    # Choose method
    print("Select extraction method:")
    print("1. Playwright (recommended)")
    print("2. Selenium")
    
    choice = input("\nEnter choice (1-2): ").strip()
    
    urls = []
    
    if choice == '1':
        urls = await extract_with_playwright(base_url)
    
    elif choice == '2':
        urls = extract_with_selenium(base_url)
    
    else:
        print("❌ Invalid choice!")
        return
    
    # Display results
    display_results(urls)
    
    if not urls:
        print("\n⚠️  No range URLs found. The page structure may have changed.")
        print("Try viewing the page with headless=False to see what's happening.")
        return
    
    # Save results
    print("\n📁 Save options:")
    
    save_txt = input("Save URLs to text file? (y/n): ").strip().lower()
    if save_txt == 'y':
        filename = input("Enter filename (default: icd10_range_urls.txt): ").strip()
        if not filename:
            filename = 'icd10_range_urls.txt'
        save_to_file(urls, filename)
    
    save_csv = input("\nSave detailed CSV? (y/n): ").strip().lower()
    if save_csv == 'y':
        filename = input("Enter filename (default: icd10_ranges_detailed.csv): ").strip()
        if not filename:
            filename = 'icd10_ranges_detailed.csv'
        save_detailed_csv(urls, filename)
    
    print("\n✅ Extraction complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
