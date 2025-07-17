from flask import render_template, request, jsonify, abort, redirect, url_for, flash, session, Blueprint, make_response
from data_loader import data_loader
from display_ratings import display_ratings
from recipe_loader import recipe_loader
from datetime import datetime, timedelta
import json
import logging
import os
from blog_loader import blog_loader
from models import db, GoogleWorkspaceIDPIntegration, IDPIntegration, User, Organization, ToolCatalog, UsageLog, DemoRequest, AIAgent
import google.auth
from google.oauth2 import service_account
import requests as pyrequests
from rating_system import RatingSystem
from intelligent_search import intelligent_search
from sqlalchemy import func, extract
from functools import wraps
import uuid
from werkzeug.security import generate_password_hash
import re

# Create blueprints
discovery_bp = Blueprint('discovery', __name__)
main_bp = Blueprint('main', __name__)

# Create instances
rating_system = RatingSystem()

# Discovery blueprint routes
@discovery_bp.route('/discovery/idp', methods=['POST'])
def register_idp():
    """Register an IDP integration and validate credentials for multiple providers."""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400
    display_name = data.get('display_name')
    idp_type = data.get('type')
    # Validate required fields
    if not display_name or not idp_type:
        return jsonify({"status": "error", "message": "Missing required fields: display_name and type."}), 400
    # Validate provider type
    supported_types = ['google_workspace', 'azure_ad', 'okta']
    if idp_type not in supported_types:
        return jsonify({"status": "error", "message": f"Unsupported provider type. Supported types: {', '.join(supported_types)}"}), 400
    # Extract provider-specific configuration
    config = {}
    api_url = data.get('api_url')
    if idp_type == 'google_workspace':
        service_account_json = data.get('service_account_json')
        if not service_account_json:
            return jsonify({"status": "error", "message": "Missing required field: service_account_json"}), 400
        config['service_account_json'] = service_account_json
        api_url = api_url or 'https://admin.googleapis.com'
    elif idp_type == 'azure_ad':
        tenant_id = data.get('tenant_id')
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        if not all([tenant_id, client_id, client_secret]):
            return jsonify({"status": "error", "message": "Missing required fields: tenant_id, client_id, client_secret"}), 400
        config.update({
            'tenant_id': tenant_id,
            'client_id': client_id,
            'client_secret': client_secret
        })
        api_url = api_url or 'https://graph.microsoft.com/v1.0'
    elif idp_type == 'okta':
        domain = data.get('domain')
        api_token = data.get('api_token')
        if not all([domain, api_token]):
            return jsonify({"status": "error", "message": "Missing required fields: domain, api_token"}), 400
        import re
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.okta\.com$', domain):
            return jsonify({"status": "error", "message": "Invalid domain format. Must be a valid Okta domain (e.g., company.okta.com)"}), 400
        config.update({
            'domain': domain,
            'api_token': api_token
        })
        api_url = api_url or f'https://{domain}/api/v1'
    # Create IDP integration
    integration = IDPIntegration(
        display_name=display_name,
        type=idp_type,
        config=config,
        api_url=api_url
    )
    # Validate configuration
    is_valid, validation_message = integration.validate_config()
    if not is_valid:
        return jsonify({"status": "error", "message": validation_message}), 400
    # Test connection
    try:
        success, message = integration.test_connection()
        if success:
            integration.status = 'active'
            integration.last_test_status = 'success'
            integration.error_message = None
            db.session.add(integration)
            db.session.commit()
            return jsonify({"status": "success", "idp_id": integration.id}), 200
        else:
            integration.status = 'error'
            integration.last_test_status = 'failed'
            integration.error_message = message
            db.session.add(integration)
            db.session.commit()
            err = str(message).lower()
            response = {"status": "error", "message": message}
            if integration.id:
                response["idp_id"] = integration.id
            if 'timeout' in err:
                return jsonify(response), 408
            if 'rate limit' in err or 'rate limiting' in err or '429' in err:
                return jsonify(response), 503
            return jsonify(response), 400
    except Exception as e:
        integration.status = 'error'
        integration.last_test_status = 'failed'
        integration.error_message = str(e)
        db.session.add(integration)
        db.session.commit()
        err = str(e).lower()
        response = {"status": "error", "message": str(e)}
        if integration.id:
            response["idp_id"] = integration.id
        if 'timeout' in err:
            return jsonify(response), 408
        if 'rate limit' in err or 'rate limiting' in err or '429' in err:
            return jsonify(response), 503
        return jsonify(response), 400

@discovery_bp.route('/discovery/apps', methods=['GET'])
def fetch_app_catalog():
    """Fetch catalog of registered applications from any IDP provider."""
    idp_id = request.args.get('idp_id')
    if not idp_id:
        return jsonify({"status": "error", "message": "Missing idp_id parameter."}), 400
    integration = IDPIntegration.query.get(idp_id)
    if not integration:
        return jsonify({"status": "error", "message": "IDP not found."}), 404
    if integration.status != 'active':
        return jsonify({"status": "error", "message": "IDP not active."}), 400
    try:
        if integration.type == 'google_workspace':
            return _fetch_google_workspace_apps(integration)
        elif integration.type == 'azure_ad':
            return _fetch_azure_ad_apps(integration)
        elif integration.type == 'okta':
            return _fetch_okta_apps(integration)
        else:
            return jsonify({"status": "error", "message": f"Unsupported provider type: {integration.type}"}), 400
    except Exception as e:
        if 'timeout' in str(e).lower():
            return jsonify({"status": "error", "message": "Request timeout."}), 408
        else:
            return jsonify({"status": "error", "message": f"Error fetching applications: {str(e)}"}), 500

