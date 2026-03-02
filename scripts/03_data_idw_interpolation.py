"""
Author: David Vanosdall
Course: GEOG 777
Date: 2026-02-10
Step 3: IDW Interpolation

Additional Information for script help
Purpose: Interpolate nitrate values across Wisconsin using Inverse Distance Weighting (IDW)

WHY? Currently have point data (wells) but need a continuous surface to compare with census
tracts. IDW estimates nitrate levels at unsampled locations by weighing nearby well
values - closer wells have more influence.

The k parameter controls this:
  higher k = nearby wells matter much more
  lower k = influence spreads farther.

IMPORTANT: This will create a NEW interpolated surface - original well measurements are
preserved unchanged. Think of it like estimating temperature between weather stations -
the station readings don't change, but we estimate values in between.

IDW Formula:
  For each grid cell, value = Σ(wi × vi) / Σ(wi)
  where: wi = 1 / distance^k

User can adjust k parameter via command line (default k=2.0)
"""

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from pathlib import Path
import argparse

def cleanup_maps_folder(maps_dir, results_dir):
    """
    Delete Step 3–5 PNGs in maps_dir and nitrate_idw_k*.tif files in results_dir.
    Keeps Step 1/2 static overview images intact.
    Also deletes maps.zip.
    """
    from pathlib import Path
    maps_dir = Path(maps_dir)
    results_dir = Path(results_dir)

    # Delete Step 3–5 PNGs
    png_patterns = ['03_*.png', '04_*.png', '05_*.png', 'maps.zip']
    for pattern in png_patterns:
        for fpath in maps_dir.glob(pattern):
            fpath.unlink()
            print(f"Deleted {fpath}")

    # Delete all Step 3 IDW rasters
    for tif_file in results_dir.glob('nitrate_idw_k*.tif'):
        tif_file.unlink()
        print(f"Deleted {tif_file}")

def idw_interpolation(points, values, grid_x, grid_y, k=2):
    """
    Inverse Distance Weighting interpolation

    Parameters:
    -----------
    points : array
        Well locations (x, y coordinates)
    values : array
        Nitrate measurements at wells
    grid_x, grid_y : arrays
        Grid coordinates for interpolation
    k : float
        Power parameter (higher = more weight to nearby points)

    Returns:
    --------
    grid_values : array
        Interpolated nitrate values at grid points

    Theory:
    -------
    IDW assumes spatial autocorrelation: nearby things are more similar.
    Each grid cell's value = weighted average of all wells.
    Weights = 1 / distance^k

    Higher k = sharper distance decay (only nearby wells matter)
    Lower k = gentler decay (distant wells still have influence)
    """

    print(f"   Running IDW with k={k}...")
    print(f"   Grid shape: {grid_x.shape}")
    print(f"   Number of wells: {len(points)}")

    # Build KD-tree for efficient nearest neighbor search
    tree = cKDTree(points)

    # Flatten grid for vectorized computation
    grid_points = np.c_[grid_x.ravel(), grid_y.ravel()]

    # Find distances to all wells for each grid point
    distances, indices = tree.query(grid_points, k=len(points))

    # Handle case where distance is exactly 0 (grid point = well location)
    # Set minimum distance to avoid division by zero
    distances = np.maximum(distances, 1e-10)

    # Calculate weights: w = 1 / d^k
    weights = 1.0 / (distances ** k)

    # Normalize weights so they sum to 1
    weights = weights / weights.sum(axis=1, keepdims=True)

    # Calculate weighted average
    grid_values = np.sum(weights * values[indices], axis=1)

    # Reshape back to grid
    grid_values = grid_values.reshape(grid_x.shape)

    print(f"   Interpolation complete")
    print(f"   Value range: {grid_values.min():.2f} to {grid_values.max():.2f}")

    return grid_values


