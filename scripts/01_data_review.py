"""
Author: David Vanosdall
Course: GEOG 777
Date: 2023-02-02
Step 1: Data Review
Purpose: Load shapefiles, examine structure, and verify data quality
IMPORTANT: Nitrate values must remain unchanged
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'g777_project1_shapefiles'
MAPS_DIR = PROJECT_ROOT / 'outputs' / 'maps'
MAPS_DIR.mkdir(parents=True, exist_ok=True)

def print_header(title):
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70 + "\n")

def explore_shapefile(gdf, name):
    """Examine a shapefile in detail"""
    print(f"\n{'─'*70}")
    print(f" {name}")
    print(f"{'─'*70}")

    print(f"Rows: {len(gdf)}")
    print(f"CRS: {gdf.crs}")
    print(f"Geometry Type: {gdf.geometry.type.unique()}")
    print(f"\nBounds (minx, miny, maxx, maxy): {gdf.total_bounds}")

    print("\n Columns:")
    for col in gdf.columns:
        if col != 'geometry':
            dtype = gdf[col].dtype
            null_count = gdf[col].isnull().sum()
            print(f"  • {col:25} [{dtype}]  (nulls: {null_count})")

    print("\n First 3 rows (non-geometry columns):")
    display_cols = [col for col in gdf.columns if col != 'geometry']
    if len(display_cols) > 0:
        print(gdf[display_cols].head(3).to_string())

    print("\n Numeric column statistics:")
    numeric_cols = gdf.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        print(gdf[numeric_cols].describe().to_string())
    else:
        print("  No numeric columns found")

def visualize_data(wells, cancer_tracts, cancer_county):
    """Create overview visualization"""
    print("\n Creating visualization...")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Wells
    wells.plot(ax=axes[0], color='blue', markersize=8, alpha=0.6, edgecolor='darkblue')
    axes[0].set_title(f'Well Locations\n(n={len(wells)})', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('X')
    axes[0].set_ylabel('Y')
    axes[0].grid(True, alpha=0.3)

    # Census Tracts
    cancer_tracts.plot(ax=axes[1], edgecolor='black', facecolor='lightgray', linewidth=0.5, alpha=0.7)
    axes[1].set_title(f'Census Tracts\n(n={len(cancer_tracts)})', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('X')
    axes[1].set_ylabel('Y')
    axes[1].grid(True, alpha=0.3)

    # Counties
    cancer_county.plot(ax=axes[2], edgecolor='darkblue', facecolor='lightblue', linewidth=1, alpha=0.7)
    axes[2].set_title(f'Counties\n(n={len(cancer_county)})', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('X')
    axes[2].set_ylabel('Y')
    axes[2].grid(True, alpha=0.3)

    plt.suptitle('GEOG 777 Project 1 - Initial Data Review', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = MAPS_DIR / '01_initial_review.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f" Saved: {output_path}")

    plt.show()

def main():
    print_header("STEP 1: DATA REVIEW")

    # Load shapefiles
    print(" Loading provided shapefiles for class...")
    try:
        wells = gpd.read_file(DATA_DIR / 'well_nitrate.shp')
        print(f"   Loaded wells: {len(wells)} features")

        cancer_tracts = gpd.read_file(DATA_DIR / 'cancer_tracts.shp')
        print(f"   Loaded census tracts: {len(cancer_tracts)} features")

        cancer_county = gpd.read_file(DATA_DIR / 'cancer_county.shp')
        print(f"   Loaded counties: {len(cancer_county)} features")

    except FileNotFoundError as e:
        print(f"\n Error: Could not find shapefiles")
        print(f"   Looking in: {DATA_DIR}")
        print(f"   Error: {e}")
        return

    # Explore each dataset
    explore_shapefile(wells, "Well Nitrate Data")
    explore_shapefile(cancer_tracts, "Cancer Census Tracts")
    explore_shapefile(cancer_county, "Cancer County Data")

    # Visualize
    visualize_data(wells, cancer_tracts, cancer_county)

    print_header("STEP 1 COMPLETE")

    print(" Key Information to Note:")
    print("  1. Column names for nitrate, cancer count, and population")
    print("  2. CRS for each dataset (should all match)")
    print("  3. Any null values in critical columns")
    print("\n  REMINDER: Nitrate values will NOT be modified")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()