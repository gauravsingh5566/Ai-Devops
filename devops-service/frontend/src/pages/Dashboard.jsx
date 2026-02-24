import { useQuery } from 'react-query';
import { Activity, GitBranch, Package, CheckCircle, XCircle } from 'lucide-react';
import { healthService, buildService, githubService } from '../services/api';

const Dashboard = () => {
  const { data: health, isLoading: healthLoading } = useQuery('health', healthService.getHealth, {
    refetchInterval: 30000,
  });

  const { data: builds, isLoading: buildsLoading } = useQuery('recentBuilds', () => buildService.listBuilds(5));
  const { data: projects, isLoading: projectsLoading } = useQuery('projects', githubService.getProjects);

  const stats = [
    {
      label: 'Active Projects',
      value: projects?.count || 0,
      icon: Package,
      color: 'bg-blue-500',
    },
    {
      label: 'Total Builds',
      value: builds?.length || 0,
      icon: Activity,
      color: 'bg-purple-500',
    },
    {
      label: 'GitHub Repos',
      value: projects?.count || 0,
      icon: GitBranch,
      color: 'bg-green-500',
    },
    {
      label: 'Success Rate',
      value: '95%',
      icon: CheckCircle,
      color: 'bg-emerald-500',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6">
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-blue-100">Overview of your DevOps pipeline</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 hover:shadow-xl transition-shadow fade-in">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg shadow-md`}>
                  <Icon className="text-white" size={24} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Service Health */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Service Health</h2>
        {healthLoading ? (
          <div className="flex justify-center py-8">
            <div className="spinner"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ServiceStatus
              name="API Gateway"
              status={health?.gateway === 'healthy'}
            />
            {health?.agents && Object.entries(health.agents).map(([name, info]) => (
              <ServiceStatus
                key={name}
                name={name.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                status={info.health === 'healthy'}
              />
            ))}
          </div>
        )}
      </div>

      {/* Recent Builds */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Recent Builds</h2>
          <a href="/builds" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
            View All →
          </a>
        </div>
        <div className="space-y-3">
          {buildsLoading ? (
            <div className="flex justify-center py-8">
              <div className="spinner"></div>
            </div>
          ) : builds && builds.length > 0 ? (
            builds.map((build, idx) => (
              <BuildItem key={idx} build={build} />
            ))
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <Activity className="mx-auto text-gray-400 mb-3" size={48} />
              <p className="text-gray-600 font-medium">No builds yet</p>
              <p className="text-gray-500 text-sm mt-1">Import a project and start building!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ServiceStatus = ({ name, status }) => (
  <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
    {status ? (
      <CheckCircle className="text-green-500 flex-shrink-0" size={20} />
    ) : (
      <XCircle className="text-red-500 flex-shrink-0" size={20} />
    )}
    <div>
      <p className="font-medium text-gray-900">{name}</p>
      <p className="text-sm text-gray-600">
        {status ? 'Healthy' : 'Unavailable'}
      </p>
    </div>
  </div>
);

const BuildItem = ({ build }) => (
  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all">
    <div className="flex items-center space-x-4">
      <div className={`w-3 h-3 rounded-full flex-shrink-0 ${
        build.status === 'completed' ? 'bg-green-500' :
        build.status === 'failed' ? 'bg-red-500' :
        'bg-yellow-500 animate-pulse'
      }`} />
      <div>
        <p className="font-medium text-gray-900">{build.image_name || 'Build'}</p>
        <p className="text-sm text-gray-500">{build.job_id?.substring(0, 8)}</p>
      </div>
    </div>
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
      build.status === 'completed' ? 'bg-green-100 text-green-800' :
      build.status === 'failed' ? 'bg-red-100 text-red-800' :
      'bg-yellow-100 text-yellow-800'
    }`}>
      {build.status}
    </span>
  </div>
);

export default Dashboard;