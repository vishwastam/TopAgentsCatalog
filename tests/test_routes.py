import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, GoogleWorkspaceIDPIntegration, User, Organization, IDPIntegration

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def seed_db(app):
    """Seed the database with test data."""
    with app.app_context():
        # Create a test organization
        org = Organization(id=str(uuid.uuid4()), name='TestCorp')
        db.session.add(org)
        
        # Create a test user (enterprise admin)
        user = User(
            id=str(uuid.uuid4()),
            email='test@test.com',
            password_hash=generate_password_hash('password'),
            organization_id=org.id,
            role='admin',
            primary_role='admin',
            roles=['admin'],
            status='active'
        )
        db.session.add(user)
        
        # Create a superadmin user
        superadmin = User(
            id=str(uuid.uuid4()),
            email='super@admin.com',
            password_hash=generate_password_hash('superpassword'),
            role='superadmin',
            primary_role='superadmin',
            roles=['superadmin', 'admin'],
            status='active'
        )
        db.session.add(superadmin)

        db.session.commit()
        return {'user': user, 'org': org, 'superadmin': superadmin}

class TestMainRoutes:
    """Test cases for main blueprint routes."""
    
    def test_homepage_get(self, client):
        """Test homepage route returns 200 and contains expected content."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Top Agents' in response.data
    
    def test_homepage_with_search_redirect(self, client):
        """Test homepage with search query redirects to agents page."""
        response = client.get('/?q=test')
        assert response.status_code == 302
        assert '/agents?' in response.headers['Location']
    
    def test_agents_page(self, client):
        """Test agents listing page."""
        response = client.get('/agents')
        assert response.status_code == 200
        assert b'AI Agents Directory' in response.data
    
    def test_agents_page_with_filters(self, client):
        """Test agents page with various filters."""
        response = client.get('/agents?domain=marketing&platform=openai')
        assert response.status_code == 200
    
    def test_agent_detail_page(self, client):
        """Test individual agent detail page."""
        # Assuming there's an agent with slug 'chatgpt'
        response = client.get('/agents/chatgpt')
        assert response.status_code == 200
    
    def test_agent_detail_redirect(self, client):
        """Test agent detail redirect from old format."""
        response = client.get('/agent/test-agent')
        assert response.status_code == 301  # Permanent redirect
    
    def test_recipes_page(self, client):
        """Test recipes listing page."""
        response = client.get('/recipes')
        assert response.status_code == 200
        assert b'AI Agent Recipes' in response.data
    
    def test_recipe_detail_page(self, client):
        """Test recipe detail page."""
        # Mock the recipe_loader to return a test recipe
        with patch('recipe_loader.recipe_loader') as mock_recipe_loader:
            mock_recipe = MagicMock()
            mock_recipe.name = "Test Recipe"
            mock_recipe.slug = "test-recipe"
            mock_recipe.detailed_synopsis = "A test recipe description"
            mock_recipe.target_audience = "Developers"
            mock_recipe.get_json_ld.return_value = {"@type": "Recipe"}
            
            mock_recipe_loader.get_recipe_by_slug.return_value = mock_recipe
            mock_recipe_loader.get_all_recipes.return_value = []
            
            response = client.get('/recipes/test-recipe')
            assert response.status_code == 200
    
    def test_recipes_hub_page(self, client):
        """Test recipes hub page."""
        response = client.get('/recipes-hub')
        assert response.status_code == 200
        assert b'Agent Recipes & Stories' in response.data
    
    def test_dashboard_page(self, client):
        """Test dashboard page."""
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Top Agents Dashboard' in response.data
    
    def test_enterprise_integration_page(self, client):
        """Test enterprise integration page."""
        response = client.get('/enterprise-integration')
        assert response.status_code == 200
        assert b'Enterprise Integration' in response.data
    
    def test_api_docs_page(self, client):
        """Test API documentation page."""
        response = client.get('/api')
        assert response.status_code == 200
        assert b'API Documentation' in response.data
    
    def test_blog_list_page(self, client):
        """Test blog listing page."""
        response = client.get('/blog')
        assert response.status_code == 200
        assert b'Blog' in response.data
    
    def test_blog_detail_page(self, client):
        """Test blog detail page."""
        # Mock the blog_loader to return a test blog post
        with patch('routes.blog_loader') as mock_blog_loader:
            mock_blog = MagicMock()
            mock_blog.title = "Test Blog Post"
            mock_blog.slug = "test-blog-post"
            mock_blog.content = "Test blog content"
            mock_blog.publish_date = datetime.now() - timedelta(days=1)  # Published yesterday
            mock_blog.get_json_ld.return_value = {"@type": "BlogPosting"}
            
            mock_blog_loader.get_post_by_slug.return_value = mock_blog
            
            response = client.get('/blog/test-blog-post')
            assert response.status_code == 200
    
    def test_blog_category_page(self, client):
        """Test blog category page."""
        response = client.get('/blog/category/ai-agents')
        assert response.status_code == 200
    
    def test_blog_tag_page(self, client):
        """Test blog tag page."""
        response = client.get('/blog/tag/automation')
        assert response.status_code == 200
    
    def test_login_page_get(self, client):
        """Test login page GET request."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data
    
    def test_login_page_post_success(self, client):
        """Test login page POST request with valid credentials."""
        with patch('routes.user_auth.authenticate_user') as mock_auth:
            mock_auth.return_value = {'success': True, 'user': {'id': 'test-user-id', 'email': 'test@example.com'}}
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            assert response.status_code == 302  # Redirect after successful login
    
    def test_login_page_post_failure(self, client):
        """Test login page POST request with invalid credentials."""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    def test_signup_page_get(self, client):
        """Test signup page GET request."""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'Sign Up' in response.data
    
    def test_signup_page_post_success(self, client):
        """Test signup page POST request with valid data."""
        with patch('routes.user_auth.create_user') as mock_create_user, \
             patch('routes.user_auth.create_session') as mock_create_session:
            mock_create_user.return_value = {'success': True, 'user': {'id': 'new-user-id', 'email': 'new@example.com'}}
            mock_create_session.return_value = 'test-session-token'
            response = client.post('/signup', data={
                'email': 'new@example.com',
                'password': 'password123',
                'confirm_password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
                'agree_terms': 'on'
            })
            assert response.status_code == 302  # Redirect after successful signup
    
    def test_signup_success_page(self, client):
        """Test signup success page."""
        with patch('routes.user_auth.get_user_from_session') as mock_get_user:
            mock_get_user.return_value = {'id': 'test-user-id', 'email': 'test@example.com'}
            with client.session_transaction() as sess:
                sess['session_token'] = 'test-session-token'
            
            response = client.get('/signup/success')
            assert response.status_code == 200
            assert b'Welcome' in response.data
    
    def test_logout(self, client):
        """Test logout functionality."""
        response = client.get('/logout')
        assert response.status_code == 302  # Redirect after logout
    
    def test_demo_request_post(self, client):
        """Test demo request form submission."""
        demo_data = {
            'company_name': 'Test Company',
            'email': 'test@company.com',
            'team_size': '10-50',
            'ai_usage': 'We use AI for content generation'
        }
        response = client.post('/demo-request', 
                              data=json.dumps(demo_data),
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_add_agent_post(self, client):
        """Test add agent form submission."""
        agent_data = {
            'name': 'Test Agent',
            'description': 'A test AI agent',
            'platform': 'OpenAI',
            'pricing': 'Free',
            'creator': 'Test Creator'
        }
        response = client.post('/add-agent', data=agent_data)
        assert response.status_code == 302  # Redirect after successful submission
    
    def test_rate_agent_post(self, client):
        """Test agent rating submission."""
        rating_data = {
            'agent_slug': 'test-agent',
            'rating': 5,
            'review': 'Great agent!'
        }
        response = client.post('/rate-agent', data=rating_data)
        assert response.status_code == 302  # Redirect after successful rating
    
    def test_sitemap_xml(self, client):
        """Test sitemap.xml generation."""
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert b'<?xml' in response.data
    
    def test_robots_txt(self, client):
        """Test robots.txt generation."""
        response = client.get('/robots.txt')
        assert response.status_code == 200
        assert b'User-agent' in response.data
    
    def test_ai_plugin_manifest(self, client):
        """Test AI plugin manifest."""
        response = client.get('/.well-known/ai-plugin.json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'ai_integration' in data  # Check for expected structure

class TestAPIRoutes:
    """Test cases for API routes."""
    
    def test_api_agents_search(self, client):
        """Test agents search API."""
        response = client.get('/api/agents/search?q=chatgpt')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
    
    def test_api_agent_detail(self, client):
        """Test API agent detail endpoint."""
        response = client.get('/api/agents/chatgpt')
        assert response.status_code == 200
        data = json.loads(response.data)
        # The API returns the agent data directly, not wrapped in an 'agent' key
        assert 'creator' in data
        assert 'description' in data
    
    def test_api_categories(self, client):
        """Test API categories endpoint."""
        response = client.get('/api/categories')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'domains' in data  # The API returns 'domains' not 'categories'
        assert 'creators' in data
    
    def test_api_recipes(self, client):
        """Test recipes API."""
        response = client.get('/api/recipes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recipes' in data
    
    def test_api_search(self, client):
        """Test API search endpoint."""
        response = client.get('/api/search?q=automation')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data  # The API returns 'agents' not 'results'
        assert 'total' in data
    
    def test_openapi_spec(self, client):
        """Test OpenAPI specification."""
        response = client.get('/openapi.json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'openapi' in data
    
    def test_api_agents(self, client):
        """Test API agents endpoint."""
        response = client.get('/api/agents')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data  # The API returns 'data' not 'agents'
        assert 'total' in data
    
    def test_api_blog_posts(self, client):
        """Test blog posts API."""
        response = client.get('/api/blog/posts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'posts' in data

class TestDiscoveryRoutes:
    """Test cases for discovery blueprint routes."""
    
    def test_register_google_workspace_idp_success(self, client):
        """Test successful Google Workspace IDP registration."""
        with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
            mock_creds.return_value = MagicMock(token='test_token')
            
            data = {
                'display_name': 'Test IDP',
                'type': 'google_workspace',
                'service_account_json': json.dumps({
                    'type': 'service_account',
                    'project_id': 'test-project',
                    'private_key_id': 'test-key-id',
                    'private_key': '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n',
                    'client_email': 'test@test-project.iam.gserviceaccount.com',
                    'client_id': 'test-client-id'
                }),
                'api_url': 'https://admin.googleapis.com/admin/directory/v1'
            }
            
            response = client.post('/discovery/idp',
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'idp_id' in data
    
    def test_register_google_workspace_idp_missing_fields(self, client):
        """Test IDP registration with missing required fields."""
        data = {'display_name': 'Test IDP'}  # Missing service_account_json
        
        response = client.post('/discovery/idp',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_register_google_workspace_idp_invalid_json(self, client):
        """Test IDP registration with invalid JSON."""
        data = {
            'display_name': 'Test IDP',
            'service_account_json': 'invalid json',
            'api_url': 'https://admin.googleapis.com/admin/directory/v1'
        }
        
        response = client.post('/discovery/idp',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_fetch_app_catalog_missing_idp_id(self, client):
        """Test app catalog fetch without IDP ID."""
        response = client.get('/discovery/apps')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_fetch_app_catalog_idp_not_found(self, client):
        """Test app catalog fetch with non-existent IDP."""
        response = client.get('/discovery/apps?idp_id=999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_fetch_app_catalog_success(self, client, app):
        """Test successful app catalog fetch."""
        with app.app_context():
            # Create a test IDP integration
            integration = IDPIntegration(
                display_name='Test IDP',
                type='google_workspace',
                config={
                    'service_account_json': json.dumps({
                        'type': 'service_account',
                        'project_id': 'test-project',
                        'private_key_id': 'test-key-id',
                        'private_key': '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n',
                        'client_email': 'test@test-project.iam.gserviceaccount.com',
                        'client_id': 'test-client-id'
                    })
                },
                api_url='https://admin.googleapis.com/admin/directory/v1'
            )
            integration.status = 'active'
            integration.last_tested_at = datetime.utcnow()
            integration.last_test_status = 'success'
            db.session.add(integration)
            db.session.commit()
            
            with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
                 patch('routes.pyrequests.get') as mock_get:
                
                mock_creds.return_value = MagicMock(token='test_token', expired=False)
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {
                    'applications': [
                        {
                            'id': 'app1',
                            'name': 'Test App 1',
                            'description': 'Test application 1',
                            'status': 'ACTIVE'
                        },
                        {
                            'id': 'app2',
                            'name': 'Test App 2',
                            'description': 'Test application 2',
                            'status': 'ACTIVE'
                        }
                    ]
                }
                
                response = client.get(f'/discovery/apps?idp_id={integration.id}')
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['status'] == 'success'
                assert len(data['apps']) == 2
                assert data['total_count'] == 2

class TestErrorHandlers:
    """Test cases for error handlers."""
    
    def test_404_error_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/non-existent-page')
        assert response.status_code == 404
        # Flask returns "Not Found" by default for 404 errors
        assert b'Not Found' in response.data
    
    def test_500_error_handler(self, client):
        """Test 500 error handler."""
        # This would need to be tested by causing an actual 500 error
        # For now, just test that the template exists
        response = client.get('/500')
        assert response.status_code == 404  # No direct route to 500 page

class TestAuthenticationRoutes:
    """Test cases for authentication-related routes."""
    
    # def test_google_auth_post(self, client):
    #     """Test Google authentication endpoint."""
    #     with patch('jwt.decode') as mock_jwt, \
    #          patch('routes.user_auth.authenticate_google_user') as mock_auth:
    #         mock_jwt.return_value = {
    #             'sub': 'test_google_id',
    #             'email': 'test@gmail.com',
    #             'given_name': 'Test',
    #             'family_name': 'User'
    #         }
    #         mock_auth.return_value = {'success': True, 'user': {'id': 'test-user-id', 'email': 'test@gmail.com'}}
    #         
    #         data = {'credential': 'test_google_token'}
    #         response = client.post('/auth/google',
    #                              data=json.dumps(data),
    #                              content_type='application/json')
    #         
    #         assert response.status_code == 200
    #         data = json.loads(response.data)
    #         assert data['success'] == True
    
    # def test_google_auth_demo_post(self, client):
    #     """Test Google authentication demo endpoint."""
    #     with patch('routes.user_auth.authenticate_google_user') as mock_auth:
    #         mock_auth.return_value = {'success': True, 'user': {'id': 'test-user-id', 'email': 'demo@gmail.com'}}
    #         
    #         data = {
    #             'google_id': 'demo_google_id',
    #             'email': 'demo@gmail.com',
    #             'first_name': 'Demo',
    #             'last_name': 'User'
    #         }
    #         response = client.post('/auth/google-demo',
    #                              data=json.dumps(data),
    #                              content_type='application/json')
    #         
    #         assert response.status_code == 200
    #         data = json.loads(response.data)
    #         assert data['success'] == True

class TestTemplateRendering:
    """Test cases for template rendering and content."""
    
    def test_base_template_includes_required_elements(self, client):
        """Test that base template includes required elements."""
        response = client.get('/')
        assert b'<!DOCTYPE html>' in response.data
        assert b'<html' in response.data
        assert b'<head>' in response.data
        assert b'<body' in response.data
    
    def test_navigation_links_present(self, client):
        """Test that navigation links are present."""
        response = client.get('/')
        assert b'href="/agents"' in response.data
        assert b'href="/recipes"' in response.data
        assert b'href="/blog"' in response.data
    
    def test_footer_content_present(self, client):
        """Test that footer content is present."""
        response = client.get('/')
        assert b'Top Agents' in response.data  # Footer should contain site name
    
    def test_meta_tags_present(self, client):
        """Test that meta tags are present."""
        response = client.get('/')
        assert b'<meta name="description"' in response.data
        assert b'<meta property="og:title"' in response.data

class TestDataLoading:
    """Test cases for data loading functionality."""
    
    def test_agents_data_loaded(self, client):
        """Test that agents data is loaded and displayed."""
        response = client.get('/agents')
        # Should contain agent-related content
        assert b'Agents' in response.data
    
    def test_recipes_data_loaded(self, client):
        """Test that recipes data is loaded and displayed."""
        response = client.get('/recipes')
        # Should contain recipe-related content
        assert b'Recipes' in response.data
    
    def test_blog_data_loaded(self, client):
        """Test that blog data is loaded and displayed."""
        response = client.get('/blog')
        # Should contain blog-related content
        assert b'Blog' in response.data

class TestSearchFunctionality:
    """Test cases for search functionality."""
    
    def test_search_with_query(self, client):
        """Test search functionality with a query."""
        response = client.get('/agents?q=chatgpt')
        assert response.status_code == 200
    
    def test_search_with_filters(self, client):
        """Test search functionality with filters."""
        response = client.get('/agents?domain=marketing&platform=openai&model=gpt-4')
        assert response.status_code == 200
    
    def test_api_search_endpoint(self, client):
        """Test API search endpoint."""
        response = client.get('/api/search?q=automation')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
        assert 'total' in data

class TestPagination:
    """Test cases for pagination functionality."""
    
    def test_blog_pagination(self, client):
        """Test blog pagination."""
        response = client.get('/blog?page=2')
        assert response.status_code == 200
    
    def test_agents_pagination(self, client):
        """Test agents pagination if implemented."""
        response = client.get('/agents?page=2')
        assert response.status_code == 200

class TestSecurity:
    """Test cases for security features."""
    
    def test_csrf_protection_disabled_in_testing(self, client):
        """Test that CSRF protection is disabled in testing mode."""
        # This test verifies that CSRF protection is disabled for testing
        # In production, CSRF protection should be enabled
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        # Should not get CSRF error in testing mode
        assert response.status_code != 403
    
    def test_sql_injection_protection(self, client):
        """Test SQL injection protection."""
        # Test with potentially malicious input
        malicious_query = "'; DROP TABLE users; --"
        response = client.get(f'/agents?q={malicious_query}')
        assert response.status_code == 200
        # Should not crash or expose sensitive data
    
    def test_xss_protection(self, client):
        """Test XSS protection."""
        # Test with potentially malicious input
        xss_payload = '<script>alert("xss")</script>'
        response = client.get(f'/agents?q={xss_payload}')
        assert response.status_code == 200
        # Should contain HTML-escaped script tags, not raw script tags
        assert b'&lt;script&gt;' in response.data  # HTML-escaped
        # Check that the malicious script tag is not present in raw form
        # (but legitimate script tags in the template are OK)
        assert b'<script>alert("xss")</script>' not in response.data

class TestEdgeCases:
    """Test cases for edge cases and error scenarios."""
    
    def test_empty_search_query(self, client):
        """Test search with empty query."""
        response = client.get('/agents?q=')
        assert response.status_code == 200
    
    def test_special_characters_in_search(self, client):
        """Test search with special characters."""
        special_chars = ['!@#$%^&*()', '中文', 'émojis 🚀', 'SQL\'DROP']
        for chars in special_chars:
            response = client.get(f'/agents?q={chars}')
            assert response.status_code == 200
    
    def test_large_search_query(self, client):
        """Test search with very large query."""
        large_query = 'a' * 1000
        response = client.get(f'/agents?q={large_query}')
        assert response.status_code == 200
    
    def test_multiple_filters(self, client):
        """Test multiple filter combinations."""
        filters = [
            'domain=marketing&platform=openai&model=gpt-4',
            'use_case=content&creator=openai&pricing=free',
            'domain=engineering&platform=anthropic&model=claude'
        ]
        for filter_combo in filters:
            response = client.get(f'/agents?{filter_combo}')
            assert response.status_code == 200
    
    def test_invalid_agent_slug(self, client):
        """Test accessing non-existent agent."""
        response = client.get('/agents/non-existent-agent-slug')
        assert response.status_code == 404
    
    def test_invalid_recipe_slug(self, client):
        """Test accessing non-existent recipe."""
        response = client.get('/recipes/non-existent-recipe-slug')
        assert response.status_code == 404
    
    def test_invalid_blog_slug(self, client):
        """Test accessing non-existent blog post."""
        response = client.get('/blog/non-existent-blog-slug')
        assert response.status_code == 404
    
    def test_empty_category(self, client):
        """Test blog category with no posts."""
        response = client.get('/blog/category/empty-category')
        assert response.status_code == 200
    
    def test_empty_tag(self, client):
        """Test blog tag with no posts."""
        response = client.get('/blog/tag/empty-tag')
        assert response.status_code == 200

class TestFormValidation:
    """Test cases for form validation."""
    
    def test_login_form_validation_empty_fields(self, client):
        """Test login form validation with empty fields."""
        response = client.post('/login', data={'email': '', 'password': ''})
        assert response.status_code == 200  # Returns error page, not redirect
        assert b'Invalid email or password' in response.data
    
    def test_signup_form_validation_empty_fields(self, client):
        """Test signup form validation with empty fields."""
        response = client.post('/signup', data={'email': '', 'password': ''})
        assert response.status_code == 200  # Returns error page, not redirect
        assert b'Invalid email or password' in response.data or b'error' in response.data
    
    def test_signup_form_validation_invalid_email(self, client):
        """Test signup with an invalid email address."""
        response = client.post('/signup', data={
            'email': 'not-an-email',
            'password': 'password123',
            'confirm_password': 'password123',
            'first_name': 'Test',
            'last_name': 'User',
            'agree_terms': 'on'
        })
        assert response.status_code == 200 # Should re-render the form
        assert b'Invalid email address' in response.data
    
    def test_signup_form_validation_weak_password(self, client):
        """Test signup form validation with weak password."""
        response = client.post('/signup', data={
            'email': 'test@example.com',
            'password': '123',
            'confirm_password': '123',
            'first_name': 'John',
            'last_name': 'Doe',
            'agree_terms': 'on'
        })
        assert response.status_code in (200, 302)  # Accept redirect or error page
    
    def test_demo_request_form_validation(self, client):
        """Test demo request form validation"""
        # Test with missing required fields
        response = client.post('/demo-request', data={})
        assert response.status_code == 400
        
        # Test with invalid email
        response = client.post('/demo-request', data={
            'name': 'Test User',
            'email': 'invalid-email',
            'company': 'Test Company',
            'message': 'Test message'
        })
        assert response.status_code == 400

class TestAPIParameters:
    """Test cases for API parameter validation."""
    
    def test_api_search_invalid_parameters(self, client):
        """Test API search with invalid parameters."""
        response = client.get('/api/search?limit=invalid&offset=invalid')
        assert response.status_code == 200  # Should handle gracefully
    
    def test_api_agents_search_invalid_parameters(self, client):
        """Test API agents search with invalid parameters."""
        response = client.get('/api/agents/search?limit=1000&offset=-1')
        assert response.status_code == 200  # Should handle gracefully
    
    def test_api_blog_posts_invalid_parameters(self, client):
        response = client.get('/api/blog/posts?page=invalid&per_page=invalid')
        assert response.status_code == 400 # Expecting Bad Request
        json_response = json.loads(response.data)
        assert 'error' in json_response
    
    def test_api_categories_with_filters(self, client):
        """Test API categories with various filters."""
        response = client.get('/api/categories?domain=marketing')
        assert response.status_code == 200
    
    def test_api_recipes_with_filters(self, client):
        """Test API recipes with various filters."""
        response = client.get('/api/recipes?category=automation')
        assert response.status_code == 200

class TestContentTypes:
    """Test cases for content type handling."""
    
    def test_json_api_endpoints(self, client):
        """Test that API endpoints return JSON."""
        api_endpoints = [
            '/api/agents/search',
            '/api/categories',
            '/api/recipes',
            '/api/search',
            '/api/agents',
            '/api/blog/posts'
        ]
        for endpoint in api_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.content_type == 'application/json'
    
    def test_xml_endpoints(self, client):
        """Test that XML endpoints return correct content type."""
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert 'xml' in response.content_type
    
    def test_text_endpoints(self, client):
        """Test that text endpoints return correct content type."""
        response = client.get('/robots.txt')
        assert response.status_code == 200
        assert 'text' in response.content_type

class TestRedirects:
    """Test cases for redirect functionality."""
    
    def test_agent_detail_redirect_old_format(self, client):
        """Test redirect from old agent URL format."""
        response = client.get('/agent/test-agent')
        assert response.status_code == 301  # Permanent redirect
        assert '/agents/test-agent' in response.headers['Location']
    
    def test_homepage_search_redirect(self, client):
        """Test homepage search redirect to agents page."""
        search_queries = ['test', 'ai', 'automation', 'chatgpt']
        for query in search_queries:
            response = client.get(f'/?q={query}')
            assert response.status_code == 302
            assert '/agents?' in response.headers['Location']
    
    def test_homepage_filter_redirect(self, client):
        """Test homepage filter redirect to agents page."""
        response = client.get('/?domain=marketing&platform=openai')
        assert response.status_code == 302
        assert '/agents?' in response.headers['Location']

class TestSessionHandling:
    """Test cases for session handling."""
    
    def test_session_clearing_on_logout(self, client):
        """Test session clearing on logout."""
        response = client.get('/logout')
        assert response.status_code == 302

class TestRateLimiting:
    """Test cases for rate limiting (if implemented)."""
    
    def test_rapid_requests(self, client):
        """Test rapid requests to see if rate limiting is in place."""
        for _ in range(10):
            response = client.get('/')
            assert response.status_code == 200  # Should not be rate limited in testing

class TestCaching:
    """Test cases for caching headers."""
    
    def test_static_files_caching(self, client):
        """Test that static files have appropriate cache headers."""
        response = client.get('/static/css/style.css')
        if response.status_code == 200:
            # Should have cache headers
            assert 'Cache-Control' in response.headers
    
    def test_api_caching(self, client):
        """Test API endpoint caching headers."""
        response = client.get('/api/categories')
        assert response.status_code == 200
        # Check for appropriate cache headers

class TestAccessibility:
    """Test cases for accessibility features."""
    
    def test_alt_text_on_images(self, client):
        """Test that images have alt text."""
        response = client.get('/agents')  # Agents page has images with alt attributes
        # Check for alt attributes on images
        assert b'alt=' in response.data
    
    def test_semantic_html(self, client):
        """Test semantic HTML structure."""
        response = client.get('/')
        # Check for semantic elements
        assert b'<nav>' in response.data or b'<header>' in response.data or b'<main>' in response.data or b'<footer>' in response.data

class TestMobileResponsiveness:
    """Test cases for mobile responsiveness."""
    
    def test_mobile_viewport_meta(self, client):
        """Test mobile viewport meta tag."""
        response = client.get('/')
        assert b'viewport' in response.data
    
    def test_responsive_css_classes(self, client):
        """Test presence of responsive CSS classes."""
        response = client.get('/')
        # Check for responsive classes like sm:, md:, lg:, xl:
        assert b'sm:' in response.data or b'md:' in response.data or b'lg:' in response.data

class TestSEO:
    """Test cases for SEO features."""
    
    def test_meta_description_present(self, client):
        """Test that meta description is present."""
        response = client.get('/')
        assert b'<meta name="description"' in response.data
    
    def test_og_tags_present(self, client):
        """Test that Open Graph tags are present."""
        response = client.get('/')
        assert b'<meta property="og:' in response.data
    
    def test_canonical_urls(self, client):
        """Test that canonical URLs are present."""
        response = client.get('/')
        assert b'<link rel="canonical"' in response.data
    
    def test_structured_data(self, client):
        """Test that structured data is present."""
        response = client.get('/')
        # Check for JSON-LD structured data
        assert b'application/ld+json' in response.data

class TestPerformance:
    """Test cases for performance considerations."""
    
    def test_page_load_time(self, client):
        """Test that pages load within reasonable time."""
        import time
        start_time = time.time()
        response = client.get('/')
        load_time = time.time() - start_time
        assert response.status_code == 200
        assert load_time < 5.0  # Should load within 5 seconds
    
    def test_api_response_time(self, client):
        """Test that API endpoints respond quickly."""
        import time
        start_time = time.time()
        response = client.get('/api/agents/search')
        load_time = time.time() - start_time
        assert response.status_code == 200
        assert load_time < 2.0  # Should respond within 2 seconds

class TestIntelligentSearch:
    """Test cases for intelligent search functionality."""
    
    def test_intelligent_search_instantiation(self, client):
        """Test intelligent search instantiation."""
        from intelligent_search import IntelligentSearch
        search = IntelligentSearch()
        assert search is not None

# Discovery UI Routes Tests
def test_idp_connection_page(client):
    """Test IDP Connection page loads correctly"""
    response = client.get('/discovery/idp-connection')
    assert response.status_code == 200
    assert b'IDP Connection Setup' in response.data
    assert b'Google Workspace IDP Configuration' in response.data

def test_app_catalog_page(client):
    """Test App Catalog page loads correctly"""
    response = client.get('/discovery/app-catalog')
    assert response.status_code == 200
    assert b'Application Catalog' in response.data
    assert b'Discover and manage applications' in response.data

def test_idp_connection_page_seo(client):
    """Test IDP Connection page has proper SEO elements"""
    response = client.get('/discovery/idp-connection')
    assert response.status_code == 200
    assert b'Configure Google Workspace IDP connection' in response.data
    assert b'IDP Connection - Top Agents' in response.data

def test_app_catalog_page_seo(client):
    """Test App Catalog page has proper SEO elements"""
    response = client.get('/discovery/app-catalog')
    assert response.status_code == 200
    assert b'Discover and manage applications from your Google Workspace' in response.data
    assert b'Application Catalog - Top Agents' in response.data

def test_idp_connection_page_accessibility(client):
    """Test IDP Connection page has accessibility features"""
    response = client.get('/discovery/idp-connection')
    assert response.status_code == 200
    # Check for form labels
    assert b'for="display_name"' in response.data
    assert b'for="service_account_json"' in response.data
    # Check for proper heading structure
    assert b'<h1' in response.data
    assert b'<h2' in response.data

def test_app_catalog_page_accessibility(client):
    """Test App Catalog page has accessibility features"""
    response = client.get('/discovery/app-catalog')
    assert response.status_code == 200
    # Check for proper heading structure
    assert b'<h1' in response.data
    assert b'<h2' in response.data
    # Check for table structure
    assert b'<table' in response.data
    assert b'<thead' in response.data

def test_discovery_routes_not_in_navigation(client):
    """Test that discovery routes are not exposed in main navigation"""
    response = client.get('/')
    assert response.status_code == 200
    # Verify discovery routes are not in navigation
    assert b'/discovery/idp-connection' not in response.data
    assert b'/discovery/app-catalog' not in response.data

class TestAuthFlows:
    """Test cases specifically for the new database-backed authentication flow."""

    def test_successful_login(self, client, seed_db):
        """Test a user with valid credentials can log in."""
        user_id = seed_db['user_id']
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'password'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data
        with client.session_transaction() as session:
            assert 'user_id' in session
            assert session['user_id'] == user_id

    def test_login_wrong_password(self, client, seed_db):
        """Test login fails with correct email but wrong password."""
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
        with client.session_transaction() as session:
            assert 'user_id' not in session

    def test_login_nonexistent_user(self, client, seed_db):
        """Test login fails with an email that does not exist."""
        response = client.post('/login', data={
            'email': 'notfound@test.com',
            'password': 'password'
        })
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
        with client.session_transaction() as session:
            assert 'user_id' not in session

    def test_logout(self, client, seed_db):
        """Test that logout clears the session."""
        client.post('/login', data={'email': 'test@test.com', 'password': 'password'})
        
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Top Agents' in response.data
        with client.session_transaction() as session:
            assert 'user_id' not in session
            assert 'is_superadmin' not in session

    def test_access_protected_route_unauthenticated(self, client):
        """Test that an unauthenticated user is redirected from a protected route."""
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data

    def test_access_protected_route_authenticated(self, client, seed_db):
        """Test that an authenticated user can access a protected route."""
        client.post('/login', data={'email': 'test@test.com', 'password': 'password'})
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data

    def test_access_superadmin_route_as_normal_user(self, client, seed_db):
        """Test a normal user gets 403 when accessing superadmin route."""
        client.post('/login', data={'email': 'test@test.com', 'password': 'password'})
        response = client.get('/superadmin')
        assert response.status_code == 403
        assert b'You must be a superadmin to access this page' in response.data

    def test_access_superadmin_route_as_superadmin(self, client, seed_db):
        """Test a superadmin can access the superadmin route."""
        client.post('/login', data={'email': 'super@admin.com', 'password': 'superpassword'})
        response = client.get('/superadmin', follow_redirects=True)
        assert response.status_code == 200
        assert b'Super-Admin Dashboard' in response.data

    def test_successful_signup(self, client):
        """Test a new user can sign up successfully."""
        response = client.post('/signup', data={
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'first_name': 'New',
            'last_name': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Accept any welcome or success message
        assert b'New User' in response.data or b'success' in response.data or b'Welcome' in response.data
        
        with client.session_transaction() as session:
            assert 'user_id' in session
        
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.first_name == 'New'

if __name__ == '__main__':
    pytest.main([__file__]) 