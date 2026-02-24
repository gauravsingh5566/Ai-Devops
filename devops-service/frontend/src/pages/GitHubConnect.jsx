import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { GitBranch, RefreshCw, Download, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import { githubService } from '../services/api';

const GitHubConnect = () => {
  const [accessToken, setAccessToken] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();

  const { data: repos, isLoading: loadingRepos, refetch } = useQuery(
    'repos',
    () => githubService.getRepositories(true),
    { enabled: isConnected }
  );

  const connectMutation = useMutation(githubService.connect, {
    onSuccess: (data) => {
      setIsConnected(true);
      toast.success(`Connected as ${data.github_username}`);
      localStorage.setItem('githubConnected', 'true');
      refetch();
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const importMutation = useMutation(
    ({ owner, repo }) => githubService.importProject(owner, repo),
    {
      onSuccess: (data) => {
        toast.success(`Project ${data.project.full_name} imported successfully!`);
        queryClient.invalidateQueries('projects');
      },
      onError: (error) => {
        toast.error(error.message);
      },
    }
  );

  const handleConnect = (e) => {
    e.preventDefault();
    if (!accessToken.trim()) {
      toast.error('Please enter GitHub access token');
      return;
    }
    connectMutation.mutate(accessToken);
  };

  const handleImport = (repo) => {
    const [owner, name] = repo.full_name.split('/');
    importMutation.mutate({ owner, repo: name });
  };

  if (!isConnected && !localStorage.getItem('githubConnected')) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200 fade-in">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <GitBranch className="text-white" size={32} />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Connect GitHub Account</h1>
            <p className="text-gray-600">
              Connect your GitHub account to import and build your projects
            </p>
          </div>

          <form onSubmit={handleConnect} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GitHub Personal Access Token
              </label>
              <input
                type="password"
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-2 text-sm text-gray-500">
                Get your token from{' '}
                <a
                  href="https://github.com/settings/tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  GitHub Settings
                </a>
              </p>
            </div>

            <button
              type="submit"
              disabled={connectMutation.isLoading}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {connectMutation.isLoading ? (
                <>
                  <div className="spinner inline-block w-4 h-4 mr-2" />
                  Connecting...
                </>
              ) : (
                'Connect GitHub'
              )}
            </button>
          </form>

          <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-900 font-medium mb-2">
              🔐 Required Scopes:
            </p>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• <code className="bg-blue-100 px-2 py-1 rounded">repo</code> - Full control of repositories</li>
              <li>• <code className="bg-blue-100 px-2 py-1 rounded">user</code> - Read user profile data</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">GitHub Repositories</h1>
            <p className="text-blue-100">Import projects from your repositories</p>
          </div>
          <button
            onClick={() => refetch()}
            disabled={loadingRepos}
            className="px-4 py-2 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className={loadingRepos ? 'animate-spin' : ''} size={20} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Repository List */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
        {loadingRepos ? (
          <div className="flex items-center justify-center py-12">
            <div className="spinner" />
          </div>
        ) : repos && repos.repositories && repos.repositories.length > 0 ? (
          <div className="space-y-3">
            {repos.repositories.map((repo) => (
              <RepoCard
                key={repo.id}
                repo={repo}
                onImport={() => handleImport(repo)}
                importing={importMutation.isLoading}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <GitBranch className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-gray-600 font-medium">No repositories found</p>
          </div>
        )}
      </div>
    </div>
  );
};

const RepoCard = ({ repo, onImport, importing }) => (
  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all">
    <div className="flex-1">
      <div className="flex items-center space-x-3">
        <GitBranch className="text-gray-400" size={20} />
        <div>
          <p className="font-medium text-gray-900">{repo.name}</p>
          <p className="text-sm text-gray-500">{repo.full_name}</p>
        </div>
      </div>
      {repo.description && (
        <p className="text-sm text-gray-600 mt-2 ml-8">{repo.description}</p>
      )}
      <div className="flex items-center space-x-4 mt-2 ml-8">
        {repo.language && (
          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded font-medium">
            {repo.language}
          </span>
        )}
        <span className="text-xs text-gray-500">
          Branch: <span className="font-medium">{repo.default_branch}</span>
        </span>
        {repo.private && (
          <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded font-medium">
            Private
          </span>
        )}
      </div>
    </div>
    <button
      onClick={onImport}
      disabled={importing}
      className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
    >
      <Download size={16} />
      <span>Import</span>
    </button>
  </div>
);

export default GitHubConnect;