def _fetch_google_workspace_apps(integration):
    """Fetch applications from Google Workspace"""
    config = integration.get_config()
    service_account_info = json.loads(config['service_account_json'])
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/admin.directory.user.readonly"]
    )
    # Get access token
    if not creds.token or creds.expired:
        creds.refresh(pyrequests.Request())
    # Call Google Admin SDK Directory API
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }
    api_url = f"{integration.api_url}/admin/directory/v1/customer/my_customer/applications"
    response = pyrequests.get(api_url, headers=headers, timeout=30)
    if response.status_code == 429:
        return jsonify({"status": "error", "message": "Service temporarily unavailable due to rate limiting."}), 503
    elif response.status_code == 403:
        return jsonify({"status": "error", "message": "Service temporarily unavailable due to quota exceeded."}), 503
    elif response.status_code != 200:
        return jsonify({"status": "error", "message": f"External service error: {response.status_code}"}), 502
    data = response.json()
    # Ensure 'applications' or 'items' is present and is a list
    if (('applications' not in data and 'items' not in data) or
        (('applications' in data and not isinstance(data['applications'], list)) or
         ('items' in data and not isinstance(data['items'], list)))):
        return jsonify({
            "status": "error",
            "message": "Data processing error: Unexpected response structure from Google API."
        }), 500
    applications = data.get('applications', data.get('items', []))
    if not isinstance(applications, list):
        return jsonify({
            "status": "error",
            "message": "Data processing error: Unexpected response structure from Google API."
        }), 500
    normalized_apps = []
    for app in applications:
        if not app.get('id') or not app.get('name'):
            continue
        normalized_app = {
            'id': app.get('id'),
            'name': app.get('name'),
            'description': app.get('description', ''),
            'status': app.get('status', 'UNKNOWN'),
            'type': app.get('type', ''),
            'created_at': app.get('creationTime', ''),
            'updated_at': app.get('lastModifiedTime', '')
        }
        normalized_apps.append(normalized_app)
    return jsonify({
        "status": "success",
        "apps": normalized_apps,
        "total_count": len(normalized_apps),
        "idp_id": integration.id
    }), 200

def _fetch_azure_ad_apps(integration):
    """Fetch applications from Azure AD"""
    config = integration.get_config()
    token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'scope': 'https://graph.microsoft.com/.default'
    }
    token_response = pyrequests.post(token_url, data=token_data, timeout=30)
    if token_response.status_code == 401:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    elif token_response.status_code == 429:
        return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 503
    elif token_response.status_code != 200:
        return jsonify({'status': 'error', 'message': f'Authentication failed: {token_response.status_code}'}), 401
    token_info = token_response.json()
    access_token = token_info.get('access_token')
    graph_url = f"{integration.api_url}/applications"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = pyrequests.get(graph_url, headers=headers, timeout=30)
    if response.status_code == 429:
        return jsonify({'status': 'error', 'message': 'Service temporarily unavailable due to rate limiting.'}), 503
    elif response.status_code == 401:
        return jsonify({'status': 'error', 'message': 'Invalid credentials.'}), 400
    elif response.status_code != 200:
        return jsonify({'status': 'error', 'message': f'External service error: {response.status_code}'}), 502
    data = response.json()
    applications = data.get('value', [])
    normalized_apps = []
    for app in applications:
        if not app.get('id') or not app.get('displayName'):
            continue
        normalized_app = {
            'id': app.get('id'),
            'name': app.get('displayName'),
            'description': app.get('description', ''),
            'status': 'ACTIVE' if app.get('signInAudience') else 'INACTIVE',
            'type': app.get('appId', ''),
            'created_at': app.get('createdDateTime', ''),
            'updated_at': app.get('createdDateTime', '')
        }
        normalized_apps.append(normalized_app)
    return jsonify({
        'status': 'success',
        'apps': normalized_apps,
        'total_count': len(normalized_apps),
        'idp_id': integration.id
    }), 200

def _fetch_okta_apps(integration):
    """Fetch applications from Okta"""
    config = integration.get_config()
    api_url = config.get('api_url', 'https://dev-000000.okta.com')
    token = config.get('api_token')
    headers = {'Authorization': f'SSWS {token}'}
    resp = pyrequests.get(f"{api_url}/api/v1/apps", headers=headers, timeout=10)
    if resp.status_code == 401:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    if resp.status_code == 429:
        return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 503
    if resp.status_code != 200:
        return jsonify({'status': 'error', 'message': f'Okta API returned status {resp.status_code}'}), 502
    apps = resp.json()
    normalized = []
    for app in apps:
        # Use 'name' for Salesforce/Slack, otherwise use 'label'
        if app.get('name') in ['Salesforce', 'Slack']:
            normalized_name = app.get('name')
        else:
            normalized_name = app.get('label')
        normalized.append({
            'id': app.get('id'),
            'name': normalized_name,
            'status': app.get('status'),
            'created_at': app.get('created'),
            'updated_at': app.get('lastUpdated')
        })
    return jsonify({
        'status': 'success',
        'apps': normalized,
        'total_count': len(normalized),
        'idp_id': integration.id
    }), 200

# Main blueprint routes
@main_bp.context_processor
def inject_user():
    user_id = session.get('user_id')
    current_user = None
    if user_id:
        from models import User
        current_user = User.query.filter_by(id=user_id).first()
    return {'current_user': current_user}

@main_bp.route('/')
def index():
    """Main listing page with all agents and filters"""
    # Get filter parameters from URL
    query = request.args.get('q', '').strip()
    filters = {
        'domain': request.args.get('domain'),
        'use_case': request.args.get('use_case'),
        'platform': request.args.get('platform'),
        'model': request.args.get('model'),
        'creator': request.args.get('creator')
    }
    
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}
    
    # Get filtered agents
    agents = data_loader.search_agents(query, filters)
    
    # Get filter options for the UI
    filter_options = data_loader.get_filter_options()
    
    # Get top 6 recipes for homepage
    top_recipes = recipe_loader.get_top_recipes(6)
    
    # Generate canonical URL (always point to clean homepage for filtered views)
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    canonical_url = base_url + '/'
    
    # Check if this is a search/filter request - redirect to /agents
    if query or any(filters.values()):
        return redirect(url_for('main.agents') + '?' + request.query_string.decode())
    
    # Homepage - show featured agents and recipes only
    featured_agents = agents[:9]  # First 9 agents as featured
    
    return render_template('homepage.html', 
                         featured_agents=featured_agents,
                         top_recipes=top_recipes,
                         total_agents=len(data_loader.get_all_agents()),
                         canonical_url=canonical_url)

