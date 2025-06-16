from flask import render_template, request, jsonify, abort, redirect, url_for, flash, session
from app import app
from data_loader import data_loader
from display_ratings import display_ratings
from recipe_loader import recipe_loader
from user_auth import user_auth
from datetime import datetime
import json
import logging

# Context processor to make current_user available in templates
@app.context_processor
def inject_user():
    session_token = session.get('session_token')
    current_user = user_auth.get_user_from_session(session_token) if session_token else None
    return {'current_user': current_user}

@app.route('/')
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
    canonical_url = url_for('index', _external=True)
    
    # Check if this is a search/filter request - redirect to /agents
    if query or any(filters.values()):
        return redirect(url_for('agents') + '?' + request.query_string.decode())
    
    # Homepage - show featured agents and recipes only
    featured_agents = agents[:9]  # First 9 agents as featured
    
    return render_template('homepage.html', 
                         featured_agents=featured_agents,
                         top_recipes=top_recipes,
                         total_agents=len(data_loader.get_all_agents()),
                         canonical_url=canonical_url)

@app.route('/demo-request', methods=['POST'])
def demo_request():
    """Handle demo request form submissions"""
    import json
    from datetime import datetime
    
    try:
        # Get form data
        data = request.get_json()
        
        # Create demo request entry
        demo_entry = {
            'id': str(hash(str(datetime.now()) + data.get('email', ''))),
            'timestamp': datetime.now().isoformat(),
            'company_name': data.get('company_name', ''),
            'email': data.get('email', ''),
            'team_size': data.get('team_size', ''),
            'ai_usage': data.get('ai_usage', ''),
            'status': 'pending'
        }
        
        # Load existing demo requests or create new file
        try:
            with open('demo_requests.json', 'r') as f:
                demo_requests = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            demo_requests = []
        
        # Add new request
        demo_requests.append(demo_entry)
        
        # Save to file
        with open('demo_requests.json', 'w') as f:
            json.dump(demo_requests, f, indent=2)
        
        logging.info(f"Demo request saved: {demo_entry['email']} from {demo_entry['company_name']}")
        
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

@app.route('/dashboard')
def dashboard():
    """Administrative dashboard for team leaders and IT administrators"""
    all_agents = data_loader.get_all_agents()
    all_recipes = recipe_loader.get_all_recipes()
    
    # Core metrics
    total_agents = len(all_agents)
    active_teams = 5
    total_usage_this_month = 24567
    success_rate = 94
    
    # Trending agents (top performers)
    trending_agents = all_agents[:5]
    
    # Team performance data with proper structure
    team_performance = [
        {'name': 'Marketing', 'agents_used': 12, 'color': 'pink', 'icon': 'megaphone'},
        {'name': 'Engineering', 'agents_used': 18, 'color': 'blue', 'icon': 'code'},
        {'name': 'Product', 'agents_used': 8, 'color': 'purple', 'icon': 'package'},
        {'name': 'Support', 'agents_used': 14, 'color': 'orange', 'icon': 'headphones'},
        {'name': 'Growth', 'agents_used': 9, 'color': 'green', 'icon': 'trending-up'}
    ]
    
    # Recent activity feed
    recent_activities = [
        {
            'message': 'Marketing team deployed new content generation agent',
            'time': '2 hours ago',
            'color': 'blue',
            'icon': 'bot'
        },
        {
            'message': 'Sarah completed customer support automation recipe',
            'time': '4 hours ago',
            'color': 'green',
            'icon': 'check-circle'
        },
        {
            'message': 'Engineering team added code review assistant',
            'time': '6 hours ago',
            'color': 'purple',
            'icon': 'code'
        },
        {
            'message': 'New agent rated 5 stars by Product team',
            'time': '8 hours ago',
            'color': 'yellow',
            'icon': 'star'
        },
        {
            'message': 'Sales team requested demo of lead generation agent',
            'time': '1 day ago',
            'color': 'orange',
            'icon': 'users'
        }
    ]
    
    return render_template('dashboard.html',
                         total_agents=total_agents,
                         active_teams=active_teams,
                         total_usage_this_month=total_usage_this_month,
                         success_rate=success_rate,
                         trending_agents=trending_agents,
                         team_performance=team_performance,
                         recent_activities=recent_activities)

