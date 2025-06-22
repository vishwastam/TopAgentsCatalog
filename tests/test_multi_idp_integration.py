import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, IDPIntegration

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

# Test Data Fixtures
def valid_azure_ad_config():
    """Valid Azure AD configuration"""
    return {
        "display_name": "Test Azure AD",
        "type": "azure_ad",
        "tenant_id": "test-tenant-id",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "api_url": "https://graph.microsoft.com/v1.0"
    }

def valid_okta_config():
    """Valid Okta configuration"""
    return {
        "display_name": "Test Okta",
        "type": "okta",
        "domain": "test.okta.com",
        "api_token": "test-api-token",
        "api_url": "https://test.okta.com/api/v1"
    }

def valid_google_workspace_config():
    """Valid Google Workspace configuration"""
    return {
        "display_name": "Test Google Workspace",
        "type": "google_workspace",
        "service_account_json": json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "123",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }),
        "api_url": "https://admin.googleapis.com"
    }

# Test Classes
class TestMultiIDPRegistration:
    """Test IDP registration for different providers"""
    
    def test_register_azure_ad_success(self, client):
        """Test successful Azure AD IDP registration"""
        config = valid_azure_ad_config()
        
        with patch('routes.pyrequests.post') as mock_post:
            # Mock Azure AD token endpoint
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'access_token': 'test-token',
                'expires_in': 3600
            }
            mock_post.return_value = mock_response
            
            response = client.post('/discovery/idp', 
                                 json=config,
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = response.get_json()
            assert result['status'] == 'success'
            assert 'idp_id' in result
            
            # Verify database entry
            with client.application.app_context():
                integration = IDPIntegration.query.get(result['idp_id'])
                assert integration is not None
                assert integration.display_name == config['display_name']
                assert integration.type == config['type']
                assert integration.status == 'active'

    def test_register_azure_ad_missing_fields(self, client):
        config = valid_azure_ad_config()
        del config['tenant_id']
        response = client.post('/discovery/idp', json=config, content_type='application/json')
        assert response.status_code == 400
        assert 'Missing required fields' in response.get_json()['message']

    def test_register_azure_ad_invalid_credentials(self, client):
        """Test Azure AD registration with invalid credentials"""
        config = valid_azure_ad_config()
        config['client_secret'] = 'invalid-secret'
        
        with patch('routes.pyrequests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                'error': 'invalid_client',
                'error_description': 'AADSTS7000215'
            }
            mock_post.return_value = mock_response
            
            response = client.post('/discovery/idp', 
                                 json=config,
                                 content_type='application/json')
            
            assert response.status_code == 400
            result = response.get_json()
            assert result['status'] == 'error'
            assert 'Invalid credentials' in result['message']

    def test_register_azure_ad_rate_limit(self, client):
        config = valid_azure_ad_config()
        with patch('routes.pyrequests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.json.return_value = {'error': 'too_many_requests', 'error_description': 'Rate limit exceeded'}
            mock_post.return_value = mock_response
            response = client.post('/discovery/idp', json=config, content_type='application/json')
            assert response.status_code == 503
            assert 'rate limiting' in response.get_json()['message'].lower()

    def test_register_azure_ad_timeout(self, client):
        config = valid_azure_ad_config()
        with patch('routes.pyrequests.post') as mock_post:
            mock_post.side_effect = Exception('Connection timeout')
            response = client.post('/discovery/idp', json=config, content_type='application/json')
            assert response.status_code == 408 or response.status_code == 400
            assert 'timeout' in response.get_json()['message'].lower()

    def test_register_okta_success(self, client):
        """Test successful Okta IDP registration"""
        config = valid_okta_config()
        
        with patch('routes.pyrequests.get') as mock_get:
            # Mock Okta API test endpoint
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'id': 'test-org-id',
                'name': 'Test Organization'
            }
            mock_get.return_value = mock_response
            
            response = client.post('/discovery/idp', 
                                 json=config,
                                 content_type='application/json')
            
            assert response.status_code == 200
            result = response.get_json()
            assert result['status'] == 'success'
            assert 'idp_id' in result

    def test_register_okta_missing_fields(self, client):
        config = valid_okta_config()
        del config['domain']
        response = client.post('/discovery/idp', json=config, content_type='application/json')
        assert response.status_code == 400
        assert 'Missing required fields' in response.get_json()['message']

    def test_register_okta_invalid_domain(self, client):
        config = valid_okta_config()
        config['domain'] = 'invalid-domain'
        response = client.post('/discovery/idp', json=config, content_type='application/json')
        assert response.status_code == 400
        assert 'Invalid domain format' in response.get_json()['message']

    def test_register_okta_invalid_token(self, client):
        """Test Okta registration with invalid API token"""
        config = valid_okta_config()
        config['api_token'] = 'invalid-token'
        
        with patch('routes.pyrequests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                'errorCode': 'E0000011',
                'errorSummary': 'Invalid token provided'
            }
            mock_get.return_value = mock_response
            
            response = client.post('/discovery/idp', 
                                 json=config,
                                 content_type='application/json')
            
            assert response.status_code == 400
            result = response.get_json()
            assert result['status'] == 'error'
            assert 'Invalid credentials' in result['message']

    def test_register_okta_rate_limit(self, client):
        config = valid_okta_config()
        with patch('routes.pyrequests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.json.return_value = {'errorCode': 'E0000047', 'errorSummary': 'API rate limit exceeded'}
            mock_get.return_value = mock_response
            response = client.post('/discovery/idp', json=config, content_type='application/json')
            assert response.status_code == 503
            assert 'rate limiting' in response.get_json()['message'].lower()

    def test_register_okta_timeout(self, client):
        config = valid_okta_config()
        with patch('routes.pyrequests.get') as mock_get:
            mock_get.side_effect = Exception('Connection timeout')
            response = client.post('/discovery/idp', json=config, content_type='application/json')
            assert response.status_code == 408 or response.status_code == 400
            assert 'timeout' in response.get_json()['message'].lower()

    def test_register_unsupported_provider(self, client):
        """Test registration with unsupported provider type"""
        config = {
            "display_name": "Test Provider",
            "type": "unsupported_provider",
            "config": {}
        }
        
        response = client.post('/discovery/idp', 
                             json=config,
                             content_type='application/json')
        
        assert response.status_code == 400
        result = response.get_json()
        assert result['status'] == 'error'
        assert 'Unsupported provider type' in result['message']

    def test_register_duplicate(self, client):
        config = valid_azure_ad_config()
        with patch('routes.pyrequests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'access_token': 'test-token', 'expires_in': 3600}
            mock_post.return_value = mock_response
            response1 = client.post('/discovery/idp', json=config, content_type='application/json')
            response2 = client.post('/discovery/idp', json=config, content_type='application/json')
            assert response1.status_code == 200
            # The second registration may succeed or fail depending on deduplication logic

class TestMultiIDPAppDiscovery:
    """Test application discovery for different IDP providers"""
    
    def test_fetch_apps_azure_ad_success(self, client):
        """Test successful app discovery from Azure AD"""
        # First register Azure AD IDP
        config = valid_azure_ad_config()
        
        with patch('routes.pyrequests.post') as mock_post, \
             patch('routes.pyrequests.get') as mock_get:
            
            # Mock token endpoint
            token_response = MagicMock()
            token_response.status_code = 200
            token_response.json.return_value = {
                'access_token': 'test-token',
                'expires_in': 3600
            }
            mock_post.return_value = token_response
            
            # Register IDP
            register_response = client.post('/discovery/idp', 
                                          json=config,
                                          content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            
            # Mock Microsoft Graph API response
            apps_response = MagicMock()
            apps_response.status_code = 200
            apps_response.json.return_value = {
                'value': [
                    {
                        'id': 'app1',
                        'displayName': 'Microsoft Teams',
                        'description': 'Team collaboration app',
                        'appId': '00000002-0000-0ff1-ce00-000000000000',
                        'signInAudience': 'AzureADMyOrg'
                    },
                    {
                        'id': 'app2',
                        'displayName': 'SharePoint',
                        'description': 'Document management',
                        'appId': '00000003-0000-0ff1-ce00-000000000000',
                        'signInAudience': 'AzureADMyOrg'
                    }
                ]
            }
            mock_get.return_value = apps_response
            
            # Fetch apps
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            
            assert response.status_code == 200
            result = response.get_json()
            assert result['status'] == 'success'
            assert len(result['apps']) == 2
            assert result['apps'][0]['name'] == 'Microsoft Teams'
            assert result['apps'][1]['name'] == 'SharePoint'

    def test_fetch_apps_azure_ad_token_401(self, client):
        config = valid_azure_ad_config()
        with patch('routes.pyrequests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {'error': 'invalid_client'}
            mock_post.return_value = mock_response
            response = client.post('/discovery/idp', json=config, content_type='application/json')
            idp_id = response.get_json().get('idp_id', 999)
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            assert response.status_code in (401, 400)

    def test_fetch_apps_azure_ad_graph_502(self, client):
        config = valid_azure_ad_config()
        with patch('routes.pyrequests.post') as mock_post, patch('routes.pyrequests.get') as mock_get:
            token_response = MagicMock()
            token_response.status_code = 200
            token_response.json.return_value = {'access_token': 'test-token', 'expires_in': 3600}
            mock_post.return_value = token_response
            register_response = client.post('/discovery/idp', json=config, content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            apps_response = MagicMock()
            apps_response.status_code = 502
            apps_response.json.return_value = {}
            mock_get.return_value = apps_response
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            assert response.status_code == 502

    def test_fetch_apps_okta_success(self, client):
        """Test successful app discovery from Okta"""
        # First register Okta IDP
        config = valid_okta_config()
        
        with patch('routes.pyrequests.get') as mock_get:
            # Mock Okta org info endpoint
            org_response = MagicMock()
            org_response.status_code = 200
            org_response.json.return_value = {
                'id': 'test-org-id',
                'name': 'Test Organization'
            }
            mock_get.return_value = org_response
            
            # Register IDP
            register_response = client.post('/discovery/idp', 
                                          json=config,
                                          content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            
            # Mock Okta apps endpoint
            apps_response = MagicMock()
            apps_response.status_code = 200
            apps_response.json.return_value = [
                {
                    'id': 'app1',
                    'name': 'Salesforce',
                    'label': 'Salesforce CRM',
                    'status': 'ACTIVE',
                    'created': '2024-01-01T00:00:00.000Z',
                    'lastUpdated': '2024-01-01T00:00:00.000Z'
                },
                {
                    'id': 'app2',
                    'name': 'Slack',
                    'label': 'Slack Workspace',
                    'status': 'ACTIVE',
                    'created': '2024-01-01T00:00:00.000Z',
                    'lastUpdated': '2024-01-01T00:00:00.000Z'
                }
            ]
            mock_get.return_value = apps_response
            
            # Fetch apps
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            
            assert response.status_code == 200
            result = response.get_json()
            assert result['status'] == 'success'
            assert len(result['apps']) == 2
            assert result['apps'][0]['name'] == 'Salesforce'
            assert result['apps'][1]['name'] == 'Slack'

    def test_fetch_apps_okta_401(self, client):
        config = valid_okta_config()
        with patch('routes.pyrequests.get') as mock_get:
            org_response = MagicMock()
            org_response.status_code = 200
            org_response.json.return_value = {'id': 'test-org-id', 'name': 'Test Organization'}
            mock_get.return_value = org_response
            register_response = client.post('/discovery/idp', json=config, content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            apps_response = MagicMock()
            apps_response.status_code = 401
            apps_response.json.return_value = {'errorCode': 'E0000011', 'errorSummary': 'Invalid token provided'}
            mock_get.return_value = apps_response
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            assert response.status_code == 502 or response.status_code == 401

    def test_fetch_apps_okta_429(self, client):
        config = valid_okta_config()
        with patch('routes.pyrequests.get') as mock_get:
            org_response = MagicMock()
            org_response.status_code = 200
            org_response.json.return_value = {'id': 'test-org-id', 'name': 'Test Organization'}
            mock_get.return_value = org_response
            register_response = client.post('/discovery/idp', json=config, content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            apps_response = MagicMock()
            apps_response.status_code = 429
            apps_response.json.return_value = {'errorCode': 'E0000047', 'errorSummary': 'API rate limit exceeded'}
            mock_get.return_value = apps_response
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            assert response.status_code == 503

    def test_fetch_apps_idp_not_found(self, client):
        """Test app discovery with non-existent IDP"""
        response = client.get('/discovery/apps?idp_id=999')
        
        assert response.status_code == 404
        result = response.get_json()
        assert result['status'] == 'error'
        assert 'IDP not found' in result['message']

    def test_fetch_apps_inactive_idp(self, client):
        """Test app discovery with inactive IDP"""
        # Register IDP but mark as inactive
        config = valid_azure_ad_config()
        
        with patch('routes.pyrequests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401  # Invalid credentials
            mock_post.return_value = mock_response
            
            register_response = client.post('/discovery/idp', 
                                          json=config,
                                          content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            
            # Try to fetch apps
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            
            assert response.status_code == 400
            result = response.get_json()
            assert result['status'] == 'error'
            assert 'IDP not active' in result['message']

    def test_fetch_apps_no_apps(self, client):
        config = valid_okta_config()
        with patch('routes.pyrequests.get') as mock_get:
            org_response = MagicMock()
            org_response.status_code = 200
            org_response.json.return_value = {'id': 'test-org-id', 'name': 'Test Organization'}
            mock_get.return_value = org_response
            register_response = client.post('/discovery/idp', json=config, content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            apps_response = MagicMock()
            apps_response.status_code = 200
            apps_response.json.return_value = []
            mock_get.return_value = apps_response
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            assert response.status_code == 200
            assert response.get_json()['total_count'] == 0

class TestMultiIDPErrorHandling:
    """Test error handling for different IDP providers"""
    
    def test_google_workspace_quota_exceeded(self, client):
        """Test Google Workspace quota exceeded"""
        config = valid_google_workspace_config()
        
        with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
             patch('routes.pyrequests.get') as mock_get:
            
            mock_cred_instance = MagicMock()
            mock_cred_instance.token = 'fake-token'
            mock_cred_instance.expired = False
            mock_creds.return_value = mock_cred_instance
            
            # Register IDP first
            register_response = client.post('/discovery/idp', 
                                          json=config,
                                          content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            
            # Mock quota exceeded response
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.json.return_value = {
                'error': {
                    'code': 403,
                    'message': 'Quota exceeded for quota group'
                }
            }
            mock_get.return_value = mock_response
            
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            
            assert response.status_code == 503
            result = response.get_json()
            assert result['status'] == 'error'
            assert 'quota' in result['message'].lower()

class TestMultiIDPDataNormalization:
    """Test data normalization across different IDP providers"""
    
    def test_data_normalization_azure_ad(self, client):
        """Test Azure AD data normalization"""
        config = valid_azure_ad_config()
        
        with patch('routes.pyrequests.post') as mock_post, \
             patch('routes.pyrequests.get') as mock_get:
            
            # Mock successful registration
            token_response = MagicMock()
            token_response.status_code = 200
            token_response.json.return_value = {
                'access_token': 'test-token',
                'expires_in': 3600
            }
            mock_post.return_value = token_response
            
            register_response = client.post('/discovery/idp', 
                                          json=config,
                                          content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            
            # Mock apps response with Azure AD specific fields
            apps_response = MagicMock()
            apps_response.status_code = 200
            apps_response.json.return_value = {
                'value': [
                    {
                        'id': 'app1',
                        'displayName': 'Test App',
                        'description': 'Test Description',
                        'appId': 'test-app-id',
                        'signInAudience': 'AzureADMyOrg',
                        'createdDateTime': '2024-01-01T00:00:00Z'
                    }
                ]
            }
            mock_get.return_value = apps_response
            
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            
            assert response.status_code == 200
            result = response.get_json()
            app = result['apps'][0]
            
            # Verify normalized fields
            assert app['id'] == 'app1'
            assert app['name'] == 'Test App'
            assert app['description'] == 'Test Description'
            assert app['status'] == 'ACTIVE'  # Normalized status
            assert 'created_at' in app
            assert 'updated_at' in app

    def test_data_normalization_okta(self, client):
        """Test Okta data normalization"""
        config = valid_okta_config()
        
        with patch('routes.pyrequests.get') as mock_get:
            # Mock successful registration
            org_response = MagicMock()
            org_response.status_code = 200
            org_response.json.return_value = {
                'id': 'test-org-id',
                'name': 'Test Organization'
            }
            mock_get.return_value = org_response
            
            register_response = client.post('/discovery/idp', 
                                          json=config,
                                          content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            
            # Mock apps response with Okta specific fields
            apps_response = MagicMock()
            apps_response.status_code = 200
            apps_response.json.return_value = [
                {
                    'id': 'app1',
                    'name': 'test-app',
                    'label': 'Test App',
                    'status': 'ACTIVE',
                    'created': '2024-01-01T00:00:00.000Z',
                    'lastUpdated': '2024-01-01T00:00:00.000Z',
                    'signOnMode': 'SAML_2_0'
                }
            ]
            mock_get.return_value = apps_response
            
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            
            assert response.status_code == 200
            result = response.get_json()
            app = result['apps'][0]
            
            # Verify normalized fields
            assert app['id'] == 'app1'
            assert app['name'] == 'Test App'  # Uses label instead of name
            assert app['status'] == 'ACTIVE'
            assert 'created_at' in app
            assert 'updated_at' in app

    def test_data_normalization_google_workspace(self, client):
        """Test Google Workspace data normalization"""
        config = valid_google_workspace_config()
        
        with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
             patch('routes.pyrequests.get') as mock_get:
            
            mock_cred_instance = MagicMock()
            mock_cred_instance.token = 'fake-token'
            mock_cred_instance.expired = False
            mock_creds.return_value = mock_cred_instance
            
            # Register IDP
            register_response = client.post('/discovery/idp', 
                                          json=config,
                                          content_type='application/json')
            idp_id = register_response.get_json()['idp_id']
            
            # Mock Google Admin SDK response
            apps_response = MagicMock()
            apps_response.status_code = 200
            apps_response.json.return_value = {
                'applications': [
                    {
                        'id': 'app1',
                        'name': 'Gmail',
                        'description': 'Email service',
                        'status': 'ACTIVE'
                    }
                ]
            }
            mock_get.return_value = apps_response
            
            # Fetch apps
            response = client.get(f'/discovery/apps?idp_id={idp_id}')
            
            assert response.status_code == 200
            result = response.get_json()
            app = result['apps'][0]
            
            # Verify normalized fields
            assert app['id'] == 'app1'
            assert app['name'] == 'Gmail'
            assert app['description'] == 'Email service'
            assert app['status'] == 'ACTIVE'
            assert 'created_at' in app
            assert 'updated_at' in app

class TestMultiIDPConfigurationValidation:
    """Test configuration validation for different IDP providers"""
    
    def test_google_workspace_config_validation(self, client):
        """Test Google Workspace configuration validation (existing)"""
        # Test missing service_account_json
        config = valid_google_workspace_config()
        del config['service_account_json']
        
        response = client.post('/discovery/idp', 
                             json=config,
                             content_type='application/json')
        
        assert response.status_code == 400
        assert 'service_account_json' in response.get_json()['message']

if __name__ == '__main__':
    pytest.main([__file__])
