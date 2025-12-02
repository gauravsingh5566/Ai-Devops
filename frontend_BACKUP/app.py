"""
AI DevOps Assistant - Streamlit Frontend
Natural Language to AWS Infrastructure
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'deployment_history' not in st.session_state:
    st.session_state.deployment_history = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'terraform_code' not in st.session_state:
    st.session_state.terraform_code = None
if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None
if 'deployment_id' not in st.session_state:
    st.session_state.deployment_id = None


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

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Generate", "📊 Validate", "🚀 Deploy", "📚 Documentation"])

# Tab 1: Generate Infrastructure
with tab1:
    st.header("Step 1: Describe Your Infrastructure")
    
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
        height=100,
        placeholder="Example: Create a VPC with 2 subnets and a NAT gateway"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        generate_btn = st.button("🎨 Generate Infrastructure", type="primary", use_container_width=True)
    with col2:
        if st.session_state.terraform_code:
            st.success("✅ Code generated and ready")
    
    if generate_btn and user_request:
        with st.spinner("🧠 Analyzing your request..."):
            # Step 1: Parse intent
            intent_result = parse_intent(user_request)
            
            if intent_result:
                st.success("✅ Intent parsed successfully")
                
                # Show parsed intent
                with st.expander("🔍 Parsed Intent"):
                    st.json(intent_result)
                
                # Step 2: Generate code
                with st.spinner("⚡ Generating Terraform code..."):
                    code_result = generate_code(intent_result, use_rag)
                    
                    if code_result:
                        st.session_state.terraform_code = code_result["terraform_code"]
                        st.session_state.current_step = 2
                        st.success("✅ Terraform code generated!")
                        
                        # Display code
                        st.subheader("📝 Generated Terraform Code")
                        st.code(code_result["terraform_code"], language="hcl")
                        
                        # Show best practices used
                        if code_result.get("best_practices_applied"):
                            with st.expander("✨ AWS Best Practices Applied"):
                                for practice in code_result["best_practices_applied"]:
                                    st.markdown(f"- {practice}")
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download Terraform Code",
                            data=code_result["terraform_code"],
                            file_name="main.tf",
                            mime="text/plain"
                        )
                        
                        # Auto-validate if enabled
                        if auto_validate:
                            st.info("🔄 Auto-validating code...")
                            time.sleep(1)
                            st.rerun()

# Tab 2: Validate
with tab2:
    st.header("Step 2: Validate Infrastructure")
    
    if not st.session_state.terraform_code:
        st.warning("⚠️ Please generate Terraform code first (Step 1)")
    else:
        st.info("📝 Code is ready for validation")
        
        # Show code preview
        with st.expander("👀 View Terraform Code"):
            st.code(st.session_state.terraform_code, language="hcl")
        
        validate_btn = st.button("🔍 Validate Infrastructure", type="primary", use_container_width=True)
        
        if validate_btn or (auto_validate and st.session_state.current_step == 2):
            with st.spinner("⏳ Validating infrastructure..."):
                validation_result = validate_code(st.session_state.terraform_code, aws_region)
                
                if validation_result:
                    st.session_state.validation_result = validation_result
                    st.session_state.current_step = 3
                    
                    # Status badge
                    status = validation_result["status"]
                    if status == "passed":
                        st.success("✅ Validation Passed - Ready to Deploy!")
                    elif status == "warning":
                        st.warning("⚠️ Validation Passed with Warnings")
                    else:
                        st.error("❌ Validation Failed")
                    
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
                        st.subheader("💰 Cost Breakdown")
                        for cost in validation_result["cost_estimates"]:
                            with st.expander(f"{cost['resource_type']}.{cost['resource_name']} - ${cost['monthly_cost']}/month"):
                                st.json(cost["cost_breakdown"])
                                if cost.get("pricing_notes"):
                                    st.info(cost["pricing_notes"])
                    
                    # Security issues
                    if validation_result.get("security_issues"):
                        st.subheader("🔒 Security Issues")
                        for issue in validation_result["security_issues"]:
                            severity = issue["severity"]
                            
                            with st.expander(f"{'🔴' if severity == 'critical' else '🟡' if severity == 'high' else '🔵'} {issue['resource']}", expanded=(severity == "critical")):
                                st.markdown(f"**Severity:** {severity.upper()}")
                                st.markdown(f"**Issue:** {issue['issue']}")
                                st.markdown(f"**Recommendation:** {issue['recommendation']}")
                                st.markdown(f"**Rule:** {issue['rule_id']}")
                    
                    # Quota warnings
                    if validation_result.get("quota_warnings"):
                        st.subheader("📊 Quota Warnings")
                        for warning in validation_result["quota_warnings"]:
                            st.warning(f"⚠️ {warning['service']} - {warning['resource_type']}: "
                                     f"Requesting {warning['requested']} (Limit: {warning['limit']})")
                    
                    # Recommendations
                    if validation_result.get("recommendations"):
                        st.subheader("💡 Recommendations")
                        for rec in validation_result["recommendations"]:
                            st.info(f"ℹ️ {rec}")
                    
                    # Deployment readiness
                    if validation_result["deployment_ready"]:
                        st.success("✅ Infrastructure is ready for deployment!")
                    else:
                        st.error("❌ Please fix critical issues before deploying")

# Tab 3: Deploy
with tab3:
    st.header("Step 3: Deploy to AWS")
    
    if not st.session_state.terraform_code:
        st.warning("⚠️ Please generate Terraform code first (Step 1)")
    elif not st.session_state.validation_result:
        st.warning("⚠️ Please validate infrastructure first (Step 2)")
    elif not st.session_state.validation_result.get("deployment_ready"):
        st.error("❌ Infrastructure has critical issues. Please fix them before deploying.")
    else:
        st.success("✅ Infrastructure validated and ready to deploy!")
        
        # Deployment name
        deployment_name = st.text_input(
            "Deployment Name",
            value=f"deployment-{int(time.time())}",
            placeholder="my-vpc-deployment"
        )
        
        # Confirmation
        st.warning("⚠️ **Warning:** This will create real AWS resources and may incur costs!")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            confirm = st.checkbox("I understand this will create AWS resources")
        
        with col2:
            deploy_btn = st.button("🚀 Deploy to AWS", type="primary", disabled=not confirm, use_container_width=True)
        
        with col3:
            if st.session_state.deployment_id:
                st.success("Deployment created")
        
        if deploy_btn and confirm:
            # Create deployment
            with st.spinner("📝 Creating deployment..."):
                deployment_result = create_deployment(
                    st.session_state.terraform_code,
                    deployment_name,
                    aws_region
                )
                
                if deployment_result:
                    st.session_state.deployment_id = deployment_result["deployment_id"]
                    st.success(f"✅ Deployment created: {deployment_result['deployment_id']}")
                    
                    # Execute deployment
                    success = deploy_infrastructure(deployment_result["deployment_id"])
                    
                    if success:
                        # Add to history
                        st.session_state.deployment_history.append({
                            "name": deployment_name,
                            "id": deployment_result["deployment_id"],
                            "status": "completed",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "region": aws_region
                        })
                        
                        st.balloons()
                        st.success("🎉 Deployment completed successfully!")
                        
                        # Show deployment details
                        with st.expander("📊 Deployment Details"):
                            st.json({
                                "deployment_id": deployment_result["deployment_id"],
                                "deployment_name": deployment_name,
                                "region": aws_region,
                                "status": "completed"
                            })
                    else:
                        st.session_state.deployment_history.append({
                            "name": deployment_name,
                            "id": deployment_result["deployment_id"],
                            "status": "failed",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "region": aws_region
                        })
        
        # View existing deployments
        st.markdown("---")
        st.subheader("📋 View Deployments")
        
        if st.button("🔄 Refresh Deployments"):
            try:
                response = requests.get(f"{INFRA_SERVICE_URL}/deployments", timeout=10)
                if response.status_code == 200:
                    deployments_data = response.json()
                    
                    if deployments_data["total"] > 0:
                        for deployment in deployments_data["deployments"]:
                            with st.expander(f"🔹 {deployment['deployment_name']} ({deployment['status']})"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.text(f"ID: {deployment['deployment_id']}")
                                    st.text(f"Status: {deployment['status']}")
                                    st.text(f"Progress: {deployment['progress_percentage']}%")
                                with col2:
                                    st.text(f"Created: {deployment['created_at']}")
                                    st.text(f"Updated: {deployment['updated_at']}")
                                
                                if deployment.get("resources_created"):
                                    st.markdown("**Resources:**")
                                    for resource in deployment["resources_created"]:
                                        st.text(f"  • {resource}")
                    else:
                        st.info("No deployments found")
            except Exception as e:
                st.error(f"Failed to fetch deployments: {str(e)}")

# Tab 4: Documentation
with tab4:
    st.header("📚 Documentation & Help")
    
    st.markdown(f"""
    ## 🎯 How to Use
    
    ### Step 1: Generate Infrastructure
    1. Describe your infrastructure needs in plain English
    2. Click "Generate Infrastructure"
    3. Review the generated Terraform code
    
    ### Step 2: Validate
    1. Click "Validate Infrastructure"
    2. Review cost estimates and security issues
    3. Address any critical issues if needed
    
    ### Step 3: Deploy
    1. Name your deployment
    2. Confirm you understand AWS charges
    3. Click "Deploy to AWS"
    4. Wait for deployment to complete
    
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
