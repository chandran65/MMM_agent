#!/usr/bin/env python3
"""
Project Structure Verification Script

Verifies that all required files and directories are in place.
"""

from pathlib import Path
import sys


def verify_structure():
    """Verify the complete project structure."""
    
    required_structure = {
        'config': [
            'global.yaml',
            'segmentation.yaml',
            'priors.yaml',
            'optimization.yaml',
            'guardrails.yaml'
        ],
        'agents/segmentation_agent': ['agent.py', 'rules.py', 'tools.py', '__init__.py'],
        'agents/trend_scanner_agent': ['agent.py', 'detectors.py', '__init__.py'],
        'agents/baseline_agent': ['agent.py', 'priors.py', 'constraints.py', '__init__.py'],
        'agents/model_optimization_agent': ['agent.py', 'transformations.py', 'saturation.py', 'trainer.py', '__init__.py'],
        'agents/budget_optimization_agent': ['agent.py', 'solver.py', 'bounds.py', '__init__.py'],
        'agents/insight_agent': ['agent.py', 'narratives.py', 'visuals.py', '__init__.py'],
        'orchestration': ['workflow.py', 'state_manager.py', 'checkpoints.py', '__init__.py'],
        'evaluation': ['backtesting.py', 'diagnostics.py', '__init__.py'],
        'cli': ['run_pipeline.py', '__init__.py'],
        'data': ['generate_sample_data.py'],
        '.': ['README.md', 'requirements.txt', 'PROJECT_SUMMARY.md', 'GETTING_STARTED.md', 'quickstart.py']
    }
    
    required_dirs = [
        'data/raw',
        'data/processed',
        'data/features',
        'data/scenarios',
        'models/trained',
        'artifacts/contributions',
        'artifacts/curves',
        'artifacts/roi',
        'artifacts/decks',
        'tests/unit'
    ]
    
    print("="*70)
    print("MMX AGENT POC - PROJECT STRUCTURE VERIFICATION")
    print("="*70)
    
    all_good = True
    
    # Check files
    print("\n📁 Checking files...")
    for directory, files in required_structure.items():
        dir_path = Path(directory)
        print(f"\n  {directory}/")
        
        for file in files:
            file_path = dir_path / file
            if file_path.exists():
                print(f"    ✅ {file}")
            else:
                print(f"    ❌ {file} (MISSING)")
                all_good = False
    
    # Check empty directories that should exist
    print("\n\n📂 Checking required directories...")
    for directory in required_dirs:
        dir_path = Path(directory)
        if dir_path.exists():
            print(f"  ✅ {directory}/")
        else:
            print(f"  ⚠️  {directory}/ (will be created on first run)")
    
    # Count files
    print("\n\n📊 Project Statistics:")
    py_files = list(Path('.').rglob('*.py'))
    yaml_files = list(Path('config').rglob('*.yaml'))
    md_files = list(Path('.').glob('*.md'))
    
    print(f"  • Python files: {len(py_files)}")
    print(f"  • Config files: {len(yaml_files)}")
    print(f"  • Documentation: {len(md_files)}")
    print(f"  • Total agents: 6")
    print(f"  • Total modules: {len([f for f in py_files if 'agent' in str(f)])}")
    
    # Summary
    print("\n" + "="*70)
    if all_good:
        print("✅ PROJECT STRUCTURE VERIFICATION PASSED")
        print("="*70)
        print("\n🚀 Ready to run!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Generate data: python data/generate_sample_data.py")
        print("  3. Run pipeline: python -m cli.run_pipeline --input data/raw/sales_data.csv --auto-approve")
        print("\nOr simply run: python quickstart.py")
        return 0
    else:
        print("❌ PROJECT STRUCTURE VERIFICATION FAILED")
        print("="*70)
        print("\nSome files are missing. Please check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(verify_structure())
