# MMX Agent Frontend

A stunning, modern web interface for the Marketing Mix Optimization (MMX) Agent system.

## ✨ Features

- **🎨 Beautiful Dark Theme UI** - Premium gradient design with smooth animations
- **📊 Interactive Visualizations** - Real-time charts powered by Canvas API
- **🚀 Pipeline Monitoring** - Live progress tracking for all agent stages
- **✅ Human-in-the-Loop** - Checkpoint approval system for critical decisions
- **📈 Results Dashboard** - Comprehensive visualization of optimization results
- **💡 AI-Generated Insights** - Actionable recommendations with confidence scores
- **📥 File Upload** - Drag-and-drop CSV data upload with validation
- **📱 Responsive Design** - Works seamlessly on desktop and mobile devices

## 🏗️ Architecture

The frontend is built with vanilla JavaScript, HTML, and CSS for maximum performance and simplicity:

- **No framework dependencies** - Pure JavaScript for fast load times
- **Canvas-based charts** - Custom chart implementations without heavy libraries
- **Modern CSS** - CSS Grid, Flexbox, and CSS Variables for maintainable styling
- **Smooth animations** - Hardware-accelerated transitions and micro-interactions

## 🚀 Quick Start

### Option 1: Static File Server (Recommended for Demo)

```bash
# Navigate to the frontend directory
cd frontend

# Start a simple HTTP server (Python 3)
python3 -m http.server 8080

# Or use Node.js http-server
npx http-server -p 8080

# Open in browser
open http://localhost:8080
```

### Option 2: With Backend API

```bash
# 1. Start the backend API server
cd ..
python backend_api.py

# 2. In a new terminal, start the frontend
cd frontend
python3 -m http.server 8080

# 3. Open in browser
open http://localhost:8080
```

## 📁 File Structure

```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # Complete styling with dark theme
├── app.js              # JavaScript application logic
├── README.md           # This file
└── assets/             # (Optional) Additional images/assets
```

## 🎨 Design System

### Color Palette

- **Primary Gradient**: `#667eea → #764ba2`
- **Success**: `#10b981`
- **Warning**: `#f59e0b`
- **Error**: `#ef4444`
- **Info**: `#3b82f6`

### Typography

- **Primary Font**: Inter (Google Fonts)
- **Monospace**: JetBrains Mono

### Spacing Scale

- XS: 0.25rem
- SM: 0.5rem
- MD: 1rem
- LG: 1.5rem
- XL: 2rem
- 2XL: 3rem
- 3XL: 4rem

## 🔌 API Integration

The frontend expects a backend API with the following endpoints:

### Upload Data

```
POST /api/upload
Content-Type: multipart/form-data

Response:
{
  "success": true,
  "file_id": "uuid",
  "message": "File uploaded successfully"
}
```

### Run Pipeline

```
POST /api/pipeline/run
Content-Type: application/json

Body:
{
  "file_id": "uuid",
  "config": {
    "auto_approve": false
  }
}

Response:
{
  "success": true,
  "pipeline_id": "uuid",
  "status": "running"
}
```

### Get Pipeline Status

```
GET /api/pipeline/{pipeline_id}/status

Response:
{
  "status": "running",
  "current_stage": "baseline",
  "progress": 50,
  "checkpoint": null
}
```

### Get Results

```
GET /api/pipeline/{pipeline_id}/results

Response:
{
  "metrics": { ... },
  "channels": [ ... ],
  "insights": [ ... ]
}
```

### Approve Checkpoint

```
POST /api/pipeline/{pipeline_id}/checkpoint/approve
Content-Type: application/json

Body:
{
  "stage": "baseline",
  "approved": true
}
```

## 🎯 Usage Flow

1. **Upload Data** - User uploads CSV with sales and marketing spend data
2. **Configure & Run** - User clicks "Run Pipeline" to start optimization
3. **Monitor Progress** - Real-time updates show progress through 6 agent stages
4. **Review Checkpoints** - User approves/rejects at critical decision points
5. **View Results** - Interactive dashboard displays optimization recommendations
6. **Explore Insights** - AI-generated insights explain key findings
7. **Download Reports** - Export results as Excel or PDF

## 📊 Chart Types

The frontend includes custom Canvas-based charts:

- **Bar Chart** - Channel contributions
- **Grouped Bar Chart** - Current vs. optimized spend
- **Multi-line Chart** - Response curves
- **Animated Wave Chart** - Hero section visualization

## 🎭 Animations

All animations use CSS transitions and keyframes for smooth 60fps performance:

- **Fade In/Out** - Content transitions
- **Slide In/Out** - Modals and notifications
- **Float** - Brand icon animation
- **Pulse** - Status indicators
- **Shimmer** - Progress bar loading effect
- **Card Float** - Hero card subtle movement

## 🔧 Customization

### Change Color Theme

Edit CSS custom properties in `styles.css`:

```css
:root {
    --primary-500: #667eea;
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* ... other variables */
}
```

### Add New Stage

1. Add stage card HTML in `index.html`
2. Add stage configuration in `app.js`:

```javascript
const stages = [
    // ... existing stages
    { name: 'new_stage', duration: 2000, hasCheckpoint: false }
];
```

### Customize Charts

Modify chart drawing functions in `app.js`:

```javascript
function drawBarChart(ctx, width, height, data) {
    // Custom chart implementation
}
```

## 🐛 Troubleshooting

### Charts Not Rendering

- Ensure Canvas API is supported in your browser
- Check browser console for JavaScript errors
- Verify canvas element IDs match JavaScript selectors

### File Upload Not Working

- Check CORS settings if using separate backend
- Ensure backend API endpoint is accessible
- Verify CSV file format matches requirements

### Animations Stuttering

- Disable hardware acceleration if needed
- Reduce animation complexity in CSS
- Check browser performance settings

## 🚀 Production Deployment

### 1. Build Optimization

```bash
# Minify CSS
npx clean-css-cli -o styles.min.css styles.css

# Minify JavaScript
npx terser app.js -o app.min.js

# Update HTML to use minified files
```

### 2. Deploy to CDN

```bash
# AWS S3
aws s3 sync frontend/ s3://your-bucket-name/ --acl public-read

# Or use Netlify/Vercel for automatic deployment
```

### 3. Configure Backend URL

Update API endpoint in `app.js`:

```javascript
const API_BASE_URL = 'https://api.your-domain.com';
```

## 📝 Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🤝 Contributing

To contribute to the frontend:

1. Follow the existing code style
2. Test on multiple browsers
3. Ensure accessibility (ARIA labels, keyboard navigation)
4. Maintain 60fps animation performance

## 📄 License

Part of the MMX Agent POC project.

---

**Built with ❤️ for Marketing Analytics**