def create_grid(wells, tracts=None, cell_size=1000):
    """
    Create regular grid covering well locations

    Parameters:
    -----------
    wells : GeoDataFrame
        Well point locations
    cell_size : float
        Grid cell size in meters

    Returns:
    --------
    grid_x, grid_y : arrays
        Meshgrid coordinates
    transform : dict
        Grid transformation parameters
    """

    print(f"   Creating grid with {cell_size}m cells...")

    if tracts is not None:
        minx, miny, maxx, maxy = tracts.total_bounds
        print("   Using TRACTS extent for grid (recommended)")
    else:
        minx, miny, maxx, maxy = wells.total_bounds
        print("   Using WELLS extent for grid")

    # Add buffer
    buffer = cell_size * 2
    minx -= buffer
    miny -= buffer
    maxx += buffer
    maxy += buffer

    x = np.arange(minx, maxx, cell_size)
    y = np.arange(miny, maxy, cell_size)
    grid_x, grid_y = np.meshgrid(x, y)

    transform = {
        'minx': minx, 'miny': miny, 'maxx': maxx, 'maxy': maxy,
        'cell_size': cell_size
    }

    print(f"   Grid dimensions: {len(y)} rows x {len(x)} cols")
    print(f"   Extent: {minx:.0f}, {miny:.0f}, {maxx:.0f}, {maxy:.0f}")

    return grid_x, grid_y, transform


def save_raster_as_geotiff(raster, transform, output_path, crs='EPSG:3071'):
    """
    Save raster as GeoTIFF using WKT (bypasses PROJ database issues)
    Falls back to pickle if any errors occur
    """

    try:
        import rasterio
        from rasterio.transform import from_origin
        from rasterio.crs import CRS

        # Create affine transform
        affine_transform = from_origin(
            transform['minx'],
            transform['maxy'],
            transform['cell_size'],
            transform['cell_size']
        )

        # Use WKT definition instead of EPSG code (bypasses PROJ database)
        # Wisconsin Transverse Mercator (EPSG:3071) in WKT format
        wkt_3071 = '''PROJCS["NAD83 / Wisconsin Transverse Mercator",
    GEOGCS["NAD83",
        DATUM["North_American_Datum_1983",
            SPHEROID["GRS 1980",6378137,298.257222101,
                AUTHORITY["EPSG","7019"]],
            AUTHORITY["EPSG","6269"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.0174532925199433,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4269"]],
    PROJECTION["Transverse_Mercator"],
    PARAMETER["latitude_of_origin",0],
    PARAMETER["central_meridian",-90],
    PARAMETER["scale_factor",0.9996],
    PARAMETER["false_easting",520000],
    PARAMETER["false_northing",-4480000],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH],
    AUTHORITY["EPSG","3071"]]'''

        # Create CRS from WKT (doesn't use PROJ database)
        crs_obj = CRS.from_wkt(wkt_3071)

        # Write GeoTIFF
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=raster.shape[0],
            width=raster.shape[1],
            count=1,
            dtype=raster.dtype,
            crs=crs_obj,
            transform=affine_transform,
            nodata=-9999
        ) as dst:
            # Flip raster vertically for correct north-up orientation
            dst.write(np.flipud(raster), 1)

        print(f"   Saved GeoTIFF: {output_path}")
        print(f"   Used WKT definition (bypassed PROJ database)")
        return True

    except Exception as e:
        print(f"   GeoTIFF failed: {str(e)[:100]}")

        # Fallback: Save as pickle
        import pickle

        pickle_path = output_path.with_suffix('.pkl')

        extent = (
            transform['minx'],
            transform['minx'] + raster.shape[1] * transform['cell_size'],
            transform['maxy'] - raster.shape[0] * transform['cell_size'],
            transform['maxy']
        )

        data = {
            'raster': raster,
            'transform': transform,
            'extent': extent,
            'crs': crs,
            'cell_size': transform['cell_size'],
            'shape': raster.shape,
            'min_value': float(raster.min()),
            'max_value': float(raster.max()),
            'mean_value': float(raster.mean())
        }

        with open(pickle_path, 'wb') as f:
            pickle.dump(data, f)

        print(f"   Saved as pickle instead: {pickle_path}")
        print(f"   Stats: min={data['min_value']:.2f}, max={data['max_value']:.2f}, mean={data['mean_value']:.2f}")

        # Save metadata
        meta_path = output_path.with_suffix('.txt')
        with open(meta_path, 'w') as f:
            f.write(f"IDW Raster Metadata\n")
            f.write(f"===================\n\n")
            f.write(f"Shape: {raster.shape[0]} rows x {raster.shape[1]} cols\n")
            f.write(f"CRS: {crs}\n")
            f.write(f"Cell Size: {transform['cell_size']} meters\n")
            f.write(f"Extent: {extent}\n")
            f.write(f"\nStatistics:\n")
            f.write(f"  Min: {data['min_value']:.4f}\n")
            f.write(f"  Max: {data['max_value']:.4f}\n")
            f.write(f"  Mean: {data['mean_value']:.4f}\n")

        print(f"   Metadata: {meta_path}")

        return False