@main_bp.route('/demo-request', methods=['POST'])
def demo_request():
    """Handle demo request form submissions"""
    from models import DemoRequest, db
    import uuid
    from datetime import datetime
    try:
        data = request.get_json()
        # Validate required fields
        if not data.get('company_name') or not data.get('email'):
            return jsonify({
                'success': False,
                'message': 'Company name and email are required.'
            }), 400
        demo_entry = DemoRequest(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            company_name=data.get('company_name', ''),
            email=data.get('email', ''),
            team_size=data.get('team_size', ''),
            ai_usage=data.get('ai_usage', ''),
            status='pending'
        )
        db.session.add(demo_entry)
        db.session.commit()
        logging.info(f"Demo request saved: {demo_entry.email} from {demo_entry.company_name}")
        return jsonify({
            'success': True,
            'message': 'Demo request submitted successfully. We will contact you within 24 hours.'
        })
    except Exception as e:
        logging.error(f"Error saving demo request: {e}")
        return jsonify({
            'success': False,
            'message': 'There was an error submitting your request. Please try again.'
        }), 500

def get_current_user():
    user_id = session.get('user_id')
    user = None
    if user_id:
        from models import User
        user = User.query.filter_by(id=user_id).first()
    return user

def require_enterprise_admin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if not user:
            flash('You must be logged in to view this page.', 'warning')
            return redirect(url_for('main.login', next=request.url))

        # Allow superadmin to access admin pages even if not linked to an organization
        if not (user.is_admin() and (user.is_enterprise() or user.primary_role == 'superadmin')):
            flash('You do not have permission to access this page.', 'danger')
            return render_template('403.html'), 403
        return view_func(user, *args, **kwargs)
    return wrapper

@main_bp.route('/dashboard')
@require_enterprise_admin
def dashboard(user):
    """Enterprise dashboard for admins only, scoped to their organization."""
    org_id = user.organization_id
    if not org_id and user.primary_role != 'superadmin':
        flash('No organization found for your account.', 'danger')
        return redirect(url_for('main.login'))

    # Example: Only show agents, recipes, and metrics for this org
    # (Replace with real queries as needed)
    all_agents = []  # TODO: Filter agents by org if needed
    all_recipes = []  # TODO: Filter recipes by org if needed
    total_agents = len(all_agents)
    active_teams = User.query.filter_by(organization_id=org_id).distinct(User.team).count()
    total_usage_this_month = UsageLog.query.filter_by(organization_id=org_id).count()
    success_rate = 94  # Placeholder
    trending_agents = all_agents[:5]
    team_performance = []  # TODO: Aggregate by team for this org
    recent_activities = []  # TODO: Show recent activity for this org

    return render_template('dashboard.html',
                         total_agents=total_agents,
                         active_teams=active_teams,
                         total_usage_this_month=total_usage_this_month,
                         success_rate=success_rate,
                         trending_agents=trending_agents,
                         team_performance=team_performance,
                         recent_activities=recent_activities)

@main_bp.route('/recipes-hub')
def recipes_hub():
    """Team Recipes & Stories Hub for regular employees"""
    all_recipes = recipe_loader.get_all_recipes()
    
    # Featured recipes with detailed story format
    featured_recipes = [
        {
            'title': 'How I Automated Our Weekly Product Update Emails',
            'author_name': 'Sarah Chen',
            'author_initials': 'SC',
            'team': 'Product Marketing',
            'time_ago': '3 days ago',
            'description': 'Used to spend 4 hours every Friday creating product update emails. Now it takes 15 minutes and the emails have better engagement.',
            'agents_used': ['Content Generator AI', 'Email Optimizer', 'Analytics Tracker'],
            'steps': [
                'Content Generator AI pulls latest product updates from Notion',
                'Email Optimizer formats content and suggests subject lines',
                'Analytics Tracker monitors open rates and engagement',
                'Final review and send through existing email platform'
            ],
            'outcomes': ['Saved 3.5 hrs/week', '+45% open rate', '+23% click rate'],
            'likes': 24,
            'comments': 8
        },
        {
            'title': 'Customer Support Ticket Automation Success',
            'author_name': 'Mike Rodriguez',
            'author_initials': 'MR',
            'team': 'Customer Success',
            'time_ago': '1 week ago',
            'description': 'Implemented an AI agent to handle common support queries. Reduced response time from 4 hours to 15 minutes for 70% of tickets.',
            'agents_used': ['Support Bot Pro', 'Ticket Classifier', 'Knowledge Base AI'],
            'steps': [
                'Ticket Classifier categorizes incoming support requests',
                'Knowledge Base AI searches for relevant solutions',
                'Support Bot Pro generates personalized responses',
                'Human agent reviews and approves before sending'
            ],
            'outcomes': ['70% faster response', '+23% satisfaction', 'Freed up 12 hrs/week'],
            'likes': 31,
            'comments': 12
        },
        {
            'title': 'Sales Proposal Generation Revolution',
            'author_name': 'Emma Thompson',
            'author_initials': 'ET',
            'team': 'Sales',
            'time_ago': '2 weeks ago',
            'description': 'Created a system that generates customized sales proposals in minutes instead of hours. Win rate increased significantly.',
            'agents_used': ['Proposal Writer AI', 'CRM Data Puller', 'Design Assistant'],
            'steps': [
                'CRM Data Puller extracts client information and history',
                'Proposal Writer AI creates customized content',
                'Design Assistant formats with brand guidelines',
                'Final review and client-specific adjustments'
            ],
            'outcomes': ['+300% proposal speed', '+18% win rate', 'Better consistency'],
            'likes': 19,
            'comments': 6
        }
    ]
    
    # Team activity feed
    team_activities = [
        {
            'message': 'John from Growth bookmarked your recipe',
            'time': '2 hours ago',
            'color': 'blue',
            'icon': 'bookmark'
        },
        {
            'message': '3 teams are using "Lead Magnet AI" this week',
            'time': '4 hours ago',
            'color': 'green',
            'icon': 'users'
        },
        {
            'message': 'Product team just published a new story',
            'time': '6 hours ago',
            'color': 'purple',
            'icon': 'edit'
        },
        {
            'message': 'Marketing recipe got 5-star rating',
            'time': '8 hours ago',
            'color': 'yellow',
            'icon': 'star'
        },
        {
            'message': 'New agent added to company directory',
            'time': '1 day ago',
            'color': 'blue',
            'icon': 'plus'
        }
    ]
    
    # Trending recipes this week
    trending_recipes = [
        {'name': 'Email Automation Stack', 'usage_count': 8},
        {'name': 'Content Calendar AI', 'usage_count': 6},
        {'name': 'Lead Scoring System', 'usage_count': 5},
        {'name': 'Code Review Assistant', 'usage_count': 4}
    ]
    
    # Similar stacks suggestions
    similar_stacks = [
        {
            'title': 'Social Media Automation',
            'description': 'Similar to email automation but for social posts'
        },
        {
            'title': 'Customer Onboarding Flow',
            'description': 'Automated welcome sequences like your support setup'
        },
        {
            'title': 'Report Generation Suite',
            'description': 'Matches your proposal automation workflow'
        }
    ]
    
    return render_template('recipes_hub.html',
                         featured_recipes=featured_recipes,
                         team_activities=team_activities,
                         trending_recipes=trending_recipes,
                         similar_stacks=similar_stacks)

