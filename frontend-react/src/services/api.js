import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost';

const api = axios.create({
  timeout: 120000, // 2 minutes
});

// Service URLs
const SERVICES = {
  AI: `${API_BASE_URL}:8001`,
  RAG: `${API_BASE_URL}:8002`,
  MCP: `${API_BASE_URL}:8003`,
  INFRA: `${API_BASE_URL}:8004`,
};

export const aiService = {
  // Parse intent from natural language
  parseIntent: async (message) => {
    try {
      const response = await api.post(`${SERVICES.AI}/parse-intent`, { message });
      console.log('Parse Intent Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Parse Intent Error:', error.response?.data || error.message);
      throw error;
    }
  },

  // Generate Terraform code
  generateCode: async (intent, ragContext = null, policies = null) => {
    try {
      const response = await api.post(`${SERVICES.AI}/generate-code`, {
        intent,
        rag_context: ragContext,
        organization_policies: policies,
      });
      console.log('Generate Code Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Generate Code Error:', error.response?.data || error.message);
      throw error;
    }
  },

  // Refine code based on feedback
  refineCode: async (originalCode, feedback, validationResults) => {
    const response = await api.post(`${SERVICES.AI}/refine-code`, {
      original_code: originalCode,
      feedback,
      validation_results: validationResults,
    });
    return response.data;
  },

  // Check health
  checkHealth: async () => {
    const response = await api.get(`${SERVICES.AI}/health`);
    return response.data;
  },
};

export const ragService = {
  // Search for best practices
  search: async (query, nResults = 5) => {
    const response = await api.post(`${SERVICES.RAG}/search`, {
      query,
      n_results: nResults,
    });
    return response.data;
  },

  // Check health
  checkHealth: async () => {
    const response = await api.get(`${SERVICES.RAG}/health`);
    return response.data;
  },
};

export const mcpService = {
  // Validate Terraform code
  validate: async (code, region = 'us-east-1') => {
    const response = await api.post(`${SERVICES.MCP}/validate`, {
      terraform_code: code,
      region,
    });
    return response.data;
  },

  // Check health
  checkHealth: async () => {
    const response = await api.get(`${SERVICES.MCP}/health`);
    return response.data;
  },
};

export const infraService = {
  // Create deployment
  createDeployment: async (code, name, region = 'us-east-1') => {
    const response = await api.post(`${SERVICES.INFRA}/deployments`, {
      terraform_code: code,
      deployment_name: name,
      region,
    });
    return response.data;
  },

  // Initialize Terraform
  initDeployment: async (deploymentId) => {
    const response = await api.post(`${SERVICES.INFRA}/deployments/${deploymentId}/init`);
    return response.data;
  },

  // Plan deployment
  planDeployment: async (deploymentId) => {
    const response = await api.post(`${SERVICES.INFRA}/deployments/${deploymentId}/plan`);
    return response.data;
  },

  // Apply deployment
  applyDeployment: async (deploymentId) => {
    const response = await api.post(`${SERVICES.INFRA}/deployments/${deploymentId}/apply`);
    return response.data;
  },

  // Get deployment status
  getDeployment: async (deploymentId) => {
    const response = await api.get(`${SERVICES.INFRA}/deployments/${deploymentId}`);
    return response.data;
  },

  // List all deployments
  listDeployments: async () => {
    const response = await api.get(`${SERVICES.INFRA}/deployments`);
    return response.data;
  },

  // Check health
  checkHealth: async () => {
    const response = await api.get(`${SERVICES.INFRA}/health`);
    return response.data;
  },
};

export const checkAllServices = async () => {
  const services = [
    { name: 'AI Service', check: aiService.checkHealth },
    { name: 'RAG Service', check: ragService.checkHealth },
    { name: 'MCP Service', check: mcpService.checkHealth },
    { name: 'Infrastructure Service', check: infraService.checkHealth },
  ];

  const results = await Promise.allSettled(
    services.map(async (service) => {
      try {
        await service.check();
        return { name: service.name, status: 'healthy' };
      } catch (error) {
        return { name: service.name, status: 'unhealthy', error: error.message };
      }
    })
  );

  return results.map((result) => result.value);
};