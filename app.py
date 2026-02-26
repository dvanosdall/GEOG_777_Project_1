from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import subprocess
import json
import geopandas as gpd
import base64
from io import BytesIO
import os
import sys

# Get the Python executable from current environment
PYTHON_EXE = sys.executable

app = Flask(__name__)

# Global paths
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / 'scripts'
MAPS_DIR = BASE_DIR / 'outputs' / 'maps'
RESULTS_DIR = BASE_DIR / 'outputs' / 'results'

# Ensure output directories exist
MAPS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/')
def index():
    """
    Serve the main web interface
    """
    return render_template('index.html')


@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    """
    Run the complete analysis pipeline for a given k value

    Steps:
    1. Run IDW interpolation
    2. Extract nitrate to tracts
    3. Perform regression analysis
    4. Return results and map paths

    Expected POST data:
    {
        "k": 2.5
    }

    Returns:
    {
        "success": true/false,
        "message": "...",
        "results": {
            "k": 2.5,
            "n": 1316,
            "r_squared": 0.0140,
            "p_value": 0.000016,
            "slope": 0.006494,
            "intercept": 0.076265,
            "maps": {
                "nitrate": "base64_encoded_image",
                "scatter": "base64_encoded_image",
                "comparison": "base64_encoded_image",
                "diagnostics": "base64_encoded_image"
            }
        }
    }
    """

    try:
        # Get k value from request
        data = request.get_json()
        k = float(data.get('k', 2.0))

        # Validate k
        if k < 1.0 or k > 5.0:
            return jsonify({
                'success': False,
                'message': f'Invalid k value: {k}. Must be between 1.0 and 5.0'
            })

        print(f"\n{'='*70}")
        print(f"Running analysis for k = {k}")
        print(f"{'='*70}\n")

        # Step 1: IDW Interpolation
        print("Step 1: Running IDW interpolation...")
        result = subprocess.run(
            [PYTHON_EXE, str(SCRIPTS_DIR / '03_data_idw_interpolation.py'), '--k', str(k)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            return jsonify({
                'success': False,
                'message': f'IDW interpolation failed: {result.stderr}'
            })

        print("--> IDW complete")

        # Step 2: Extract to Tracts
        print("Step 2: Extracting nitrate to census tracts...")
        result = subprocess.run(
            [PYTHON_EXE, str(SCRIPTS_DIR / '04_nitrate_to_tracts.py'), '--k', str(k)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            return jsonify({
                'success': False,
                'message': f'Tract extraction failed: {result.stderr}'
            })

        print("--> Extraction complete")

        # Step 3: Regression Analysis
        print("Step 3: Running regression analysis...")
        result = subprocess.run(
            [PYTHON_EXE, str(SCRIPTS_DIR / '05_regression_analysis.py'), '--k', str(k)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            return jsonify({
                'success': False,
                'message': f'Regression analysis failed: {result.stderr}'
            })

        print("--> Regression complete")

        # Extract results from regression output
        stats = parse_regression_results(result.stdout)

        # Load and encode images as base64
        maps = {}

        map_files = {
            'nitrate': MAPS_DIR / '04_nitrate_by_tract.png',
            'scatter': MAPS_DIR / '05_scatter_regression_raw.png',
            'comparison': MAPS_DIR / '05_comparison_maps_raw.png',
            'diagnostics': MAPS_DIR / '05_residual_diagnostics_raw.png'
        }

        for key, path in map_files.items():
            if path.exists():
                with open(path, 'rb') as f:
                    maps[key] = base64.b64encode(f.read()).decode('utf-8')
            else:
                maps[key] = None

        # Return success response
        response = {
            'success': True,
            'message': f'Analysis complete for k = {k}',
            'results': {
                'k': k,
                'n': stats.get('n', 0),
                'r_squared': stats.get('r_squared', 0),
                'p_value': stats.get('p_value', 0),
                'slope': stats.get('slope', 0),
                'intercept': stats.get('intercept', 0),
                'maps': maps
            }
        }

        print(f"\n{'='*70}")
        print(f"Analysis complete for k = {k}")
        print(f"{'='*70}\n")

        return jsonify(response)

    except Exception as e:
        import traceback
        print(f"Exception occurred: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })


def parse_regression_results(output):
    """
    Parse regression statistics from script output

    Extracts key statistics from the console output of the
    regression analysis script.

    Parameters:
    -----------
    output : str
        Console output from regression script

    Returns:
    --------
    dict with keys: n, r_squared, p_value, slope, intercept
    """

    stats = {}

    lines = output.split('\n')

    for line in lines:
        line = line.strip()

        if 'Sample Size (n):' in line:
            try:
                stats['n'] = int(line.split(':')[1].strip())
            except:
                pass

        elif 'R-squared (R²):' in line:
            try:
                stats['r_squared'] = float(line.split(':')[1].strip())
            except:
                pass

        elif 'p-value:' in line and 'R-squared' not in line:
            try:
                stats['p_value'] = float(line.split(':')[1].strip())
            except:
                pass

        elif 'Slope (Beta1):' in line:
            try:
                # Format: "Slope (Beta1):     0.006494 ± 0.001501"
                parts = line.split(':')[1].strip().split('±')
                stats['slope'] = float(parts[0].strip())
            except:
                pass

        elif 'Intercept (Beta0):' in line:
            try:
                stats['intercept'] = float(line.split(':')[1].strip())
            except:
                pass

    return stats


@app.route('/api/download-results', methods=['GET'])
def download_results():
    """
    Download the regression results CSV file
    """

    csv_path = RESULTS_DIR / 'regression_results_raw.csv'

    if csv_path.exists():
        return send_file(
            csv_path,
            as_attachment=True,
            download_name='regression_results_raw.csv',
            mimetype='text/csv'
        )
    else:
        return jsonify({
            'success': False,
            'message': 'Results file not found. Run analysis first.'
        }), 404


@app.route('/api/download-report', methods=['GET'])
def download_report():
    """
    Download the full statistical report
    """

    report_path = RESULTS_DIR / 'regression_analysis_report_raw.txt'

    if report_path.exists():
        return send_file(
            report_path,
            as_attachment=True,
            download_name='regression_analysis_report_raw.txt',
            mimetype='text/plain'
        )
    else:
        return jsonify({
            'success': False,
            'message': 'Report file not found. Run analysis first.'
        }), 404


@app.route('/api/get-initial-results', methods=['GET'])
def get_initial_results():
    """
    Get results from the last analysis run (if available)

    Used to populate the page on initial load
    """

    try:
        # Check if results exist
        csv_path = RESULTS_DIR / 'regression_results.csv'

        if not csv_path.exists():
            return jsonify({
                'success': False,
                'message': 'No previous results found. Run analysis first.'
            })

        # Load maps if they exist
        maps = {}

        map_files = {
            'nitrate': MAPS_DIR / '04_nitrate_by_tract.png',
            'scatter': MAPS_DIR / '05_scatter_regression.png',
            'comparison': MAPS_DIR / '05_comparison_maps.png',
            'diagnostics': MAPS_DIR / '05_residual_diagnostics.png'
        }

        for key, path in map_files.items():
            if path.exists():
                with open(path, 'rb') as f:
                    maps[key] = base64.b64encode(f.read()).decode('utf-8')

        # Try to get stats from last run
        # Default to showing that results exist
        return jsonify({
            'success': True,
            'maps': maps
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/download-maps', methods=['GET'])
def download_maps():
    """
    Download a ZIP archive of all map images (for 'All Maps' button)
    """
    maps_zip = MAPS_DIR / 'maps.zip'
    if not maps_zip.exists():
        return "Zip not found.", 404
    return send_file(
        maps_zip,
        as_attachment=True,
        download_name='maps.zip',
        mimetype='application/zip'
    )


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  GEOG 777 - Nitrate Cancer Analysis Web Application")
    print("="*70)
    print("\n  Starting Flask server...")
    print(f"  Open your browser to: http://localhost:5000")
    print(f"\n  Press Ctrl+C to stop the server\n")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)