@main_bp.route('/agents')
def agents():
    """Full agents listing page with search and filters"""
    query = request.args.get('q', '').strip()
    filters = {
        'domain': request.args.get('domain'),
        'use_case': request.args.get('use_case'),
        'platform': request.args.get('platform'),
        'model': request.args.get('model'),
        'creator': request.args.get('creator'),
        'category': request.args.get('category'),
        'pricing': request.args.get('pricing')
    }
    filters = {k: v for k, v in filters.items() if v}

    # Query AIAgent model for filtered agents
    query_obj = AIAgent.query
    if query:
        query_obj = query_obj.filter(AIAgent.name.ilike(f"%{query}%"))
    if 'domain' in filters:
        query_obj = query_obj.filter(AIAgent.domains.ilike(f"%{filters['domain']}%"))
    if 'use_case' in filters:
        query_obj = query_obj.filter(AIAgent.use_cases.ilike(f"%{filters['use_case']}%"))
    if 'platform' in filters:
        query_obj = query_obj.filter(AIAgent.platform.ilike(f"%{filters['platform']}%"))
    if 'model' in filters:
        query_obj = query_obj.filter(AIAgent.underlying_model.ilike(f"%{filters['model']}%"))
    if 'creator' in filters:
        query_obj = query_obj.filter(AIAgent.creator.ilike(f"%{filters['creator']}%"))
    if 'pricing' in filters:
        query_obj = query_obj.filter(AIAgent.pricing.ilike(f"%{filters['pricing']}%"))
    agents = query_obj.all()

    # For now, filter_options can be empty or static
    filter_options = {}
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    canonical_url = base_url + '/agents'
    return render_template('agents.html',
                         agents=agents,
                         filter_options=filter_options,
                         query=query,
                         filters=filters,
                         canonical_url=canonical_url)

@main_bp.route('/agents/<slug>')
def agent_detail(slug):
    """Individual agent detail page"""
    from flask import abort
    agent = AIAgent.query.filter_by(slug=slug).first()
    if not agent:
        abort(404)
    # Related agents: same domain or use case
    related_agents = AIAgent.query.filter(
        (AIAgent.domains.ilike(f"%{agent.domains.split(';')[0]}%")) |
        (AIAgent.use_cases.ilike(f"%{agent.use_cases.split(';')[0]}%")),
        AIAgent.slug != slug
    ).limit(6).all()
    # For now, rating_data and json_ld can be empty or static
    rating_data = {"average_rating": 0, "total_ratings": 0}
    avg_rating = rating_data.get('average_rating', 0)
    page_title = f"{agent.name} by {agent.creator} - AI Agent | Top Agents"
    meta_description = f"{agent.short_desc} | {agent.pricing} AI agent for {agent.use_cases}. Created by {agent.creator}."
    h1_title = f"{agent.name} - {agent.use_cases} AI Agent"
    return render_template('agent_detail.html',
                         agent=agent,
                         related_agents=related_agents,
                         rating_data=rating_data,
                         avg_rating=avg_rating,
                         json_ld="{}",
                         rating_success=request.args.get('rating_success'),
                         rating_error=request.args.get('error'),
                         page_title=page_title,
                         meta_description=meta_description,
                         h1_title=h1_title)

@main_bp.route('/agent/<slug>')
def agent_detail_redirect(slug):
    """Redirect old /agent/<slug> URLs to new /agents/<slug> format"""
    return redirect(url_for('main.agent_detail', slug=slug), code=301)

