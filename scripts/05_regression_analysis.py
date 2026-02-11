"""
Author: David Vanosdall
Course: GEOG 777
Date: 2026-02-10
Step 5: Regression Analysis - Nitrate vs Cancer

Purpose: Analyze the relationship between nitrate exposure and cancer rates
at the census tract level using linear regression.

Research Question: Do higher nitrate levels predict higher cancer rates?

Statistical Method: Ordinary Least Squares (OLS) Linear Regression
    Model: cancer_rate = Beta0 + Beta1 * nitrate_mean + ε

    Where:
    - Beta0 = intercept (baseline cancer rate)
    - Beta1 = slope (change in cancer rate per mg/L nitrate)
    - ε = error term (unexplained variation)

Output: Statistical report, visualizations, and model diagnostics
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
import argparse
import warnings

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100


def load_data(data_path):
    """
    Load census tracts with nitrate and cancer data

    Purpose: Read the combined dataset from Step 4 that contains both
    nitrate exposure (from IDW) and cancer rates (from original data)

    Returns:
    --------
    GeoDataFrame with columns:
        - GEOID10: Census tract identifier
        - nitr_mean: Average nitrate (mg/L)
        - canrate: Cancer rate (cases per person)
        - geometry: Tract boundaries
    """

    print(f"   Loading data from: {data_path.name}")

    gdf = gpd.read_file(data_path)

    print(f"   Total tracts: {len(gdf)}")
    print(f"   Columns: {gdf.columns.tolist()}")

    return gdf


def prepare_data(gdf):
    """
    Prepare data for regression analysis

    Purpose: Filter to only tracts with valid data for both variables
    and handle any missing values or outliers.

    Data Quality Checks:
    - Remove tracts with missing nitrate data (no wells nearby)
    - Remove tracts with missing cancer data
    - Check for extreme outliers
    - Verify data ranges are reasonable

    Parameters:
    -----------
    gdf : GeoDataFrame
        Raw data with potential missing values

    Returns:
    --------
    DataFrame with clean X (nitrate) and y (cancer) variables
    """

    print("\n" + "-" * 70)
    print("Preparing Data for Analysis")
    print("-" * 70)

    # Create analysis dataframe
    df = gdf[['GEOID10', 'nitr_mean', 'canrate']].copy()

    print(f"   Starting with {len(df)} tracts")

    # Remove missing nitrate values
    # These are tracts outside the interpolation area
    df_clean = df.dropna(subset=['nitr_mean'])
    removed_nitrate = len(df) - len(df_clean)
    print(f"   Removed {removed_nitrate} tracts with missing nitrate data")

    # Remove missing cancer values
    df_clean = df_clean.dropna(subset=['canrate'])
    removed_cancer = len(df) - removed_nitrate - len(df_clean)
    print(f"   Removed {removed_cancer} tracts with missing cancer data")

    print(f"   Final sample size: {len(df_clean)} tracts")

    # Display summary statistics
    print("\n   Summary Statistics:")
    print(f"     Nitrate (mg/L):")
    print(f"       Mean: {df_clean['nitr_mean'].mean():.2f}")
    print(f"       Std:  {df_clean['nitr_mean'].std():.2f}")
    print(f"       Min:  {df_clean['nitr_mean'].min():.2f}")
    print(f"       Max:  {df_clean['nitr_mean'].max():.2f}")
    print(f"\n     Cancer Rate:")
    print(f"       Mean: {df_clean['canrate'].mean():.4f}")
    print(f"       Std:  {df_clean['canrate'].std():.4f}")
    print(f"       Min:  {df_clean['canrate'].min():.4f}")
    print(f"       Max:  {df_clean['canrate'].max():.4f}")

    return df_clean


def perform_regression(df):
    """
    Perform linear regression analysis

    Purpose: Test the hypothesis that nitrate levels predict cancer rates.
    Uses Ordinary Least Squares (OLS) regression to estimate the relationship.

    Mathematical Model:
    Y = Beta0 + Beta1*X + ε

    Where:
    - Y = cancer rate (dependent variable)
    - X = nitrate level (independent variable)
    - Beta0 = intercept (expected cancer rate when nitrate = 0)
    - Beta1 = slope (change in cancer rate per unit nitrate)
    - ε = residual error

    Statistical Tests:
    - R² (R-squared): Proportion of variance explained (0 to 1)
    - p-value: Probability result is due to chance (< 0.05 = significant)
    - F-statistic: Overall model significance

    Parameters:
    -----------
    df : DataFrame
        Clean data with nitr_mean and canrate columns

    Returns:
    --------
    Dictionary containing regression results and diagnostics
    """

    print("\n" + "-" * 70)
    print("Performing Linear Regression")
    print("-" * 70)

    # Extract variables
    X = df['nitr_mean'].values
    y = df['canrate'].values
    n = len(X)

    # Calculate regression statistics using scipy
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)

    # Calculate predicted values and residuals
    y_pred = intercept + slope * X
    residuals = y - y_pred

    # Calculate R-squared
    r_squared = r_value ** 2

    # Calculate adjusted R-squared
    # Adjusts for number of predictors (more conservative than R²)
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - 2)

    # Calculate Mean Squared Error (MSE) and Root MSE
    mse = np.mean(residuals ** 2)
    rmse = np.sqrt(mse)

    # Calculate confidence intervals for slope
    # 95% confidence interval
    t_critical = stats.t.ppf(0.975, n - 2)
    ci_lower = slope - t_critical * std_err
    ci_upper = slope + t_critical * std_err

    # Calculate F-statistic
    # Tests overall model significance
    ss_total = np.sum((y - np.mean(y)) ** 2)
    ss_residual = np.sum(residuals ** 2)
    ss_regression = ss_total - ss_residual
    f_statistic = (ss_regression / 1) / (ss_residual / (n - 2))

    # Print results
    print("\n   Regression Results:")
    print(f"     Sample Size (n): {n}")
    print(f"\n     Model: cancer_rate = {intercept:.6f} + {slope:.6f} * nitrate")
    print(f"\n     Intercept (Beta0): {intercept:.6f}")
    print(f"     Slope (Beta1):     {slope:.6f} ± {std_err:.6f}")
    print(f"     95% CI:         [{ci_lower:.6f}, {ci_upper:.6f}]")
    print(f"\n     R-squared (R²):     {r_squared:.4f}")
    print(f"     Adjusted R²:        {adj_r_squared:.4f}")
    print(f"     RMSE:               {rmse:.6f}")
    print(f"     F-statistic:        {f_statistic:.2f}")
    print(f"     p-value:            {p_value:.6f}")

    # Interpretation
    print("\n   Interpretation:")
    if p_value < 0.001:
        print(f"     *** Highly significant (p < 0.001)")
    elif p_value < 0.01:
        print(f"     ** Very significant (p < 0.01)")
    elif p_value < 0.05:
        print(f"     * Significant (p < 0.05)")
    else:
        print(f"     Not significant (p >= 0.05)")

    if slope > 0:
        print(f"     Direction: Positive relationship")
        print(f"     For every 1 mg/L increase in nitrate,")
        print(f"     cancer rate increases by {slope:.6f} on average")
    else:
        print(f"     Direction: Negative relationship")
        print(f"     For every 1 mg/L increase in nitrate,")
        print(f"     cancer rate decreases by {abs(slope):.6f} on average")

    # Strength of relationship
    if r_squared > 0.7:
        strength = "Strong"
    elif r_squared > 0.4:
        strength = "Moderate"
    elif r_squared > 0.2:
        strength = "Weak"
    else:
        strength = "Very weak"

    print(f"     Strength: {strength} (R² = {r_squared:.4f})")
    print(f"     {r_squared * 100:.1f}% of cancer variance explained by nitrate")

    # Package results
    results = {
        'n': n,
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared,
        'p_value': p_value,
        'std_err': std_err,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'rmse': rmse,
        'f_statistic': f_statistic,
        'y_pred': y_pred,
        'residuals': residuals,
        'X': X,
        'y': y
    }

    return results


def create_scatter_plot(results, output_path):
    """
    Create scatter plot with regression line

    Purpose: Visualize the relationship between nitrate and cancer.
    Shows individual data points, regression line, and confidence interval.

    Plot Elements:
    - Blue dots: Individual census tracts
    - Red line: Regression line (predicted values)
    - Gray band: 95% confidence interval
    - Statistics: R², p-value, equation

    Parameters:
    -----------
    results : dict
        Regression results from perform_regression()
    output_path : Path
        Where to save the figure
    """

    print(f"   Creating scatter plot...")

    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract data
    X = results['X']
    y = results['y']
    y_pred = results['y_pred']

    # Scatter plot of actual data
    ax.scatter(X, y, alpha=0.5, s=50, edgecolors='black', linewidth=0.5, label='Census Tracts')

    # Sort for smooth regression line
    sort_idx = np.argsort(X)
    X_sorted = X[sort_idx]
    y_pred_sorted = y_pred[sort_idx]

    # Regression line
    ax.plot(X_sorted, y_pred_sorted, 'r-', linewidth=2, label='Regression Line')

    # Calculate confidence interval for regression line
    # Shows uncertainty in predicted values
    n = results['n']
    t_val = stats.t.ppf(0.975, n - 2)
    se_line = results['rmse'] * np.sqrt(1/n + (X_sorted - np.mean(X))**2 / np.sum((X - np.mean(X))**2))
    ci_upper = y_pred_sorted + t_val * se_line
    ci_lower = y_pred_sorted - t_val * se_line

    # Plot confidence interval
    ax.fill_between(X_sorted, ci_lower, ci_upper, alpha=0.2, color='red', label='95% CI')

    # Labels and title
    ax.set_xlabel('Mean Nitrate Level (mg/L)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cancer Rate (cases per person)', fontsize=12, fontweight='bold')
    ax.set_title('Nitrate Exposure vs Cancer Rate\nCensus Tract Level Analysis',
                 fontsize=14, fontweight='bold')

    # Add equation and statistics
    eq_text = f"y = {results['intercept']:.4f} + {results['slope']:.4f}x"
    stats_text = f"R² = {results['r_squared']:.4f}\np = {results['p_value']:.4f}\nn = {results['n']}"

    ax.text(0.05, 0.95, eq_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.text(0.95, 0.05, stats_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    ax.legend(loc='upper right', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   Saved: {output_path}")


def create_residual_plots(results, output_path):
    """
    Create diagnostic residual plots

    Purpose: Check regression assumptions and identify problems:
    1. Residuals vs Fitted: Check for non-linearity, heteroscedasticity
    2. Q-Q Plot: Check if residuals are normally distributed
    3. Scale-Location: Check for equal variance (homoscedasticity)
    4. Residuals vs Leverage: Identify influential outliers

    Why These Matter:
    - Linear regression assumes residuals are:
      * Normally distributed
      * Have constant variance
      * Independent
      * No influential outliers
    - These plots help verify these assumptions

    Parameters:
    -----------
    results : dict
        Regression results
    output_path : Path
        Where to save the figure
    """

    print(f"   Creating residual diagnostic plots...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Extract data
    residuals = results['residuals']
    y_pred = results['y_pred']

    # Standardized residuals
    # Scale residuals by standard deviation for easier interpretation
    std_residuals = residuals / np.std(residuals)

    # Plot 1: Residuals vs Fitted Values
    # Should show random scatter with no pattern
    # Pattern indicates non-linearity or heteroscedasticity
    ax = axes[0, 0]
    ax.scatter(y_pred, residuals, alpha=0.5, edgecolors='black', linewidth=0.5)
    ax.axhline(y=0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Fitted Values', fontweight='bold')
    ax.set_ylabel('Residuals', fontweight='bold')
    ax.set_title('Residuals vs Fitted\n(Should be random scatter)', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add LOWESS smoother to detect patterns
    # LOWESS = Locally Weighted Scatterplot Smoothing
    from scipy.signal import savgol_filter
    sort_idx = np.argsort(y_pred)
    try:
        smoothed = savgol_filter(residuals[sort_idx], window_length=51, polyorder=3)
        ax.plot(y_pred[sort_idx], smoothed, 'b-', linewidth=2, label='Trend')
        ax.legend()
    except:
        pass

    # Plot 2: Q-Q Plot (Quantile-Quantile)
    # Checks if residuals follow normal distribution
    # Points should fall on diagonal line
    ax = axes[0, 1]
    stats.probplot(residuals, dist="norm", plot=ax)
    ax.set_title('Normal Q-Q Plot\n(Points should follow line)', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Plot 3: Scale-Location (Spread-Location)
    # Checks for homoscedasticity (equal variance)
    # Should show horizontal line with equal spread
    ax = axes[1, 0]
    sqrt_abs_residuals = np.sqrt(np.abs(std_residuals))
    ax.scatter(y_pred, sqrt_abs_residuals, alpha=0.5, edgecolors='black', linewidth=0.5)
    ax.set_xlabel('Fitted Values', fontweight='bold')
    ax.set_ylabel('√|Standardized Residuals|', fontweight='bold')
    ax.set_title('Scale-Location\n(Should be horizontal)', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Plot 4: Histogram of Residuals
    # Another way to check normality
    # Should look like bell curve
    ax = axes[1, 1]
    ax.hist(residuals, bins=30, edgecolor='black', alpha=0.7)
    ax.set_xlabel('Residuals', fontweight='bold')
    ax.set_ylabel('Frequency', fontweight='bold')
    ax.set_title('Distribution of Residuals\n(Should be bell-shaped)', fontweight='bold')
    ax.axvline(x=0, color='r', linestyle='--', linewidth=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   Saved: {output_path}")


def create_comparison_maps(gdf, df_clean, output_path):
    """
    Create side-by-side choropleth maps

    Purpose: Visually compare spatial patterns of nitrate exposure
    and cancer rates. Helps identify if high-nitrate areas also have
    high cancer rates.

    Map 1: Nitrate levels by tract
    Map 2: Cancer rates by tract

    Both use same color scheme for easy comparison.

    Parameters:
    -----------
    gdf : GeoDataFrame
        All tracts with geometry
    df_clean : DataFrame
        Clean data used in regression
    output_path : Path
        Where to save the figure
    """

    print(f"   Creating comparison maps...")

    # Filter to tracts used in analysis
    gdf_analysis = gdf[gdf['GEOID10'].isin(df_clean['GEOID10'])]

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))

    # Map 1: Nitrate levels
    ax = axes[0]
    gdf_analysis.plot(
        column='nitr_mean',
        ax=ax,
        cmap='YlOrRd',
        edgecolor='black',
        linewidth=0.2,
        legend=True,
        legend_kwds={
            'label': 'Mean Nitrate (mg/L)',
            'orientation': 'horizontal',
            'shrink': 0.8,
            'pad': 0.05
        }
    )
    ax.set_title('Nitrate Exposure by Census Tract', fontsize=14, fontweight='bold')
    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style='plain')

    # Map 2: Cancer rates
    ax = axes[1]
    gdf_analysis.plot(
        column='canrate',
        ax=ax,
        cmap='YlOrRd',
        edgecolor='black',
        linewidth=0.2,
        legend=True,
        legend_kwds={
            'label': 'Cancer Rate',
            'orientation': 'horizontal',
            'shrink': 0.8,
            'pad': 0.05
        }
    )
    ax.set_title('Cancer Rate by Census Tract', fontsize=14, fontweight='bold')
    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style='plain')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   Saved: {output_path}")


def create_report(results, output_path):
    """
    Generate text report of regression analysis

    Purpose: Create a comprehensive summary of the statistical analysis
    that can be included in a research paper or presentation.

    Report includes:
    - Research question
    - Sample description
    - Regression results
    - Statistical tests
    - Interpretation
    - Assumptions checks

    Parameters:
    -----------
    results : dict
        Regression results
    output_path : Path
        Where to save the report (.txt file)
    """

    print(f"   Creating statistical report...")

    report = []
    report.append("=" * 70)
    report.append("     REGRESSION ANALYSIS REPORT: NITRATE VS CANCER")
    report.append("=" * 70)
    report.append("")

    # Introduction
    report.append("RESEARCH QUESTION")
    report.append("-" * 70)
    report.append("Do higher nitrate levels in drinking water predict higher cancer rates")
    report.append("at the census tract level in Wisconsin?")
    report.append("")

    # Methods
    report.append("METHODS")
    report.append("-" * 70)
    report.append("Analysis: Ordinary Least Squares (OLS) Linear Regression")
    report.append("Dependent Variable: Cancer rate (cases per person)")
    report.append("Independent Variable: Mean nitrate level (mg/L)")
    report.append("Unit of Analysis: Census tracts")
    report.append(f"Sample Size: {results['n']} tracts with complete data")
    report.append("")

    # Descriptive statistics
    report.append("DESCRIPTIVE STATISTICS")
    report.append("-" * 70)
    report.append(f"Nitrate (mg/L):")
    report.append(f"  Mean: {np.mean(results['X']):.2f}")
    report.append(f"  SD:   {np.std(results['X']):.2f}")
    report.append(f"  Range: [{np.min(results['X']):.2f}, {np.max(results['X']):.2f}]")
    report.append("")
    report.append(f"Cancer Rate:")
    report.append(f"  Mean: {np.mean(results['y']):.4f}")
    report.append(f"  SD:   {np.std(results['y']):.4f}")
    report.append(f"  Range: [{np.min(results['y']):.4f}, {np.max(results['y']):.4f}]")
    report.append("")

    # Regression results
    report.append("REGRESSION RESULTS")
    report.append("-" * 70)
    report.append(f"Model Equation:")
    report.append(f"  cancer_rate = {results['intercept']:.6f} + {results['slope']:.6f} * nitrate")
    report.append("")
    report.append(f"Coefficients:")
    report.append(f"  Intercept (Beta0): {results['intercept']:.6f}")
    report.append(f"  Slope (Beta1):     {results['slope']:.6f} (SE = {results['std_err']:.6f})")
    report.append(f"  95% CI:         [{results['ci_lower']:.6f}, {results['ci_upper']:.6f}]")
    report.append("")
    report.append(f"Model Fit:")
    report.append(f"  R-squared:      {results['r_squared']:.4f}")
    report.append(f"  Adjusted R²:    {results['adj_r_squared']:.4f}")
    report.append(f"  RMSE:           {results['rmse']:.6f}")
    report.append(f"  F-statistic:    {results['f_statistic']:.2f}")
    report.append(f"  p-value:        {results['p_value']:.6f}")
    report.append("")

    # Statistical significance
    report.append("STATISTICAL SIGNIFICANCE")
    report.append("-" * 70)
    if results['p_value'] < 0.001:
        report.append("Result: HIGHLY SIGNIFICANT (p < 0.001)")
        report.append("Interpretation: Strong evidence against null hypothesis.")
        report.append("The relationship is very unlikely to be due to chance.")
    elif results['p_value'] < 0.01:
        report.append("Result: VERY SIGNIFICANT (p < 0.01)")
        report.append("Interpretation: Strong evidence of a real relationship.")
    elif results['p_value'] < 0.05:
        report.append("Result: SIGNIFICANT (p < 0.05)")
        report.append("Interpretation: Evidence of a relationship exists.")
    else:
        report.append("Result: NOT SIGNIFICANT (p >= 0.05)")
        report.append("Interpretation: Insufficient evidence of a relationship.")
        report.append("Cannot reject the null hypothesis.")
    report.append("")

    # Effect size
    report.append("EFFECT SIZE AND INTERPRETATION")
    report.append("-" * 70)
    if results['slope'] > 0:
        report.append("Direction: POSITIVE relationship")
        report.append(f"For every 1 mg/L increase in nitrate, cancer rate")
        report.append(f"increases by {results['slope']:.6f} on average.")
    else:
        report.append("Direction: NEGATIVE relationship")
        report.append(f"For every 1 mg/L increase in nitrate, cancer rate")
        report.append(f"decreases by {abs(results['slope']):.6f} on average.")
    report.append("")

    # R-squared interpretation
    variance_explained = results['r_squared'] * 100
    report.append(f"Variance Explained: {variance_explained:.1f}%")
    report.append(f"Nitrate levels explain {variance_explained:.1f}% of the variation")
    report.append(f"in cancer rates across census tracts.")
    report.append("")

    if results['r_squared'] > 0.7:
        report.append("Strength: STRONG relationship")
    elif results['r_squared'] > 0.4:
        report.append("Strength: MODERATE relationship")
    elif results['r_squared'] > 0.2:
        report.append("Strength: WEAK relationship")
    else:
        report.append("Strength: VERY WEAK relationship")
    report.append("")

    # Assumptions
    report.append("REGRESSION ASSUMPTIONS")
    report.append("-" * 70)
    report.append("1. Linearity: Relationship between X and Y should be linear")
    report.append("   Check: Residuals vs Fitted plot")
    report.append("")
    report.append("2. Independence: Observations should be independent")
    report.append("   Limitation: Spatial autocorrelation may exist (nearby tracts similar)")
    report.append("")
    report.append("3. Homoscedasticity: Constant variance of residuals")
    report.append("   Check: Scale-Location plot")
    report.append("")
    report.append("4. Normality: Residuals should be normally distributed")
    report.append("   Check: Q-Q plot and histogram")
    report.append("")

    # Limitations
    report.append("LIMITATIONS")
    report.append("-" * 70)
    report.append("1. Ecological fallacy: Tract-level associations may not apply to individuals")
    report.append("2. Confounding variables: Other factors may affect cancer rates")
    report.append("3. Temporal mismatch: Cancer and nitrate data may be from different periods")
    report.append("4. Spatial autocorrelation: Violates independence assumption")
    report.append("5. Interpolation error: IDW introduces uncertainty in nitrate estimates")
    report.append("")

    # Conclusion
    report.append("CONCLUSION")
    report.append("-" * 70)
    if results['p_value'] < 0.05 and results['slope'] > 0:
        report.append("There is statistically significant evidence of a positive relationship")
        report.append("between nitrate levels and cancer rates at the census tract level.")
        report.append("However, causation cannot be inferred from this observational analysis.")
    elif results['p_value'] < 0.05 and results['slope'] < 0:
        report.append("There is statistically significant evidence of a negative relationship")
        report.append("between nitrate levels and cancer rates at the census tract level.")
        report.append("This unexpected result warrants further investigation.")
    else:
        report.append("No statistically significant relationship was found between nitrate")
        report.append("levels and cancer rates at the census tract level.")
        report.append("This does not prove no relationship exists, only that it was not")
        report.append("detected in this analysis.")
    report.append("")

    report.append("=" * 70)
    report.append("                         END OF REPORT")
    report.append("=" * 70)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"   Saved: {output_path}")


def main():
    """
    Main execution function

    Workflow:
    1. Load data (census tracts with nitrate and cancer)
    2. Prepare data (clean, filter, summarize)
    3. Perform regression analysis
    4. Create visualizations
    5. Generate report
    """

    # Parse arguments
    parser = argparse.ArgumentParser(description='Regression Analysis: Nitrate vs Cancer')
    parser.add_argument('--k', type=float, default=2.0, help='k value used in IDW (for reference)')
    args = parser.parse_args()

    # Print header
    print("=" * 70)
    print("         STEP 5: REGRESSION ANALYSIS - NITRATE VS CANCER")
    print("=" * 70)
    print()

    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / 'data' / 'processed' / 'census_tracts_with_nitrate.shp'

    output_dir = base_dir / 'outputs' / 'results'
    maps_dir = base_dir / 'outputs' / 'maps'

    output_dir.mkdir(parents=True, exist_ok=True)
    maps_dir.mkdir(parents=True, exist_ok=True)

    # Check input file exists
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        print(f"Run Step 4 first: python scripts/04_nitrate_to_tracts.py")
        return

    # Load data
    print("-" * 70)
    print("Loading Data")
    print("-" * 70)
    gdf = load_data(data_path)
    print()

    # Prepare data for analysis
    df_clean = prepare_data(gdf)
    print()

    # Perform regression
    results = perform_regression(df_clean)
    print()

    # Create visualizations
    print("-" * 70)
    print("Creating Visualizations")
    print("-" * 70)

    scatter_path = maps_dir / '05_scatter_regression.png'
    create_scatter_plot(results, scatter_path)

    residual_path = maps_dir / '05_residual_diagnostics.png'
    create_residual_plots(results, residual_path)

    maps_path = maps_dir / '05_comparison_maps.png'
    create_comparison_maps(gdf, df_clean, maps_path)

    print()

    # Generate report
    print("-" * 70)
    print("Generating Report")
    print("-" * 70)

    report_path = output_dir / 'regression_analysis_report.txt'
    create_report(results, report_path)
    print()

    # Save results as CSV
    results_df = df_clean.copy()
    results_df['predicted_cancer'] = results['y_pred']
    results_df['residual'] = results['residuals']

    csv_path = output_dir / 'regression_results.csv'
    results_df.to_csv(csv_path, index=False)
    print(f"   Saved results: {csv_path}")
    print()

    # Final summary
    print("=" * 70)
    print("                      STEP 5 COMPLETE")
    print("=" * 70)
    print()
    print(" Analysis Summary:")
    print(f"  - Sample size: {results['n']} census tracts")
    print(f"  - R-squared: {results['r_squared']:.4f}")
    print(f"  - p-value: {results['p_value']:.6f}")
    print(f"  - Slope: {results['slope']:.6f}")
    print()
    print(" Outputs:")
    print(f"  - Scatter plot: {scatter_path}")
    print(f"  - Diagnostics: {residual_path}")
    print(f"  - Comparison maps: {maps_path}")
    print(f"  - Statistical report: {report_path}")
    print(f"  - Results CSV: {csv_path}")
    print()
    print(" Next Steps:")
    print("  - Review scatter plot for relationship strength")
    print("  - Check residual plots for assumption violations")
    print("  - Read full statistical report")
    print("  - Consider trying different k values (--k parameter)")
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()