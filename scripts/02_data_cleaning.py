"""
Author: David Vanosdall
Course: GEOG 777
Date: 2023-02-02
Step 2: Data Cleaning

Additional Information for help
Purpose: Reproject to Wisconsin CRS (EPSG:3071) for accurate distance calculations

WHY? The data is currently in latitude/longitude (degrees), but IDW needs to
calculate distances. At Wisconsin's latitude, 1° east ≠ 1° north in actual distance
(degrees measure angles, not distances on the ground). EPSG:3071 converts everything
to meters so 1 meter east = 1 meter north, making distance calculations accurate.

IMPORTANT: Nitrate values remain unchanged - only coordinates are transformed.
Think of it like converting a street address to GPS coordinates - the house
doesn't move, just how we describe its location changes.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'g777_project1_shapefiles'
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
MAPS_DIR = PROJECT_ROOT / 'outputs' / 'maps'

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MAPS_DIR.mkdir(parents=True, exist_ok=True)

# Target CRS
TARGET_CRS = "EPSG:3071"  # Wisconsin Transverse Mercator (units: meters)
SOURCE_CRS = "EPSG:4269"  # NAD83 Geographic (current)

def print_header(title):
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70 + "\n")

def print_section(title):
    print("\n" + "─"*70)
    print(title)
    print("─"*70)

def validate_nitrate_data(wells_gdf):
    """Check nitrate data quality (but don't modify values)"""
    print_section("Validating Nitrate Data")

    nitrate_col = 'nitr_ran'
    nitrate_values = wells_gdf[nitrate_col]

    print(f"Nitrate Column: '{nitrate_col}'")
    print(f"  Count: {len(nitrate_values)}")
    print(f"  Range: {nitrate_values.min():.2f} to {nitrate_values.max():.2f}")
    print(f"  Mean: {nitrate_values.mean():.2f}")
    print(f"  Std Dev: {nitrate_values.std():.2f}")
    print(f"  Negative values: {(nitrate_values < 0).sum()}")

    print("\n  NOTE: Negative values are expected (data manipulated for testing)")
    print("  All nitrate values will be preserved unchanged")

    return wells_gdf

def validate_cancer_data(tracts_gdf):
    """Check cancer rate data quality"""
    print_section("Validating Cancer Data")

    cancer_col = 'canrate'
    cancer_values = tracts_gdf[cancer_col]

    print(f"Cancer Rate Column: '{cancer_col}'")
    print(f"  Count: {len(cancer_values)}")
    print(f"  Range: {cancer_values.min():.4f} to {cancer_values.max():.4f}")
    print(f"  Mean: {cancer_values.mean():.4f}")
    print(f"  Std Dev: {cancer_values.std():.4f}")
    print(f"  Zero values: {(cancer_values == 0).sum()}")

    print("\n Cancer rates appear to be already normalized (0-1 range)")

    return tracts_gdf

def reproject_data(gdf, name, target_crs=TARGET_CRS):
    """Reproject GeoDataFrame to target CRS"""
    print(f"\n Reprojecting {name}...")
    print(f"   From: {gdf.crs}")
    print(f"   To:   {target_crs}")

    # Store original bounds for comparison
    orig_bounds = gdf.total_bounds
    print(f"   Original bounds: [{orig_bounds[0]:.2f}, {orig_bounds[1]:.2f}, {orig_bounds[2]:.2f}, {orig_bounds[3]:.2f}]")

    # Reproject (this only changes coordinates, not attribute values)
    gdf_reprojected = gdf.to_crs(target_crs)

    # Show new bounds
    new_bounds = gdf_reprojected.total_bounds
    print(f"   New bounds:      [{new_bounds[0]:.0f}, {new_bounds[1]:.0f}, {new_bounds[2]:.0f}, {new_bounds[3]:.0f}] meters")

    print(f"    Reprojected {len(gdf_reprojected)} features")

    return gdf_reprojected

def save_cleaned_data(gdf, filename, name):
    """Save cleaned shapefile"""
    output_path = PROCESSED_DIR / filename
    gdf.to_file(output_path)
    print(f"   Saved: {output_path}")
    return output_path

def visualize_reprojected(wells, tracts, county):
    """Visualize data in new coordinate system"""
    print_section("Creating Visualization")

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left: Nitrate points
    ax1 = axes[0]
    tracts.plot(ax=ax1, edgecolor='black', facecolor='lightgray', linewidth=0.3, alpha=0.5)
    wells.plot(ax=ax1, column='nitr_ran', cmap='YlOrRd', markersize=5,
               alpha=0.7, edgecolor='black', linewidth=0.3, legend=True,
               legend_kwds={'label': 'Nitrate (mg/L)', 'shrink': 0.8})
    ax1.set_title(f'Well Nitrate Levels (EPSG:3071)\nn={len(wells)} wells',
                  fontsize=12, fontweight='bold')
    ax1.set_xlabel('Easting (meters)')
    ax1.set_ylabel('Northing (meters)')
    ax1.grid(True, alpha=0.3)

    # Right: Cancer rates
    ax2 = axes[1]
    tracts.plot(ax=ax2, column='canrate', cmap='Reds', edgecolor='black',
                linewidth=0.3, legend=True,
                legend_kwds={'label': 'Cancer Rate', 'shrink': 0.8})
    ax2.set_title(f'Cancer Rates by Census Tract (EPSG:3071)\nn={len(tracts)} tracts',
                  fontsize=12, fontweight='bold')
    ax2.set_xlabel('Easting (meters)')
    ax2.set_ylabel('Northing (meters)')
    ax2.grid(True, alpha=0.3)

    plt.suptitle('Cleaned and Reprojected Data - Wisconsin Transverse Mercator',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = MAPS_DIR / '02_cleaned_reprojected.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f" Saved visualization: {output_path}")

    plt.show()

def main():
    print_header("STEP 2: DATA CLEANING & CRS REPROJECTION")

    # Load original data
    print_section("Loading Original Shapefiles")
    wells = gpd.read_file(DATA_DIR / 'well_nitrate.shp')
    print(f" Loaded {len(wells)} wells")

    tracts = gpd.read_file(DATA_DIR / 'cancer_tracts.shp')
    print(f" Loaded {len(tracts)} census tracts")

    county = gpd.read_file(DATA_DIR / 'cancer_county.shp')
    print(f" Loaded {len(county)} counties")

     # Validate data (doesn't modify, just checks)
    wells = validate_nitrate_data(wells)
    tracts = validate_cancer_data(tracts)

    # depending what we want to do for neg values we can uncomment either
    # option 1 sets negative values to 0 but keeps all wells, option 2 removes
    # wells with negative values entirely
    ############################################################################
    # # *** CLIP NEGATIVE NITRATE TO ZERO, RIGHT HERE ***
    # wells['nitr_ran'] = wells['nitr_ran'].clip(lower=0)
    # print(f"Set negative nitrate values to 0. New min: {wells['nitr_ran'].min()}")

    #############################################################################
    # wells = wells[wells['nitr_ran'] >= 0].copy()
    # print(f"Set negative nitrate values to 0. New min: {wells['nitr_ran'].min()}")

    # Reproject to Wisconsin CRS for accurate distance calculations
    print_section("Reprojecting to Wisconsin Transverse Mercator")
    print("Why? IDW uses distances, which need to be in meters, not degrees")

    wells_proj = reproject_data(wells, "Wells")
    tracts_proj = reproject_data(tracts, "Census Tracts")
    county_proj = reproject_data(county, "County")

    # Verify nitrate values unchanged
    print_section("Verifying Data Integrity")
    original_mean = wells['nitr_ran'].mean()
    reprojected_mean = wells_proj['nitr_ran'].mean()
    print(f"Original nitrate mean:     {original_mean:.6f}")
    print(f"Reprojected nitrate mean:  {reprojected_mean:.6f}")
    print(f"Difference:                {abs(original_mean - reprojected_mean):.10f}")

    if abs(original_mean - reprojected_mean) < 1e-10:
        print(" Nitrate values unchanged (as required)")
    else:
        print("  WARNING: Nitrate values may have changed!")

    # Save cleaned data
    print_section("Saving Cleaned Data")
    save_cleaned_data(wells_proj, 'wells_cleaned.shp', 'Wells')
    save_cleaned_data(tracts_proj, 'tracts_cleaned.shp', 'Census Tracts')
    save_cleaned_data(county_proj, 'county_cleaned.shp', 'County')

    # Visualize
    visualize_reprojected(wells_proj, tracts_proj, county_proj)

    print_header("STEP 2 COMPLETE")

    print(" Summary:")
    print(f"  • Reprojected from EPSG:4269 to EPSG:3071")
    print(f"  • Nitrate values preserved unchanged")
    print(f"  • Cancer rates validated")
    print(f"  • Cleaned data saved to: {PROCESSED_DIR}")
    print(f"\n Data Ready For:")
    print(f"  • IDW interpolation (distances now in meters)")
    print(f"  • Spatial analysis")
    print(f"  • Regression modeling")

    print("\n  Next Step: IDW Interpolation (Step 3)")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()