@app.route('/recipes-hub')
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

@app.route('/agents')
def agents():
    """Full agents listing page with search and filters"""
    # Get filter parameters from URL
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
    
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}
    
    # Get filtered agents
    agents = data_loader.search_agents(query, filters)
    
    # Get filter options for the UI
    filter_options = data_loader.get_filter_options()
    
    # Generate canonical URL
    canonical_url = url_for('agents', _external=True)
    
    return render_template('agents.html', 
                         agents=agents,
                         filter_options=filter_options,
                         current_query=query,
                         current_filters=filters,
                         total_agents=len(data_loader.get_all_agents()),
                         last_updated=data_loader.get_last_updated_time(),
                         canonical_url=canonical_url)

@app.route('/agents/<slug>')
def agent_detail(slug):
    """Individual agent detail page"""
    agent = data_loader.get_agent_by_slug(slug)
    
    if not agent:
        abort(404)
    
    # Get related agents (same primary domain or use case)
    all_agents = data_loader.get_all_agents()
    related_agents = [
        a for a in all_agents 
        if a.slug != slug and (
            a.primary_domain == agent.primary_domain or 
            a.primary_use_case == agent.primary_use_case
        )
    ][:6]  # Limit to 6 related agents
    
    # Get rating data for this agent
    rating_data = data_loader.rating_system.get_agent_ratings(agent.slug)
    
    # Generate unique SEO metadata
    page_title = f"{agent.name} by {agent.creator} - AI Agent | Top Agents"
    meta_description = f"{agent.short_desc} | {agent.pricing_clean} AI agent for {agent.primary_use_case}. Created by {agent.creator}."
    h1_title = f"{agent.name} - {agent.primary_use_case} AI Agent"
    
    return render_template('agent_detail.html', 
                         agent=agent,
                         related_agents=related_agents,
                         rating_data=rating_data,
                         json_ld=json.dumps(agent.get_json_ld(), indent=2),
                         rating_success=request.args.get('rating_success'),
                         rating_error=request.args.get('error'),
                         page_title=page_title,
                         meta_description=meta_description,
                         h1_title=h1_title)

@app.route('/agent/<slug>')
def agent_detail_redirect(slug):
    """Redirect old /agent/<slug> URLs to new /agents/<slug> format"""
    return redirect(url_for('agent_detail', slug=slug), code=301)

@app.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for search engines and LLM crawlers"""
    all_agents = data_loader.get_all_agents()
    
    # Build sitemap URLs
    urls = []
    
    # Add main pages
    urls.append({
        'loc': url_for('index', _external=True),
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'daily',
        'priority': '1.0'
    })
    
    urls.append({
        'loc': url_for('agents', _external=True),
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'daily',
        'priority': '0.9'
    })
    
    urls.append({
        'loc': url_for('recipes', _external=True),
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'weekly',
        'priority': '0.8'
    })
    
    # Add recipe detail pages
    from recipe_loader import recipe_loader
    recipes = recipe_loader.get_all_recipes()
    for recipe in recipes:
        urls.append({
            'loc': url_for('recipe_detail', slug=recipe.slug, _external=True),
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'monthly',
            'priority': '0.7'
        })
    
    # Add all agent detail pages
    for agent in all_agents:
        urls.append({
            'loc': url_for('agent_detail', slug=agent.slug, _external=True),
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.9'
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
    
    response = app.response_class(
        response=sitemap_xml,
        status=200,
        mimetype='application/xml'
    )
    return response

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt file for search engines"""
    with open('robots.txt', 'r') as f:
        content = f.read()
    
    response = app.response_class(
        response=content,
        status=200,
        mimetype='text/plain'
    )
    return response

