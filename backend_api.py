"""
Backend API Server for MMX Agent Frontend
Provides REST API endpoints to connect the web UI to the actual MMX pipeline
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import uuid
import logging
from datetime import datetime
from threading import Thread
import time
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import MMX Agents and Orchestration
from orchestration.state_manager import StateManager
from agents.segmentation_agent.agent import SegmentationAgent
from agents.trend_scanner_agent.agent import TrendScannerAgent
from agents.baseline_agent.agent import BaselineAgent
from agents.model_optimization_agent.agent import ModelOptimizationAgent
from agents.budget_optimization_agent.agent import BudgetOptimizationAgent
from agents.insight_agent.agent import InsightAgent

app = Flask(__name__, static_folder='frontend')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'data/raw'
ARTIFACTS_FOLDER = 'artifacts'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for pipeline states
pipelines = {}
uploaded_files = {}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================================
# PIPELINE EXECUTION LOGIC
# ===================================

def run_pipeline_async(pipeline_id, file_path, config):
    """Run the actual MMX pipeline asynchronously"""
    try:
        pipeline = pipelines[pipeline_id]
        
        # Initialize State Manager (mock config for now or load real one)
        # We assume global.yaml exists in config/
        import yaml
        with open('config/global.yaml', 'r') as f:
            global_config = yaml.safe_load(f)
            
        # Override config with user provided config if any
        auto_approve = config.get('auto_approve', False)
        
        state_manager = StateManager(global_config)
        
        # Update status
        pipeline['status'] = 'running'
        pipeline['current_stage'] = 'initializing'
        pipeline['progress'] = 5
        
        # --- STAGE 1: SEGMENTATION ---
        pipeline['current_stage'] = 'segmentation'
        logger.info("Executing Segmentation Agent...")
        seg_agent = SegmentationAgent()
        seg_result = seg_agent.execute(file_path)
        state_manager.save_stage_output("segmentation", seg_result)
        pipeline['progress'] = 20
        
        # --- STAGE 2: TREND SCANNER ---
        pipeline['current_stage'] = 'trend'
        logger.info("Executing Trend Scanner Agent...")
        trend_agent = TrendScannerAgent()
        # We assume no events file for now as UI doesn't upload it yet, or make it optional
        trend_result = trend_agent.execute(file_path, None)
        state_manager.save_stage_output("trend_scanner", trend_result)
        pipeline['progress'] = 35
        
        # --- STAGE 3: BASELINE ESTIMATION ---
        pipeline['current_stage'] = 'baseline'
        logger.info("Executing Baseline Agent...")
        baseline_agent = BaselineAgent()
        baseline_result = baseline_agent.execute(
            file_path,
            trend_result['output_paths']['event_metadata']
        )
        state_manager.save_stage_output("baseline", baseline_result)
        pipeline['progress'] = 50
        
        # CHECKPOINT 1
        if not auto_approve:
            logger.info("Waiting for Baseline Checkpoint approval...")
            pipeline['checkpoint'] = {
                'stage': 'baseline',
                'pending': True,
                'message': 'Review Baseline Estimates before proceeding',
                'data': {
                    'baseline_file': baseline_result['output_paths']['baseline_estimates']
                }
            }
            wait_for_checkpoint(pipeline)
            if pipeline['status'] == 'stopped':
                return
        
        # --- STAGE 4: MODEL OPTIMIZATION ---
        pipeline['current_stage'] = 'model'
        logger.info("Executing Model Optimization Agent...")
        model_agent = ModelOptimizationAgent()
        model_result = model_agent.execute(
            file_path,
            baseline_result['output_paths']['priors'],
            baseline_result['output_paths']['baseline_estimates']
        )
        state_manager.save_stage_output("model_optimization", model_result)
        pipeline['progress'] = 70
        
        # --- STAGE 5: BUDGET OPTIMIZATION ---
        pipeline['current_stage'] = 'budget'
        logger.info("Executing Budget Optimization Agent...")
        
        # CHECKPOINT 2
        if not auto_approve:
            logger.info("Waiting for Budget Checkpoint approval...")
            pipeline['checkpoint'] = {
                'stage': 'budget',
                'pending': True,
                'message': 'Review Model Performance before optimization',
                'data': {
                    'metrics': model_result['model_metrics']
                }
            }
            wait_for_checkpoint(pipeline)
            if pipeline['status'] == 'stopped':
                return

        budget_agent = BudgetOptimizationAgent()
        budget_result = budget_agent.execute(
            model_result['output_paths']['response_curves'],
            file_path
        )
        state_manager.save_stage_output("budget_optimization", budget_result)
        pipeline['progress'] = 85
        
        # --- STAGE 6: INSIGHT GENERATION ---
        pipeline['current_stage'] = 'insight'
        logger.info("Executing Insight Generation Agent...")
        insight_agent = InsightAgent()
        insight_result = insight_agent.execute(
            model_result['output_paths']['contributions_csv'],
            budget_result['output_paths']['recommendations'],
            model_result['output_paths']['metrics'],
            model_result['output_paths'].get('response_curves')
        )
        state_manager.save_stage_output("insight_generation", insight_result)
        pipeline['progress'] = 100
        
        # COMPLETE
        pipeline['status'] = 'completed'
        pipeline['completed_at'] = datetime.now().isoformat()
        
        # Prepare real results for frontend
        prepare_results(pipeline, model_result, budget_result, insight_result)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        pipeline['status'] = 'failed'
        pipeline['error'] = str(e)

def wait_for_checkpoint(pipeline):
    """Wait until checkpoint is approved or rejected"""
    while pipeline['checkpoint']['pending']:
        time.sleep(0.5)
        if pipeline['status'] == 'stopped': # Can be set externally to stop
            return
        
        # Check if rejected
        if pipeline['checkpoint'].get('approved') is False:
             pipeline['status'] = 'stopped'
             pipeline['checkpoint'] = None
             return

    # Checkpoint handled
    pipeline['checkpoint'] = None

def prepare_results(pipeline, model_result, budget_result, insight_result):
    """Read actual artifact files to structure results for frontend"""
    try:
        # 1. Metrics
        metrics = model_result.get('metrics', {})
        
        # 2. Channels (Contributions + Optimization Recommendations)
        # Load recommendations CSV
        rec_path = budget_result['output_paths']['recommendations']
        rec_df = pd.read_csv(rec_path)
        
        # Load contribution CSV
        contrib_path = model_result['output_paths']['contributions_csv']
        contrib_df = pd.read_csv(contrib_path)
        
        # Merge or construct channel objects
        channels = []
        for _, row in rec_df.iterrows():
            channel_name = row['channel']
            
            contrib_row = contrib_df[contrib_df['channel'] == channel_name]
            contribution_val = float(contrib_row['contribution_pct'].iloc[0]) * 100 if not contrib_row.empty else 0
            
            channels.append({
                'name': channel_name,
                'current': float(row['current_spend']),
                'optimized': float(row['optimized_spend']),
                'contribution': contribution_val,
                'roi': float(row['expected_response']) / float(row['optimized_spend']) if float(row['optimized_spend']) > 0 else 0
            })
            
        # 3. Insights - Read from generated JSON or narratives
        insights = []
        # In a real scenario, we might parse insight_agent output files
        # For now, we'll create some basic ones based on data or read the insights.json if it exists
        insights_json_path = insight_result['output_paths'].get('insights_json')
        if insights_json_path and os.path.exists(insights_json_path):
            with open(insights_json_path, 'r') as f:
                loaded_insights = json.load(f)
                # Map to frontend structure if needed
                for item in loaded_insights:
                     insights.append({
                         'type': 'recommendation', # derive from content
                         'title': item.get('title', 'Insight'),
                         'description': item.get('content', ''),
                         'confidence': 90.0 # placeholder
                     })
        
        results = {
            'metrics': {
                'roi_lift': float(budget_result.get('uplift_pct', 0)),
                'model_accuracy': float(metrics.get('r2_score', 0)),
                'total_budget': sum(c['current'] for c in channels),
                'channels_optimized': len(channels)
            },
            'channels': channels,
            'insights': insights
        }
        
        pipeline['results'] = results
        
    except Exception as e:
        logger.error(f"Error preparing results: {e}", exc_info=True)
        # Fallback to empty results to avoid UI crash
        pipeline['results'] = {'metrics': {}, 'channels': [], 'insights': []}

# ===================================
# API ENDPOINTS
# ===================================

@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('frontend', path)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload sales data CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        filename = f"sales_data_{file_id}.csv" 
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file to where pipeline expects input
        file.save(filepath)
        
        # Store file info
        uploaded_files[file_id] = {
            'filename': file.filename,
            'filepath': filepath,
            'uploaded_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'message': 'File uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/run', methods=['POST'])
def run_pipeline():
    """Start the optimization pipeline"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        config = data.get('config', {})
        
        if not file_id or file_id not in uploaded_files:
            return jsonify({'error': 'Invalid file_id'}), 400
        
        # Generate pipeline ID
        pipeline_id = str(uuid.uuid4())
        
        # Initialize pipeline state
        pipelines[pipeline_id] = {
            'id': pipeline_id,
            'file_id': file_id,
            'status': 'initializing',
            'current_stage': None,
            'progress': 0,
            'started_at': datetime.now().isoformat(),
            'checkpoint': None,
            'results': None
        }
        
        # Start pipeline in background thread
        file_path = uploaded_files[file_id]['filepath']
        thread = Thread(target=run_pipeline_async, args=(pipeline_id, file_path, config))
        thread.start()
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_id,
            'status': 'running'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/<pipeline_id>/status', methods=['GET'])