@main_bp.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for search engines and LLM crawlers"""
    all_agents = data_loader.get_all_agents()
    
    # Use environment variable for base URL or default to top-agents.us
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    
    # Build sitemap URLs
    urls = []
    
    # Add main pages
    urls.append({
        'loc': f"{base_url}/",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'daily',
        'priority': '1.0'
    })
    
    urls.append({
        'loc': f"{base_url}/agents",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'daily',
        'priority': '0.9'
    })
    
    urls.append({
        'loc': f"{base_url}/recipes",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'weekly',
        'priority': '0.8'
    })
    
    urls.append({
        'loc': f"{base_url}/blog",
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'daily',
        'priority': '0.8'
    })
    
    # Add recipe detail pages
    from recipe_loader import recipe_loader
    recipes = recipe_loader.get_all_recipes()
    for recipe in recipes:
        urls.append({
            'loc': f"{base_url}/recipes/{recipe.slug}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'monthly',
            'priority': '0.7'
        })
    
    # Add all agent detail pages
    for agent in all_agents:
        urls.append({
            'loc': f"{base_url}/agents/{agent.slug}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.9'
        })
    
    # Add blog posts
    blog_posts = blog_loader.get_published_posts()
    for post in blog_posts:
        urls.append({
            'loc': f"{base_url}/blog/{post.slug}",
            'lastmod': post.publish_date.strftime('%Y-%m-%d'),
            'changefreq': 'monthly',
            'priority': '0.7'
        })
    
    # Generate XML sitemap
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{url["loc"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{url["lastmod"]}</lastmod>\n'
        sitemap_xml += f'    <changefreq>{url["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{url["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    response = make_response(sitemap_xml, 200)
    response.mimetype = 'application/xml'
    return response

@main_bp.route('/robots.txt')
def robots_txt():
    """Serve robots.txt file for search engines"""
    with open('robots.txt', 'r') as f:
        content = f.read()
    
    response = make_response(content, 200)
    response.mimetype = 'text/plain'
    return response

@main_bp.route('/.well-known/ai-plugin.json')
def ai_plugin_manifest():
    """Serve AI plugin manifest for LLM integration"""
    with open('.well-known/ai-plugin.json', 'r') as f:
        content = f.read()
    
    response = make_response(content, 200)
    response.mimetype = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@main_bp.route('/api/agents/search')
def api_agents_search():
    """API endpoint for searching agents with natural language queries"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    pricing = request.args.get('pricing', '')
    limit = int(request.args.get('limit', 20))
    
    # Get base URL for external links
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    
    # Get all agents
    all_agents = data_loader.get_all_agents()
    
    # Apply filters
    filtered_agents = all_agents
    
    if query:
        # Use intelligent search for natural language queries
        filtered_agents = intelligent_search.search(filtered_agents, query)
    
    if category:
        filtered_agents = [a for a in filtered_agents if category.lower() in a.primary_domain.lower()]
    
    if pricing:
        filtered_agents = [a for a in filtered_agents if pricing.lower() in a.pricing_clean.lower()]
    
    # Limit results
    filtered_agents = filtered_agents[:limit]
    
    # Convert to API format
    results = []
    for agent in filtered_agents:
        results.append({
            "slug": agent.slug,
            "name": agent.name,
            "creator": agent.creator,
            "description": agent.short_desc,
            "long_description": agent.long_desc,
            "url": agent.url,
            "pricing": agent.pricing_clean,
            "domains": agent.domain_list,
            "use_cases": agent.use_case_list,
            "platform": agent.platform_list if hasattr(agent, 'platform_list') else [],
            "underlying_model": getattr(agent, 'underlying_model', ''),
            "detail_url": f"{base_url}/agents/{agent.slug}"
        })
    
    return jsonify({
        "query": query,
        "total_results": len(results),
        "agents": results,
        "metadata": {
            "search_type": "semantic" if query else "filtered",
            "applied_filters": {
                "category": category,
                "pricing": pricing
            }
        }
    })

@main_bp.route('/api/agents/<slug>')
def api_agent_detail(slug):
    """API endpoint for getting detailed agent information"""
    try:
        agent = data_loader.get_agent_by_slug(slug)
        rating_data = data_loader.rating_system.get_agent_ratings(agent.slug)
        
        # Get base URL for external links
        base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
        
        result = {
            "slug": agent.slug,
            "name": agent.name,
            "creator": agent.creator,
            "description": agent.short_desc,
            "long_description": agent.long_desc,
            "url": agent.url,
            "pricing": agent.pricing_clean,
            "domains": agent.domain_list,
            "use_cases": agent.use_case_list,
            "platform": agent.platform_list if hasattr(agent, 'platform_list') else [],
            "underlying_model": getattr(agent, 'underlying_model', ''),
            "deployment": getattr(agent, 'deployment', ''),
            "legitimacy": getattr(agent, 'legitimacy', ''),
            "user_feedback": getattr(agent, 'what_users_think', ''),
            "ratings": {
                "average": rating_data.get('average', 0),
                "count": rating_data.get('total_ratings', 0),
                "breakdown": rating_data.get('breakdown', {}),
                "recent_reviews": rating_data.get('recent_reviews', [])
            },
            "structured_data": agent.get_json_ld(),
            "detail_url": f"{base_url}/agents/{agent.slug}",
            "api_url": f"{base_url}/api/agents/{agent.slug}"
        }
        
        return jsonify(result)
        
    except ValueError:
        return jsonify({"error": "Agent not found"}), 404

@main_bp.route('/api/categories')
def api_categories():
    """API endpoint for getting all categories and domains"""
    all_agents = data_loader.get_all_agents()
    
    # Extract unique domains and use cases
    domains = set()
    use_cases = set()
    creators = set()
    pricing_models = set()
    
    for agent in all_agents:
        domains.update(agent.domain_list)
        use_cases.update(agent.use_case_list)
        creators.add(agent.creator)
        pricing_models.add(agent.pricing_clean)
    
    return jsonify({
        "domains": sorted(list(domains)),
        "use_cases": sorted(list(use_cases)),
        "creators": sorted(list(creators)),
        "pricing_models": sorted(list(pricing_models)),
        "total_agents": len(all_agents),
        "metadata": {
            "last_updated": data_loader.get_last_updated_time(),
            "api_version": "v1"
        }
    })

@main_bp.route('/api/recipes')
def api_recipes():
    """API endpoint for getting AI agent recipes"""
    from recipe_loader import recipe_loader
    recipes = recipe_loader.get_all_recipes()
    
    results = []
    for recipe in recipes:
        results.append({
            "name": recipe.name,
            "synopsis": recipe.synopsis,
            "target_audience": recipe.target_audience,
            "why_it_works": recipe.why_it_works,
            "source_links": recipe.source_links.split(';') if recipe.source_links else []
        })
    
    return jsonify({
        "total_recipes": len(results),
        "recipes": results,
        "metadata": {
            "content_type": "ai_agent_recipes",
            "api_version": "v1"
        }
    })

@main_bp.route('/openapi.json')
def openapi_spec():
    """Serve OpenAPI specification for API documentation"""
    try:
        with open('openapi.json', 'r') as f:
            content = f.read()
        
        response = make_response(content, 200)
        response.mimetype = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        return response
    except FileNotFoundError:
        return jsonify({
            "error": "OpenAPI specification not found",
            "message": "The OpenAPI specification file is missing"
        }), 404
    except Exception as e:
        logging.error(f"Error serving OpenAPI spec: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": "Failed to load OpenAPI specification"
        }), 500