@app.route('/.well-known/ai-plugin.json')
def ai_plugin_manifest():
    """Serve AI plugin manifest for LLM integration"""
    with open('.well-known/ai-plugin.json', 'r') as f:
        content = f.read()
    
    response = app.response_class(
        response=content,
        status=200,
        mimetype='application/json'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/agents/search')
def api_agents_search():
    """API endpoint for searching agents with natural language queries"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    pricing = request.args.get('pricing', '')
    limit = int(request.args.get('limit', 20))
    
    # Get all agents
    all_agents = data_loader.get_all_agents()
    
    # Apply filters
    filtered_agents = all_agents
    
    if query:
        # Use intelligent search for natural language queries
        from intelligent_search import IntelligentSearch
        searcher = IntelligentSearch()
        filtered_agents = searcher.search(filtered_agents, query)
    
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
            "detail_url": url_for('agent_detail', slug=agent.slug, _external=True)
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

@app.route('/api/agents/<slug>')
def api_agent_detail(slug):
    """API endpoint for getting detailed agent information"""
    try:
        agent = data_loader.get_agent_by_slug(slug)
        rating_data = data_loader.rating_system.get_agent_ratings(agent.slug)
        
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
            "detail_url": url_for('agent_detail', slug=agent.slug, _external=True),
            "api_url": url_for('api_agent_detail', slug=agent.slug, _external=True)
        }
        
        return jsonify(result)
        
    except ValueError:
        return jsonify({"error": "Agent not found"}), 404

@app.route('/api/categories')
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

@app.route('/api/recipes')
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

@app.route('/openapi.json')
def openapi_spec():
    """Serve OpenAPI specification for API documentation"""
    with open('openapi.json', 'r') as f:
        content = f.read()
    
    response = app.response_class(
        response=content,
        status=200,
        mimetype='application/json'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/api/agents')
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

@app.route('/api/search')
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

@app.route('/add-agent', methods=['POST'])
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
            return redirect(url_for('index', error='missing_fields'))
        
        # Add the agent
        success = data_loader.add_user_agent(agent_data)
        
        if success:
            return redirect(url_for('index', success='submitted'))
        else:
            return redirect(url_for('index', error='save_failed'))
            
    except Exception as e:
        logging.error(f"Error in add_agent route: {e}")
        return redirect(url_for('index', error='general'))

@app.route('/recipes')
def recipes():
    """Agent recipes listing page"""
    recipes = recipe_loader.get_all_recipes()
    return render_template('recipes.html', recipes=recipes)

@app.route('/api')
def api_docs():
    """API documentation page"""
    return render_template('api_docs.html')

@app.route('/enterprise-integration')
def enterprise_integration():
    """Enterprise integration architecture page"""
    return render_template('enterprise_integration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            return render_template('login_new.html', error="Please fill in all fields")
        
        result = user_auth.authenticate_user(email, password)
        
        if result['success']:
            # Create session
            session_token = user_auth.create_session(result['user']['id'])
            session['session_token'] = session_token
            session.permanent = True
            
            # Redirect to dashboard or intended page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            return render_template('login_new.html', error=result['error'])
    
    return render_template('login_new.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validation
        if not email or not password:
            return render_template('signup_new.html', error="Email and password are required")
        
        if len(password) < 8:
            return render_template('signup_new.html', error="Password must be at least 8 characters long")
        
        if password != confirm_password:
            return render_template('signup_new.html', error="Passwords do not match")
        
        if not request.form.get('agree_terms'):
            return render_template('signup_new.html', error="You must agree to the Terms of Service")
        
        # Create user
        result = user_auth.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        if result['success']:
            # Create session
            session_token = user_auth.create_session(result['user']['id'])
            session['session_token'] = session_token
            session.permanent = True
            
            return redirect(url_for('signup_success'))
        else:
            return render_template('signup_new.html', error=result['error'])
    
    return render_template('signup_new.html')

@app.route('/signup/success')
def signup_success():
    """Post-signup success page"""
    # Check if user is logged in (should be after signup)
    session_token = session.get('session_token')
    if not session_token:
        return redirect(url_for('signup'))
    
    user = user_auth.get_user_from_session(session_token)
    if not user:
        return redirect(url_for('signup'))
    
    return render_template('signup_success.html', user=user)

@app.route('/logout')
def logout():
    """User logout"""
    session_token = session.get('session_token')
    if session_token:
        user_auth.logout_session(session_token)
    
    session.clear()
    return redirect(url_for('index'))

@app.route('/auth/google', methods=['POST'])
def google_auth():
    """Handle Google OAuth authentication"""
    try:
        import jwt
        
        # Get the credential from the request
        data = request.get_json()
        credential = data.get('credential')
        action = data.get('action', 'signin')
        
        if not credential:
            return jsonify({'success': False, 'error': 'No credential provided'})
        
        # For demo purposes, we'll simulate the Google token verification
        # In production, you would verify the JWT token with Google's public keys
        try:
            # Decode without verification for demo (DO NOT use in production)
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
        
        # Authenticate or create user with Google
        result = user_auth.authenticate_google_user(
            google_id=google_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            profile_image=profile_image
        )
        
        if result['success']:
            # Create session
            session_token = user_auth.create_session(result['user']['id'])
            session['session_token'] = session_token
            session.permanent = True
            
            return jsonify({
                'success': True,
                'redirect': url_for('dashboard')
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logging.error(f"Google auth error: {e}")
        return jsonify({'success': False, 'error': 'Authentication failed'})

@app.route('/auth/google-demo', methods=['POST'])
def google_auth_demo():
    """Demo Google OAuth authentication without requiring actual Google credentials"""
    try:
        data = request.get_json()
        google_id = data.get('google_id')
        email = data.get('email')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        profile_image = data.get('profile_image', '')
        action = data.get('action', 'signin')
        
        if not google_id or not email:
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        # Authenticate or create user with Google
        result = user_auth.authenticate_google_user(
            google_id=google_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            profile_image=profile_image
        )
        
        if result['success']:
            # Create session
            session_token = user_auth.create_session(result['user']['id'])
            session['session_token'] = session_token
            session.permanent = True
            
            # Check if this was a new user creation (signup) or existing user (signin)
            is_new_user = result.get('is_new_user', False)
            redirect_url = url_for('signup_success') if (action == 'signup' or is_new_user) else url_for('dashboard')
            
            return jsonify({
                'success': True,
                'redirect': redirect_url
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logging.error(f"Demo Google auth error: {e}")
        return jsonify({'success': False, 'error': 'Authentication failed'})

@app.route('/rate-agent', methods=['POST'])
def rate_agent():
    """Handle agent rating submission"""
    try:
        # Get form data
        agent_slug = request.form.get('agent_slug', '').strip()
        rating = request.form.get('rating', type=int)
        feedback = request.form.get('feedback', '').strip()
        
        # Validate data
        if not agent_slug or not rating or not (1 <= rating <= 5):
            return redirect(url_for('agent_detail', slug=agent_slug, error='invalid_rating'))
        
        # Check if agent exists
        try:
            agent = data_loader.get_agent_by_slug(agent_slug)
        except ValueError:
            return redirect(url_for('index', error='agent_not_found'))
        
        # Add rating
        success = data_loader.rating_system.add_rating(
            agent_slug=agent_slug,
            rating=rating,
            feedback=feedback,
            user_identifier=request.remote_addr or 'anonymous'  # Use IP as simple user identifier
        )
        
        if success:
            return redirect(url_for('agent_detail', slug=agent_slug, rating_success='1'))
        else:
            return redirect(url_for('agent_detail', slug=agent_slug, error='rating_failed'))
            
    except Exception as e:
        logging.error(f"Error in rate_agent route: {e}")
        return redirect(url_for('index', error='general'))

@app.route('/recipes/<slug>')
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
    
    return render_template('recipe_detail.html',
                         recipe=recipe,
                         related_recipes=related_recipes,
                         json_ld=json.dumps(recipe.get_json_ld(), indent=2),
                         page_title=page_title,
                         meta_description=meta_description,
                         canonical_url=url_for('recipe_detail', slug=slug, _external=True))

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logging.error(f"Internal server error: {error}")
    return render_template('500.html'), 500
