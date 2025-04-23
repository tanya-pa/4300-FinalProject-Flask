import pandas as pd
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def combine_csv_files():
    # Read the CSV files
    try:
        mens_data = pd.read_csv("ebay_mens_perfume.csv")
        womens_data = pd.read_csv("ebay_womens_perfume.csv")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Combine the data
    combined_data = pd.concat([mens_data, womens_data], ignore_index=True)

    # Save the combined data to a new CSV file
    output_file = "combined_perfume_data.csv"  # Define the output file name
    combined_data.to_csv(output_file, index=False)
    print(f"Combined CSV file saved to {output_file}")

def check_csv_size():
    # Load the CSV file
    csv_file = "combined_perfume_data.csv"  # Replace with your CSV file path
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} does not exist.")
        return
    rows, cols = combined_data.shape
    print(f"Combined data contains {rows} rows and {cols} columns.")

def merge_frag_clean_and_combined_on_brand_and_perfume():
    try:
        frag_clean_data = pd.read_csv("frag_clean.csv")
        combined_perfume_data = pd.read_csv("combined_perfume_data.csv")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Ensure column names are consistent
    frag_clean_data.columns = frag_clean_data.columns.str.strip().str.lower()
    combined_perfume_data.columns = combined_perfume_data.columns.str.strip().str.lower()

    # Normalize 'brand' and 'perfume' columns for case and semantic insensitivity
    for df in [frag_clean_data]:
        if 'brand' in df.columns and 'perfume' in df.columns:
            df['brand'] = df['brand'].str.strip().str.lower()
            df['perfume'] = df['perfume'].str.strip().str.lower()
        else:
            print("Error: 'brand' and 'perfume' columns must exist in both datasets.")
            return
    for df in [combined_perfume_data]:
        if 'brand' in df.columns and 'title' in df.columns:
            df['brand'] = df['brand'].str.strip().str.lower()
            df['title'] = df['title'].str.strip().str.lower()
            df.rename(columns={'title': 'perfume'}, inplace=True)

    print("frag_clean_data:")
    print(frag_clean_data[['brand', 'perfume']].head())

    print("\ncombined_perfume_data:")
    print(combined_perfume_data[['brand', 'perfume']].head())

    # Merge the data on 'brand' and fuzzy match on 'perfume'
    merged_data = []
    for _, frag_row in frag_clean_data.iterrows():
        brand_matches = combined_perfume_data[combined_perfume_data['brand'] == frag_row['brand']]
        if not brand_matches.empty:
            for _, combined_row in brand_matches.iterrows():
                # Perform fuzzy matching on 'perfume'
                similarity = fuzz.partial_ratio(frag_row['perfume'], combined_row['perfume'])
                if similarity > 80:  # Threshold for fuzzy matching
                    merged_row = {**frag_row.to_dict(), **combined_row.to_dict()}
                    merged_data.append(merged_row)

    # Convert merged data to DataFrame
    merged_data_df = pd.DataFrame(merged_data)

    # Save the merged data to a new CSV file
    output_file = "merged_frag_combined_data.csv"
    merged_data_df.to_csv(output_file, index=False)
    print(f"Merged CSV file saved to {output_file}")
    rows, cols = merged_data_df.shape
    print(f"Merged data contains {rows} rows and {cols} columns.")


if __name__ == "__main__":
    #combine_csv_files()
    merge_frag_clean_and_combined_on_brand_and_perfume()