def get_pipeline_status(pipeline_id):
    """Get pipeline execution status"""
    if pipeline_id not in pipelines:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    pipeline = pipelines[pipeline_id]
    
    response = {
        'pipeline_id': pipeline_id,
        'status': pipeline['status'],
        'current_stage': pipeline['current_stage'],
        'progress': pipeline['progress'],
        'checkpoint': pipeline['checkpoint']
    }
    
    # If failed, include error
    if pipeline['status'] == 'failed':
        response['error'] = pipeline.get('error')
        
    return jsonify(response)

@app.route('/api/pipeline/<pipeline_id>/checkpoint', methods=['POST'])
def handle_checkpoint(pipeline_id):
    """Approve or reject a checkpoint"""
    try:
        if pipeline_id not in pipelines:
            return jsonify({'error': 'Pipeline not found'}), 404
        
        data = request.get_json()
        approved = data.get('approved', False)
        
        pipeline = pipelines[pipeline_id]
        
        if not pipeline['checkpoint']:
            return jsonify({'error': 'No pending checkpoint'}), 400
        
        pipeline['checkpoint']['approved'] = approved
        pipeline['checkpoint']['pending'] = False # This signals the thread to proceed
        
        return jsonify({
            'success': True,
            'approved': approved
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline/<pipeline_id>/results', methods=['GET'])
def get_results(pipeline_id):
    """Get pipeline results"""
    if pipeline_id not in pipelines:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    pipeline = pipelines[pipeline_id]
    
    if pipeline['status'] != 'completed':
        return jsonify({'error': 'Pipeline not completed'}), 400
    
    return jsonify({
        'pipeline_id': pipeline_id,
        'results': pipeline['results']
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MMX Agent Backend API Server")
    print("="*60)
    print(f"\n✅ Server starting...")
    print(f"📍 API Base URL: http://localhost:8080")
    print("\n" + "="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True,
        threaded=True
    )
