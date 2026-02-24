import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Package, Trash2, Play, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { githubService, buildService } from '../services/api';

const Projects = () => {
  const queryClient = useQueryClient();
  
  const { data: projects, isLoading } = useQuery('projects', githubService.getProjects);

  const buildMutation = useMutation(
    ({ projectPath, imageName }) => buildService.build(projectPath, imageName),
    {
      onSuccess: (data) => {
        toast.success(`Build started: ${data.job_id}`);
        queryClient.invalidateQueries('recentBuilds');
      },
      onError: (error) => {
        toast.error(error.message);
      },
    }
  );

  const deleteMutation = useMutation(
    ({ owner, repo }) => githubService.deleteProject(owner, repo),
    {
      onSuccess: () => {
        toast.success('Project deleted');
        queryClient.invalidateQueries('projects');
      },
      onError: (error) => {
        toast.error(error.message);
      },
    }
  );

  const handleBuild = (project) => {
    const imageName = project.repo.toLowerCase();
    buildMutation.mutate({
      projectPath: project.local_path,
      imageName,
    });
  };

  const handleDelete = (project) => {
    if (confirm(`Delete project ${project.full_name}?`)) {
      deleteMutation.mutate({
        owner: project.owner,
        repo: project.repo,
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6">
        <h1 className="text-3xl font-bold text-white mb-2">My Projects</h1>
        <p className="text-blue-100">Manage your imported projects</p>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="spinner" />
          </div>
        ) : projects && projects.projects && projects.projects.length > 0 ? (
          projects.projects.map((project) => (
            <ProjectCard
              key={project._id}
              project={project}
              onBuild={() => handleBuild(project)}
              onDelete={() => handleDelete(project)}
              building={buildMutation.isLoading}
              deleting={deleteMutation.isLoading}
            />
          ))
        ) : (
          <div className="col-span-full bg-white rounded-xl shadow-lg p-12 text-center border border-gray-200">
            <Package className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-gray-600 font-medium mb-4">No projects imported yet</p>
            <a href="/github" className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
              Import from GitHub
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

const ProjectCard = ({ project, onBuild, onDelete, building, deleting }) => (
  <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 hover:shadow-xl transition-shadow fade-in">
    <div className="flex items-start justify-between mb-4">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
          <Package className="text-white" size={20} />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{project.repo}</h3>
          <p className="text-sm text-gray-500">{project.full_name}</p>
        </div>
      </div>
      <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">Ready</span>
    </div>

    <div className="space-y-2 mb-4">
      {project.language && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Language:</span>
          <span className="font-medium text-gray-900">{project.language}</span>
        </div>
      )}
      {project.framework && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Framework:</span>
          <span className="font-medium text-gray-900">{project.framework}</span>
        </div>
      )}
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">Branch:</span>
        <span className="font-medium text-gray-900">{project.branch}</span>
      </div>
    </div>

    <div className="flex space-x-2 pt-4 border-t border-gray-200">
      <button
        onClick={onBuild}
        disabled={building}
        className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Play size={16} />
        <span>Build</span>
      </button>
      <button
        onClick={onDelete}
        disabled={deleting}
        className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Trash2 size={16} />
      </button>
    </div>
  </div>
);

export default Projects;