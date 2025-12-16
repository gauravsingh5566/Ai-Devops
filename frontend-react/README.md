# 🎨 AI DevOps Assistant - React Frontend

Modern, interactive dark-themed React frontend for the AI DevOps Assistant.

## ✨ Features

### 🎯 **Interactive Dark Theme**
- Custom dark color scheme optimized for long sessions
- Smooth animations and transitions
- Professional gradient effects
- Responsive design for all screen sizes

### 🚀 **Progressive Workflow**
- Step-by-step infrastructure creation
- Real-time progress indicators
- Approval gates at each stage
- Context preservation throughout

### 💻 **Advanced UI Components**
- Syntax-highlighted code editor with copy/download
- Interactive validation results with expandable sections
- Real-time deployment progress tracking
- Service health monitoring dashboard
- Toast notifications for user feedback

### 🎨 **Modern Tech Stack**
- **React 18** - Latest React features
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Beautiful icons
- **React Syntax Highlighter** - Code highlighting
- **React Hot Toast** - Elegant notifications

---

## 🚀 Quick Start

### **Option 1: Development Mode**

```bash
# Navigate to frontend directory
cd frontend-react

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

### **Option 2: Docker (Production)**

```bash
# Build Docker image
docker build -t ai-devops-frontend .

# Run container
docker run -p 80:80 ai-devops-frontend
```

Frontend will be available at: **http://localhost**

### **Option 3: Docker Compose (Recommended)**

```bash
# Start all services including frontend
docker-compose up -d

# Frontend will be at http://localhost:80
# Backend services at their respective ports
```

---

## 📁 Project Structure

```
frontend-react/
├── public/                  # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── CodeEditor.jsx       # Syntax-highlighted code display
│   │   ├── ValidationResults.jsx # Validation metrics & issues
│   │   ├── DeploymentProgress.jsx # Deployment status
│   │   └── ServiceStatus.jsx    # Health monitoring
│   ├── services/           # API services
│   │   └── api.js              # Backend API calls
│   ├── App.jsx             # Main application component
│   ├── main.jsx            # React entry point
│   └── index.css           # Global styles & Tailwind
├── index.html              # HTML template
├── package.json            # Dependencies
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS config
├── Dockerfile              # Production build
└── nginx.conf              # Nginx configuration

```

---

## 🎨 UI Components

### **1. Main Workflow**

```
┌────────────────────────────────────────────┐
│  Header: AI DevOps Assistant               │
│  Actions: Services | New Request           │
└────────────────────────────────────────────┘
┌────────────────────────────────────────────┐
│  Progress: Input → Generated → Validated → │
│            Deployed                        │
└────────────────────────────────────────────┘
┌────────────────────────────────────────────┐
│  Current Step Content                      │
│  - Input: Textarea + Examples              │
│  - Generated: Code + Approval              │
│  - Validated: Metrics + Issues             │
│  - Deployed: Status + Resources            │
└────────────────────────────────────────────┘
```

### **2. Code Editor**
- Syntax highlighting for Terraform (HCL)
- Line numbers
- Copy to clipboard button
- Download as .tf file
- Dark theme optimized

### **3. Validation Results**
- 4 metric cards: Cost, Security, Resources, Issues
- Expandable sections:
  - Cost breakdown by resource
  - Security issues with severity
  - Quota warnings
  - Recommendations
- Color-coded severity levels

### **4. Deployment Progress**
- Real-time status updates
- Progress percentage bar
- Step-by-step tracking
- Resources created list
- Error messages

### **5. Service Health Dashboard**
- 4 service cards
- Status indicators (healthy/unhealthy)
- Auto-refresh every 30s
- Error details

---

## 🎨 Color Scheme

### **Dark Theme Palette**

```javascript
{
  dark: {
    bg: '#0a0e1a',        // Main background
    surface: '#151b2e',   // Cards, panels
    border: '#1f2937',    // Borders
    hover: '#1e2841',     // Hover states
  },
  primary: {
    500: '#3b82f6',       // Primary blue
    600: '#2563eb',       // Darker blue
  },
  success: {
    500: '#10b981',       // Green
  },
  warning: {
    500: '#f59e0b',       // Orange
  },
  danger: {
    500: '#ef4444',       // Red
  }
}
```

---

## 🔧 Configuration

### **Environment Variables**

```bash
# .env file
VITE_API_BASE_URL=http://localhost  # Backend API base URL
```

### **API Endpoints**

```javascript
{
  AI_SERVICE: 'http://localhost:8001',
  RAG_SERVICE: 'http://localhost:8002',
  MCP_SERVICE: 'http://localhost:8003',
  INFRA_SERVICE: 'http://localhost:8004',
}
```

---

## 📊 User Journey

### **Step 1: Input (Natural Language)**
1. User enters infrastructure requirement
2. Examples provided for inspiration
3. Click "Generate Infrastructure" or Ctrl+Enter

### **Step 2: Generated Code**
1. View parsed intent (expandable)
2. View retrieved best practices (if used)
3. Review generated Terraform code
4. Copy or download code
5. Approve to proceed to validation

### **Step 3: Validation Results**
1. View metrics:
   - Monthly cost estimate
   - Security score (0-100)
   - Resource count
   - Issues found
2. Expand sections for details:
   - Cost breakdown per resource
   - Security issues with recommendations
   - Quota warnings
3. If deployment ready:
   - Enter deployment name
   - Check confirmation box
   - Click "Deploy to AWS"

### **Step 4: Deployment**
1. Watch real-time progress:
   - Creating deployment
   - Initializing Terraform
   - Generating plan
   - Applying infrastructure
2. View created resources
3. See deployment summary
4. Option to deploy new infrastructure

---

## 🎯 Key Features

### **1. Progressive Workflow**
- Clear step-by-step process
- Visual progress indicator
- Context preservation
- Collapsible previous steps

### **2. Approval Gates**
- Explicit user approval required
- Clear warning messages
- Confirmation checkboxes
- Understanding required before deployment

### **3. Real-Time Feedback**
- Loading states with messages
- Progress bars
- Toast notifications
- Status indicators

### **4. Interactive Elements**
- Expandable/collapsible sections
- Hover effects
- Smooth animations
- Responsive interactions

### **5. Professional Design**
- Dark theme for reduced eye strain
- Consistent color coding
- Clear visual hierarchy
- Modern UI patterns

---

## 🛠️ Development

### **Available Scripts**

```bash
# Start development server (port 3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### **Adding New Components**

