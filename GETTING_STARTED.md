# Getting Started with MMX Agent POC

## 🎯 What is this?

This is a complete, production-ready **Marketing Mix Modeling (MMM) and Optimization system** built using an **agent-based architecture**. It's designed to run **locally** on your machine without any cloud dependencies.

## ⚡ Quick Start (5 minutes)

### Option 1: Automated Quick Start (Recommended)

```bash
cd mmx-agent-poc
python quickstart.py
```

This will:

1. Install all dependencies
2. Generate synthetic sample data
3. Run the complete 6-agent pipeline
4. Show you where all outputs are saved

### Option 2: Manual Step-by-Step

```bash
# 1. Navigate to project
cd mmx-agent-poc

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate sample data
python data/generate_sample_data.py

# 5. Run the pipeline
python -m cli.run_pipeline --input data/raw/sales_data.csv --auto-approve

# 6. View results
cat artifacts/decks/executive_summary.md
```

## 📊 What You'll Get

After running the pipeline, you'll have:

### 1. Executive Reports

- **Markdown Summary**: `artifacts/decks/executive_summary.md`
- **Excel Report**: `artifacts/decks/mmx_summary_report.xlsx`
- **Key Insights (JSON)**: `artifacts/decks/key_insights.json`

### 2. Data Outputs

- **Segment Mappings**: `data/processed/segment_mappings.csv`
- **Baseline Estimates**: `data/processed/baseline_estimates.csv`
- **Channel Contributions**: `artifacts/contributions/channel_contributions.csv`
- **Optimization Results**: `artifacts/roi/optimization_recommendations.csv`

### 3. Visualizations

- Channel contribution bar chart
- Current vs optimized allocation comparison
- Response curves for each channel
- Scenario comparison chart

All in: `artifacts/decks/*.png`

## 🔧 Using Your Own Data

### Data Format Required

Create a CSV file with these columns:

```csv
date,sub_category,sales,total_sales,total_volume,tv_spend,digital_spend,print_spend,ooh_spend,radio_spend
2022-01-03,Category_A,50000,50000,1000,10000,8000,3000,2000,1000
2022-01-10,Category_A,52000,52000,1040,10500,8200,3100,2100,1100
...
```

**Required columns:**

- `date`: Weekly dates (YYYY-MM-DD format)
- `sales` or `total_sales`: Sales values
- `total_volume`: Units sold
- `{channel}_spend`: Marketing spend per channel (e.g., `tv_spend`, `digital_spend`)

**Optional:**

- `sub_category`: Category/product identifier

### Running with Your Data

```bash
python -m cli.run_pipeline --input path/to/your_data.csv --auto-approve
```

## 🎛️ Customization

### Change Budget and Constraints

Edit `config/optimization.yaml`:

```yaml
optimization:
  budget:
    total_budget: 1000000  # Change this
    channel_bounds:
      TV:
        min: 0.15  # Minimum 15% of budget
        max: 0.40  # Maximum 40% of budget
```

### Adjust Model Priors

Edit `config/priors.yaml`:

```yaml
channels:
  TV:
    adstock_range: [0.3, 0.7]  # Carryover effect range
    saturation_alpha_range: [1.0, 5.0]  # Saturation curve shape
    roi_expected: 1.5  # Expected ROI
```

### Enable/Disable Checkpoints

Edit `config/global.yaml`:

```yaml
orchestration:
  enable_checkpoints: false  # Set to false for auto-approval
```

## 🔍 Understanding the Pipeline

The system runs in **6 sequential stages**:

```
1. SEGMENTATION → Groups categories by similarity
          ↓
2. TREND SCANNER → Detects patterns and anomalies
          ↓
3. BASELINE ESTIMATION → Estimates organic sales
          ↓ [CHECKPOINT: Review baseline]
4. MODEL OPTIMIZATION → Trains MMM with adstock/saturation
          ↓ [CHECKPOINT: Review model]
5. BUDGET OPTIMIZATION → Optimizes spend allocation
          ↓
6. INSIGHT GENERATION → Creates reports and visualizations
```

### Checkpoints

By default, the pipeline will pause at checkpoints for you to review:

```bash
# To run without pausing (auto-approve all checkpoints):
python -m cli.run_pipeline --input data.csv --auto-approve

# To review at each checkpoint (interactive):
python -m cli.run_pipeline --input data.csv
```

## 📖 Understanding the Outputs

### Channel Contributions

Shows how much each channel contributes to incremental sales:

```
Channel     Contribution    Contribution %
Digital     $450,000       35.2%
TV          $380,000       29.7%
Print       $210,000       16.4%
```

### Optimization Recommendations

Shows how to reallocate budget for maximum ROI:

```
Channel    Current      Optimized    Change
Digital    $200,000    $280,000     +40.0%
TV         $400,000    $320,000     -20.0%
```

### Response Curves

Shows diminishing returns for each channel:

- Helps identify saturation points
- Guides optimal spend levels

## 🐛 Troubleshooting

### "ModuleNotFoundError"

```bash
# Make sure you're in the project directory and have activated venv
cd mmx-agent-poc
source venv/bin/activate
pip install -r requirements.txt
```

### "Input file not found"

```bash
# Generate sample data first
python data/generate_sample_data.py
```

### "KeyError: channel_spend"

Your data is missing required spend columns. Ensure you have columns like:

- `tv_spend`, `digital_spend`, `print_spend`, etc.

### Pipeline fails at a specific stage

```bash
# Run with verbose logging to see details
python -m cli.run_pipeline --input data.csv --verbose
```

## 💡 Tips

1. **Start with sample data** to understand the system before using your own
2. **Review checkpoints** the first time to understand each stage
3. **Check the logs** in `logs/mmx_pipeline.log` for detailed execution info
4. **Iterate on config** - adjust priors and constraints based on your domain knowledge
5. **Validate outputs** - use the diagnostic tools in `evaluation/` to check model quality

## 📚 Next Steps

1. **Read the full README**: `README.md`
2. **Review project summary**: `PROJECT_SUMMARY.md`
3. **Explore the code**: Start with `orchestration/workflow.py`
4. **Customize configs**: Adjust settings in `config/`
5. **Add your data**: Replace sample data with real data

## 🆘 Need Help?

- Full documentation: `README.md`
- Technical summary: `PROJECT_SUMMARY.md`
- Config examples: `config/*.yaml`
- Sample data generator: `data/generate_sample_data.py`

## 🎉 Success Indicators

You'll know it worked when you see:

```
============================================================
PIPELINE COMPLETED SUCCESSFULLY
============================================================
Duration: XX.X seconds
Completed stages: segmentation, trend_scanner, baseline, 
                  model_optimization, budget_optimization, 
                  insight_generation

Outputs:
  - Executive Summary: artifacts/decks/executive_summary.md
  - Excel Report: artifacts/decks/mmx_summary_report.xlsx
  - Insights JSON: artifacts/decks/key_insights.json
```

**That's it! You now have a working MMX optimization system!** 🚀