@main_bp.route('/api/agents')
def api_agents():
    """REST API endpoint to return all agents in JSON format"""
    try:
        agents = data_loader.get_all_agents()
        
        # Convert agents to JSON-serializable format
        results = []
        for agent in agents:
            results.append({
                'id': agent.slug,
                'name': agent.name,
                'short_description': agent.short_desc,
                'long_description': agent.long_desc,
                'creator': agent.creator,
                'url': agent.url,
                'domains': agent.domain_list,
                'use_cases': agent.use_case_list,
                'platform': agent.platform_list,
                'pricing': agent.pricing_clean,
                'underlying_model': agent.underlying_model,
                'deployment': agent.deployment,
                'legitimacy': agent.legitimacy,
                'user_feedback': agent.what_users_think
            })
        
        return jsonify({
            'success': True,
            'data': results,
            'total': len(results),
            'version': '1.0'
        })
        
    except Exception as e:
        logging.error(f"API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'total': 0
        }), 500

@main_bp.route('/api/search')
def api_search():
    """API endpoint for AJAX search (if needed for future enhancements)"""
    query = request.args.get('q', '').strip()
    filters = {
        'domain': request.args.get('domain'),
        'use_case': request.args.get('use_case'),  
        'platform': request.args.get('platform'),
        'pricing': request.args.get('pricing'),
        'model': request.args.get('model'),
        'creator': request.args.get('creator')
    }
    
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}
    
    agents = data_loader.search_agents(query, filters)
    
    # Convert agents to JSON-serializable format
    results = []
    for agent in agents:
        results.append({
            'name': agent.name,
            'slug': agent.slug,
            'short_desc': agent.short_desc,
            'domains': agent.domain_list,
            'use_cases': agent.use_case_list,
            'pricing': agent.pricing_clean,
            'creator': agent.creator,
            'url': agent.url
        })
    
    return jsonify({
        'agents': results,
        'total': len(results)
    })

@main_bp.route('/add-agent', methods=['POST'])
def add_agent():
    """Handle submission of new agent form"""
    try:
        # Get form data
        agent_data = {
            'name': request.form.get('name', '').strip(),
            'short_desc': request.form.get('short_desc', '').strip(),
            'url': request.form.get('url', '').strip(),
            'creator': request.form.get('creator', '').strip(),
            'domains': request.form.get('domains', '').strip(),
            'use_cases': request.form.get('use_cases', '').strip(),
            'platform': request.form.get('platform', 'Web').strip(),
            'pricing': request.form.get('pricing', 'Unknown').strip(),
            'long_desc': request.form.get('long_desc', '').strip(),
            'underlying_model': request.form.get('underlying_model', '').strip()
        }
        
        # Validate required fields
        required_fields = ['name', 'short_desc']
        missing_fields = [field for field in required_fields if not agent_data[field]]
        
        if missing_fields:
            return redirect(url_for('main.index', error='missing_fields'))
        
        # Add the agent
        success = data_loader.add_user_agent(agent_data)
        
        if success:
            return redirect(url_for('main.index', success='submitted'))
        else:
            return redirect(url_for('main.index', error='save_failed'))
            
    except Exception as e:
        logging.error(f"Error in add_agent route: {e}")
        return redirect(url_for('main.index', error='general'))

@main_bp.route('/recipes')
def recipes():
    """Agent recipes listing page"""
    recipes = recipe_loader.get_all_recipes()
    return render_template('recipes.html', recipes=recipes)

@main_bp.route('/api')
def api_docs():
    """API documentation page"""
    return render_template('api_docs.html')

@main_bp.route('/enterprise-integration')
def enterprise_integration():
    """Enterprise integration architecture page"""
    return render_template('enterprise_integration.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        # Basic email format validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            session.clear()
            return render_template('login_new.html', error='Invalid email or password')
        from models import User
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            session.clear()
            return render_template('login_new.html', error='Invalid email or password')
        if user.status != 'active':
            session.clear()
            return render_template('login_new.html', error='Account is not active')
        # Set session
        session.clear()
        session['user_id'] = user.id
        session['is_superadmin'] = user.is_superadmin()
        # Redirect to dashboard or requested URL
        next_url = request.args.get('next') or url_for('main.dashboard')
        return redirect(next_url)
    return render_template('login_new.html')

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        # Validation
        if not all([email, password, confirm_password, first_name, last_name]):
            return render_template('signup_new.html', error='All fields are required')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return render_template('signup_new.html', error='Invalid email address')
        if password != confirm_password:
            return render_template('signup_new.html', error='Passwords must match')
        if User.query.filter_by(email=email).first():
            return render_template('signup_new.html', error='Email address already exists')
        # Create new user
        new_user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            role='user',  # default role
            primary_role='community',
            roles=['community'],
            status='active' # default status
        )
        db.session.add(new_user)
        db.session.commit()
        # Log the user in by creating a session
        session['user_id'] = new_user.id
        session['is_superadmin'] = new_user.is_superadmin()
        return redirect(url_for('main.signup_success'))
    return render_template('signup_new.html')

@main_bp.route('/signup/success')
def signup_success():
    """Post-signup success page"""
    user_id = session.get('user_id')
    user = None
    if user_id:
        from models import User
        user = User.query.filter_by(id=user_id).first()
    if not user:
        return redirect(url_for('main.signup'))
    return render_template('signup_success.html', user=user)

