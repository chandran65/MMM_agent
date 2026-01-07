# MMX Agent POC - Marketing Mix Optimization

A **local, filesystem-based proof-of-concept** for an agentic Marketing Mix Modeling (MMM) and Optimization system.

This system implements a **deterministic, explainable, and auditable** workflow for marketing budget optimization using specialized autonomous agents.

---

## 🎯 Objective

Build an end-to-end MMX system that:

- **Segments** sub-categories based on sales/volume patterns
- **Discovers** trends, seasonality, and anomalies
- **Estimates** baseline sales and sets modeling priors
- **Trains** MMM models with adstock and saturation transformations
- **Optimizes** budget allocation across channels
- **Generates** stakeholder-ready insights and recommendations

---

## 🌐 Web Interface

**NEW!** A beautiful, interactive web interface is now available for the MMX Agent system.

### Features

- 🎨 **Modern Dark Theme UI** with smooth animations
- 📊 **Real-time Pipeline Monitoring** with live progress tracking
- 📈 **Interactive Visualizations** using Canvas-based charts
- ✅ **Human-in-the-Loop Checkpoints** for critical decisions
- 💡 **AI-Generated Insights** with confidence scores
- 📥 **Easy Data Upload** via drag-and-drop interface
- 📱 **Responsive Design** works on any device

### Quick Start (Web)

```bash
# Start the web server
./start_server.sh

# Open browser to http://localhost:8080
```

See **[QUICKSTART_WEB.md](QUICKSTART_WEB.md)** for detailed instructions.

---

## 🏗️ Architecture

### Agent-per-Responsibility Design

| Agent | Responsibility |
|-------|---------------|
| **Segmentation Agent** | Groups sub-categories using clustering |
| **Trend Scanner Agent** | Detects YoY trends, seasonality, anomalies, events |
| **Baseline Agent** | Estimates baseline sales and sets priors/constraints |
| **Model Optimization Agent** | Applies transformations and trains MMM |
| **Budget Optimization Agent** | Runs constrained optimization (scipy SLSQP) |
| **Insight Agent** | Generates narratives, tables, and visualizations |

### Orchestration Layer

- **Workflow Orchestrator**: Manages agent execution order
- **State Manager**: Persists state between stages
- **Checkpoint Manager**: Implements human-in-the-loop approval gates

---

## 📁 Folder Structure

```
mmx-agent-poc/
├── README.md                           # This file
├── requirements.txt                     # Python dependencies
│
├── config/                             # Configuration files
│   ├── global.yaml                     # System-wide settings
│   ├── segmentation.yaml               # Segmentation parameters
│   ├── priors.yaml                     # MMM priors and constraints
│   ├── optimization.yaml               # Budget optimization settings
│   └── guardrails.yaml                 # Validation rules
│
├── data/                               # Data directories
│   ├── raw/                            # Input data
│   ├── processed/                      # Processed artifacts
│   ├── features/                       # Engineered features
│   └── scenarios/                      # Scenario outputs
│
├── agents/                             # Agent implementations
│   ├── segmentation_agent/
│   │   ├── agent.py                   # Main agent logic
│   │   ├── rules.py                   # Validation rules
│   │   └── tools.py                   # Feature engineering & clustering
│   ├── trend_scanner_agent/
│   │   ├── agent.py
│   │   └── detectors.py               # Trend/anomaly detection
│   ├── baseline_agent/
│   │   ├── agent.py
│   │   ├── priors.py                  # Prior estimation
│   │   └── constraints.py             # Constraint builder
│   ├── model_optimization_agent/
│   │   ├── agent.py
│   │   ├── transformations.py         # Adstock transformations
│   │   ├── saturation.py              # Hill/Weibull saturation
│   │   └── trainer.py                 # Model training
│   ├── budget_optimization_agent/
│   │   ├── agent.py
│   │   ├── solver.py                  # Scipy optimization
│   │   └── bounds.py                  # Bounds management
│   └── insight_agent/
│       ├── agent.py
│       ├── narratives.py              # Text generation
│       └── visuals.py                 # Chart creation
│
├── orchestration/                      # Workflow management
│   ├── workflow.py                    # Main orchestrator
│   ├── state_manager.py               # State persistence
│   └── checkpoints.py                 # Checkpoint management
│
├── models/                            # Model artifacts
│   ├── trained/                       # Trained models
│   └── registry.json                  # Model registry
│
├── artifacts/                         # Generated outputs
│   ├── contributions/                 # Channel contributions
│   ├── curves/                        # Response curves
│   ├── roi/                          # ROI optimization results
│   └── decks/                        # Stakeholder reports
│
├── evaluation/                        # Validation utilities
│   ├── backtesting.py                # Backtest framework
│   └── diagnostics.py                # Model diagnostics
│
├── cli/                              # Command-line interface
│   └── run_pipeline.py               # CLI runner
│
└── tests/                            # Unit tests
    └── unit/
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd mmx-agent-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Input Data

Create a CSV file with sales and marketing spend data:

```csv
date,sub_category,sales,total_sales,total_volume,tv_spend,digital_spend,print_spend,ooh_spend,radio_spend
2022-01-03,Category_A,50000,50000,1000,10000,8000,3000,2000,1000
2022-01-10,Category_A,52000,52000,1040,10500,8200,3100,2100,1100
...
```

**Required columns:**

- `date`: Weekly date (YYYY-MM-DD)
- `sales` or `total_sales`: Sales values
- `total_volume`: Volume sold
- `{channel}_spend`: Spend for each marketing channel (e.g., `tv_spend`, `digital_spend`)

Place your data in `data/raw/sales_data.csv`.

### 3. Run the Pipeline

```bash
# Basic execution
python -m cli.run_pipeline --input data/raw/sales_data.csv --auto-approve

