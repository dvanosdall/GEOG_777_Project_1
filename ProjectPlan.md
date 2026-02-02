# Python-Based Data Analysis + ArcGIS Visualization

## Introduction

Nitrogen-based compounds, such as nitrates in groundwater, can pose significant public health risks, including links to cancer. This project aims to explore the spatial relationship between nitrate concentrations in groundwater and cancer rates in Wisconsin. Using datasets provided in shapefiles:

- **`well_nitrate.shp`**: Contains well nitrate concentrations.  
- **`cancer_tracts.shp`**: Contains cancer cases aggregated at the census tract level.  
- **`cancer_county.shp`**: Contains county-level cancer data (optional, for high-level comparisons).

The goal is to determine whether a statistical relationship exists between groundwater nitrate levels and cancer occurrences. The deliverables require an application layer to:

- Analyze and process data using Python for automation and reproducibility.
- Visualize results (e.g., nitrate heatmaps, cancer choropleths, overlay maps) in ArcGIS.
- Export polished maps, datasets, and analyses for inclusion in the project report and video demo.

This plan leverages Python for data preprocessing, interpolation, and regression analysis while utilizing ArcGIS for visualization and map styling.

---

## 1. Problem Overview

High nitrate concentrations in groundwater pose a significant health concern for Wisconsin communities. Evidence suggests a potential link between nitrate levels and cancer occurrences. To test this hypothesis:

1. **Nitrate Analysis**: Interpolate scattered nitrate well data into a continuous raster (heatmap).  
2. **Cancer Data**: Normalize census-based cancer incidences to adjust for population differences.  
3. **Spatial Alignment**: Align datasets (nitrate raster with census tracts) to conduct correlation analyses.  
4. **Regression**: Perform regression analysis to assess relationships between nitrate levels and cancer rates.  
5. **Outputs**: Communicate analysis results using clean, styled maps and comprehensive reports.

---

## 2. Workflow to Solve the Problem

### Python Workflow: Heavy-Lifting Tasks

1. **Data Preparation**
   - Load and clean provided shapefiles (`well_nitrate.shp`, `cancer_tracts.shp`, `cancer_county.shp`) using **Geopandas**.
   - Reproject (as needed) all datasets to a consistent CRS (e.g., EPSG:4326) using **GDAL/Geopandas**.
   - Validate (as needed) all data attributes (e.g., remove null values and check nitrate and population fields).

2. **IDW Interpolation for Nitrate Surface**
   - Use **SciPy** to implement Inverse Distance Weighting (IDW) for interpolating nitrate data.
   - Generate a continuous nitrate raster (GeoTIFF file) with an adjustable decay coefficient (\( k > 1 \)).
   - Example: Produce raster maps for \( k = 2, 3, 4 \).

3. **Normalize Cancer Rates**
   - Compute population-normalized cancer rates for each census tract:  
     \[
     \text{Cancer Rate} = \frac{\text{Cancer Incidences}}{\text{Population}}
     \]
   - Output as an enriched shapefile (e.g., `cancer_tracts_with_rates.shp`).

4. **Aggregate Data (Alignment)**
   - Use **Rasterstats** to calculate mean nitrate concentrations for each census tract:
     - Overlay raster data with census tract polygons.
     - Compute mean nitrate values per census tract, outputting aligned data.
   - Merge the aggregated nitrate data and normalized cancer rates into one unified dataset (e.g., `aligned_data.csv`).

5. **Regression Analysis**
   - Use **Statsmodels** or **SciPy** to perform regression analysis:
     - Dependent variable (\( y \)): Cancer rates by census tract.
     - Independent variable (\( x \)): Mean nitrate levels per census tract.
   - Export regression outputs, including coefficients, residuals, \( R^2 \), and p-values.

---

### ArcGIS Workflow: Visualization and Outputs

1. **Import Outputs**
   - Load Python-generated nitrate rasters and enriched census tract shapefiles into ArcGIS.
   - Ensure compatibility for creating visualizations.

2. **Map Styling**
   - Create nitrate heatmaps with graduated color schemes to emphasize concentration differences.
   - Generate cancer rate choropleths using census tract data.
   - Overlay nitrate heatmaps and cancer choropleths for spatial correlation visualization.

3. **Final Map Elements**
   - Add titles, legends, scale bars, and north arrows.
   - Annotate any spatial trends (e.g., regions with high nitrate and high cancer rates).

4. **Export Results**
   - Export polished maps as high-resolution PNG, TIFF, or PDF files for the project report.

---

### High-Level Workflow Diagram

The following diagram illustrates the workflow for the data processing steps:

![Diagram](Diagram.png)

---

## Steps
1. **Input Shapefiles:**
   - Load the following shapefiles from the `g777_project1_shapefiles` folder:
     - [well_nitrate.shp](g777_project1_shapefiles/well_nitrate.shp)
     - [cancer_tracts.shp](g777_project1_shapefiles/cancer_tracts.shp)
     - [cancer_county.shp](g777_project1_shapefiles/cancer_county.shp)

2. **Data Preparation & Cleaning:**
   - Perform necessary data preprocessing and cleaning to prepare for analysis.

3. **Interpolation (IDW):**
   - Create a continuous raster surface for nitrate data.
   - Allow user adjustment of the \( k > 1 \) parameter.

4. **Normalization of Cancer Rates:**
   - Perform population-based normalization at the tract level.

5. **Data Alignment:**
   - Align raster data with census boundaries using zonal statistics.
   - Combine nitrate and cancer data into a single unified table.

6. **Statistical Regression:**
   - Perform regression analysis comparing nitrate data to cancer rates.
   - Output metrics such as \( R^2 \) and p-values.

7. **Visualization & Map Creation:**
   - Generate the following map types:
     - Heatmaps (nitrate data).
     - Choropleths (cancer rates).
     - Overlay maps for comparative insights.