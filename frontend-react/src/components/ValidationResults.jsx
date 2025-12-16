import { DollarSign, Shield, AlertCircle, CheckCircle2, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

function ValidationResults({ validation }) {
  const [expandedSections, setExpandedSections] = useState({
    cost: false,
    security: false,
    quota: false,
    recommendations: false,
  });

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const getStatusBadge = () => {
    if (validation.status === 'passed') {
      return (
        <div className="flex items-center space-x-2 px-4 py-2 bg-success-500/20 border border-success-500/30 rounded-lg">
          <CheckCircle2 className="w-5 h-5 text-success-500" />
          <span className="text-success-500 font-semibold">Validation Passed</span>
        </div>
      );
    }
    
    if (validation.deployment_ready) {
      return (
        <div className="flex items-center space-x-2 px-4 py-2 bg-warning-500/20 border border-warning-500/30 rounded-lg">
          <AlertCircle className="w-5 h-5 text-warning-500" />
          <span className="text-warning-500 font-semibold">Warnings Found</span>
        </div>
      );
    }
    
    return (
      <div className="flex items-center space-x-2 px-4 py-2 bg-danger-500/20 border border-danger-500/30 rounded-lg">
        <XCircle className="w-5 h-5 text-danger-500" />
        <span className="text-danger-500 font-semibold">Validation Failed</span>
      </div>
    );
  };

  const getSecurityScoreColor = (score) => {
    if (score >= 80) return 'text-success-500';
    if (score >= 60) return 'text-warning-500';
    return 'text-danger-500';
  };

  return (
    <div className="space-y-6">
      {/* Status Badge */}
      <div className="flex justify-center">
        {getStatusBadge()}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Monthly Cost */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 text-primary-500" />
          </div>
          <p className="text-2xl font-bold text-gray-100">
            ${validation.total_monthly_cost?.toFixed(2) || '0.00'}
          </p>
          <p className="text-sm text-gray-400 mt-1">Monthly Cost</p>
        </div>

        {/* Security Score */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-2">
            <Shield className="w-8 h-8 text-primary-500" />
          </div>
          <p className={`text-2xl font-bold ${getSecurityScoreColor(validation.security_score)}`}>
            {validation.security_score}/100
          </p>
          <p className="text-sm text-gray-400 mt-1">Security Score</p>
        </div>

        {/* Resources */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-2">
            <svg className="w-8 h-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
            </svg>
          </div>
          <p className="text-2xl font-bold text-gray-100">
            {validation.resources_count || 0}
          </p>
          <p className="text-sm text-gray-400 mt-1">Resources</p>
        </div>

        {/* Issues */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-2">
            <AlertCircle className="w-8 h-8 text-primary-500" />
          </div>
          <p className="text-2xl font-bold text-gray-100">
            {validation.security_issues?.length || 0}
          </p>
          <p className="text-sm text-gray-400 mt-1">Issues Found</p>
        </div>
      </div>

      {/* Cost Breakdown */}
      {validation.cost_estimates && validation.cost_estimates.length > 0 && (
        <div className="card">
          <button
            onClick={() => toggleSection('cost')}
            className="w-full p-4 flex items-center justify-between hover:bg-dark-hover transition-colors"
          >
            <div className="flex items-center space-x-3">
              <DollarSign className="w-6 h-6 text-primary-500" />
              <h3 className="text-lg font-semibold">Cost Breakdown</h3>
            </div>
            {expandedSections.cost ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {expandedSections.cost && (
            <div className="p-4 border-t border-dark-border">
              <div className="space-y-3">
                {validation.cost_estimates.map((cost, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-dark-hover rounded-lg">
                    <span className="text-gray-300">{cost.resource_type}.{cost.resource_name}</span>
                    <span className="font-semibold text-primary-400">
                      ${cost.monthly_cost?.toFixed(2) || '0.00'}/mo
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Security Issues */}
      {validation.security_issues && validation.security_issues.length > 0 && (
        <div className="card">
          <button
            onClick={() => toggleSection('security')}
            className="w-full p-4 flex items-center justify-between hover:bg-dark-hover transition-colors"
          >
            <div className="flex items-center space-x-3">
              <Shield className="w-6 h-6 text-danger-500" />
              <h3 className="text-lg font-semibold">Security Issues</h3>
            </div>
            {expandedSections.security ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {expandedSections.security && (
            <div className="p-4 border-t border-dark-border">
              <div className="space-y-4">
                {validation.security_issues.map((issue, index) => (
                  <div key={index} className="p-4 bg-dark-hover rounded-lg border-l-4 border-danger-500">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={`badge ${
                            issue.severity === 'critical' ? 'badge-danger' :
                            issue.severity === 'high' ? 'badge-warning' :
                            'badge-info'
                          }`}>
                            {issue.severity.toUpperCase()}
                          </span>
                          <span className="text-sm text-gray-400">{issue.resource}</span>
                        </div>
                        <p className="text-gray-200 font-medium">{issue.issue}</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-400 mt-2">
                      💡 {issue.recommendation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quota Warnings */}
      {validation.quota_warnings && validation.quota_warnings.length > 0 && (
        <div className="card">
          <button
            onClick={() => toggleSection('quota')}
            className="w-full p-4 flex items-center justify-between hover:bg-dark-hover transition-colors"
          >
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-6 h-6 text-warning-500" />
              <h3 className="text-lg font-semibold">Quota Warnings</h3>
            </div>
            {expandedSections.quota ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {expandedSections.quota && (
            <div className="p-4 border-t border-dark-border">
              <div className="space-y-3">
                {validation.quota_warnings.map((warning, index) => (
                  <div key={index} className="p-3 bg-warning-500/10 border border-warning-500/30 rounded-lg">
                    <p className="text-warning-500">{warning.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ValidationResults;
