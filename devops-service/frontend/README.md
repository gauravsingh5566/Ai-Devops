# 🎨 DevOps Platform Frontend

**Modern React frontend for AI-Powered DevOps automation**

---

## 🚀 Features

✅ **Dashboard** - Overview of projects, builds, and service health  
✅ **GitHub Integration** - Connect account and browse repositories  
✅ **Project Management** - Import and manage projects  
✅ **Build Monitoring** - Real-time build status and history  
✅ **Settings** - Configure user preferences  
✅ **Responsive Design** - Works on desktop and mobile  
✅ **Real-time Updates** - Auto-refresh data  

---

## 🛠️ Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **React Router** - Navigation
- **React Query** - Data fetching
- **Tailwind CSS** - Styling
- **Axios** - API client
- **Lucide React** - Icons
- **React Hot Toast** - Notifications

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

Built files will be in `dist/` directory.

---

## 📁 Project Structure

```
devops-frontend/
├── src/
│   ├── components/
│   │   └── Layout.jsx         # Main layout with sidebar
│   ├── pages/
│   │   ├── Dashboard.jsx      # Dashboard page
│   │   ├── GitHubConnect.jsx  # GitHub integration
│   │   ├── Projects.jsx       # Projects management
│   │   ├── Builds.jsx         # Build history
│   │   └── Settings.jsx       # Settings page
│   ├── services/
│   │   └── api.js             # API service layer
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # Entry point
│   └── index.css              # Global styles
├── public/
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## 🎨 Pages

### 1. Dashboard (`/dashboard`)
- Service health status
- Quick stats (projects, builds, repos)
- Recent builds
- System overview

### 2. GitHub (`/github`)
- Connect GitHub account
- Browse repositories
- Import projects
- View repo details

### 3. Projects (`/projects`)
- View imported projects
- Build projects
- Delete projects
- Project details

### 4. Builds (`/builds`)
- Build history
- Build status (pending, building, completed, failed)
- Build details
- Dockerfile preview

### 5. Settings (`/settings`)
- User configuration
- API settings
- System information

---

## 📡 API Integration

### Base URL
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Services

**GitHub Service:**
- `POST /github/connect` - Connect account
- `GET /github/repos` - List repositories
- `POST /github/import` - Import project
- `GET /github/projects` - List projects

**Build Service:**
- `POST /build/analyze` - Analyze project
- `POST /build/build` - Build image
- `GET /build/build/:id` - Get build status
- `GET /build/builds` - List builds

**Health Service:**
- `GET /health` - System health
- `GET /agents` - Agent status

---

## 🎨 Styling

### Tailwind CSS

Custom theme in `tailwind.config.js`:

```javascript
colors: {
  primary: {
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
  },
  success: {
    500: '#22c55e',
  },
  danger: {
    500: '#ef4444',
  }
}
```

### Custom Classes

```css
.btn - Base button
.btn-primary - Primary button
.btn-secondary - Secondary button
.btn-success - Success button
.btn-danger - Danger button
.card - Card container
.input - Input field
.badge - Badge component
```

---

## 🔧 Development

### Run Dev Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

### Lint Code
```bash
npm run lint
```

---

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t devops-frontend .
```

### Run Container
```bash
docker run -p 3000:80 \
  -e VITE_API_URL=http://api-gateway:8000 \
  devops-frontend
```

---

## 🔄 State Management

### React Query

```javascript
// Fetch data
const { data, isLoading } = useQuery('projects', fetchProjects);

// Mutations
const mutation = useMutation(importProject, {
  onSuccess: () => {
    queryClient.invalidateQueries('projects');
  }
});
```

### Local Storage

```javascript
// User ID
localStorage.getItem('userId');
localStorage.setItem('userId', 'user123');

// GitHub connection
localStorage.getItem('githubConnected');
```

---

## 📱 Responsive Design

- **Mobile:** Single column layout
- **Tablet:** 2-column grid
- **Desktop:** 3-column grid + sidebar

Breakpoints:
- `sm:` 640px
- `md:` 768px
- `lg:` 1024px
- `xl:` 1280px

---

## 🎯 User Flow

### Complete Workflow

```
1. Dashboard
   ↓
2. Connect GitHub (/github)
   ↓
3. Import Project
   ↓
4. View in Projects (/projects)
   ↓
5. Build Project
   ↓
6. Monitor Build (/builds)
   ↓
7. View Results
```

---

## 🔐 Authentication

Currently uses simple User ID header:

```javascript
headers: {
  'X-User-ID': userId
}
```

**For Production:**
- Add JWT authentication
- Implement login/signup
- Add OAuth flow
- Secure API endpoints

---

## 🚀 Features to Add

- [ ] Real-time WebSocket updates
- [ ] Deployment tracking
- [ ] Security scan results
- [ ] Test results view
- [ ] Analytics dashboard
- [ ] Team collaboration
- [ ] Role-based access
- [ ] Advanced filtering
- [ ] Export reports
- [ ] Dark mode

---

## 🐛 Troubleshooting

### API Connection Issues
```bash
# Check API is running
curl http://localhost:8000/health

# Update VITE_API_URL in .env
VITE_API_URL=http://your-api-url:8000
```

### Build Errors
```bash
# Clear node_modules
rm -rf node_modules package-lock.json
npm install
```

### CORS Errors
```bash
# API must allow CORS from frontend URL
# Check api-gateway CORS configuration
```

---

## 📚 Resources

- **React:** https://react.dev
- **Vite:** https://vitejs.dev
- **Tailwind:** https://tailwindcss.com
- **React Query:** https://tanstack.com/query
- **React Router:** https://reactrouter.com

---

## ✅ Summary

**Frontend includes:**
- ✅ 5 complete pages
- ✅ GitHub integration UI
- ✅ Project management
- ✅ Build monitoring
- ✅ Real-time updates
- ✅ Responsive design
- ✅ Production ready

**Status:** Ready to use! 🎉

---

**Version:** 1.0.0  
**Last Updated:** 2024-02-18
