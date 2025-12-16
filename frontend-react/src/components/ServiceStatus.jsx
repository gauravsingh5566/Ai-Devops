import { Activity, CheckCircle2, XCircle, X } from 'lucide-react';

function ServiceStatus({ services, onClose }) {
  const healthyCount = services.filter(s => s.status === 'healthy').length;
  const totalCount = services.length;

  return (
    <div className="card p-6 slide-in">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Activity className="w-6 h-6 text-primary-500" />
          <div>
            <h3 className="text-xl font-semibold">Service Health</h3>
            <p className="text-sm text-gray-400">
              {healthyCount} of {totalCount} services healthy
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {services.map((service, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg border-2 transition-all ${
              service.status === 'healthy'
                ? 'bg-success-500/10 border-success-500/30'
                : 'bg-danger-500/10 border-danger-500/30'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              {service.status === 'healthy' ? (
                <CheckCircle2 className="w-6 h-6 text-success-500" />
              ) : (
                <XCircle className="w-6 h-6 text-danger-500" />
              )}
              <span className={`badge ${
                service.status === 'healthy' ? 'badge-success' : 'badge-danger'
              }`}>
                {service.status}
              </span>
            </div>
            <p className="font-medium text-gray-100">{service.name}</p>
            {service.error && (
              <p className="text-xs text-danger-400 mt-2">{service.error}</p>
            )}
          </div>
        ))}
      </div>

      {healthyCount < totalCount && (
        <div className="mt-4 p-4 bg-warning-500/10 border border-warning-500/30 rounded-lg">
          <p className="text-sm text-warning-500">
            ⚠️ Some services are unhealthy. Please check your Docker containers.
          </p>
        </div>
      )}
    </div>
  );
}

export default ServiceStatus;
