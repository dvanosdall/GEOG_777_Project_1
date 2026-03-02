"""
Author: David Vanosdall
Course: GEOG 777
Date: 2026-02-10
Step 4: Extract Nitrate Values to Census Tracts

Purpose: Use zonal statistics to calculate average nitrate exposure per census tract.
Takes continuous IDW raster surface and summarizes to polygon boundaries.

WHY? Regression analysis needs one nitrate value per tract to compare with health outcomes.
Zonal statistics gives us the spatial average of all raster cells within each tract boundary.

Output: census_tracts_with_nitrate.shp ready for Step 5 (regression analysis)
"""

import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import warnings
import logging


def load_raster(raster_path):
    """
    Load raster and return as array with metadata

    Purpose: Read the IDW interpolated raster created in Step 3 and extract
    the data array, spatial transformation, and coordinate system.

    Returns:
    --------
    array : numpy array
        Raster cell values (nitrate concentrations)
    affine : Affine transform
        Spatial transformation matrix (links pixel coordinates to real-world coordinates)
    crs : CRS object
        Coordinate reference system
    """

    print(f"   Loading raster: {raster_path.name}")

    # Suppress PROJ database warnings
    # These are cosmetic warnings due to PROJ database version mismatch
    # They do not affect data accuracy or processing
    logging.getLogger('rasterio').setLevel(logging.ERROR)

    try:
        # Suppress Python warnings temporarily during file read
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')

            # Open raster file using rasterio context manager
            with rasterio.open(raster_path) as src:
                array = src.read(1)
                affine = src.transform
                crs = src.crs
                bounds = src.bounds

        # Restore normal logging level after successful read
        logging.getLogger('rasterio').setLevel(logging.WARNING)

        # Display raster information for verification
        print(f"   Raster shape: {array.shape}")
        print(f"   Value range: {array.min():.2f} to {array.max():.2f}")
        print(f"   CRS: EPSG:3071 (Wisconsin Transverse Mercator)")

        return array, affine, crs

    except Exception as e:
        print(f"   ERROR loading raster: {str(e)}")
        raise