def visualize_idw(wells, raster, transform, k, output_path):
    """
    Create visualization of IDW results
    """

    print(f"   Creating visualization...")

    fig, ax = plt.subplots(figsize=(12, 10))

    # Calculate extent for imshow
    extent = (
        transform['minx'],
        transform['minx'] + raster.shape[1] * transform['cell_size'],
        transform['maxy'] - raster.shape[0] * transform['cell_size'],
        transform['maxy']
    )

    # Plot raster (already flipped in save function, so flip here too for consistency)
    im = ax.imshow(
        np.flipud(raster),
        extent=extent,
        cmap='RdYlGn_r',
        alpha=0.7,
        aspect='equal'
    )

    # Plot well locations
    wells.plot(
        ax=ax,
        color='black',
        markersize=20,
        edgecolor='white',
        linewidth=0.5,
        alpha=0.6,
        zorder=2
    )

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Nitrate Concentration (mg/L)', rotation=270, labelpad=20, fontsize=12)

    # Labels
    ax.set_xlabel('Easting (m)', fontsize=12)
    ax.set_ylabel('Northing (m)', fontsize=12)
    ax.set_title(f'IDW Interpolation of Nitrate Concentrations (k={k})', fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Format axis labels
    ax.ticklabel_format(style='plain', axis='both')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   Saved visualization: {output_path}")


def compare_k_values(wells, grid_x, grid_y, transform, output_dir):
    """
    Compare IDW results with different k values
    """

    print("\n   Comparing k values: 2, 3, 4...")

    k_values = [2, 3, 4]
    rasters = []

    # Get well coordinates and values
    points = np.array([[geom.x, geom.y] for geom in wells.geometry])
    values = wells['nitr_ran'].values

    # Run IDW for each k
    for k in k_values:
        raster = idw_interpolation(points, values, grid_x, grid_y, k=k)
        rasters.append(raster)

        # Save individual raster
        output_path = output_dir / f'nitrate_idw_k{k}.tif'
        save_raster_as_geotiff(raster, transform, output_path)

    # Create comparison visualization
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    extent = (
        transform['minx'],
        transform['minx'] + grid_x.shape[1] * transform['cell_size'],
        transform['maxy'] - grid_x.shape[0] * transform['cell_size'],
        transform['maxy']
    )

    for idx, (k, raster, ax) in enumerate(zip(k_values, rasters, axes)):
        im = ax.imshow(
            np.flipud(raster),
            extent=extent,
            cmap='RdYlGn_r',
            alpha=0.7,
            vmin=min([r.min() for r in rasters]),
            vmax=max([r.max() for r in rasters])
        )

        wells.plot(ax=ax, color='black', markersize=10, edgecolor='white', linewidth=0.5, alpha=0.6)

        ax.set_title(f'k = {k}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Easting (m)')
        ax.set_ylabel('Northing (m)')
        ax.grid(True, alpha=0.3)
        ax.ticklabel_format(style='plain')

    # Shared colorbar
    fig.colorbar(im, ax=axes, fraction=0.046, pad=0.04, label='Nitrate (mg/L)')

    plt.suptitle('IDW Interpolation Comparison: Effect of k Parameter', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = output_dir / '../maps/03_idw_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   Saved comparison: {output_path}")


def main():
    """
    Main execution function
    """

    # Clean up old map files
    base_dir = Path(__file__).parent.parent
    maps_dir = base_dir / 'outputs' / 'maps'
    results_dir = base_dir / 'outputs' / 'results'
    cleanup_maps_folder(maps_dir, results_dir)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='IDW Interpolation of Nitrate Data')
    parser.add_argument('--k', type=float, default=2.0, help='Power parameter for IDW (default: 2.0)')
    parser.add_argument('--cell-size', type=int, default=1000, help='Grid cell size in meters (default: 1000)')
    parser.add_argument('--compare', action='store_true', help='Compare different k values (2, 3, 4)')
    args = parser.parse_args()

    print("=" * 70)
    print("                      STEP 3: IDW INTERPOLATION")
    print("=" * 70)
    print()

    # Setup paths
    base_dir = Path(__file__).parent.parent
    wells_path = base_dir / 'data' / 'processed' / 'wells_cleaned.shp'
    tracts_path = base_dir / 'data' / 'processed' / 'tracts_cleaned.shp'

    output_dir = base_dir / 'outputs' / 'results'
    maps_dir = base_dir / 'outputs' / 'maps'

    output_dir.mkdir(parents=True, exist_ok=True)
    maps_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("-" * 70)
    print("Loading Cleaned Data")
    print("-" * 70)
    wells = gpd.read_file(wells_path)
    print(f"   Loaded {len(wells)} wells")
    print(f"   Nitrate range: {wells['nitr_ran'].min():.2f} to {wells['nitr_ran'].max():.2f} mg/L")
    print()
    tracts = gpd.read_file(tracts_path)
    print(f"   Loaded {len(tracts)} census tracts (for grid extent)")

    # Create grid
    print("-" * 70)
    print("Creating Interpolation Grid")
    print("-" * 70)
    grid_x, grid_y, transform = create_grid(wells, tracts=tracts, cell_size=args.cell_size)
    print()

    # Get well coordinates and values
    points = np.array([[geom.x, geom.y] for geom in wells.geometry])
    values = wells['nitr_ran'].values

    if args.compare:
        # Comparison mode
        print("-" * 70)
        print("Running Comparison Mode")
        print("-" * 70)
        compare_k_values(wells, grid_x, grid_y, transform, output_dir)
    else:
        # Single k value
        print("-" * 70)
        print(f"Running IDW (k={args.k})")
        print("-" * 70)
        raster = idw_interpolation(points, values, grid_x, grid_y, k=args.k)
        print()

        # Visualize
        print("-" * 70)
        print("Creating Visualization")
        print("-" * 70)
        viz_path = maps_dir / f'03_idw_k{args.k}.png'
        visualize_idw(wells, raster, transform, args.k, viz_path)
        print()

        # Save raster
        print("-" * 70)
        print("Saving Raster")
        print("-" * 70)
        output_path = output_dir / f'nitrate_idw_k{args.k}.tif'
        save_raster_as_geotiff(raster, transform, output_path)

    print()
    print("=" * 70)
    print("                           STEP 3 COMPLETE")
    print("=" * 70)
    print()
    print(" Summary:")
    print(f"  - IDW interpolation completed")
    print(f"  - Cell size: {args.cell_size} meters")
    print(f"  - k value: {args.k if not args.compare else '2, 3, 4 (comparison)'}")
    print(f"  - Results saved to: {output_dir}")
    print(f"  - Maps saved to: {maps_dir}")
    print()
    print(" Next Steps:")
    print("  - Import GeoTIFF into ArcGIS for visualization")
    print("  - Use raster for zonal statistics with census tracts")
    print("  - Proceed to Step 4: Extract values to census tracts")
    print()
    print(" Usage Examples:")
    print("  python scripts/03_idw_interpolation.py --k 2.5")
    print("  python scripts/03_idw_interpolation.py --compare")
    print("  python scripts/03_idw_interpolation.py --k 3 --cell-size 500")
    print("=" * 70)


if __name__ == '__main__':
    main()