```javascript
// src/components/MyComponent.jsx
import { MyIcon } from 'lucide-react';

function MyComponent({ prop1, prop2 }) {
  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold">Title</h3>
      {/* Component content */}
    </div>
  );
}

export default MyComponent;
```

### **Using API Services**

```javascript
import { aiService } from './services/api';

// Parse intent
const intent = await aiService.parseIntent(message);

// Generate code
const code = await aiService.generateCode(intent, context);

// Validate code
const validation = await mcpService.validate(code);

// Deploy
const deployment = await infraService.createDeployment(code, name);
```

---

## 🎨 Customization

### **Changing Colors**

Edit `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      dark: {
        bg: '#your-color',
        // ... more colors
      }
    }
  }
}
```

### **Adding Animations**

```css
/* src/index.css */
@keyframes myAnimation {
  from { opacity: 0; }
  to { opacity: 1; }
}

.my-class {
  animation: myAnimation 0.3s ease-out;
}
```

---

## 🐛 Troubleshooting

### **Services Not Connecting**

```bash
# Check if backend services are running
docker ps

# Check environment variables
cat .env

# Verify API_BASE_URL matches your setup
```

### **Build Errors**

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### **Styling Issues**

```bash
# Rebuild Tailwind CSS
npm run build

# Check if Tailwind is processing correctly
# Tailwind classes should be in final CSS
```

---

## 📦 Production Deployment

### **Building for Production**

```bash
# Build optimized production bundle
npm run build

# Output will be in /dist directory
# Contains static HTML, CSS, JS
```

### **Docker Production Build**

```bash
# Build image
docker build -t ai-devops-frontend:latest .

# Run container
docker run -d -p 80:80 ai-devops-frontend:latest

# With custom API URL
docker run -d -p 80:80 \
  -e VITE_API_BASE_URL=https://api.yourdomain.com \
  ai-devops-frontend:latest
```

---

## 🎯 Performance

### **Optimizations**

- Code splitting with Vite
- Lazy loading for components
- Optimized bundle size
- Gzip compression (nginx)
- Static asset caching
- Tree shaking for unused code

### **Bundle Sizes (approx)**

```
- React + React DOM: ~140KB
- Tailwind CSS: ~10KB (purged)
- Syntax Highlighter: ~50KB
- Icons: ~20KB
- Total: ~220KB gzipped
```

---

## 🔐 Security

- No sensitive data in frontend code
- API keys handled by backend
- CORS properly configured
- Input validation on backend
- XSS protection
- CSP headers (nginx)

---

## 🎨 Screenshots

### Dark Theme
- Deep blue-black background
- Subtle borders and shadows
- Color-coded status indicators
- Smooth hover effects

### Interactive Elements
- Expandable sections
- Toast notifications
- Progress animations
- Loading states

### Responsive Design
- Mobile-friendly
- Tablet optimized
- Desktop experience
- Consistent across devices

---

## 📚 Resources

- [React Documentation](https://react.dev)
- [Vite Guide](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Lucide Icons](https://lucide.dev)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📄 License

Part of the AI DevOps Assistant project.

---

**Built with ❤️ using React + Vite + Tailwind CSS**

**Experience modern infrastructure automation with a beautiful dark-themed interface!** 🚀
