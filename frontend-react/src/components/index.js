// DeploymentProgress.jsx
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';

export function DeploymentProgress({ deployment }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-success-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-danger-500" />;
      default:
        return <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />;
    }
  };

  return (
    <div className="card p-6">
      <div className="flex items-center space-x-3 mb-4">
        {getStatusIcon(deployment.status)}
        <h3 className="text-xl font-semibold">
          {deployment.status === 'completed' ? 'Deployment Complete!' :
           deployment.status === 'failed' ? 'Deployment Failed' :
           'Deploying...'}
        </h3>
      </div>

      {deployment.resources_created && deployment.resources_created.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-400 mb-3">Resources Created:</h4>
          <div className="space-y-2">
            {deployment.resources_created.map((resource, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-dark-hover rounded">
                <CheckCircle2 className="w-4 h-4 text-success-500 flex-shrink-0" />
                <span className="text-sm text-gray-300">{resource}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ServiceStatus.jsx
import { Activity, CheckCircle2, XCircle } from 'lucide-react';

export function ServiceStatus({ services, onClose }) {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Activity className="w-6 h-6 text-primary-500" />
          <h3 className="text-xl font-semibold">Service Health</h3>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-200">
          ×
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {services.map((service, index) => (
          <div key={index} className="p-4 bg-dark-hover rounded-lg border border-dark-border">
            <div className="flex items-center justify-between">
              <span className="font-medium">{service.name}</span>
              {service.status === 'healthy' ? (
                <div className="flex items-center space-x-2 text-success-500">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="text-sm">Healthy</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2 text-danger-500">
                  <XCircle className="w-5 h-5" />
                  <span className="text-sm">Unhealthy</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default { DeploymentProgress, ServiceStatus };
