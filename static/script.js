/*************************************************************
* Author: David Vanosdall
* Course: GEOG 777
* Date: 2026-02-11
* GEOG 777 - Nitrate Cancer Analysis
* Frontend JavaScript
*
* Handles:
* - K slider updates
* - Running analysis via API
* - Displaying results and maps
* - Tab switching
*************************************************************/

// DOM Elements
const kSlider = document.getElementById('k-slider');
const kValue = document.getElementById('k-value');
const runBtn = document.getElementById('run-btn');
const btnText = document.getElementById('btn-text');
const btnSpinner = document.getElementById('btn-spinner');
const progressContainer = document.getElementById('progress-container');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

const resultsSection = document.getElementById('results-section');
const mapsSection = document.getElementById('maps-section');
const downloadSection = document.getElementById('download-section');

// Statistics elements
const statN = document.getElementById('stat-n');
const statR2 = document.getElementById('stat-r2');
const statP = document.getElementById('stat-p');
const statSlope = document.getElementById('stat-slope');
const statSig = document.getElementById('stat-sig');
const interpretationText = document.getElementById('interpretation-text');

// Map images
const mapNitrate = document.getElementById('map-nitrate');
const mapScatter = document.getElementById('map-scatter');
const mapComparison = document.getElementById('map-comparison');
const mapDiagnostics = document.getElementById('map-diagnostics');

// Tab buttons
const tabButtons = document.querySelectorAll('.tab-btn');


// Event Listeners
// K slider update
kSlider.addEventListener('input', (e) => {
    kValue.textContent = parseFloat(e.target.value).toFixed(1);
});

// Run analysis button
runBtn.addEventListener('click', runAnalysis);

// Tab switching
tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        switchTab(tabName);
    });
});

// Load initial results on page load
window.addEventListener('load', loadInitialResults);

// Functions
/**
 * Load results from previous analysis (if available)
 */
async function loadInitialResults() {
    try {
        const response = await fetch('/api/get-initial-results');
        const data = await response.json();

        if (data.success && data.maps) {
            displayMaps(data.maps);
            mapsSection.style.display = 'block';
            downloadSection.style.display = 'block';
        }
    } catch (error) {
        console.log('No previous results found');
    }
}

/**
 * Run the complete analysis pipeline
 */
async function runAnalysis() {
    const k = parseFloat(kSlider.value);

    // Disable button
    runBtn.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline-block';

    // Show progress bar
    progressContainer.style.display = 'block';
    updateProgress(0, 'Initializing analysis...');

    try {
        // Simulate progress updates
        updateProgress(10, 'Step 1/3: Running IDW interpolation...');

        // Call API
        const response = await fetch('/api/run-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ k: k })
        });

        updateProgress(40, 'Step 2/3: Extracting nitrate to census tracts...');

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message);
        }

        updateProgress(70, 'Step 3/3: Running regression analysis...');

        // Small delay for effect
        await new Promise(resolve => setTimeout(resolve, 500));

        updateProgress(100, 'Analysis complete!');

        // Display results
        displayResults(data.results);
        displayMaps(data.results.maps);

        // Show sections
        resultsSection.style.display = 'block';
        mapsSection.style.display = 'block';
        downloadSection.style.display = 'block';

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        alert(`Error: ${error.message}`);
        updateProgress(0, 'Analysis failed');
    } finally {
        // Re-enable button
        runBtn.disabled = false;
        btnText.style.display = 'inline-block';
        btnSpinner.style.display = 'none';

        // Hide progress after delay
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 2000);
    }
}

/**
 * Update progress bar
 */
function updateProgress(percent, text) {
    progressFill.style.width = percent + '%';
    progressText.textContent = text;
}

/**
 * Display regression results
 */
function displayResults(results) {
    // Update statistics
    statN.textContent = results.n.toLocaleString();
    statR2.textContent = results.r_squared.toFixed(4);
    statP.textContent = results.p_value.toExponential(3);
    statSlope.textContent = results.slope.toFixed(6);

    // Significance
    let sigText = '';
    let sigColor = '';

    if (results.p_value < 0.001) {
        sigText = '*** Highly Significant';
        sigColor = '#28a745';
    } else if (results.p_value < 0.01) {
        sigText = '** Very Significant';
        sigColor = '#28a745';
    } else if (results.p_value < 0.05) {
        sigText = '* Significant';
        sigColor = '#ffc107';
    } else {
        sigText = 'Not Significant';
        sigColor = '#dc3545';
    }

    statSig.textContent = sigText;
    statSig.style.color = sigColor;

    // Interpretation
    const direction = results.slope > 0 ? 'positive' : 'negative';
    const strength = getStrength(results.r_squared);
    const variance = (results.r_squared * 100).toFixed(1);

    interpretationText.innerHTML = `
        <strong>There is a ${direction} relationship between nitrate levels and cancer rates.</strong><br><br>
        For every 1 mg/L increase in nitrate, cancer rate ${results.slope > 0 ? 'increases' : 'decreases'}
        by ${Math.abs(results.slope).toFixed(6)} on average.<br><br>
        The relationship is <strong>${strength.toLowerCase()}</strong> (R² = ${results.r_squared.toFixed(4)}),
        with nitrate explaining ${variance}% of the variation in cancer rates across census tracts.<br><br>
        ${results.p_value < 0.05
            ? 'This relationship is <strong>statistically significant</strong>, suggesting it is unlikely due to chance.'
            : 'This relationship is <strong>not statistically significant</strong>, so it may be due to chance.'}
    `;
}

