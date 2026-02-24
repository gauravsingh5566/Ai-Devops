import { useQuery } from 'react-query';
import { Activity, Clock, CheckCircle, XCircle, Package } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { buildService } from '../services/api';

const Builds = () => {
  const { data: builds, isLoading } = useQuery(
    'builds',
    () => buildService.listBuilds(20),
    { refetchInterval: 5000 }
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6">
        <h1 className="text-3xl font-bold text-white mb-2">Build History</h1>
        <p className="text-blue-100">View all your builds and their status</p>
      </div>

      {/* Builds List */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="spinner" />
          </div>
        ) : builds && builds.length > 0 ? (
          <div className="space-y-4">
            {builds.map((build) => (
              <BuildCard key={build.job_id} build={build} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Activity className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-gray-600 font-medium mb-4">No builds yet</p>
            <a href="/projects" className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
              Start Building
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

const BuildCard = ({ build }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={24} />;
      case 'failed':
        return <XCircle className="text-red-500" size={24} />;
      default:
        return <Clock className="text-yellow-500 animate-pulse" size={24} />;
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      building: 'bg-yellow-100 text-yellow-800',
      pending: 'bg-blue-100 text-blue-800',
    };
    return badges[status] || 'bg-blue-100 text-blue-800';
  };

  return (
    <div className="border border-gray-200 rounded-lg p-6 hover:border-blue-400 hover:bg-blue-50 transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-4">
          {getStatusIcon(build.status)}
          <div>
            <div className="flex items-center space-x-3">
              <h3 className="font-semibold text-gray-900">
                {build.image_name || 'Build'}
              </h3>
              {build.image_tag && (
                <span className="text-sm text-gray-500">:{build.image_tag}</span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              ID: {build.job_id?.substring(0, 12)}
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(build.status)}`}>
          {build.status}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {build.project_info && (
          <>
            <InfoItem label="Language" value={build.project_info.language} />
            <InfoItem label="Framework" value={build.project_info.framework} />
          </>
        )}
        {build.image_size && (
          <InfoItem label="Image Size" value={build.image_size} />
        )}
        {build.created_at && (
          <InfoItem
            label="Started"
            value={formatDistanceToNow(new Date(build.created_at), { addSuffix: true })}
          />
        )}
      </div>

      {build.message && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-700">{build.message}</p>
        </div>
      )}

      {build.dockerfile && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-medium text-blue-600 hover:text-blue-700">
            View Dockerfile
          </summary>
          <pre className="mt-2 p-4 bg-gray-900 text-gray-100 rounded-lg text-xs overflow-x-auto">
            {build.dockerfile}
          </pre>
        </details>
      )}
    </div>
  );
};

const InfoItem = ({ label, value }) => (
  <div>
    <p className="text-xs text-gray-500">{label}</p>
    <p className="text-sm font-medium text-gray-900 mt-1">
      {value || 'N/A'}
    </p>
  </div>
);

export default Builds;