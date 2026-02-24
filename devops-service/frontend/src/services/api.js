import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add user ID
api.interceptors.request.use((config) => {
  const userId = localStorage.getItem('userId') || 'demo-user';
  config.headers['X-User-ID'] = userId;
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

// GitHub Service
export const githubService = {
  // Connect GitHub account
  connect: async (accessToken) => {
    const res = await api.post('/github/connect', { access_token: accessToken });
    return res.data;
  },

  // Get repositories
  getRepositories: async (refresh = false) => {
    const res = await api.get('/github/repos', { params: { refresh } });
    return res.data;
  },

  // Import project
  importProject: async (owner, repo, branch = null) => {
    const res = await api.post('/github/import', { owner, repo, branch });
    return res.data;
  },

  // Get imported projects
  getProjects: async () => {
    const res = await api.get('/github/projects');
    return res.data;
  },

  // Sync project
  syncProject: async (owner, repo) => {
    const res = await api.post('/github/sync', { owner, repo });
    return res.data;
  },

  // Delete project
  deleteProject: async (owner, repo) => {
    const res = await api.delete(`/github/projects/${owner}/${repo}`);
    return res.data;
  },
};

// Build Service
export const buildService = {
  // Analyze project
  analyze: async (projectPath) => {
    const res = await api.post('/build/analyze', { project_path: projectPath });
    return res.data;
  },

  // Generate Dockerfile
  generateDockerfile: async (projectPath) => {
    const res = await api.post('/build/generate-dockerfile', { project_path: projectPath });
    return res.data;
  },

  // Build image
  build: async (projectPath, imageName, tag = 'latest', optimize = true) => {
    const res = await api.post('/build/build', {
      project_path: projectPath,
      image_name: imageName,
      tag,
      optimize,
      push_to_registry: false,
    });
    return res.data;
  },

  // Get build status
  getBuildStatus: async (jobId) => {
    const res = await api.get(`/build/build/${jobId}`);
    return res.data;
  },

  // List builds
  listBuilds: async (limit = 10) => {
    const res = await api.get('/build/builds', { params: { limit } });
    return res.data;
  },
};

// Health Service
export const healthService = {
  // Get overall health
  getHealth: async () => {
    const res = await api.get('/health');
    return res.data;
  },

  // Get agents status
  getAgents: async () => {
    const res = await api.get('/agents');
    return res.data;
  },
};

// Docker Agent Service
export const dockerService = {
  // Validate Dockerfile with AI
  validateDockerfile: async (dockerfileContent, context = null) => {
    const res = await api.post('/docker/validate-dockerfile', { 
      dockerfile_content: dockerfileContent,
      context 
    });
    return res.data;
  },

  // Build Docker image with validation
  buildImage: async (config) => {
    const res = await api.post('/docker/build', {
      dockerfile_path: config.dockerfilePath,
      image_name: config.imageName,
      tag: config.tag,
      validate_before_build: config.validateBefore,
      validate_after_build: config.validateAfter
    });
    return res.data;
  },

  // Validate built image
  validateImage: async (imageName, tag = 'latest') => {
    const res = await api.post('/docker/validate-image', { 
      image_name: imageName, 
      tag 
    });
    return res.data;
  },

  // Test if image can run
  testImage: async (imageName, tag = 'latest') => {
    const res = await api.post('/docker/test-image', { 
      image_name: imageName, 
      tag 
    });
    return res.data;
  },

  // Get build job status
  getJob: async (jobId) => {
    const res = await api.get(`/docker/job/${jobId}`);
    return res.data;
  },

  // List build jobs
  listJobs: async (limit = 20) => {
    const res = await api.get('/docker/jobs', { params: { limit } });
    return res.data;
  }
};

export default api;