"""
AI DevOps Assistant - Streamlit Frontend
Natural Language to AWS Infrastructure - Single Page Workflow
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Optional
import os

# Configuration
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")
MCP_SERVICE_URL = os.getenv("MCP_SERVICE_URL", "http://localhost:8003")
INFRA_SERVICE_URL = os.getenv("INFRA_SERVICE_URL", "http://localhost:8004")

# Page configuration
st.set_page_config(
    page_title="AI DevOps Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .step-container {
        border: 2px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: white;
    }
    .step-active {
        border-color: #1f77b4;
        background-color: #e3f2fd;
    }
    .step-complete {
        border-color: #28a745;
        background-color: #d4edda;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .process-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.3rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .approval-box {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'deployment_history' not in st.session_state:
    st.session_state.deployment_history = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0  # 0: input, 1: generated, 2: validated, 3: deployed
if 'terraform_code' not in st.session_state:
    st.session_state.terraform_code = None
if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None
if 'deployment_id' not in st.session_state:
    st.session_state.deployment_id = None
if 'intent_result' not in st.session_state:
    st.session_state.intent_result = None
if 'rag_context' not in st.session_state:
    st.session_state.rag_context = []
if 'deployment_result' not in st.session_state:
    st.session_state.deployment_result = None
if 'show_process' not in st.session_state:
    st.session_state.show_process = True


# Helper Functions
def check_service_health(service_name: str, url: str) -> Dict:
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "data": response.json()}
        else:
            return {"status": "unhealthy", "data": None}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}


def parse_intent(message: str) -> Optional[Dict]:
    """Call AI Service to parse user intent"""
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/parse-intent",
            json={"message": message},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error parsing intent: {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to connect to AI Service: {str(e)}")
        return None


def generate_code(intent: Dict, use_rag: bool = True) -> Optional[Dict]:
    """Call AI Service to generate Terraform code"""
    try:
        # Get RAG context if needed
        rag_context = []
        if use_rag and intent.get("needs_rag"):
            query = " ".join(intent.get("resources", []))
            rag_response = requests.post(
                f"{RAG_SERVICE_URL}/search",
                json={"query": query, "n_results": 5},
                timeout=10
            )
            if rag_response.status_code == 200:
                rag_data = rag_response.json()
                rag_context = rag_data.get("results", [])
        
        # Generate code
        response = requests.post(
            f"{AI_SERVICE_URL}/generate-code",
            json={
                "intent": intent,
                "rag_context": rag_context
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error generating code: {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to generate code: {str(e)}")
        return None


def validate_code(terraform_code: str, region: str = "us-east-1") -> Optional[Dict]:
    """Call MCP Service to validate Terraform code"""
    try:
        response = requests.post(
            f"{MCP_SERVICE_URL}/validate",
            json={
                "terraform_code": terraform_code,
                "region": region,
                "validation_level": "standard"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error validating code: {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to validate code: {str(e)}")
        return None


def create_deployment(terraform_code: str, deployment_name: str, region: str = "us-east-1") -> Optional[Dict]:
    """Call Infrastructure Service to create deployment"""
    try:
        response = requests.post(
            f"{INFRA_SERVICE_URL}/deployments",
            json={
                "terraform_code": terraform_code,
                "deployment_name": deployment_name,
                "region": region,
                "auto_approve": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating deployment: {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to create deployment: {str(e)}")
        return None


def deploy_infrastructure(deployment_id: str) -> bool:
    """Execute complete deployment workflow"""
    try:
        # Init
        st.info("⏳ Initializing Terraform...")
        response = requests.post(f"{INFRA_SERVICE_URL}/deployments/{deployment_id}/init", timeout=60)
        if response.status_code != 200:
            st.error(f"Init failed: {response.text}")
            return False
        st.success("✅ Terraform initialized")
        
        # Plan
        st.info("⏳ Generating execution plan...")
        response = requests.post(f"{INFRA_SERVICE_URL}/deployments/{deployment_id}/plan", timeout=60)
        if response.status_code != 200:
            st.error(f"Plan failed: {response.text}")
            return False
        plan_data = response.json()
        st.success(f"✅ Plan generated: {plan_data['resources_to_add']} to add, "
                  f"{plan_data['resources_to_change']} to change, "
                  f"{plan_data['resources_to_destroy']} to destroy")
        
        # Apply
        st.info("⏳ Applying infrastructure changes...")
        response = requests.post(
            f"{INFRA_SERVICE_URL}/deployments/{deployment_id}/apply?auto_approve=true",
            timeout=600
        )
        if response.status_code != 200:
            st.error(f"Apply failed: {response.text}")
            return False
        
        apply_data = response.json()
        st.success(f"✅ Infrastructure deployed successfully!")
        st.success(f"Resources created: {', '.join(apply_data.get('resources_created', []))}")
        
        return True
        
    except Exception as e:
        st.error(f"Deployment failed: {str(e)}")
        return False


# Header
st.markdown('<div class="main-header">🚀 AI DevOps Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Transform Natural Language into AWS Infrastructure</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Service health checks
    st.subheader("Service Status")
    
    services = {
        "AI Service": AI_SERVICE_URL,
        "RAG Service": RAG_SERVICE_URL,
        "MCP Service": MCP_SERVICE_URL,
        "Infrastructure": INFRA_SERVICE_URL
    }
    
    for service_name, service_url in services.items():
        health = check_service_health(service_name, service_url)
        if health["status"] == "healthy":
            st.success(f"✅ {service_name}")
        elif health["status"] == "unhealthy":
            st.warning(f"⚠️ {service_name}")
        else:
            st.error(f"❌ {service_name}")
    
    st.markdown("---")
    
    # Configuration
    st.subheader("Configuration")
    aws_region = st.selectbox(
        "AWS Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        index=0
    )
    
    use_rag = st.checkbox("Use AWS Best Practices", value=True)
    auto_validate = st.checkbox("Auto-validate code", value=True)
    
    st.markdown("---")
    
    # Deployment history
    st.subheader("📜 Recent Deployments")
    if st.session_state.deployment_history:
        for idx, deployment in enumerate(reversed(st.session_state.deployment_history[-5:])):
            with st.expander(f"🔹 {deployment['name'][:30]}..."):
                st.text(f"Status: {deployment['status']}")
                st.text(f"Time: {deployment['timestamp']}")
    else:
        st.info("No deployments yet")

# Main content - Single Page Workflow
st.markdown("---")

# Progress indicator
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.current_step >= 1:
        st.success("✅ 1. Generated")
    else:
        st.info("⏳ 1. Generate")
with col2:
    if st.session_state.current_step >= 2:
        st.success("✅ 2. Validated")
    elif st.session_state.current_step == 1:
        st.warning("⏳ 2. Validate")
    else:
        st.info("⭕ 2. Validate")
with col3:
    if st.session_state.current_step >= 3:
        st.success("✅ 3. Deployed")
    elif st.session_state.current_step == 2:
        st.warning("⏳ 3. Deploy")
    else:
        st.info("⭕ 3. Deploy")

st.markdown("---")

# Step 0: User Input
if st.session_state.current_step == 0:
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    st.markdown('<div class="step-header">🎯 Step 1: Describe Your Infrastructure</div>', unsafe_allow_html=True)
    
    # Example requests
    with st.expander("💡 Example Requests"):
        st.markdown("""
        - "Create a VPC with 2 public and 2 private subnets across 2 availability zones"
        - "Set up a production environment with load balancer, EC2 instances, and RDS database"
        - "Create an S3 bucket with versioning and encryption enabled"
        - "Deploy a NAT gateway in each availability zone"
        - "Set up a basic network infrastructure for a web application"
        """)
    
    # User input
    user_request = st.text_area(
        "What infrastructure do you need?",
        height=150,
        placeholder="Example: Create a VPC with 2 subnets and a NAT gateway"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        generate_btn = st.button("🚀 Start Process", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.current_step = 0
            st.session_state.terraform_code = None
            st.session_state.validation_result = None
            st.session_state.deployment_id = None
            st.session_state.intent_result = None
            st.session_state.rag_context = []
            st.session_state.deployment_result = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if generate_btn and user_request:
        # Run the complete generation process
        progress_container = st.container()
        
        with progress_container:
            st.markdown('<div class="process-box">', unsafe_allow_html=True)
            st.subheader("🔄 Processing Your Request")
            
            # Step 1.1: Parse intent
            status_placeholder = st.empty()
            status_placeholder.info("⏳ Step 1/3: Parsing your intent...")
            
            intent_result = parse_intent(user_request)
            
            if not intent_result:
                status_placeholder.error("❌ Failed to parse intent")
                st.markdown('</div>', unsafe_allow_html=True)
                st.stop()
            
            st.session_state.intent_result = intent_result
            status_placeholder.success("✅ Step 1/3: Intent parsed successfully")
            
            with st.expander("🔍 View Parsed Intent"):
                st.json(intent_result)
            
            # Step 1.2: Get RAG context
            if intent_result.get("needs_rag") and use_rag:
                status_placeholder.info("⏳ Step 2/3: Retrieving AWS best practices...")
                
                query = " ".join(intent_result.get("resources", []))
                rag_response = requests.post(
                    f"{RAG_SERVICE_URL}/search",
                    json={"query": query, "n_results": 5},
                    timeout=10
                )
                
                if rag_response.status_code == 200:
                    rag_data = rag_response.json()
                    st.session_state.rag_context = rag_data.get("results", [])
                    status_placeholder.success(f"✅ Step 2/3: Retrieved {len(st.session_state.rag_context)} best practices")
                    
                    with st.expander("📚 View Best Practices Applied"):
                        for idx, result in enumerate(st.session_state.rag_context, 1):
                            st.markdown(f"**{idx}. {result.get('metadata', {}).get('title', 'Best Practice')}**")
                            st.text(result.get('content', '')[:200] + "...")
                else:
                    status_placeholder.warning("⚠️ Step 2/3: Continuing without best practices")
            else:
                status_placeholder.info("ℹ️ Step 2/3: Skipping RAG (not needed)")
            
            # Step 1.3: Generate code
            status_placeholder.info("⏳ Step 3/3: Generating Terraform code...")
            
            code_result = generate_code(intent_result, use_rag)
            
            if not code_result:
                status_placeholder.error("❌ Failed to generate code")
                st.markdown('</div>', unsafe_allow_html=True)
                st.stop()
            
            st.session_state.terraform_code = code_result["terraform_code"]
            st.session_state.current_step = 1
            status_placeholder.success("✅ Step 3/3: Terraform code generated!")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            time.sleep(1)
            st.rerun()

# Step 1: Show Generated Code and Request Approval for Validation
elif st.session_state.current_step == 1:
    st.markdown('<div class="step-container step-complete">', unsafe_allow_html=True)
    st.markdown('<div class="step-header">✅ Step 1: Code Generated</div>', unsafe_allow_html=True)
    
    # Show intent
    with st.expander("🔍 View Parsed Intent"):
        st.json(st.session_state.intent_result)
    
    # Show best practices
    if st.session_state.rag_context:
        with st.expander(f"📚 View {len(st.session_state.rag_context)} Best Practices Applied"):
            for idx, result in enumerate(st.session_state.rag_context, 1):
                st.markdown(f"**{idx}. {result.get('metadata', {}).get('title', 'Best Practice')}**")
                st.text(result.get('content', '')[:200] + "...")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show generated code
    st.markdown('<div class="step-container step-active">', unsafe_allow_html=True)
    st.markdown('<div class="step-header">📝 Generated Terraform Code</div>', unsafe_allow_html=True)
    
    st.code(st.session_state.terraform_code, language="hcl")
    
    # Download button
    st.download_button(
        label="⬇️ Download Terraform Code",
        data=st.session_state.terraform_code,
        file_name="main.tf",
        mime="text/plain"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Approval box for validation
    st.markdown('<div class="approval-box">', unsafe_allow_html=True)
    st.markdown("### 🔍 Ready to Validate?")
    st.markdown("The next step will validate:")
    st.markdown("- 💰 **Cost estimation** for AWS resources")
    st.markdown("- 🔒 **Security analysis** for vulnerabilities")
    st.markdown("- 📊 **Quota checking** for AWS limits")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        validate_btn = st.button("✅ Proceed to Validation", type="primary", use_container_width=True)
    with col2:
        if st.button("🔙 Start Over", use_container_width=True):
            st.session_state.current_step = 0
            st.session_state.terraform_code = None
            st.session_state.validation_result = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if validate_btn:
        # Run validation
        progress_container = st.container()
        
        with progress_container:
            st.markdown('<div class="process-box">', unsafe_allow_html=True)
            st.subheader("🔄 Validating Infrastructure")
            
            status_placeholder = st.empty()
            status_placeholder.info("⏳ Running validation checks...")
            
            validation_result = validate_code(st.session_state.terraform_code, aws_region)
            
            if not validation_result:
                status_placeholder.error("❌ Validation failed")
                st.markdown('</div>', unsafe_allow_html=True)
                st.stop()
            
            st.session_state.validation_result = validation_result
            st.session_state.current_step = 2
            status_placeholder.success("✅ Validation completed!")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            time.sleep(1)
            st.rerun()

# Step 2: Show Validation Results and Request Approval for Deployment
elif st.session_state.current_step == 2:
    # Show previous steps collapsed
    st.markdown('<div class="step-container step-complete">', unsafe_allow_html=True)
    with st.expander("✅ Step 1: Generated Code"):
        st.code(st.session_state.terraform_code, language="hcl")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show validation results
    st.markdown('<div class="step-container step-active">', unsafe_allow_html=True)
    st.markdown('<div class="step-header">📊 Step 2: Validation Results</div>', unsafe_allow_html=True)
    
    validation_result = st.session_state.validation_result
    
    # Status badge
    status = validation_result["status"]
    if status == "passed":
        st.success("✅ Validation Passed - Infrastructure is Ready!")
    elif status == "warning":
        st.warning("⚠️ Validation Passed with Warnings")
    else:
        st.error("❌ Validation Failed - Please Review Issues")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value">${validation_result["total_monthly_cost"]}</div>'
            f'<div class="metric-label">Monthly Cost</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with col2:
        score = validation_result["security_score"]
        color = "#28a745" if score >= 80 else "#ffc107" if score >= 60 else "#dc3545"
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color: {color}">{score}/100</div>'
            f'<div class="metric-label">Security Score</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value">{validation_result["resources_count"]}</div>'
            f'<div class="metric-label">Resources</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with col4:
        issues_count = len(validation_result["security_issues"])
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value">{issues_count}</div>'
            f'<div class="metric-label">Issues Found</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Cost breakdown
    if validation_result.get("cost_estimates"):
        with st.expander("💰 Cost Breakdown Details"):
            for cost in validation_result["cost_estimates"]:
                st.markdown(f"**{cost['resource_type']}.{cost['resource_name']}** - ${cost['monthly_cost']}/month")
                if cost.get("cost_breakdown"):
                    st.json(cost["cost_breakdown"])
    
    # Security issues
    if validation_result.get("security_issues"):
        with st.expander("🔒 Security Issues Details"):
            for issue in validation_result["security_issues"]:
                severity = issue["severity"]
                st.markdown(f"**{'🔴' if severity == 'critical' else '🟡' if severity == 'high' else '🔵'} {issue['resource']}** - {severity.upper()}")
                st.markdown(f"- **Issue:** {issue['issue']}")
                st.markdown(f"- **Recommendation:** {issue['recommendation']}")
                st.markdown("---")
    
    # Quota warnings
    if validation_result.get("quota_warnings"):
        with st.expander("📊 Quota Warnings"):
            for warning in validation_result["quota_warnings"]:
                st.warning(f"⚠️ {warning['service']} - {warning['resource_type']}: "
                         f"Requesting {warning['requested']} (Limit: {warning['limit']})")
    
    # Recommendations
    if validation_result.get("recommendations"):
        with st.expander("💡 Recommendations"):
            for rec in validation_result["recommendations"]:
                st.info(f"ℹ️ {rec}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Approval box for deployment
    st.markdown('<div class="approval-box">', unsafe_allow_html=True)
    
    if validation_result["deployment_ready"]:
        st.markdown("### 🚀 Ready to Deploy?")
        st.markdown("The infrastructure will be deployed to AWS with the following:")
        st.markdown(f"- **Region:** {aws_region}")
        st.markdown(f"- **Resources:** {validation_result['resources_count']}")
        st.markdown(f"- **Estimated Cost:** ${validation_result['total_monthly_cost']}/month")
        st.markdown(f"- **Security Score:** {validation_result['security_score']}/100")
        
        st.warning("⚠️ **Warning:** This will create REAL AWS resources and may incur costs!")
        
        # Deployment name
        deployment_name = st.text_input(
            "Deployment Name",
            value=f"deployment-{int(time.time())}",
            placeholder="my-vpc-deployment"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            confirm = st.checkbox("I understand this will create AWS resources and may incur costs")
        with col2:
            deploy_btn = st.button("🚀 Deploy to AWS", type="primary", disabled=not confirm, use_container_width=True)
        with col3:
            if st.button("🔙 Regenerate", use_container_width=True):
                st.session_state.current_step = 0
                st.session_state.terraform_code = None
                st.session_state.validation_result = None
                st.rerun()
        
        if deploy_btn and confirm:
            # Run deployment
            progress_container = st.container()
            
            with progress_container:
                st.markdown('<div class="process-box">', unsafe_allow_html=True)
                st.subheader("🔄 Deploying Infrastructure")
                
                status_placeholder = st.empty()
                
                # Create deployment
                status_placeholder.info("⏳ Step 1/4: Creating deployment...")
                deployment_result = create_deployment(
                    st.session_state.terraform_code,
                    deployment_name,
                    aws_region
                )
                
                if not deployment_result:
                    status_placeholder.error("❌ Failed to create deployment")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.stop()
                
                st.session_state.deployment_id = deployment_result["deployment_id"]
                status_placeholder.success(f"✅ Step 1/4: Deployment created: {deployment_result['deployment_id']}")
                
                # Execute deployment
                success = deploy_infrastructure(deployment_result["deployment_id"])
                
                if success:
                    st.session_state.deployment_result = {
                        "deployment_id": deployment_result["deployment_id"],
                        "deployment_name": deployment_name,
                        "status": "completed",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "region": aws_region
                    }
                    
                    # Add to history
                    st.session_state.deployment_history.append(st.session_state.deployment_result)
                    
                    st.session_state.current_step = 3
                    status_placeholder.success("✅ Deployment completed successfully!")
                else:
                    st.session_state.deployment_result = {
                        "deployment_id": deployment_result["deployment_id"],
                        "deployment_name": deployment_name,
                        "status": "failed",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "region": aws_region
                    }
                    st.session_state.deployment_history.append(st.session_state.deployment_result)
                    status_placeholder.error("❌ Deployment failed")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                time.sleep(1)
                st.rerun()
    else:
        st.error("❌ Cannot Deploy - Critical Issues Found")
        st.markdown("Please fix the following issues before deploying:")
        for issue in validation_result["security_issues"]:
            if issue["severity"] in ["critical", "high"]:
                st.markdown(f"- **{issue['resource']}:** {issue['issue']}")
        
        if st.button("🔙 Start Over", use_container_width=True):
            st.session_state.current_step = 0
            st.session_state.terraform_code = None
            st.session_state.validation_result = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Step 3: Show Deployment Results
elif st.session_state.current_step == 3:
    # Show all previous steps collapsed
    st.markdown('<div class="step-container step-complete">', unsafe_allow_html=True)
    with st.expander("✅ Step 1: Generated Code"):
        st.code(st.session_state.terraform_code, language="hcl")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="step-container step-complete">', unsafe_allow_html=True)
    with st.expander("✅ Step 2: Validation Results"):
        validation_result = st.session_state.validation_result
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monthly Cost", f"${validation_result['total_monthly_cost']}")
        with col2:
            st.metric("Security Score", f"{validation_result['security_score']}/100")
        with col3:
            st.metric("Resources", validation_result['resources_count'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show deployment results
    st.markdown('<div class="step-container step-complete">', unsafe_allow_html=True)
    st.markdown('<div class="step-header">🎉 Step 3: Deployment Complete!</div>', unsafe_allow_html=True)
    
    if st.session_state.deployment_result["status"] == "completed":
        st.success("✅ Infrastructure successfully deployed to AWS!")
        st.balloons()
        
        deployment = st.session_state.deployment_result
        
        st.markdown("### 📊 Deployment Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Deployment ID:** {deployment['deployment_id']}")
            st.markdown(f"**Name:** {deployment['deployment_name']}")
            st.markdown(f"**Status:** {deployment['status'].upper()}")
        with col2:
            st.markdown(f"**Region:** {deployment['region']}")
            st.markdown(f"**Time:** {deployment['timestamp']}")
            st.markdown(f"**Resources:** {st.session_state.validation_result['resources_count']}")
        
        # Get deployment details
        try:
            response = requests.get(f"{INFRA_SERVICE_URL}/deployments/{deployment['deployment_id']}", timeout=10)
            if response.status_code == 200:
                deployment_details = response.json()
                
                if deployment_details.get("resources_created"):
                    st.markdown("### 📦 Resources Created")
                    for resource in deployment_details["resources_created"]:
                        st.markdown(f"- ✅ `{resource}`")
                
                if deployment_details.get("terraform_output"):
                    with st.expander("📋 Terraform Output"):
                        st.json(deployment_details["terraform_output"])
        except Exception as e:
            st.warning(f"Could not fetch deployment details: {str(e)}")
        
    else:
        st.error("❌ Deployment Failed")
        st.markdown("The deployment encountered errors. Please check the logs.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Deploy New Infrastructure", type="primary", use_container_width=True):
            st.session_state.current_step = 0
            st.session_state.terraform_code = None
            st.session_state.validation_result = None
            st.session_state.deployment_id = None
            st.session_state.intent_result = None
            st.session_state.rag_context = []
            st.session_state.deployment_result = None
            st.rerun()
    
    with col2:
        if st.button("📋 View All Deployments", use_container_width=True):
            try:
                response = requests.get(f"{INFRA_SERVICE_URL}/deployments", timeout=10)
                if response.status_code == 200:
                    deployments_data = response.json()
                    st.write(f"Total deployments: {deployments_data['total']}")
                    for dep in deployments_data["deployments"]:
                        with st.expander(f"🔹 {dep['deployment_name']} ({dep['status']})"):
                            st.json(dep)
            except Exception as e:
                st.error(f"Failed to fetch deployments: {str(e)}")

# Documentation section at bottom
st.markdown("---")
with st.expander("📚 Documentation & Help"):
    st.markdown(f"""
    ## 🎯 How to Use
    
    This is a single-page workflow that guides you through three steps:
    
    ### Step 1: Generate 🎯
    1. Describe your infrastructure needs in plain English
    2. Click "Start Process"
    3. Review the generated Terraform code
    4. Approve to continue to validation
    
    ### Step 2: Validate 📊
    1. Review cost estimates and security analysis
    2. Check for any issues or warnings
    3. Approve to continue to deployment
    
    ### Step 3: Deploy 🚀
    1. Enter deployment name
    2. Confirm you understand AWS charges
    3. Deploy to AWS
    4. View deployment results
    
    ---
    
    ## 💡 Example Requests
    
    **Basic VPC:**
    ```
    Create a VPC with CIDR 10.0.0.0/16
    ```
    
    **Complete Network:**
    ```
    Create a production VPC with 2 public and 2 private subnets
    across 2 availability zones with NAT gateways
    ```
    
    **Web Application:**
    ```
    Set up infrastructure for a web application with load balancer,
    EC2 instances, and RDS database
    ```
    
    ---
    
    ## 🔧 Service URLs
    
    - **AI Service:** `{AI_SERVICE_URL}`
    - **RAG Service:** `{RAG_SERVICE_URL}`
    - **MCP Service:** `{MCP_SERVICE_URL}`
    - **Infrastructure Service:** `{INFRA_SERVICE_URL}`
    
    ---
    
    ## 📞 Support
    
    For more information, check the service documentation:
    - [AI Service Docs]({AI_SERVICE_URL}/docs)
    - [RAG Service Docs]({RAG_SERVICE_URL}/docs)
    - [MCP Service Docs]({MCP_SERVICE_URL}/docs)
    - [Infrastructure Service Docs]({INFRA_SERVICE_URL}/docs)
    """)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666;">'
    '🚀 AI DevOps Assistant | Natural Language to AWS Infrastructure'
    '</div>',
    unsafe_allow_html=True
)
