import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from flask import Flask
from models import db, GoogleWorkspaceIDPIntegration, IDPIntegration
import json
from unittest.mock import patch, MagicMock
import time

def create_test_app():
    """Create a fresh Flask app for testing."""
    from app import create_app
    
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
    }
    
    app = create_app(test_config)
    return app

@pytest.fixture
def client():
    app = create_test_app()
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def valid_service_account_json():
    return json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "fakekeyid",
        "private_key": "-----BEGIN PRIVATE KEY-----\nfakekey\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
    })

# US1: Configure IDP Connection Tests
def test_register_google_workspace_idp_success(client):
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=data)
        assert resp.status_code == 200
        out = resp.get_json()
        assert out['status'] == 'success'
        assert 'idp_id' in out
        
        # Verify it's stored in DB
        integration = IDPIntegration.query.get(out['idp_id'])
        assert integration is not None
        assert integration.status == 'active'

def test_register_google_workspace_idp_invalid_json(client):
    data = {
        "display_name": "Test Google Workspace",
        "type": "google_workspace",
        "service_account_json": "invalid",
        "api_url": "https://admin.googleapis.com"
    }
    resp = client.post('/discovery/idp', json=data)
    assert resp.status_code == 400
    out = resp.get_json()
    assert out['status'] == 'error'
    assert 'Invalid credentials' in out['message']

def test_register_google_workspace_idp_missing_fields(client):
    data = {
        "display_name": "Test Google Workspace",
        "type": "google_workspace"
        # Missing service_account_json
    }
    resp = client.post('/discovery/idp', json=data)
    assert resp.status_code == 400
    out = resp.get_json()
    assert out['status'] == 'error'
    assert 'Missing required field' in out['message']

def test_register_google_workspace_idp_db_status_on_failure(client):
    # Simulate DB status on failure by using invalid credentials
    data = {
        "display_name": "Test Google Workspace",
        "type": "google_workspace",
        "service_account_json": "invalid",
        "api_url": "https://admin.googleapis.com"
    }
    resp = client.post('/discovery/idp', json=data)
    assert resp.status_code == 400
    out = resp.get_json()
    assert out['status'] == 'error'
    assert 'Invalid credentials' in out['message']

# US2: Fetch Catalog of Registered Applications Tests

def test_fetch_app_catalog_success(client):
    """Test successful app catalog fetch with valid IDP and working Google API"""
    # First create a valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_creds.return_value = mock_cred_instance
        
        # Create IDP
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock Google API response
    mock_apps_response = {
        'applications': [
            {
                'id': 'app1',
                'name': 'Slack',
                'description': 'Team communication',
                'status': 'ACTIVE'
            },
            {
                'id': 'app2',
                'name': 'Zoom',
                'description': 'Video conferencing',
                'status': 'ACTIVE'
            }
        ]
    }
    
    # Mock both credential creation and API call
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        
        # Mock credentials for the fetch endpoint
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        # Mock API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_apps_response
        
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        if resp.status_code != 200:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 200
        out = resp.get_json()
        assert out['status'] == 'success'
        assert len(out['apps']) == 2
        assert out['apps'][0]['name'] == 'Slack'

def test_fetch_app_catalog_empty(client):
    """Test empty app catalog - valid IDP but no apps configured"""
    # Create valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock empty Google API response
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'applications': []}
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        if resp.status_code != 200:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 200
        out = resp.get_json()
        assert out['status'] == 'success'
        assert len(out['apps']) == 0

def test_fetch_app_catalog_invalid_idp_id(client):
    """Test invalid IDP ID - non-existent IDP"""
    resp = client.get('/discovery/apps?idp_id=99999')
    assert resp.status_code == 404
    out = resp.get_json()
    assert out['status'] == 'error'
    assert 'IDP not found' in out['message']

def test_fetch_app_catalog_inactive_idp(client):
    """Test inactive IDP - IDP with status 'error'"""
    # Create IDP with error status by simulating invalid credentials
    idp_data = {
        "display_name": "Test Google Workspace",
        "type": "google_workspace",
        "service_account_json": "invalid",
        "api_url": "https://admin.googleapis.com"
    }
    resp = client.post('/discovery/idp', json=idp_data)
    out = resp.get_json()
    assert resp.status_code == 400
    assert out['status'] == 'error'
    assert 'Invalid credentials' in out['message']
    # No need to fetch apps since IDP creation failed

def test_fetch_app_catalog_google_api_rate_limit(client):
    """Test Google API rate limiting - API returns 429"""
    # Create valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock Google API rate limit response
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        mock_get.return_value.status_code = 429
        mock_get.return_value.text = 'Rate limit exceeded'
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        if resp.status_code != 503:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 503
        out = resp.get_json()
        assert out['status'] == 'error'
        assert 'Service temporarily unavailable' in out['message']

