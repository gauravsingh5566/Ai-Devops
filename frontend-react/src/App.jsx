import { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { 
  Terminal, 
  Rocket, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Cloud,
  Shield,
  DollarSign,
  Activity,
  Zap,
  Code,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Server,
  FileText,
  LogOut
} from 'lucide-react';
import { aiService, ragService, mcpService, infraService, checkAllServices } from './services/api';
import CodeEditor from './components/CodeEditor';
import ValidationResults from './components/ValidationResults';
import DeploymentProgress from './components/DeploymentProgress';
import ServiceStatus from './components/ServiceStatus';
import Login from './components/Login';

const STEPS = {
  INPUT: 0,
  INTENT_PARSED: 1,
  GENERATED: 2,
  VALIDATED: 3,
  PLAN_REVIEW: 4,  // NEW: Review Terraform plan before deployment
  DEPLOYED: 5,
};

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  
  const [currentStep, setCurrentStep] = useState(STEPS.INPUT);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  
  // Data states
  const [intent, setIntent] = useState(null);
  const [ragContext, setRagContext] = useState(null);
  const [terraformCode, setTerraformCode] = useState('');
  const [explanation, setExplanation] = useState('');
  const [resources, setResources] = useState([]);
  const [costInfo, setCostInfo] = useState('');
  
  const [validationResult, setValidationResult] = useState(null);
  const [deploymentData, setDeploymentData] = useState(null);
  const [planData, setPlanData] = useState(null);  // NEW: Store Terraform plan
  const [deploymentName, setDeploymentName] = useState('');
  const [confirmDeploy, setConfirmDeploy] = useState(false);
  
  // UI states
  const [expandedSections, setExpandedSections] = useState({
    intent: false,
    ragContext: false,
    costBreakdown: false,
    securityDetails: false,
    recommendations: false,
  });
  const [serviceHealth, setServiceHealth] = useState([]);
  const [showServiceStatus, setShowServiceStatus] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    const auth = localStorage.getItem('isAuthenticated');
    const savedUsername = localStorage.getItem('username');
    if (auth === 'true' && savedUsername) {
      setIsAuthenticated(true);
      setUsername(savedUsername);
    }
  }, []);

  // Check service health on mount
  useEffect(() => {
    if (!isAuthenticated) return;
    checkServices();
    const interval = setInterval(checkServices, 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const handleLogin = (user) => {
    setIsAuthenticated(true);
    setUsername(user);
  };

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('username');
    setIsAuthenticated(false);
    setUsername('');
    resetAll();
  };

  const checkServices = async () => {
    try {
      const health = await checkAllServices();
      setServiceHealth(health);
    } catch (error) {
      console.error('Error checking services:', error);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const resetAll = () => {
    setCurrentStep(STEPS.INPUT);
    setUserInput('');
    setIntent(null);
    setRagContext(null);
    setTerraformCode('');
    setExplanation('');
    setResources([]);
    setCostInfo('');
    setValidationResult(null);
    setDeploymentData(null);
    setDeploymentName('');
    setConfirmDeploy(false);
    setExpandedSections({
      intent: false,
      ragContext: false,
      costBreakdown: false,
      securityDetails: false,
      recommendations: false,
    });
  };

  const handleParseIntent = async () => {
    if (!userInput.trim()) {
      toast.error('Please enter infrastructure requirements');
      return;
    }

    setLoading(true);
    try {
      setLoadingMessage('🧠 Parsing your infrastructure requirements...');
      const intentData = await aiService.parseIntent(userInput);
      
      const parsedIntent = intentData.intent || intentData;
      setIntent(parsedIntent);
      toast.success('✅ Intent parsed successfully');
      
      setCurrentStep(STEPS.INTENT_PARSED);
    } catch (error) {
      console.error('Intent parsing error:', error);
      toast.error(`Failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const handleGenerateCode = async () => {
    setLoading(true);
    try {
      // Get RAG context if needed
      let contextData = null;
      const needsRag = intent?.needs_rag !== false;
      
      if (needsRag) {
        setLoadingMessage('📚 Retrieving AWS best practices...');
        try {
          const ragResponse = await ragService.search(userInput);
          contextData = ragResponse.results || ragResponse;
          setRagContext(contextData);
          toast.success(`✅ Retrieved ${Array.isArray(contextData) ? contextData.length : 0} best practices`);
        } catch (ragError) {
          console.warn('RAG retrieval failed, continuing without context:', ragError);
          toast.warning('Continuing without best practices');
        }
      }

      setLoadingMessage('⚡ Generating Terraform code...');
      const codeData = await aiService.generateCode(intent, contextData);
      
      setTerraformCode(codeData.terraform_code || '');
      setExplanation(codeData.explanation || 'Infrastructure code generated');
      setResources(codeData.resources_created || []);
      setCostInfo(codeData.estimated_cost_info || 'Cost varies by usage');
      
      toast.success('✅ Terraform code generated!');
      setCurrentStep(STEPS.GENERATED);
    } catch (error) {
      console.error('Generation error:', error);
      toast.error(`Failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const handleValidate = async () => {
    setLoading(true);
    try {
      setLoadingMessage('🔍 Running validation checks...');
      const result = await mcpService.validate(terraformCode);
      setValidationResult(result);
      toast.success('✅ Validation complete!');
      setCurrentStep(STEPS.VALIDATED);
    } catch (error) {
      console.error('Validation error:', error);
      toast.error(`Validation failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const handleDeploy = async () => {
    if (!deploymentName.trim()) {
      toast.error('Please enter a deployment name');
      return;
    }
    
    if (!confirmDeploy) {
      toast.error('Please confirm you understand this will create AWS resources');
      return;
    }

    setLoading(true);
    try {
      setLoadingMessage('📦 Creating deployment...');
      const deployment = await infraService.createDeployment(terraformCode, deploymentName);
      setDeploymentData(deployment);
      toast.success(`✅ Deployment created: ${deployment.deployment_id}`);

      setLoadingMessage('🔧 Initializing Terraform...');
      await infraService.initDeployment(deployment.deployment_id);
      toast.success('✅ Terraform initialized');

      setLoadingMessage('📋 Generating plan...');
      const plan = await infraService.planDeployment(deployment.deployment_id);
      setPlanData(plan);  // Store plan data
      toast.success(`✅ Plan ready: ${plan.plan_summary?.add || 0} resources to add`);
      
      // STOP HERE - Show plan for user review and approval
      setCurrentStep(STEPS.PLAN_REVIEW);
      
    } catch (error) {
      console.error('Deployment error:', error);
      toast.error(`Deployment failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  // NEW: Apply deployment after user reviews and approves the plan
  const handleApplyDeployment = async () => {
    if (!deploymentData?.deployment_id) {
      toast.error('No deployment to apply');
      return;
    }

    setLoading(true);
    try {
      setLoadingMessage('🚀 Applying infrastructure to AWS...');
      const result = await infraService.applyDeployment(deploymentData.deployment_id);
      setDeploymentData(result);
      toast.success('🎉 Infrastructure deployed successfully to AWS!');
      setCurrentStep(STEPS.DEPLOYED);
    } catch (error) {
      console.error('Apply error:', error);
      toast.error(`Apply failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg text-gray-100">
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#151b2e',
            color: '#fff',
            border: '1px solid #1f2937',
          },
        }}
      />

      {/* Show login if not authenticated */}
      {!isAuthenticated ? (
        <Login onLogin={handleLogin} />
      ) : (
        <>
          {/* Header */}
          <header className="bg-dark-surface border-b border-dark-border sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                    <Terminal className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                      AI DevOps Assistant
                    </h1>
                    <p className="text-sm text-gray-400">Natural Language to AWS Infrastructure</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  {/* User info */}
                  <div className="flex items-center space-x-2 px-3 py-2 bg-dark-hover rounded-lg">
                    <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-white">
                        {username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className="text-sm text-gray-300">{username}</span>
                  </div>
                  
                  <button
                    onClick={() => setShowServiceStatus(!showServiceStatus)}
                    className="btn btn-secondary flex items-center space-x-2"
                  >
                <Activity className="w-4 h-4" />
                <span>Services</span>
              </button>
              
              {currentStep > STEPS.INPUT && (
                <button
                  onClick={resetAll}
                  className="btn btn-secondary flex items-center space-x-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>New Request</span>
                </button>
              )}
              
              <button
                onClick={handleLogout}
                className="btn btn-danger flex items-center space-x-2"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {showServiceStatus && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <ServiceStatus services={serviceHealth} onClose={() => setShowServiceStatus(false)} />
        </div>
      )}

      {/* Progress Indicator */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-between">
          {[
            { step: STEPS.INPUT, label: 'Input', icon: Terminal },
            { step: STEPS.INTENT_PARSED, label: 'Intent', icon: CheckCircle2 },
            { step: STEPS.GENERATED, label: 'Generated', icon: Code },
            { step: STEPS.VALIDATED, label: 'Validated', icon: Shield },
            { step: STEPS.PLAN_REVIEW, label: 'Plan', icon: FileText },
            { step: STEPS.DEPLOYED, label: 'Deployed', icon: Rocket },
          ].map((item, index) => (
            <div key={item.step} className="flex items-center flex-1">
              <div className={`flex flex-col items-center flex-1 ${index === 5 ? '' : 'relative'}`}>
                <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                  currentStep > item.step ? 'bg-success-600 border-success-600' :
                  currentStep === item.step ? 'bg-primary-600 border-primary-600 animate-pulse' :
                  'bg-dark-surface border-dark-border'
                }`}>
                  <item.icon className={`w-6 h-6 ${currentStep >= item.step ? 'text-white' : 'text-gray-500'}`} />
                </div>
                <span className={`mt-2 text-sm font-medium ${currentStep >= item.step ? 'text-gray-100' : 'text-gray-500'}`}>
                  {item.label}
                </span>
                
                {index < 5 && (
                  <div className={`absolute top-6 left-1/2 w-full h-0.5 transition-all duration-300 ${
                    currentStep > item.step ? 'bg-success-600' : 'bg-dark-border'
                  }`} style={{ transform: 'translateY(-50%)' }} />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-20">
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-40 flex items-center justify-center">
            <div className="card p-8 max-w-md w-full mx-4">
              <div className="flex flex-col items-center space-y-4">
                <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
                <p className="text-lg font-medium text-gray-100">{loadingMessage}</p>
                <div className="w-full bg-dark-hover rounded-full h-2">
                  <div className="bg-primary-600 h-full rounded-full animate-pulse" style={{ width: '70%' }} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 0: INPUT */}
        {currentStep === STEPS.INPUT && (
          <div className="space-y-6">
            <div className="card p-8">
              <div className="flex items-center space-x-3 mb-6">
                <Cloud className="w-8 h-8 text-primary-500" />
                <h2 className="text-2xl font-bold">What infrastructure do you need?</h2>
              </div>
              
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Example: Create a production VPC with 2 public and 2 private subnets across 2 availability zones with NAT gateways"
                className="input min-h-[200px] resize-none"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.ctrlKey) handleGenerate();
                }}
              />
              
              <div className="mt-6 flex justify-between items-center">
                <p className="text-sm text-gray-400">Press Ctrl+Enter or click the button to generate</p>
                <button
                  onClick={handleParseIntent}
                  disabled={loading || !userInput.trim()}
                  className="btn btn-primary flex items-center space-x-2 px-6 py-3 text-lg disabled:opacity-50"
                >
                  <Zap className="w-5 h-5" />
                  <span>Parse Requirements</span>
                </button>
              </div>
            </div>

            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-primary-500" />
                <span>Example Requests</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  'Create a VPC with 2 public and 2 private subnets',
                  'Set up an EC2 instance with Auto Scaling and Load Balancer',
                  'Deploy a MySQL RDS database with Multi-AZ',
                  'Create an S3 bucket with encryption and lifecycle policies',
                ].map((example, index) => (
                  <button
                    key={index}
                    onClick={() => setUserInput(example)}
                    className="text-left p-4 bg-dark-hover hover:bg-dark-border rounded-lg border border-dark-border transition-colors"
                  >
                    <p className="text-sm text-gray-300">{example}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* STEP 1: INTENT PARSED - Review and Confirm */}
        {currentStep === STEPS.INTENT_PARSED && (
          <div className="space-y-6">
            {/* Parsed Intent Display */}
            <div className="card p-8">
              <div className="flex items-center space-x-3 mb-6">
                <CheckCircle2 className="w-8 h-8 text-success-500" />
                <h2 className="text-2xl font-bold">Intent Parsed Successfully!</h2>
              </div>

              {intent && (
                <div className="space-y-6">
                  {/* Resources */}
                  {intent.resources && intent.resources.length > 0 && (
                    <div className="bg-dark-hover p-6 rounded-lg">
                      <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                        <Server className="w-5 h-5 text-primary-500" />
                        <span>AWS Resources Identified</span>
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {intent.resources.map((resource, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-primary-500/20 border border-primary-500/30 rounded-full text-primary-400 text-sm font-medium"
                          >
                            {resource}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Requirements */}
                  {intent.requirements && Object.keys(intent.requirements).length > 0 && (
                    <div className="bg-dark-hover p-6 rounded-lg">
                      <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                        <Code className="w-5 h-5 text-primary-500" />
                        <span>Requirements Extracted</span>
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(intent.requirements).map(([key, value]) => (
                          <div key={key} className="flex justify-between items-center p-3 bg-dark-surface rounded">
                            <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}:</span>
                            <span className="text-gray-100 font-medium">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Complexity */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {intent.estimated_complexity && (
                      <div className="bg-dark-hover p-6 rounded-lg">
                        <h3 className="text-sm font-semibold text-gray-400 mb-2">Complexity Level</h3>
                        <div className="flex items-center space-x-2">
                          <span className={`px-4 py-2 rounded-lg text-lg font-bold ${
                            intent.estimated_complexity === 'simple' ? 'bg-success-500/20 text-success-500' :
                            intent.estimated_complexity === 'moderate' ? 'bg-warning-500/20 text-warning-500' :
                            'bg-danger-500/20 text-danger-500'
                          }`}>
                            {intent.estimated_complexity?.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    )}

                    {intent.needs_rag !== undefined && (
                      <div className="bg-dark-hover p-6 rounded-lg">
                        <h3 className="text-sm font-semibold text-gray-400 mb-2">Best Practices Lookup</h3>
                        <div className="flex items-center space-x-2">
                          {intent.needs_rag ? (
                            <>
                              <CheckCircle2 className="w-6 h-6 text-success-500" />
                              <span className="text-success-500 font-semibold">Will retrieve AWS best practices</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-6 h-6 text-gray-500" />
                              <span className="text-gray-400">Not needed</span>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Raw Intent (Expandable) */}
                  <div className="card">
                    <button
                      onClick={() => toggleSection('intent')}
                      className="w-full p-4 flex items-center justify-between hover:bg-dark-hover transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <Terminal className="w-6 h-6 text-primary-500" />
                        <h3 className="text-lg font-semibold">View Raw Intent JSON</h3>
                      </div>
                      {expandedSections.intent ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </button>
                    
                    {expandedSections.intent && (
                      <div className="p-4 border-t border-dark-border">
                        <pre className="bg-dark-surface p-4 rounded-lg overflow-x-auto text-sm">
                          {JSON.stringify(intent, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Approval Gate */}
            <div className="card p-6 bg-primary-500/10 border-2 border-primary-500/30">
              <div className="flex items-start space-x-4">
                <Zap className="w-8 h-8 text-primary-500 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-primary-400 mb-3">
                    ⚡ Ready to Generate Code?
                  </h3>
                  <p className="text-gray-300 mb-4">
                    Based on the parsed intent above, we will:
                  </p>
                  <ul className="space-y-2 mb-6">
                    {intent?.needs_rag && (
                      <li className="flex items-center space-x-2">
                        <CheckCircle2 className="w-5 h-5 text-success-500" />
                        <span>Retrieve relevant AWS best practices from knowledge base</span>
                      </li>
                    )}
                    <li className="flex items-center space-x-2">
                      <CheckCircle2 className="w-5 h-5 text-success-500" />
                      <span>Generate production-ready Terraform code</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircle2 className="w-5 h-5 text-success-500" />
                      <span>Include security best practices and proper tagging</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <CheckCircle2 className="w-5 h-5 text-success-500" />
                      <span>Add comments and documentation</span>
                    </li>
                  </ul>

                  <div className="bg-dark-hover p-4 rounded-lg mb-6">
                    <p className="text-sm text-gray-400">
                      💡 <strong>Tip:</strong> If the parsed intent doesn't match your requirements, 
                      click "Start Over" to refine your request.
                    </p>
                  </div>
                  
                  <div className="flex space-x-4">
                    <button
                      onClick={handleGenerateCode}
                      disabled={loading}
                      className="btn btn-success flex items-center space-x-2 disabled:opacity-50"
                    >
                      <Code className="w-5 h-5" />
                      <span>Generate Terraform Code</span>
                    </button>
                    <button
                      onClick={() => setCurrentStep(STEPS.INPUT)}
                      className="btn btn-secondary flex items-center space-x-2"
                    >
                      <RefreshCw className="w-5 h-5" />
                      <span>Modify Request</span>
                    </button>
                    <button
                      onClick={resetAll}
                      className="btn btn-secondary flex items-center space-x-2"
                    >
                      <XCircle className="w-5 h-5" />
                      <span>Start Over</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: GENERATED CODE */}
        {currentStep === STEPS.GENERATED && (
          <div className="space-y-6">
            <CodeEditor code={terraformCode} language="hcl" title="Generated Terraform Code" />

            {explanation && (
              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-3">📝 What This Creates</h3>
                <p className="text-gray-300">{explanation}</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

              {costInfo && (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold mb-4">💰 Estimated Costs</h3>
                  <p className="text-gray-300 text-sm">{costInfo}</p>
                </div>
              )}
            </div>

            <div className="card p-6 bg-warning-500/10 border-2 border-warning-500/30">
              <div className="flex items-start space-x-4">
                <AlertCircle className="w-8 h-8 text-warning-500 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-warning-500 mb-3">🔍 Ready to Validate?</h3>
                  <p className="text-gray-300 mb-4">Validation will check this infrastructure for:</p>
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
                    <button onClick={resetAll} className="btn btn-secondary flex items-center space-x-2">
                      <RefreshCw className="w-5 h-5" />
                      <span>Start Over</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: VALIDATED */}
        {currentStep === STEPS.VALIDATED && (
          <div className="space-y-6">
            {validationResult && <ValidationResults validation={validationResult} />}

            {validationResult?.deployment_ready ? (
              <div className="card p-6 bg-success-500/10 border-2 border-success-500/30">
                <div className="flex items-start space-x-4">
                  <Rocket className="w-8 h-8 text-success-500 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-success-500 mb-3">🚀 Ready to Deploy?</h3>
                    
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
                        <label className="block text-sm font-medium text-gray-300 mb-2">Deployment Name</label>
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
                          className="btn btn-success flex items-center space-x-2 disabled:opacity-50"
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
                    <h3 className="text-xl font-semibold text-danger-500 mb-3">❌ Cannot Deploy - Critical Issues Found</h3>
                    <p className="text-gray-300 mb-4">Please fix the following critical issues before deployment:</p>
                    
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

                    <button onClick={resetAll} className="btn btn-secondary flex items-center space-x-2 mt-4">
                      <RefreshCw className="w-5 h-5" />
                      <span>Start Over</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* STEP 4: PLAN REVIEW */}
        {currentStep === STEPS.PLAN_REVIEW && planData && (
          <div className="space-y-6">
            {/* Plan Summary Card */}
            <div className="card p-8 border-2 border-warning-500/30">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <FileText className="w-8 h-8 text-warning-500" />
                  <div>
                    <h2 className="text-2xl font-bold text-gray-100">Review Terraform Plan</h2>
                    <p className="text-gray-400 mt-1">Review what will be created in AWS before deploying</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-400">Deployment ID</p>
                  <p className="font-mono text-sm text-primary-400">{deploymentData?.deployment_id}</p>
                </div>
              </div>

              {/* Resources Summary */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-success-500/10 border border-success-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-success-400 text-sm font-medium">To Add</span>
                    <span className="text-2xl font-bold text-success-400">{planData.plan_summary?.add || 0}</span>
                  </div>
                </div>
                <div className="bg-warning-500/10 border border-warning-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-warning-400 text-sm font-medium">To Change</span>
                    <span className="text-2xl font-bold text-warning-400">{planData.plan_summary?.change || 0}</span>
                  </div>
                </div>
                <div className="bg-danger-500/10 border border-danger-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-danger-400 text-sm font-medium">To Destroy</span>
                    <span className="text-2xl font-bold text-danger-400">{planData.plan_summary?.destroy || 0}</span>
                  </div>
                </div>
              </div>

              {/* Plan Output */}
              <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center">
                  <Terminal className="w-4 h-4 mr-2" />
                  Terraform Plan Output
                </h3>
                <pre className="text-xs text-gray-300 overflow-x-auto max-h-96 overflow-y-auto">
                  {planData.plan_output || 'No plan output available'}
                </pre>
              </div>

              {/* Warning Notice */}
              <div className="mt-6 bg-warning-500/10 border border-warning-500/30 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-warning-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-warning-500 mb-1">Important: Review Before Deploying</h4>
                    <p className="text-sm text-gray-300">
                      Clicking "Deploy to AWS" will create <strong>{planData.plan_summary?.add || 0} resources</strong> in your AWS account.
                      This will incur costs. Please review the plan carefully before proceeding.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between mt-8">
                <button
                  onClick={() => setCurrentStep(STEPS.VALIDATED)}
                  className="btn-secondary"
                >
                  <ChevronUp className="w-4 h-4 mr-2" />
                  Back to Validation
                </button>

                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => {
                      setCurrentStep(STEPS.INPUT);
                      setPlanData(null);
                      setDeploymentData(null);
                    }}
                    className="btn-secondary"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Cancel
                  </button>

                  <button
                    onClick={handleApplyDeployment}
                    disabled={loading}
                    className="btn-primary px-8"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        <span>Deploying...</span>
                      </>
                    ) : (
                      <>
                        <Rocket className="w-4 h-4 mr-2" />
                        <span>Deploy to AWS</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 5: DEPLOYED */}
        {currentStep === STEPS.DEPLOYED && (
          <div className="space-y-6">
            {deploymentData && <DeploymentProgress deployment={deploymentData} />}

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
                      deploymentData.status === 'failed' ? 'text-danger-500' : 'text-warning-500'
                    }`}>{deploymentData.status?.toUpperCase()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Region</p>
                    <p className="text-gray-100">{deploymentData.region || 'us-east-1'}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex space-x-4">
              <button onClick={resetAll} className="btn btn-primary flex items-center space-x-2">
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
      </main>
      </>
      )}
    </div>
  );
}

export default App;