# With event data
python -m cli.run_pipeline \
    --input data/raw/sales_data.csv \
    --events data/raw/events.csv \
    --auto-approve

# Interactive mode with checkpoints
python -m cli.run_pipeline --input data/raw/sales_data.csv

# Verbose logging
python -m cli.run_pipeline --input data/raw/sales_data.csv --auto-approve --verbose
```

### 4. Review Outputs

After execution, find outputs in:

- **Executive Summary**: `artifacts/decks/executive_summary.md`
- **Excel Report**: `artifacts/decks/mmx_summary_report.xlsx`
- **Insights**: `artifacts/decks/key_insights.json`
- **Visualizations**: `artifacts/decks/*.png`
- **Contributions**: `artifacts/contributions/channel_contributions.csv`
- **Optimization**: `artifacts/roi/optimization_recommendations.csv`

---

## 📊 Pipeline Stages

### Stage 1: Segmentation

**Agent**: `SegmentationAgent`  
**Input**: Raw sales data  
**Output**: Segment mappings, statistics, visualizations  
**Checkpoint**: User reviews segment quality before proceeding

### Stage 2: Trend Scanner

**Agent**: `TrendScannerAgent`  
**Input**: Time series sales data  
**Output**: Flagged periods, event metadata, trend visualizations

### Stage 3: Baseline Estimation

**Agent**: `BaselineAgent`  
**Input**: Sales data + event metadata  
**Output**: Baseline estimates, priors, constraints  
**Checkpoint**: User reviews baseline before modeling

### Stage 4: Model Optimization

**Agent**: `ModelOptimizationAgent`  
**Input**: Sales data + priors + baseline  
**Output**: Trained model, contributions, response curves  
**Actions**:

- Applies adstock transformation (geometric decay)
- Applies saturation (Hill function)
- Trains Ridge regression model
- Calculates channel contributions
- Generates response curves

### Stage 5: Budget Optimization

**Agent**: `BudgetOptimizationAgent`  
**Input**: Response curves + constraints  
**Output**: Optimized allocations for multiple scenarios  
**Checkpoint**: User reviews model before optimization  
**Actions**:

- Runs scipy SLSQP optimizer
- Applies channel bounds
- Generates base, aggressive, conservative scenarios

### Stage 6: Insight Generation

**Agent**: `InsightAgent`  
**Input**: Contributions + optimization results + model metrics  
**Output**: Narratives, visualizations, Excel reports  
**Actions**:

- Generates executive narratives
- Creates contribution charts
- Creates optimization comparison charts
- Produces stakeholder-ready Excel report

---

## ⚙️ Configuration

### Global Configuration (`config/global.yaml`)

```yaml
data:
  time_granularity: "weekly"
  
modeling:
  granularity: "channel"
  response_curve: "hill"
  adstock_type: "geometric"
  
optimization:
  solver: "scipy"
  method: "SLSQP"
  
orchestration:
  enable_checkpoints: true
  checkpoint_locations:
    - "after_segmentation"
    - "after_baseline"
    - "before_optimization"
```

### Budget Configuration (`config/optimization.yaml`)

```yaml
optimization:
  budget:
    total_budget: 1000000
    channel_bounds:
      TV:
        min: 0.15
        max: 0.40
      Digital:
        min: 0.20
        max: 0.50
    channel_constraints:
      TV:
        min_absolute_spend: 100000
```

---

## 🔬 Modeling Approach

### Adstock Transformation

Models carryover effects of marketing spend:

```
effect[t] = spend[t] + decay_rate * effect[t-1]
```

### Saturation (Hill Function)

Models diminishing returns:

```
response = spend^alpha / (gamma^alpha + spend^alpha)
```

### MMM Model

Ridge regression with transformed features:

```
incremental_sales = Σ (beta_i * transformed_spend_i) + baseline
```

### Optimization

Maximize response subject to:

- Total budget constraint
- Channel min/max bounds
- Maximum change from current spend
- Minimum budget utilization

---

## 🧪 Testing & Validation

### Run Unit Tests

```bash
pytest tests/ -v --cov=agents --cov=orchestration
```

### Model Diagnostics

```python
from evaluation.diagnostics import ModelDiagnostics

diagnostics = ModelDiagnostics()
report = diagnostics.generate_diagnostic_report(y_true, y_pred, X, feature_names)
print(report['issues'])
```

### Backtesting

```python
from evaluation.backtesting import Backtester

backtester = Backtester()
results = backtester.time_series_backtest(model, X, y, n_splits=5)
print(f"Average R²: {results['avg_r2']:.3f}")
```

---

## 📈 Example Outputs

### Channel Contributions

| Channel | Contribution | Contribution % |
|---------|-------------|----------------|
| Digital | $450,000 | 35.2% |
| TV | $380,000 | 29.7% |
| Print | $210,000 | 16.4% |
| OOH | $150,000 | 11.7% |
| Radio | $90,000 | 7.0% |

### Optimization Recommendations

| Channel | Current Spend | Optimized Spend | Change % |
|---------|---------------|-----------------|----------|
| Digital | $200,000 | $280,000 | +40.0% |
| TV | $400,000 | $320,000 | -20.0% |
| Print | $180,000 | $160,000 | -11.1% |
| OOH | $140,000 | $150,000 | +7.1% |
| Radio | $80,000 | $90,000 | +12.5% |

---

## 🛡️ Guardrails

The system includes comprehensive guardrails at multiple levels:

### Data Quality

- Missing data thresholds
- Outlier detection
- Date continuity checks

### Model Quality

- Minimum R² thresholds
- Coefficient sign validation
- Multicollinearity detection

### Business Logic

- ROI feasibility ranges
- Contribution validity checks
- Saturation efficiency bounds

### Optimization

- Maximum change constraints
- Budget preservation validation
- Bounds compliance checks

---

## 🔄 Checkpoints

The pipeline enforces human-in-the-loop checkpoints at:

1. **After Segmentation**: Review segment quality and mappings
2. **After Baseline**: Review baseline estimates and priors
3. **Before Optimization**: Review model performance before budget allocation

To bypass checkpoints:

```bash
python -m cli.run_pipeline --input data/raw/sales_data.csv --auto-approve
```

---

## 🐛 Troubleshooting

### Import Errors

```bash
# Ensure you're in the project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Missing Data Columns

Ensure your input CSV has:

- `date` column (datetime)
- `sales` or `total_sales`
- `{channel}_spend` columns for each marketing channel

### Optimization Not Converging

- Check that response curves are properly calibrated
- Ensure budget constraints are not too restrictive
- Increase `maxiter` in `config/optimization.yaml`

---

## 📝 License

This is a proof-of-concept implementation for demonstration purposes.

---

## 🤝 Contributing

This is a POC system. For production use, consider:

- Adding Bayesian MMM (PyMC, Stan)
- Cloud deployment (AWS, GCP)
- UI dashboards (Streamlit, Dash)
- Advanced optimization (evolutionary algorithms)
- Integration with marketing platforms

---

## 📚 References

- **Marketing Mix Modeling**: Chan, D. & Perry, M. (2017). Challenges and Opportunities in Media Mix Modeling
- **Adstock & Saturation**: Broadbent, S. (1979). One Way TV Advertisements Work
- **Hill Function**: Hill, A.V. (1910). The possible effects of the aggregation of the molecules of haemoglobin
- **Optimization**: Nocedal, J. & Wright, S. (2006). Numerical Optimization

---

**Built with ❤️ for Marketing Analytics**
