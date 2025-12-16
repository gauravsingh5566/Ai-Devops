import { CheckCircle2, Loader2, XCircle, Clock } from 'lucide-react';

function DeploymentProgress({ deployment }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-6 h-6 text-success-500" />;
      case 'failed':
        return <XCircle className="w-6 h-6 text-danger-500" />;
      case 'in_progress':
      case 'applying':
      case 'planning':
      case 'initializing':
        return <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />;
      default:
        return <Clock className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-success-500';
      case 'failed':
        return 'text-danger-500';
      case 'in_progress':
      case 'applying':
      case 'planning':
      case 'initializing':
        return 'text-primary-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-3">
        {getStatusIcon(deployment.status)}
        <div>
          <h3 className={`text-xl font-semibold ${getStatusColor(deployment.status)}`}>
            {deployment.status === 'completed' ? '🎉 Deployment Complete!' :
             deployment.status === 'failed' ? '❌ Deployment Failed' :
             `⏳ ${deployment.current_step || 'Processing'}...`}
          </h3>
          {deployment.deployment_name && (
            <p className="text-sm text-gray-400 mt-1">{deployment.deployment_name}</p>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {deployment.progress_percentage !== undefined && (
        <div className="w-full bg-dark-hover rounded-full h-2">
          <div
            className="bg-primary-600 h-full rounded-full transition-all duration-300"
            style={{ width: `${deployment.progress_percentage}%` }}
          />
        </div>
      )}

      {/* Resources Created */}
      {deployment.resources_created && deployment.resources_created.length > 0 && (
        <div className="card p-4">
          <h4 className="text-sm font-semibold text-gray-400 mb-3">📦 Resources Created:</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {deployment.resources_created.map((resource, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-dark-hover rounded">
                <CheckCircle2 className="w-4 h-4 text-success-500 flex-shrink-0" />
                <span className="text-sm text-gray-300 font-mono">{resource}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Message */}
      {deployment.error_message && (
        <div className="card p-4 border-l-4 border-danger-500">
          <h4 className="text-sm font-semibold text-danger-500 mb-2">Error:</h4>
          <p className="text-sm text-gray-300">{deployment.error_message}</p>
        </div>
      )}
    </div>
  );
}

export default DeploymentProgress;
