#!/usr/bin/env python3
"""
ICD-10 CSV Cleaner
Removes Source URL column and cleans descriptions (removes colon and everything after)
"""

import csv
import sys
import os

def clean_description(description):
    """
    Remove colon and everything after it from description
    Examples:
    - "Typhoid fever Incl.: Infection due to..." -> "Typhoid fever"
    - "Cholera, unspecified" -> "Cholera, unspecified"
    """
    # Find the position of colon followed by space or specific keywords
    for keyword in [' Incl.:', ' Excl.:', ' Note:', ':']:
        if keyword in description:
            description = description.split(keyword)[0]
            break
    
    return description.strip()

def clean_csv(input_file, output_file=None):
    """
    Read CSV, remove Source URL column, and clean descriptions
    """
    if not output_file:
        # Create output filename
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_cleaned{ext}"
    
    cleaned_rows = []
    row_count = 0
    
    print(f"📂 Reading: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # Read header
            header = next(reader)
            print(f"📋 Original columns: {header}")
            
            # Process rows
            for row in reader:
                if len(row) >= 2:  # Make sure we have at least Code and Description
                    code = row[0]
                    description = row[1]
                    
                    # Clean the description
                    cleaned_desc = clean_description(description)
                    
                    cleaned_rows.append([code, cleaned_desc])
                    row_count += 1
        
        # Write cleaned CSV
        print(f"\n💾 Writing cleaned data to: {output_file}")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header (only Code and Description)
            writer.writerow(['Code', 'Description'])
            
            # Write cleaned rows
            writer.writerows(cleaned_rows)
        
        print(f"✅ Success! Processed {row_count} rows")
        print(f"\n📊 Sample of cleaned data (first 10 rows):")
        print("-" * 80)
        for i, row in enumerate(cleaned_rows[:10], 1):
            desc = row[1][:60] + '...' if len(row[1]) > 60 else row[1]
            print(f"{i:2d}. {row[0]:<10s} {desc}")
        
        if len(cleaned_rows) > 10:
            print(f"\n... and {len(cleaned_rows) - 10} more rows")
        
        return output_file
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {input_file}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("\n" + "="*80)
    print(" ICD-10 CSV Cleaner")
    print("="*80 + "\n")
    
    # Get input file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = input("Enter input CSV file path: ").strip()
    
    if not input_file:
        print("❌ No file specified!")
        return
    
    # Get output file (optional)
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = input("Enter output CSV file path (press Enter for auto-name): ").strip()
        if not output_file:
            output_file = None
    
    # Clean the CSV
    result = clean_csv(input_file, output_file)
    
    if result:
        print(f"\n✅ Cleaned file saved as: {result}\n")
    else:
        print("\n❌ Cleaning failed!\n")

if __name__ == "__main__":
    main()