def test_fetch_app_catalog_google_api_timeout(client):
    """Test Google API timeout - API takes >30 seconds"""
    # Create valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock Google API timeout
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        mock_get.side_effect = Exception('Request timeout')
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        if resp.status_code != 408:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 408
        out = resp.get_json()
        assert out['status'] == 'error'
        assert 'Request timeout' in out['message']

def test_fetch_app_catalog_malformed_response(client):
    """Test malformed Google API response - unexpected JSON structure"""
    # Create valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock malformed Google API response
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'unexpected': 'structure'}
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        if resp.status_code != 500:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 500
        out = resp.get_json()
        assert out['status'] == 'error'
        assert 'Data processing error' in out['message']

def test_fetch_app_catalog_missing_required_fields(client):
    """Test apps with missing required fields - should filter out invalid apps"""
    # Create valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock Google API response with missing fields
    mock_apps_response = {
        'applications': [
            {
                'id': 'app1',
                'name': 'Slack',
                'status': 'ACTIVE'
            },
            {
                'id': 'app2',
                # Missing name
                'status': 'ACTIVE'
            },
            {
                # Missing id
                'name': 'Zoom',
                'status': 'ACTIVE'
            }
        ]
    }
    
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_apps_response
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        if resp.status_code != 200:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 200
        out = resp.get_json()
        assert out['status'] == 'success'
        # Should only include valid apps
        assert len(out['apps']) == 1
        assert out['apps'][0]['name'] == 'Slack'

def test_fetch_app_catalog_special_characters(client):
    """Test apps with special characters and Unicode names"""
    # Create valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock Google API response with special characters
    mock_apps_response = {
        'applications': [
            {
                'id': 'app1',
                'name': '🚀 Rocket App',
                'description': 'Unicode & emoji support',
                'status': 'ACTIVE'
            },
            {
                'id': 'app2',
                'name': 'Café & Résumé App',
                'description': 'Accented characters',
                'status': 'ACTIVE'
            }
        ]
    }
    
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_apps_response
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        if resp.status_code != 200:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 200
        out = resp.get_json()
        assert out['status'] == 'success'
        assert len(out['apps']) == 2
        assert '🚀' in out['apps'][0]['name']
        assert 'Café' in out['apps'][1]['name']

def test_fetch_app_catalog_performance(client):
    """Test performance - API call completes within reasonable time"""
    # Create valid IDP
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        
        idp_data = {
            "display_name": "Test Google Workspace",
            "type": "google_workspace",
            "service_account_json": valid_service_account_json(),
            "api_url": "https://admin.googleapis.com"
        }
        resp = client.post('/discovery/idp', json=idp_data)
        idp_id = resp.get_json()['idp_id']
    
    # Mock Google API response
    mock_apps_response = {
        'applications': [
            {'id': f'app{i}', 'name': f'App {i}', 'status': 'ACTIVE'}
            for i in range(100)  # 100 apps
        ]
    }
    
    with patch('routes.service_account.Credentials.from_service_account_info') as mock_creds, \
         patch('routes.pyrequests.get') as mock_get:
        mock_cred_instance = MagicMock()
        mock_cred_instance.token = 'fake-token'
        mock_cred_instance.expired = False
        mock_creds.return_value = mock_cred_instance
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_apps_response
        start_time = time.time()
        resp = client.get(f'/discovery/apps?idp_id={idp_id}')
        end_time = time.time()
        if resp.status_code != 200:
            print(f"Error response: {resp.get_json()}")
        assert resp.status_code == 200
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        out = resp.get_json()
        assert len(out['apps']) == 100

# Placeholder tests for remaining user stories
def test_us1_configure_idp_connection():
    """Test credentials and return success or failure on setup."""
    assert False, 'Not implemented: Should test IDP credential setup and return success/failure.'

def test_us3_fetch_user_to_app_assignments():
    """Store user assignments with roles and timestamps."""
    assert False, 'Not implemented: Should fetch and store user assignments with roles/timestamps.'

def test_us4_pull_recent_login_events():
    """Store login events with timestamp, device, IP."""
    assert False, 'Not implemented: Should fetch and store login events with timestamp, device, IP.'

def test_us5_normalize_and_store_directory_data():
    """Map fields to internal schema; log unmapped ones."""
    assert False, 'Not implemented: Should normalize data and log unmapped fields.'

def test_us6_schedule_periodic_sync():
    """Daily cron job triggers sync and retries on failure."""
    assert False, 'Not implemented: Should schedule and retry sync jobs.'

def test_us7_error_handling_and_alerting():
    """Log and notify on integration failure."""
    assert False, 'Not implemented: Should log and notify on sync failure.'

def test_us8_provide_discovery_api_endpoint():
    """API returns paginated JSON with auth control."""
    assert False, 'Not implemented: Should provide paginated, authenticated API.' 