def extract_zonal_stats(tracts, raster_path):
    """
    Calculate zonal statistics for each census tract

    Purpose: For each census tract polygon, calculate summary statistics
    from all raster cells that fall within that tract. This gives us a
    single nitrate value per tract by averaging all raster cells inside.

    Zonal statistics = summarizing raster values within polygon boundaries

    Theory:
    We have continuous raster data (IDW surface) and discrete polygons (census tracts).
    To analyze by census tract, we need to extract the raster values within each
    polygon and calculate meaningful summaries (mean, min, max, std dev).

    Parameters:
    -----------
    tracts : GeoDataFrame
        Census tract polygons (1401 tracts in Wisconsin)
    raster_path : Path
        Path to IDW raster file

    Returns:
    --------
    GeoDataFrame with added nitrate statistics columns:
        - nitr_mean: Average nitrate across all cells in tract
        - nitr_min: Minimum nitrate value in tract
        - nitr_max: Maximum nitrate value in tract
        - nitr_std: Standard deviation (variability within tract)
        - nitr_count: Number of raster cells in tract
    """

    print(f"   Calculating zonal statistics for {len(tracts)} tracts...")
    print(f"   This may take 1-2 minutes...")

    try:
        # Suppress PROJ warnings during calculation
        logging.getLogger('rasterio').setLevel(logging.ERROR)

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)

            # Calculate statistics for each polygon using rasterstats library
            # This is the core operation: extract raster values within each polygon
            stats = zonal_stats(
                tracts,
                str(raster_path),
                stats=['mean', 'min', 'max', 'std', 'count'],
                nodata=-9999,
                all_touched=True
            )

        # Restore normal logging after calculation
        logging.getLogger('rasterio').setLevel(logging.WARNING)

        print(f"   Zonal statistics complete!")

    except Exception as e:
        print(f"   ERROR in zonal statistics: {str(e)}")
        print(f"   This may be due to CRS mismatch or raster issues")
        raise

    # Create a copy to avoid modifying original GeoDataFrame
    tracts = tracts.copy()

    # Add statistics as new columns to the GeoDataFrame
    # Column names limited to 10 characters for shapefile compatibility
    # Handle None values (tracts with no raster coverage) by converting to NaN
    tracts['nitr_mean'] = [s['mean'] if s['mean'] is not None else np.nan for s in stats]
    tracts['nitr_min'] = [s['min'] if s['min'] is not None else np.nan for s in stats]
    tracts['nitr_max'] = [s['max'] if s['max'] is not None else np.nan for s in stats]
    tracts['nitr_std'] = [s['std'] if s['std'] is not None else np.nan for s in stats]
    tracts['nitr_count'] = [s['count'] if s['count'] is not None else 0 for s in stats]
    zero_cells = (tracts["nitr_count"] == 0).sum()
    print(f"   DEBUG: {zero_cells} tracts have nitr_count == 0 (no raster cells captured)")

    # Check for missing values
    # Some tracts may fall outside the raster extent (no well data nearby)
    missing = tracts['nitr_mean'].isna().sum()
    if missing > 0:
        print(f"   WARNING: {missing} tracts have no raster coverage")
        print(f"   This may be due to tracts outside the interpolation area")

    # Filter to tracts with valid data for statistical summary
    valid_tracts = tracts[tracts['nitr_mean'].notna()]

    # Display summary statistics for verification
    print(f"   Nitrate statistics (n={len(valid_tracts)} tracts with data):")
    print(f"     Mean: {valid_tracts['nitr_mean'].mean():.2f} mg/L")
    print(f"     Min: {valid_tracts['nitr_mean'].min():.2f} mg/L")
    print(f"     Max: {valid_tracts['nitr_mean'].max():.2f} mg/L")
    print(f"     Std: {valid_tracts['nitr_mean'].std():.2f} mg/L")

    return tracts


def create_choropleth(tracts, output_path, column='nitr_mean'):
    """
    Create choropleth map of nitrate exposure

    Purpose: Visualize spatial patterns of nitrate exposure across Wisconsin
    census tracts. Choropleth maps color polygons by data values, making it
    easy to see geographic patterns and clusters.

    Parameters:
    -----------
    tracts : GeoDataFrame
        Census tracts with nitrate data
    output_path : Path
        Where to save the map image
    column : str
        Column to visualize (default: nitr_mean)
    """

    print(f"   Creating choropleth map...")

    # Create figure and axis for plotting
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot census tracts colored by nitrate concentration
    # Uses a diverging color scheme: red (high) to yellow (medium) to green (low)
    tracts.plot(
        column=column,
        ax=ax,
        cmap='RdYlGn_r',
        edgecolor='black',
        linewidth=0.3,
        legend=True,
        legend_kwds={
            'label': 'Mean Nitrate (mg/L)',
            'orientation': 'vertical',
            'shrink': 0.8
        },
        missing_kwds={'color': 'lightgrey', 'label': 'No Data'}
    )

    # Add axis labels for coordinate reference
    ax.set_xlabel('Easting (m)', fontsize=12)
    ax.set_ylabel('Northing (m)', fontsize=12)

    # Add descriptive title
    ax.set_title('Average Nitrate Exposure by Census Tract', fontsize=14, fontweight='bold')

    # Add grid for easier visual reference
    ax.grid(True, alpha=0.3, linestyle='--')

    # Format axis tick labels to show full numbers (not scientific notation)
    ax.ticklabel_format(style='plain', axis='both')

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save figure at high resolution
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    # Close figure to free memory
    plt.close()

    print(f"   Saved map: {output_path}")


