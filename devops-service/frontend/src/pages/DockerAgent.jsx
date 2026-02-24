import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Container, 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Lightbulb,
  Play,
  Loader,
  Star,
  Shield,
  Zap,
  FolderOpen
} from 'lucide-react';
import toast from 'react-hot-toast';
import { dockerService, githubService } from '../services/api';

const DockerAgent = () => {
  const [activeTab, setActiveTab] = useState('validate'); // validate, build, jobs
  const [dockerfileContent, setDockerfileContent] = useState(
    `FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]`
  );
  const [buildConfig, setBuildConfig] = useState({
    selectedProject: null,
    imageName: '',
    tag: 'latest',
    validateBefore: true,
    validateAfter: true
  });

  const queryClient = useQueryClient();

  // Fetch imported projects
  const { data: projectsData, isLoading: projectsLoading } = useQuery(
    'projects',
    githubService.getProjects,
    {
      enabled: activeTab === 'build'
    }
  );

  // Validate Dockerfile mutation
  const validateMutation = useMutation(
    (content) => dockerService.validateDockerfile(content),
    {
      onSuccess: (data) => {
        toast.success('Dockerfile validated!');
      },
      onError: (error) => {
        toast.error('Validation failed');
      }
    }
  );

  // Build image mutation
  const buildMutation = useMutation(
    (config) => dockerService.buildImage(config),
    {
      onSuccess: (data) => {
        toast.success(`Build started: ${data.job_id.substring(0, 8)}`);
        queryClient.invalidateQueries('dockerJobs');
      },
      onError: (error) => {
        toast.error('Build failed to start');
      }
    }
  );

  // Fetch jobs
  const { data: jobs, isLoading: jobsLoading } = useQuery(
    'dockerJobs',
    () => dockerService.listJobs(10),
    { 
      refetchInterval: 5000,
      enabled: activeTab === 'jobs'
    }
  );

  const handleValidate = () => {
    validateMutation.mutate(dockerfileContent);
  };

  const handleProjectSelect = (project) => {
    setBuildConfig({
      ...buildConfig,
      selectedProject: project,
      imageName: project.repo.toLowerCase(),
      dockerfilePath: `${project.local_path}/Dockerfile`
    });
  };

  const handleBuild = () => {
    if (!buildConfig.selectedProject || !buildConfig.imageName) {
      toast.error('Please select a project');
      return;
    }
    
    buildMutation.mutate({
      dockerfilePath: buildConfig.dockerfilePath,
      imageName: buildConfig.imageName,
      tag: buildConfig.tag,
      validateBefore: buildConfig.validateBefore,
      validateAfter: buildConfig.validateAfter
    });
  };

  const validation = validateMutation.data;
  const projects = projectsData?.projects || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6">
        <div className="flex items-center space-x-3 mb-2">
          <Container className="text-white" size={32} />
          <h1 className="text-3xl font-bold text-white">Docker Agent</h1>
        </div>
        <p className="text-blue-100">AI-powered Docker validation and building</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 bg-white rounded-lg p-2 shadow">
        <button
          onClick={() => setActiveTab('validate')}
          className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'validate'
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <FileText className="inline mr-2" size={18} />
          Validate Dockerfile
        </button>
        <button
          onClick={() => setActiveTab('build')}
          className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'build'
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <Play className="inline mr-2" size={18} />
          Build Image
        </button>
        <button
          onClick={() => setActiveTab('jobs')}
          className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'jobs'
              ? 'bg-blue-600 text-white'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <Container className="inline mr-2" size={18} />
          Build Jobs
        </button>
      </div>

      {/* Validate Tab */}
      {activeTab === 'validate' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Dockerfile Editor */}
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Dockerfile</h2>
            <textarea
              value={dockerfileContent}
              onChange={(e) => setDockerfileContent(e.target.value)}
              className="w-full h-96 px-4 py-3 font-mono text-sm bg-gray-900 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Paste your Dockerfile here..."
            />
            <button
              onClick={handleValidate}
              disabled={validateMutation.isLoading}
              className="mt-4 w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {validateMutation.isLoading ? (
                <>
                  <Loader className="animate-spin mr-2" size={20} />
                  Validating with AI...
                </>
              ) : (
                <>
                  <Shield className="mr-2" size={20} />
                  Validate Dockerfile
                </>
              )}
            </button>
          </div>

          {/* Validation Results */}
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Validation Results</h2>
            
            {validateMutation.isLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader className="animate-spin text-blue-600" size={48} />
              </div>
            )}

            {validation && (
              <div className="space-y-6">
                {/* Score */}
                <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700 font-medium">Quality Score</span>
                    <div className="flex items-center space-x-2">
                      <Star className="text-yellow-500" size={24} />
                      <span className="text-3xl font-bold text-gray-900">
                        {validation.score}/100
                      </span>
                    </div>
                  </div>
                  <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all ${
                        validation.score >= 90 ? 'bg-green-500' :
                        validation.score >= 75 ? 'bg-blue-500' :
                        validation.score >= 60 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${validation.score}%` }}
                    />
                  </div>
                </div>

                {/* Issues */}
                {validation.issues && validation.issues.length > 0 && (
                  <div>
                    <h3 className="flex items-center text-lg font-semibold text-red-700 mb-3">
                      <XCircle className="mr-2" size={20} />
                      Critical Issues ({validation.issues.length})
                    </h3>
                    <div className="space-y-2">
                      {validation.issues.map((issue, idx) => (
                        <div key={idx} className="p-3 bg-red-50 border-l-4 border-red-500 rounded">
                          <p className="font-medium text-red-900">{issue.message}</p>
                          {issue.fix && (
                            <p className="text-sm text-red-700 mt-1">
                              💡 Fix: {issue.fix}
                            </p>
                          )}
                          {issue.line && (
                            <p className="text-xs text-red-600 mt-1">Line: {issue.line}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {validation.warnings && validation.warnings.length > 0 && (
                  <div>
                    <h3 className="flex items-center text-lg font-semibold text-yellow-700 mb-3">
                      <AlertTriangle className="mr-2" size={20} />
                      Warnings ({validation.warnings.length})
                    </h3>
                    <div className="space-y-2">
                      {validation.warnings.map((warning, idx) => (
                        <div key={idx} className="p-3 bg-yellow-50 border-l-4 border-yellow-500 rounded">
                          <p className="font-medium text-yellow-900">{warning.message}</p>
                          {warning.fix && (
                            <p className="text-sm text-yellow-700 mt-1">
                              💡 Fix: {warning.fix}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {validation.recommendations && validation.recommendations.length > 0 && (
                  <div>
                    <h3 className="flex items-center text-lg font-semibold text-blue-700 mb-3">
                      <Lightbulb className="mr-2" size={20} />
                      Recommendations ({validation.recommendations.length})
                    </h3>
                    <div className="space-y-2">
                      {validation.recommendations.map((rec, idx) => (
                        <div key={idx} className="p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
                          <p className="font-medium text-blue-900">{rec.message}</p>
                          {rec.impact && (
                            <p className="text-sm text-blue-700 mt-1">
                              ⚡ Impact: {rec.impact}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Summary */}
                {validation.summary && (
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm text-gray-700">{validation.summary}</p>
                  </div>
                )}

                {/* No issues */}
                {(!validation.issues || validation.issues.length === 0) &&
                 (!validation.warnings || validation.warnings.length === 0) && (
                  <div className="p-4 bg-green-50 border-l-4 border-green-500 rounded flex items-center">
                    <CheckCircle className="text-green-600 mr-3" size={24} />
                    <div>
                      <p className="font-semibold text-green-900">Excellent!</p>
                      <p className="text-sm text-green-700">No critical issues found</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {!validation && !validateMutation.isLoading && (
              <div className="text-center py-12 text-gray-500">
                <FileText className="mx-auto mb-4 text-gray-400" size={48} />
                <p>Validate a Dockerfile to see AI-powered analysis</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Build Tab */}
      {activeTab === 'build' && (
        <div className="space-y-6">
          {/* Project Selection */}
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <FolderOpen className="mr-2 text-blue-600" size={24} />
              Select Project with Dockerfile
            </h2>
            
            {projectsLoading ? (
              <div className="flex justify-center py-8">
                <Loader className="animate-spin text-blue-600" size={32} />
              </div>
            ) : projects.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((project) => (
                  <div
                    key={project._id}
                    onClick={() => handleProjectSelect(project)}
                    className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                      buildConfig.selectedProject?._id === project._id
                        ? 'border-blue-500 bg-blue-50 shadow-lg'
                        : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Container className="text-blue-600" size={20} />
                        <h3 className="font-semibold text-gray-900">{project.repo}</h3>
                      </div>
                      {buildConfig.selectedProject?._id === project._id && (
                        <CheckCircle className="text-blue-600" size={20} />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{project.full_name}</p>
                    <div className="flex items-center space-x-2 text-xs">
                      {project.language && (
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">
                          {project.language}
                        </span>
                      )}
                      {project.framework && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                          {project.framework}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      📁 {project.local_path}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 rounded-lg">
                <FolderOpen className="mx-auto text-gray-400 mb-4" size={48} />
                <p className="text-gray-600 font-medium mb-2">No projects found</p>
                <p className="text-gray-500 text-sm mb-4">
                  Import a project from GitHub first
                </p>
                <a
                  href="/github"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                >
                  Import from GitHub
                </a>
              </div>
            )}
          </div>

          {/* Build Configuration */}
          {buildConfig.selectedProject && (
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Build Configuration</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Image Name *
                  </label>
                  <input
                    type="text"
                    value={buildConfig.imageName}
                    onChange={(e) => setBuildConfig({...buildConfig, imageName: e.target.value})}
                    placeholder="my-app"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tag
                  </label>
                  <input
                    type="text"
                    value={buildConfig.tag}
                    onChange={(e) => setBuildConfig({...buildConfig, tag: e.target.value})}
                    placeholder="latest"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg mb-6">
                <p className="text-sm font-medium text-gray-700 mb-1">Selected Project:</p>
                <p className="text-gray-900">{buildConfig.selectedProject.full_name}</p>
                <p className="text-sm text-gray-600 mt-1">
                  Dockerfile: {buildConfig.dockerfilePath}
                </p>
              </div>

              <div className="space-y-3 mb-6">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={buildConfig.validateBefore}
                    onChange={(e) => setBuildConfig({...buildConfig, validateBefore: e.target.checked})}
                    className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-gray-700">
                    <Shield className="inline mr-2 text-blue-600" size={18} />
                    Validate Dockerfile before building
                  </span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={buildConfig.validateAfter}
                    onChange={(e) => setBuildConfig({...buildConfig, validateAfter: e.target.checked})}
                    className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-gray-700">
                    <Zap className="inline mr-2 text-blue-600" size={18} />
                    Validate image after building
                  </span>
                </label>
              </div>

              <button
                onClick={handleBuild}
                disabled={buildMutation.isLoading}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center"
              >
                {buildMutation.isLoading ? (
                  <>
                    <Loader className="animate-spin mr-2" size={20} />
                    Starting Build...
                  </>
                ) : (
                  <>
                    <Play className="mr-2" size={20} />
                    Build Docker Image
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Jobs Tab */}
      {activeTab === 'jobs' && (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Build Jobs</h2>
          
          {jobsLoading ? (
            <div className="flex justify-center py-12">
              <Loader className="animate-spin text-blue-600" size={48} />
            </div>
          ) : jobs && jobs.jobs && jobs.jobs.length > 0 ? (
            <div className="space-y-4">
              {jobs.jobs.map((job) => (
                <JobCard key={job.job_id} job={job} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Container className="mx-auto mb-4 text-gray-400" size={48} />
              <p>No build jobs yet</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const JobCard = ({ job }) => {
  const [expanded, setExpanded] = useState(false);
  
  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-blue-100 text-blue-800',
      validating_dockerfile: 'bg-yellow-100 text-yellow-800',
      building: 'bg-purple-100 text-purple-800',
      validating_image: 'bg-indigo-100 text-indigo-800',
      testing: 'bg-cyan-100 text-cyan-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden hover:border-blue-400 transition-all">
      {/* Header */}
      <div 
        className="p-4 cursor-pointer hover:bg-blue-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="font-semibold text-gray-900">
              {job.image_name}:{job.image_tag}
            </p>
            <p className="text-sm text-gray-500">ID: {job.job_id.substring(0, 12)}</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
              {job.status.replace(/_/g, ' ')}
            </span>
            <button className="text-gray-400 hover:text-gray-600">
              {expanded ? '▼' : '▶'}
            </button>
          </div>
        </div>

        {/* Quick Summary */}
        <div className="flex items-center space-x-4 text-sm">
          {job.dockerfile_validation && (
            <div className="flex items-center space-x-1">
              <Shield className="text-blue-600" size={16} />
              <span className="text-gray-600">
                Dockerfile: <span className="font-bold text-gray-900">{job.dockerfile_validation.score}/100</span>
              </span>
            </div>
          )}
          {job.image_validation && (
            <div className="flex items-center space-x-1">
              <CheckCircle className="text-green-600" size={16} />
              <span className="text-gray-600">
                Image: <span className="font-bold text-gray-900">{job.image_validation.score}/100</span>
              </span>
            </div>
          )}
          {job.image_size && (
            <div className="flex items-center space-x-1">
              <Container className="text-gray-600" size={16} />
              <span className="text-gray-600">{job.image_size}</span>
            </div>
          )}
        </div>

        {/* Error Message */}
        {job.error && (
          <div className="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
            ❌ {job.error}
          </div>
        )}
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-4 space-y-4">
          {/* Dockerfile Validation */}
          {job.dockerfile_validation && (
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                <Shield className="mr-2 text-blue-600" size={20} />
                Dockerfile Validation
              </h4>
              
              {/* Score */}
              <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Quality Score</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {job.dockerfile_validation.score}/100
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      job.dockerfile_validation.score >= 90 ? 'bg-green-500' :
                      job.dockerfile_validation.score >= 75 ? 'bg-blue-500' :
                      job.dockerfile_validation.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${job.dockerfile_validation.score}%` }}
                  />
                </div>
              </div>

              {/* Critical Issues */}
              {job.dockerfile_validation.issues && job.dockerfile_validation.issues.length > 0 && (
                <div className="mb-3">
                  <p className="text-sm font-semibold text-red-700 mb-2 flex items-center">
                    <XCircle className="mr-1" size={16} />
                    Critical Issues ({job.dockerfile_validation.issues.length})
                  </p>
                  <div className="space-y-2">
                    {job.dockerfile_validation.issues.map((issue, idx) => (
                      <div key={idx} className="p-3 bg-red-50 border-l-4 border-red-500 rounded">
                        <p className="text-red-900 font-medium">{issue.message}</p>
                        {issue.fix && (
                          <p className="text-red-700 mt-2 text-sm flex items-start">
                            <Lightbulb className="mr-1 flex-shrink-0 mt-0.5" size={14} />
                            <span><strong>Fix:</strong> {issue.fix}</span>
                          </p>
                        )}
                        {issue.line && (
                          <p className="text-red-600 text-xs mt-1">Line: {issue.line}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Warnings */}
              {job.dockerfile_validation.warnings && job.dockerfile_validation.warnings.length > 0 && (
                <div className="mb-3">
                  <p className="text-sm font-semibold text-yellow-700 mb-2 flex items-center">
                    <AlertTriangle className="mr-1" size={16} />
                    Warnings ({job.dockerfile_validation.warnings.length})
                  </p>
                  <div className="space-y-2">
                    {job.dockerfile_validation.warnings.map((warning, idx) => (
                      <div key={idx} className="p-3 bg-yellow-50 border-l-4 border-yellow-500 rounded">
                        <p className="text-yellow-900 font-medium">{warning.message}</p>
                        {warning.fix && (
                          <p className="text-yellow-700 mt-2 text-sm flex items-start">
                            <Lightbulb className="mr-1 flex-shrink-0 mt-0.5" size={14} />
                            <span><strong>Fix:</strong> {warning.fix}</span>
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {job.dockerfile_validation.recommendations && job.dockerfile_validation.recommendations.length > 0 && (
                <div>
                  <p className="text-sm font-semibold text-blue-700 mb-2 flex items-center">
                    <Star className="mr-1" size={16} />
                    Recommendations ({job.dockerfile_validation.recommendations.length})
                  </p>
                  <div className="space-y-2">
                    {job.dockerfile_validation.recommendations.map((rec, idx) => (
                      <div key={idx} className="p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
                        <p className="text-blue-900 font-medium">{rec.message}</p>
                        {rec.impact && (
                          <p className="text-blue-700 mt-1 text-sm flex items-start">
                            <Zap className="mr-1 flex-shrink-0 mt-0.5" size={14} />
                            <span><strong>Impact:</strong> {rec.impact}</span>
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Build Logs */}
          {job.build_logs && (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <details>
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-blue-600 p-3 bg-gray-100">
                  📄 View Build Logs ({job.build_logs.split('\n').length} lines)
                </summary>
                <pre className="p-4 bg-gray-900 text-gray-100 text-xs font-mono overflow-x-auto max-h-96 overflow-y-auto">
                  {job.build_logs}
                </pre>
              </details>
            </div>
          )}

          {/* Image Validation */}
          {job.image_validation && (
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                <CheckCircle className="mr-2 text-green-600" size={20} />
                Image Validation
              </h4>
              
              {/* Similar structure as Dockerfile validation... */}
              <div className="mb-3 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Quality Score</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {job.image_validation.score}/100
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      job.image_validation.score >= 90 ? 'bg-green-500' :
                      job.image_validation.score >= 75 ? 'bg-blue-500' :
                      job.image_validation.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${job.image_validation.score}%` }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DockerAgent;