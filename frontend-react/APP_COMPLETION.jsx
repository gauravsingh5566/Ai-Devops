// This file contains the remaining JSX for the App component
// Add this content after the STEPS.INPUT section in App.jsx

/* 
  STEP 2: GENERATED CODE VIEW
  Shows generated Terraform code with approval gate
*/
{currentStep === STEPS.GENERATED && (
  <div className="space-y-6 slide-in">
    {/* Generated Code */}
    <CodeEditor 
      code={terraformCode} 
      language="hcl"
      title="Generated Terraform Code"
    />

    {/* Explanation */}
    {explanation && (
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-3">📝 What This Creates</h3>
        <p className="text-gray-300">{explanation}</p>
      </div>
    )}

    {/* Resources & Cost Info */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Resources Created */}
      {resources && resources.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">📦 Resources to Create</h3>
          <div className="space-y-2">
            {resources.map((resource, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-dark-hover rounded">
                <CheckCircle2 className="w-4 h-4 text-success-500 flex-shrink-0" />
                <span className="text-sm text-gray-300">{resource}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Info */}
      {costInfo && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">💰 Estimated Costs</h3>
          <p className="text-gray-300 text-sm">{costInfo}</p>
        </div>
      )}
    </div>

    {/* Expandable Sections */}
    {intent && (
      <div className="card">
        <button
          onClick={() => toggleSection('intent')}
          className="w-full p-4 flex items-center justify-between hover:bg-dark-hover transition-colors"
        >
          <div className="flex items-center space-x-3">
            <Terminal className="w-6 h-6 text-primary-500" />
            <h3 className="text-lg font-semibold">Parsed Intent</h3>
          </div>
          {expandedSections.intent ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>
        
        {expandedSections.intent && (
          <div className="p-4 border-t border-dark-border">
            <pre className="bg-dark-hover p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(intent, null, 2)}
            </pre>
          </div>
        )}
      </div>
    )}

    {ragContext && ragContext.length > 0 && (
      <div className="card">
        <button
          onClick={() => toggleSection('ragContext')}
          className="w-full p-4 flex items-center justify-between hover:bg-dark-hover transition-colors"
        >
          <div className="flex items-center space-x-3">
            <Shield className="w-6 h-6 text-primary-500" />
            <h3 className="text-lg font-semibold">AWS Best Practices Applied</h3>
          </div>
          {expandedSections.ragContext ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>
        
        {expandedSections.ragContext && (
          <div className="p-4 border-t border-dark-border space-y-3">
            {ragContext.map((doc, index) => (
              <div key={index} className="p-4 bg-dark-hover rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-primary-400">
                    {doc.metadata?.title || `Best Practice ${index + 1}`}
                  </h4>
                  <span className="badge badge-info">
                    Score: {(doc.score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-sm text-gray-300">{doc.content.substring(0, 200)}...</p>
              </div>
            ))}
          </div>
        )}
      </div>
    )}

    {/* Approval Gate */}
    <div className="card p-6 bg-warning-500/10 border-2 border-warning-500/30">
      <div className="flex items-start space-x-4">
        <AlertCircle className="w-8 h-8 text-warning-500 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-warning-500 mb-3">
            🔍 Ready to Validate?
          </h3>
          <p className="text-gray-300 mb-4">
            Validation will check this infrastructure for:
          </p>
          <ul className="space-y-2 mb-6">
            <li className="flex items-center space-x-2">
              <DollarSign className="w-5 h-5 text-primary-500" />
              <span>Cost estimation for AWS resources</span>
            </li>
            <li className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-primary-500" />
              <span>Security analysis for vulnerabilities</span>
            </li>
            <li className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-primary-500" />
              <span>Quota checking for AWS limits</span>
            </li>
          </ul>
          
          <div className="flex space-x-4">
            <button
              onClick={handleValidate}
              disabled={loading}
              className="btn btn-success flex items-center space-x-2 disabled:opacity-50"
            >
              <CheckCircle2 className="w-5 h-5" />
              <span>Proceed to Validation</span>
            </button>
            <button
              onClick={resetAll}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <RefreshCw className="w-5 h-5" />
              <span>Start Over</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
)}

/*
  STEP 3: VALIDATION RESULTS
  Shows validation metrics and deployment approval
*/
{currentStep === STEPS.VALIDATED && (
  <div className="space-y-6 slide-in">
    {/* Validation Results Component */}
    {validationResult && <ValidationResults validation={validationResult} />}

    {/* Approval Gate for Deployment */}
    {validationResult?.deployment_ready ? (
      <div className="card p-6 bg-success-500/10 border-2 border-success-500/30">
        <div className="flex items-start space-x-4">
          <Rocket className="w-8 h-8 text-success-500 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-success-500 mb-3">
              🚀 Ready to Deploy?
            </h3>
            
            <div className="bg-dark-hover p-4 rounded-lg mb-4">
              <h4 className="font-semibold mb-2">Deployment Summary:</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Region:</span>
                  <span className="text-gray-100 ml-2">us-east-1</span>
                </div>
                <div>
                  <span className="text-gray-400">Resources:</span>
                  <span className="text-gray-100 ml-2">{validationResult.resources_count}</span>
                </div>
                <div>
                  <span className="text-gray-400">Monthly Cost:</span>
                  <span className="text-gray-100 ml-2">${validationResult.total_monthly_cost?.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Security Score:</span>
                  <span className="text-gray-100 ml-2">{validationResult.security_score}/100</span>
                </div>
              </div>
            </div>

            <div className="bg-danger-500/20 border border-danger-500/30 rounded-lg p-4 mb-6">
              <p className="text-danger-400 flex items-start space-x-2">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Warning:</strong> This will create REAL AWS resources in your account and may incur costs!
                </span>
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Deployment Name
                </label>
                <input
                  type="text"
                  value={deploymentName}
                  onChange={(e) => setDeploymentName(e.target.value)}
                  placeholder="e.g., production-vpc-deployment"
                  className="input"
                />
              </div>

              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  id="confirmDeploy"
                  checked={confirmDeploy}
                  onChange={(e) => setConfirmDeploy(e.target.checked)}
                  className="mt-1"
                />
                <label htmlFor="confirmDeploy" className="text-sm text-gray-300">
                  I understand this will create AWS resources in my account and may incur costs. I have reviewed the validation results and approve this deployment.
                </label>
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={handleDeploy}
                  disabled={loading || !deploymentName.trim() || !confirmDeploy}
                  className="btn btn-success flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Rocket className="w-5 h-5" />
                  <span>Deploy to AWS</span>
                </button>
                <button
                  onClick={() => setCurrentStep(STEPS.GENERATED)}
                  className="btn btn-secondary flex items-center space-x-2"
                >
                  <RefreshCw className="w-5 h-5" />
                  <span>Back to Code</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    ) : (
      <div className="card p-6 bg-danger-500/10 border-2 border-danger-500/30">
        <div className="flex items-start space-x-4">
          <XCircle className="w-8 h-8 text-danger-500 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-danger-500 mb-3">
              ❌ Cannot Deploy - Critical Issues Found
            </h3>
            <p className="text-gray-300 mb-4">
              Please fix the following critical issues before deployment:
            </p>
            
            {validationResult?.security_issues
              ?.filter(issue => issue.severity === 'critical' || issue.severity === 'high')
              .map((issue, index) => (
                <div key={index} className="p-3 bg-dark-hover rounded-lg mb-3 border-l-4 border-danger-500">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="badge badge-danger">{issue.severity.toUpperCase()}</span>
                    <span className="text-sm text-gray-400">{issue.resource}</span>
                  </div>
                  <p className="text-gray-200 font-medium">{issue.issue}</p>
                  <p className="text-sm text-gray-400 mt-2">💡 {issue.recommendation}</p>
                </div>
              ))}

            <button
              onClick={resetAll}
              className="btn btn-secondary flex items-center space-x-2 mt-4"
            >
              <RefreshCw className="w-5 h-5" />
              <span>Start Over</span>
            </button>
          </div>
        </div>
      </div>
    )}
  </div>
)}

/*
  STEP 4: DEPLOYMENT COMPLETE
  Shows deployment status and created resources
*/
{currentStep === STEPS.DEPLOYED && (
  <div className="space-y-6 slide-in">
    {deploymentData && <DeploymentProgress deployment={deploymentData} />}

    {/* Deployment Details */}
    {deploymentData && (
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">Deployment Details</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400">Deployment ID</p>
            <p className="text-gray-100 font-mono text-sm">{deploymentData.deployment_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Deployment Name</p>
            <p className="text-gray-100">{deploymentData.deployment_name || deploymentName}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Status</p>
            <p className={`font-semibold ${
              deploymentData.status === 'completed' ? 'text-success-500' :
              deploymentData.status === 'failed' ? 'text-danger-500' :
              'text-warning-500'
            }`}>
              {deploymentData.status?.toUpperCase()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Region</p>
            <p className="text-gray-100">{deploymentData.region || 'us-east-1'}</p>
          </div>
        </div>
      </div>
    )}

    {/* Action Buttons */}
    <div className="flex space-x-4">
      <button
        onClick={resetAll}
        className="btn btn-primary flex items-center space-x-2"
      >
        <Zap className="w-5 h-5" />
        <span>Deploy New Infrastructure</span>
      </button>
      <button
        onClick={async () => {
          const deployments = await infraService.listDeployments();
          console.log('All deployments:', deployments);
          toast.success('Check console for deployment history');
        }}
        className="btn btn-secondary flex items-center space-x-2"
      >
        <Server className="w-5 h-5" />
        <span>View All Deployments</span>
      </button>
    </div>
  </div>
)}