def create_summary_stats(tracts, output_path):
    """
    Create summary statistics visualization

    Purpose: Create a 4-panel figure showing different views of the nitrate data:
    1. Histogram: Distribution of nitrate values across tracts
    2. Boxplot: Summary statistics (quartiles, outliers)
    3. Area vs Nitrate: Does tract size affect nitrate levels?
    4. Variability: How much do nitrate levels vary within tracts?

    These visualizations help identify patterns, outliers, and data quality issues.

    Parameters:
    -----------
    tracts : GeoDataFrame
        Census tracts with nitrate data
    output_path : Path
        Where to save the summary figure
    """

    print(f"   Creating summary statistics...")

    # Filter to only tracts with valid nitrate data
    tracts_data = tracts[tracts['nitr_mean'].notna()].copy()

    # Create 2x2 grid of subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Panel 1: Histogram showing distribution of nitrate values
    # Shows how nitrate concentrations are spread across census tracts
    # Helps identify if data is normally distributed, skewed, or has multiple peaks
    ax = axes[0, 0]
    tracts_data['nitr_mean'].hist(bins=30, ax=ax, edgecolor='black', alpha=0.7, color='steelblue')
    ax.set_xlabel('Mean Nitrate (mg/L)')
    ax.set_ylabel('Number of Tracts')
    ax.set_title('Distribution of Tract-Level Nitrate Exposure')

    # Add vertical lines for mean and median
    ax.axvline(tracts_data['nitr_mean'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax.axvline(tracts_data['nitr_mean'].median(), color='orange', linestyle='--', linewidth=2, label='Median')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: Boxplot showing quartiles and outliers
    # Shows median, 25th/75th percentiles, and potential outliers
    # Useful for identifying extreme values
    ax = axes[0, 1]
    box = ax.boxplot(tracts_data['nitr_mean'].dropna(), patch_artist=True)
    box['boxes'][0].set_facecolor('lightblue')
    ax.set_ylabel('Mean Nitrate (mg/L)')
    ax.set_title('Nitrate Exposure Summary')
    ax.set_xticklabels(['Census Tracts'])
    ax.grid(True, alpha=0.3, axis='y')

    # Panel 3: Scatter plot of tract area vs nitrate concentration
    # Explores relationship between census tract size and nitrate levels
    # Large tracts might average out local variation, small tracts might be more variable
    ax = axes[1, 0]

    # Calculate tract area in square kilometers
    tracts_data['area_km2'] = tracts_data.geometry.area / 1e6

    # Create scatter plot
    ax.scatter(tracts_data['area_km2'], tracts_data['nitr_mean'], alpha=0.5, color='green')
    ax.set_xlabel('Tract Area (km²)')
    ax.set_ylabel('Mean Nitrate (mg/L)')
    ax.set_title('Tract Area vs Nitrate Exposure')
    ax.grid(True, alpha=0.3)

    # Panel 4: Scatter plot of raster cell count vs standard deviation
    # Shows relationship between number of cells sampled and spatial variability
    # More cells = better representation, high std dev = heterogeneous tract
    ax = axes[1, 1]
    ax.scatter(tracts_data['nitr_count'], tracts_data['nitr_std'], alpha=0.5, color='purple')
    ax.set_xlabel('Number of Raster Cells in Tract')
    ax.set_ylabel('Nitrate Std Dev (mg/L)')
    ax.set_title('Spatial Variability within Tracts')
    ax.grid(True, alpha=0.3)

    # Adjust layout to prevent overlapping labels
    plt.tight_layout()

    # Save figure at high resolution
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    # Close figure to free memory
    plt.close()

    print(f"   Saved summary: {output_path}")


def main():
    """
    Main execution function

    Controls the workflow:
    1. Parse command line arguments
    2. Load census tracts and IDW raster
    3. Extract zonal statistics
    4. Save results as shapefile and CSV
    5. Create visualizations
    """

    # Parse command line arguments
    # Allows user to specify which k value raster to use
    parser = argparse.ArgumentParser(description='Extract Nitrate to Census Tracts')
    parser.add_argument('--k', type=float, default=2.0, help='k value used in IDW (default: 2.0)')
    args = parser.parse_args()

    # Print header
    print("=" * 70)
    print("              STEP 4: EXTRACT NITRATE TO CENSUS TRACTS")
    print("=" * 70)
    print()

    # Setup file paths
    base_dir = Path(__file__).parent.parent
    tracts_path = base_dir / 'data' / 'processed' / 'tracts_cleaned.shp'
    raster_path = base_dir / 'outputs' / 'results' / f'nitrate_idw_k{args.k}.tif'

    output_dir = base_dir / 'data' / 'processed'
    maps_dir = base_dir / 'outputs' / 'maps'

    # Create output directories if they don't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    maps_dir.mkdir(parents=True, exist_ok=True)

    # Check that required input files exist
    if not raster_path.exists():
        print(f"ERROR: Raster not found: {raster_path}")
        print(f"Run Step 3 first: python scripts/03_idw_interpolation.py --k {args.k}")
        return

    if not tracts_path.exists():
        print(f"ERROR: Census tracts not found: {tracts_path}")
        return

    # Load census tract data
    print("-" * 70)
    print("Loading Data")
    print("-" * 70)
    tracts = gpd.read_file(tracts_path)
    print(f"   Loaded {len(tracts)} census tracts")
    print(f"   CRS: {tracts.crs}")
    print()

    # Load IDW raster and display metadata
    print("-" * 70)
    print("Loading IDW Raster")
    print("-" * 70)
    load_raster(raster_path)
    print()

    # Extract zonal statistics for each census tract
    # This is the core operation of Step 4
    print("-" * 70)
    print("Extracting Zonal Statistics")
    print("-" * 70)
    tracts = extract_zonal_stats(tracts, raster_path)
    print()

    # Save results to disk
    print("-" * 70)
    print("Saving Results")
    print("-" * 70)

    # Save as shapefile for use in GIS software
    output_path = output_dir / 'census_tracts_with_nitrate.shp'

    # Suppress shapefile format warnings
    # Shapefiles have 10-character column name limit, already handled with short names
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Column names longer than 10 characters')
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        tracts.to_file(output_path)

    print(f"   Saved: {output_path}")

    # Save as CSV for easy viewing in Excel or text editor
    csv_path = output_dir / 'census_tracts_with_nitrate.csv'
    tracts_csv = tracts.drop(columns='geometry')
    tracts_csv.to_csv(csv_path, index=False)
    print(f"   Saved: {csv_path}")
    print()

    # Create visualizations
    print("-" * 70)
    print("Creating Visualizations")
    print("-" * 70)

    # Create choropleth map showing spatial patterns
    choropleth_path = maps_dir / '04_nitrate_by_tract.png'
    create_choropleth(tracts, choropleth_path)

    # Create summary statistics figure
    summary_path = maps_dir / '04_summary_statistics.png'
    create_summary_stats(tracts, summary_path)
    print()

    # Calculate summary statistics for final report
    valid_count = tracts['nitr_mean'].notna().sum()
    mean_nitrate = tracts['nitr_mean'].mean()
    min_nitrate = tracts['nitr_mean'].min()
    max_nitrate = tracts['nitr_mean'].max()

    # Print completion summary
    print("=" * 70)
    print("                         STEP 4 COMPLETE")
    print("=" * 70)
    print()
    print(" Summary:")
    print(f"  - Extracted nitrate values for {len(tracts)} census tracts")
    print(f"  - {valid_count} tracts with valid data")
    print(f"  - Mean nitrate: {mean_nitrate:.2f} mg/L")
    print(f"  - Range: {min_nitrate:.2f} to {max_nitrate:.2f} mg/L")
    print(f"  - Output: {output_path}")
    print()
    print(" Next Steps:")
    print("  - Review choropleth map to see spatial patterns")
    print("  - Check for tracts with missing data")
    print("  - Proceed to Step 5: Regression analysis")
    print()
    print(" Usage:")
    print(f"  python scripts/04_extract_to_tracts.py --k {args.k}")
    print("=" * 70)


if __name__ == '__main__':
    main()