/**
 * Get strength description from R²
 */
function getStrength(r2) {
    if (r2 > 0.7) return 'Strong';
    if (r2 > 0.4) return 'Moderate';
    if (r2 > 0.2) return 'Weak';
    return 'Very Weak';
}

/**
 * Display maps
 */
function displayMaps(maps) {
    if (maps.nitrate) {
        mapNitrate.src = 'data:image/png;base64,' + maps.nitrate;
    }
    if (maps.scatter) {
        mapScatter.src = 'data:image/png;base64,' + maps.scatter;
    }
    if (maps.comparison) {
        mapComparison.src = 'data:image/png;base64,' + maps.comparison;
    }
    if (maps.diagnostics) {
        mapDiagnostics.src = 'data:image/png;base64,' + maps.diagnostics;
    }
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update buttons
    tabButtons.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update panes
    const panes = document.querySelectorAll('.tab-pane');
    panes.forEach(pane => {
        if (pane.id === 'tab-' + tabName) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });
}

/**
 * Open help modal with specific content
 */
function openHelpModal(topic) {
    const modal = document.getElementById('help-modal');
    const modalBody = document.getElementById('modal-body');

    let content = '';

    if (topic === 'nitrate') {
        content = `
            <h4>Understanding This Map</h4>
            <p><strong>What it shows:</strong> This choropleth map displays the average nitrate concentration (in mg/L) for each census tract in Wisconsin.</p>

            <p><strong>Colors:</strong></p>
            <ul>
                <li><span class="color-box" style="background: #ffffb2;"></span> <strong>Light yellow</strong> = Low nitrate levels (safer)</li>
                <li><span class="color-box" style="background: #fd8d3c;"></span> <strong>Orange</strong> = Moderate nitrate levels</li>
                <li><span class="color-box" style="background: #bd0026;"></span> <strong>Dark red</strong> = High nitrate levels (higher exposure)</li>
            </ul>

            <p><strong>Axes explained:</strong></p>
            <ul>
                <li><strong>Easting (m)</strong> = Horizontal position in meters (left-right on map)</li>
                <li><strong>Northing (m)</strong> = Vertical position in meters (up-down on map)</li>
                <li>These are UTM coordinates (Universal Transverse Mercator), a metric mapping system</li>
            </ul>

            <p><strong>How nitrate values were calculated:</strong>
                Well nitrate measurements were interpolated across space using IDW (Inverse Distance Weighting),
                then averaged within each census tract boundary.
            </p>

            <p><strong>What to look for:</strong> Areas with darker red colors indicate higher nitrate exposure,
            which may be associated with agricultural runoff, well contamination, or geological factors.</p>
        `;
    } else if (topic === 'scatter') {
        content = `
            <h4>Understanding This Plot</h4>
            <p><strong>What it shows:</strong> This scatter plot displays the relationship between nitrate exposure (x-axis) and cancer rates (y-axis) across census tracts.</p>

            <p><strong>Elements:</strong></p>
            <ul>
                <li><span class="color-box" style="background: #1f77b4;"></span> <strong>Blue dots</strong> = Individual census tracts (each dot is one tract)</li>
                <li><span class="color-box" style="background: #d62728;"></span> <strong>Red line</strong> = Best-fit regression line (predicted relationship)</li>
                <li><span class="color-box" style="background: #cccccc;"></span> <strong>Gray shading</strong> = 95% confidence interval (uncertainty range)</li>
            </ul>

            <p><strong>Axes explained:</strong></p>
            <ul>
                <li><strong>X-axis (Mean Nitrate Level)</strong> = Average nitrate in mg/L for each tract</li>
                <li><strong>Y-axis (Cancer Rate)</strong> = Proportion of people with cancer (e.g., 0.10 = 10%)</li>
            </ul>

            <p><strong>How to read the equation:</strong><br>
                <code>y = intercept + slope × x</code><br>
                This tells you the predicted cancer rate for any given nitrate level.
            </p>

            <p><strong>Statistics box:</strong></p>
            <ul>
                <li><strong>R²</strong> = How much of cancer variation is explained by nitrate (0-1 scale)</li>
                <li><strong>p</strong> = Probability this result is due to chance (&lt; 0.05 = significant)</li>
                <li><strong>n</strong> = Number of census tracts analyzed</li>
            </ul>

            <p><strong>What to look for:</strong> An upward-sloping red line indicates that higher nitrate is associated with higher cancer rates. A tight fit (less scatter) means a stronger relationship.</p>
        `;
    } else if (topic === 'comparison') {
        content = `
            <h4>Understanding These Maps</h4>
            <p><strong>What it shows:</strong> These two maps let you visually compare the spatial patterns of nitrate exposure (left) and cancer rates (right) across the same census tracts.</p>

            <p><strong>Left map - Nitrate Exposure:</strong></p>
            <ul>
                <li>Shows mean nitrate levels (mg/L) by tract</li>
                <li>Derived from IDW interpolation of well measurements</li>
                <li>Darker red = higher nitrate contamination</li>
            </ul>

            <p><strong>Right map - Cancer Rates:</strong></p>
            <ul>
                <li>Shows cancer incidence (proportion of population) by tract</li>
                <li>Same color scheme for easy comparison</li>
                <li>Darker red = higher cancer rates</li>
            </ul>

            <p><strong>Why compare them?</strong><br>
                If nitrate causes cancer, you'd expect to see similar spatial patterns - areas with high nitrate (dark red on left)
                should also have high cancer (dark red on right). Visual comparison helps identify spatial correlations.
            </p>

            <p><strong>What to look for:</strong></p>
            <ul>
                <li>Do high-nitrate areas also have high cancer?</li>
                <li>Are there regions where patterns diverge? (This might suggest other factors at play)</li>
                <li>Are there spatial clusters of both high nitrate AND high cancer?</li>
            </ul>

            <p><strong>Limitations:</strong> Visual similarity doesn't prove causation - other confounding factors
            (demographics, healthcare access, industrial pollution) may also influence cancer rates.</p>
        `;
    } else if (topic === 'diagnostics') {
        content = `
            <h4>Understanding Diagnostic Plots</h4>
            <p><strong>What they show:</strong> These four plots check whether the linear regression assumptions are met. If assumptions are violated, the statistical results may be unreliable.</p>

            <p><strong>Top Left - Residuals vs Fitted:</strong></p>
            <ul>
                <li><strong>What it checks:</strong> Linearity and equal variance (homoscedasticity)</li>
                <li><strong>What to look for:</strong> Random scatter around the horizontal red line (no patterns)</li>
                <li><strong>Red flags:</strong> Curved pattern = non-linear relationship; funnel shape = unequal variance</li>
            </ul>

            <p><strong>Top Right - Normal Q-Q Plot:</strong></p>
            <ul>
                <li><strong>What it checks:</strong> Whether residuals follow a normal distribution</li>
                <li><strong>What to look for:</strong> Points falling along the diagonal line</li>
                <li><strong>Red flags:</strong> Points curving away from line = non-normal residuals (may affect p-values)</li>
            </ul>

            <p><strong>Bottom Left - Scale-Location:</strong></p>
            <ul>
                <li><strong>What it checks:</strong> Equal variance (homoscedasticity) across fitted values</li>
                <li><strong>What to look for:</strong> Horizontal red line with evenly spread points</li>
                <li><strong>Red flags:</strong> Increasing or decreasing spread = variance changes with predicted values</li>
            </ul>

            <p><strong>Bottom Right - Histogram of Residuals:</strong></p>
            <ul>
                <li><strong>What it checks:</strong> Normal distribution of errors</li>
                <li><strong>What to look for:</strong> Bell-shaped curve centered at zero</li>
                <li><strong>Red flags:</strong> Skewed distribution or multiple peaks = non-normal errors</li>
            </ul>

            <p><strong>Why this matters:</strong> Linear regression assumes residuals are normally distributed with constant variance.
            Violations don't necessarily invalidate results, but suggest caution in interpretation or the need for alternative methods
            (e.g., spatial regression, robust standard errors).</p>

            <p><strong>Common issues in spatial data:</strong> Spatial autocorrelation (nearby tracts are similar) often violates
            the independence assumption. Consider spatial regression models if patterns suggest clustering.</p>
        `;
    }

    modalBody.innerHTML = content;
    modal.style.display = 'block';
}

/**
 * Close help modal
 */
function closeHelpModal() {
    const modal = document.getElementById('help-modal');
    modal.style.display = 'none';
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('help-modal');
    if (event.target === modal) {
        closeHelpModal();
    }
};