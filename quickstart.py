#!/usr/bin/env python3
"""
Quick Start Script for MMX Agent POC

Generates sample data and runs a complete pipeline demonstration.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        return False
    
    print(f"\n✅ Completed: {description}")
    return True


def main():
    """Run the quick start process."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║       MMX AGENT POC - QUICK START                        ║
    ║       Marketing Mix Optimization System                  ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Error: Please run this script from the mmx-agent-poc directory")
        sys.exit(1)
    
    # Step 2: Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command(
        f"{sys.executable} -m pip install -q -r requirements.txt",
        "Installing Python packages"
    ):
        print("\n⚠️  Warning: Some packages may not have installed correctly")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Step 3: Generate sample data
    print("\n🔨 Generating sample data...")
    if not run_command(
        f"{sys.executable} data/generate_sample_data.py",
        "Creating synthetic MMX data"
    ):
        print("❌ Failed to generate sample data")
        sys.exit(1)
    
    # Step 4: Run the pipeline
    print("\n🚀 Running MMX Pipeline...")
    print("\nThis will execute all 6 agents:")
    print("  1. Segmentation Agent")
    print("  2. Trend Scanner Agent")
    print("  3. Baseline Agent")
    print("  4. Model Optimization Agent")
    print("  5. Budget Optimization Agent")
    print("  6. Insight Agent")
    
    if not run_command(
        f"{sys.executable} -m cli.run_pipeline --input data/raw/sales_data.csv --auto-approve --verbose",
        "Executing complete MMX workflow"
    ):
        print("❌ Pipeline execution failed")
        sys.exit(1)
    
    # Step 5: Show results
    print("\n" + "="*60)
    print("📊 RESULTS")
    print("="*60)
    
    print("\n✨ Pipeline completed successfully!")
    print("\n📁 Generated outputs:")
    
    outputs = [
        ("Executive Summary", "artifacts/decks/executive_summary.md"),
        ("Excel Report", "artifacts/decks/mmx_summary_report.xlsx"),
        ("Key Insights", "artifacts/decks/key_insights.json"),
        ("Channel Contributions", "artifacts/contributions/channel_contributions.csv"),
        ("Optimization Results", "artifacts/roi/optimization_recommendations.csv"),
        ("Visualizations", "artifacts/decks/")
    ]
    
    for name, path in outputs:
        if Path(path).exists():
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ⚠️  {name}: {path} (not found)")
    
    print("\n" + "="*60)
    print("🎉 Quick Start Complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Review the executive summary: cat artifacts/decks/executive_summary.md")
    print("  2. Open the Excel report: open artifacts/decks/mmx_summary_report.xlsx")
    print("  3. View visualizations in: artifacts/decks/")
    print("\nTo run with your own data:")
    print("  python -m cli.run_pipeline --input your_data.csv --auto-approve")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Quick start interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
