import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import GitHubConnect from './pages/GitHubConnect';
import Projects from './pages/Projects';
import Builds from './pages/Builds';
import Settings from './pages/Settings';
import DockerAgent from './pages/DockerAgent';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="github" element={<GitHubConnect />} />
        <Route path="projects" element={<Projects />} />
        <Route path="builds" element={<Builds />} />
        <Route path="docker" element={<DockerAgent />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;