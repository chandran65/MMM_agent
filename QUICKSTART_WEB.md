# 🚀 Quick Start - Web Interface

Get started with the MMX Agent web interface in under 2 minutes!

## Prerequisites

- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, or Edge)

## Start the Server

### Option 1: Using the Startup Script (Recommended)

```bash
# From the project root directory
./start_server.sh
```

This script will:

1. ✅ Create a virtual environment (if needed)
2. ✅ Install all dependencies
3. ✅ Start the backend API server
4. ✅ Serve the frontend interface

### Option 2: Manual Start

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python backend_api.py
```

## Access the Web Interface

Once the server is running, open your browser and navigate to:

**🌐 <http://localhost:8080>**

You should see the beautiful MMX Agent dashboard!

## Using the Interface

### 1. Upload Your Data

Click the **"Upload Data & Start"** button and upload your CSV file with the following columns:

- `date` - Weekly date (YYYY-MM-DD format)
- `sales` or `total_sales` - Sales values
- `total_volume` - Volume sold
- `{channel}_spend` - Spend for each channel (e.g., `tv_spend`, `digital_spend`)

### 2. Run the Pipeline

Click **"Run Pipeline"** to start the optimization process. You'll see:

- ✅ Real-time progress through 6 AI agent stages
- ⚠️ Checkpoint approval prompts at critical stages
- 📊 Live status updates

### 3. Review Results

After completion, explore:

- **📈 Optimization Results** - Key metrics and ROI improvements
- **📊 Interactive Charts** - Channel contributions, budget allocation, response curves
- **💡 AI Insights** - Actionable recommendations with confidence scores
- **📥 Download Reports** - Export as Excel or PDF

## Example Workflow

1. **Upload** → `data/raw/sales_data.csv`
2. **Run Pipeline** → Monitor progress through all stages
3. **Checkpoint 1** → Review baseline estimates → **Approve**
4. **Checkpoint 2** → Review model performance → **Approve**
5. **View Results** → Explore optimization recommendations
6. **Download** → Export Excel report for stakeholders

## API Endpoints (for developers)

The backend exposes RESTful API endpoints:

- `POST /api/upload` - Upload data file
- `POST /api/pipeline/run` - Start pipeline
- `GET /api/pipeline/{id}/status` - Get status
- `POST /api/pipeline/{id}/checkpoint` - Approve/reject checkpoint
- `GET /api/pipeline/{id}/results` - Get results

Full API documentation: See `frontend/README.md`

## Troubleshooting

### Port Already in Use

If port 8080 is already in use, edit `backend_api.py` and change the port:

```python
app.run(host='0.0.0.0', port=5000, debug=True)  # Use port 5000 instead
```

### File Upload Issues

- Ensure your CSV file is properly formatted
- Check that required columns are present
- File size should be under 50MB

### Pipeline Not Starting

- Verify the file was uploaded successfully
- Check the browser console for errors
- Review backend logs for detailed error messages

## Next Steps

- 📖 Read the full documentation in `README.md`
- 🎨 Explore customization options in `frontend/README.md`
- 🧪 Run tests with `pytest tests/`
- 🚀 Deploy to production (see deployment guide)

---

**Need Help?** Check the main README.md or open an issue on GitHub.

**Built with ❤️ for Marketing Analytics**