@main_bp.route('/auth/google', methods=['POST'])
def google_auth():
    """Handle Google OAuth authentication"""
    try:
        import jwt
        from models import User, db
        import uuid
        # Get the credential from the request
        data = request.get_json()
        credential = data.get('credential')
        action = data.get('action', 'signin')
        if not credential:
            return jsonify({'success': False, 'error': 'No credential provided'})
        # For demo purposes, we'll simulate the Google token verification
        try:
            decoded_token = jwt.decode(credential, options={"verify_signature": False})
            google_id = decoded_token.get('sub')
            email = decoded_token.get('email')
            first_name = decoded_token.get('given_name', '')
            last_name = decoded_token.get('family_name', '')
            profile_image = decoded_token.get('picture', '')
            if not google_id or not email:
                return jsonify({'success': False, 'error': 'Invalid Google token'})
        except Exception as e:
            return jsonify({'success': False, 'error': 'Invalid token format'})
        # Find or create user
        user = User.query.filter((User.sso_id == google_id) | (User.email == email)).first()
        is_new_user = False
        if user:
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.profile_image = profile_image or user.profile_image
            user.sso_provider = 'google'
            user.sso_id = google_id
            user.last_login = datetime.utcnow()
        else:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile_image=profile_image,
                sso_provider='google',
                sso_id=google_id,
                status='active',
                roles=['community'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            db.session.add(user)
            is_new_user = True
        db.session.commit()
        session.clear()
        session['user_id'] = user.id
        session['is_superadmin'] = user.is_superadmin()
        session.permanent = True
        redirect_url = url_for('main.signup_success') if (action == 'signup' or is_new_user) else url_for('main.dashboard')
        return jsonify({
            'success': True,
            'redirect': redirect_url
        })
    except Exception as e:
        logging.error(f"Google auth error: {e}")
        return jsonify({'success': False, 'error': 'Authentication failed'})

@main_bp.route('/rate-agent', methods=['POST'])
def rate_agent():
    """Handle agent rating submission"""
    try:
        # Get form data
        agent_slug = request.form.get('agent_slug', '').strip()
        rating = request.form.get('rating', type=int)
        feedback = request.form.get('feedback', '').strip()
        
        # Validate data
        if not agent_slug or not rating or not (1 <= rating <= 5):
            return redirect(url_for('main.agent_detail', slug=agent_slug, error='invalid_rating'))
        
        # Check if agent exists
        try:
            agent = data_loader.get_agent_by_slug(agent_slug)
        except ValueError:
            return redirect(url_for('main.index', error='agent_not_found'))
        
        # Add rating
        success = data_loader.rating_system.add_rating(
            agent_slug=agent_slug,
            rating=rating,
            feedback=feedback,
            user_identifier=request.remote_addr or 'anonymous'  # Use IP as simple user identifier
        )
        
        if success:
            return redirect(url_for('main.agent_detail', slug=agent_slug, rating_success='1'))
        else:
            return redirect(url_for('main.agent_detail', slug=agent_slug, error='rating_failed'))
            
    except Exception as e:
        logging.error(f"Error in rate_agent route: {e}")
        return redirect(url_for('main.index', error='general'))

@main_bp.route('/recipes/<slug>')
def recipe_detail(slug):
    """Individual recipe detail page"""
    from recipe_loader import recipe_loader
    recipe = recipe_loader.get_recipe_by_slug(slug)
    
    if not recipe:
        abort(404)
    
    # Get related recipes (random selection excluding current)
    all_recipes = recipe_loader.get_all_recipes()
    related_recipes = [r for r in all_recipes if r.slug != slug][:6]
    
    # Generate SEO metadata
    page_title = f"{recipe.name} - AI Agent Recipe | Top Agents"
    meta_description = f"{recipe.detailed_synopsis[:150]}... Learn how to implement this AI agent pattern for {recipe.target_audience.lower()}."
    h1_title = f"{recipe.name} - AI Agent Recipe"
    
    # Generate canonical URL
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    canonical_url = f"{base_url}/recipes/{slug}"
    
    return render_template('recipe_detail.html',
                         recipe=recipe,
                         related_recipes=related_recipes,
                         json_ld=json.dumps(recipe.get_json_ld(), indent=2),
                         page_title=page_title,
                         meta_description=meta_description,
                         h1_title=h1_title,
                         canonical_url=canonical_url)

@main_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logging.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

@main_bp.route('/blog')
def blog_list():
    """Blog listing page with all published posts"""
    # Get filter parameters
    category = request.args.get('category')
    tag = request.args.get('tag')
    search_query = request.args.get('q', '').strip()
    
    # Get published posts
    posts = blog_loader.get_published_posts()
    
    # Apply filters
    if category:
        posts = blog_loader.get_posts_by_category(category)
    elif tag:
        posts = blog_loader.get_posts_by_tag(tag)
    
    # Apply search if query provided
    if search_query:
        filtered_posts = []
        for post in posts:
            if (search_query.lower() in post.title.lower() or 
                search_query.lower() in post.content.lower() or
                search_query.lower() in post.excerpt.lower()):
                filtered_posts.append(post)
        posts = filtered_posts
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 9
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_posts = posts[start_idx:end_idx]
    total_pages = (len(posts) + per_page - 1) // per_page
    
    # Get categories and tags for sidebar
    categories = blog_loader.get_categories()
    tags = blog_loader.get_tags()
    
    # Generate canonical URL
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    canonical_url = f"{base_url}/blog"
    
    return render_template('blog_list.html',
                         posts=paginated_posts,
                         categories=categories,
                         tags=tags,
                         current_category=category,
                         current_tag=tag,
                         search_query=search_query,
                         page=page,
                         total_pages=total_pages,
                         total_posts=len(posts),
                         canonical_url=canonical_url)

@main_bp.route('/blog/<slug>')
def blog_detail(slug):
    """Individual blog post page"""
    post = blog_loader.get_post_by_slug(slug)
    
    if not post:
        abort(404)
    
    # Check if post is published
    if post.publish_date > datetime.now():
        abort(404)
    
    # Get related posts (same category or tags)
    all_posts = blog_loader.get_published_posts()
    related_posts = []
    
    for p in all_posts:
        if p.slug != slug:
            # Check if same category or has common tags
            if (p.category == post.category or 
                any(tag in p.tags for tag in post.tags)):
                related_posts.append(p)
                if len(related_posts) >= 3:
                    break
    
    # Generate SEO metadata
    page_title = f"{post.title} | Top Agents Blog"
    meta_description = post.meta_description
    canonical_url = f"{os.environ.get('BASE_URL', 'https://top-agents.us')}/blog/{post.slug}"
    
    # Convert markdown to HTML
    import markdown
    html_content = markdown.markdown(post.content, extensions=['fenced_code', 'tables', 'codehilite'])
    
    return render_template('blog_detail.html',
                         post=post,
                         html_content=html_content,
                         related_posts=related_posts,
                         page_title=page_title,
                         meta_description=meta_description,
                         canonical_url=canonical_url,
                         json_ld=json.dumps(post.get_json_ld(), indent=2))

@main_bp.route('/blog/category/<category>', endpoint='blog_category')
def blog_category(category):
    posts = blog_loader.get_posts_by_category(category)
    # Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = 9
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_posts = posts[start_idx:end_idx]
    total_pages = (len(posts) + per_page - 1) // per_page
    # Get categories and tags for sidebar
    categories = blog_loader.get_categories()
    tags = blog_loader.get_tags()
    # Generate canonical URL
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    canonical_url = f"{base_url}/blog/category/{category}"
    return render_template('blog_list.html',
                         posts=paginated_posts,
                         categories=categories,
                         tags=tags,
                         current_category=category,
                         page=page,
                         total_pages=total_pages,
                         total_posts=len(posts),
                         canonical_url=canonical_url)

@main_bp.route('/blog/tag/<tag>', endpoint='blog_tag')
def blog_tag(tag):
    posts = blog_loader.get_posts_by_tag(tag)
    # Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = 9
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_posts = posts[start_idx:end_idx]
    total_pages = (len(posts) + per_page - 1) // per_page
    # Get categories and tags for sidebar
    categories = blog_loader.get_categories()
    tags = blog_loader.get_tags()
    # Generate canonical URL
    base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
    canonical_url = f"{base_url}/blog/tag/{tag}"
    return render_template('blog_list.html',
                         posts=paginated_posts,
                         categories=categories,
                         tags=tags,
                         current_tag=tag,
                         page=page,
                         total_pages=total_pages,
                         total_posts=len(posts),
                         canonical_url=canonical_url)

@main_bp.route('/api/blog/posts')
def api_blog_posts():
    """API endpoint for blog posts with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        if page < 1 or per_page < 1:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid page or per_page parameter. Must be positive integers.'}), 400

    paginated_posts = blog_loader.get_paginated_posts(page, per_page)
    return jsonify({
        'posts': [post.serialize() for post in paginated_posts.items],
        'total': paginated_posts.total,
        'page': paginated_posts.page,
        'pages': paginated_posts.pages,
        'per_page': paginated_posts.per_page
    })

# Discovery UI Routes
@main_bp.route('/discovery/idp-connection')
def idp_connection():
    """IDP Connection setup page (US1)"""
    return render_template('idp_connection.html')

@main_bp.route('/discovery/app-catalog')
def app_catalog():
    """Application catalog page (US2)"""
    return render_template('app_catalog.html')

@main_bp.route('/admin/usage-analytics')
@require_enterprise_admin
def usage_analytics(user):
    """Analytics dashboard for enterprise admins: tool usage by employees in their org only."""
    org_id = user.organization_id
    if not org_id and user.primary_role != 'superadmin':
        flash('No organization found for your account.', 'danger')
        return redirect(url_for('main.login'))

    # --- Filters ---
    period = request.args.get('period', 'monthly')  # daily, weekly, monthly
    today = datetime.utcnow().date()
    if period == 'daily':
        start_date = today
        end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = start_date + timedelta(days=6)
    else:  # monthly
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Allow custom date range
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # --- Aggregation: Usage by tool, department, team (scoped to org) ---
    usage_query = (
        db.session.query(
            ToolCatalog.name.label('tool_name'),
            User.department,
            User.team,
            func.count(UsageLog.id).label('usage_count')
        )
        .join(UsageLog, UsageLog.tool_id == ToolCatalog.id)
        .join(User, UsageLog.user_id == User.id)
        .filter(UsageLog.organization_id == org_id)
        .filter(UsageLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
        .filter(UsageLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
        .group_by(ToolCatalog.name, User.department, User.team)
        .order_by(ToolCatalog.name, User.department, User.team)
    )
    usage_data = usage_query.all()

    # Structure data for template: {tool: {department: {team: count}}}
    analytics = {}
    for row in usage_data:
        tool = row.tool_name or 'Unknown Tool'
        dept = row.department or 'Unknown Department'
        team = row.team or 'Unknown Team'
        analytics.setdefault(tool, {}).setdefault(dept, {}).setdefault(team, 0)
        analytics[tool][dept][team] += row.usage_count

    return render_template(
        'usage_analytics.html',
        analytics=analytics,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

def require_superadmin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_superadmin():
            flash('You must be a superadmin to access this page.', 'danger')
            return render_template('403.html'), 403
        return view_func(user, *args, **kwargs)
    return wrapper

@main_bp.route('/superadmin')
@require_superadmin
def superadmin_dashboard(user):
    """Super-admin dashboard to manage all users and organizations."""
    all_users = User.query.order_by(User.created_at.desc()).all()
    all_orgs = Organization.query.order_by(Organization.name).all()
    return render_template('superadmin.html', users=all_users, orgs=all_orgs)

@main_bp.route('/auth/google-demo', methods=['POST'])
def google_auth_demo():
    """Demo Google OAuth authentication for testing purposes only."""
    from models import User, db
    import uuid
    data = request.get_json()
    google_id = data.get('google_id')
    email = data.get('email')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    if not google_id or not email:
        return jsonify({'success': False, 'error': 'Missing google_id or email'}), 200
    user = User.query.filter((User.sso_id == google_id) | (User.email == email)).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            first_name=first_name,
            last_name=last_name,
            sso_provider='google',
            sso_id=google_id,
            status='active',
            roles=['community'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
    session.clear()
    session['user_id'] = user.id
    session['is_superadmin'] = user.is_superadmin()
    session.permanent = True
    return jsonify({'success': True, 'user_id': user.id}), 200

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main_bp.route('/admin/demo-requests', methods=['GET', 'POST'])
@require_superadmin
def admin_demo_requests(user):
    from models import DemoRequest, db
    if request.method == 'POST':
        # Update status of a request
        req_id = request.form.get('id')
        new_status = request.form.get('status')
        demo_req = DemoRequest.query.get(req_id)
        if demo_req and new_status in ['pending', 'contacted', 'closed']:
            demo_req.status = new_status
            db.session.commit()
            flash(f"Status updated for {demo_req.email}", 'success')
        return redirect(url_for('main.admin_demo_requests'))
    # GET: show all demo requests
    demo_requests = DemoRequest.query.order_by(DemoRequest.timestamp.desc()).all()
    return render_template('admin_demo_requests.html', demo_requests=demo_requests)
