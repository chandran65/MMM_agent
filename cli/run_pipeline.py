"""
MMX Pipeline CLI Runner

Command-line interface for executing the MMX pipeline.
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.workflow import WorkflowOrchestrator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run the MMX (Marketing Mix Optimization) Agent Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with sample data
  python -m cli.run_pipeline --input data/raw/sales_data.csv
  
  # Run with event data and auto-approve checkpoints
  python -m cli.run_pipeline --input data/raw/sales_data.csv --events data/raw/events.csv --auto-approve
  
  # Use custom config
  python -m cli.run_pipeline --input data/raw/sales_data.csv --config config/custom.yaml
        """
    )
    
    parser.add_argument(
        '--input',
        '-i',
        required=True,
        help='Path to input sales and spend data (CSV)'
    )
    
    parser.add_argument(
        '--events',
        '-e',
        help='Path to events data (CSV, optional)'
    )
    
    parser.add_argument(
        '--config',
        '-c',
        default='config/global.yaml',
        help='Path to configuration file (default: config/global.yaml)'
    )
    
    parser.add_argument(
        '--auto-approve',
        '-a',
        action='store_true',
        help='Auto-approve all checkpoints (no human intervention)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Validate events file if provided
    events_path = None
    if args.events:
        events_path = Path(args.events)
        if not events_path.exists():
            logger.warning(f"Events file not found: {args.events} - continuing without events")
            events_path = None
        else:
            events_path = str(events_path)
    
    # Initialize orchestrator
    try:
        orchestrator = WorkflowOrchestrator(config_path=args.config)
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)
    
    # Execute pipeline
    logger.info("Starting MMX Pipeline...")
    logger.info(f"Input data: {args.input}")
    if events_path:
        logger.info(f"Events data: {events_path}")
    logger.info(f"Auto-approve: {args.auto_approve}")
    
    try:
        result = orchestrator.execute_full_pipeline(
            input_data_path=str(input_path),
            events_path=events_path,
            auto_approve_checkpoints=args.auto_approve
        )
        
        if result['status'] == 'success':
            logger.info("\n" + "="*60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            logger.info(f"Duration: {result['duration_seconds']:.1f} seconds")
            logger.info(f"Completed stages: {', '.join(result['completed_stages'])}")
            logger.info("\nOutputs:")
            
            # Print key outputs
            if 'outputs' in result:
                insight_outputs = result['outputs'].get('insight_generation', {}).get('output_paths', {})
                logger.info(f"  - Executive Summary: {insight_outputs.get('executive_summary', 'N/A')}")
                logger.info(f"  - Excel Report: {insight_outputs.get('excel_report', 'N/A')}")
                logger.info(f"  - Insights JSON: {insight_outputs.get('insights_json', 'N/A')}")
            
            sys.exit(0)
        
        else:
            logger.error("\n" + "="*60)
            logger.error("PIPELINE FAILED")
            logger.error("="*60)
            logger.error(f"Failed at stage: {result.get('failed_stage', 'unknown')}")
            logger.error(f"Error: {result.get('error', 'unknown')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\nUnexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
