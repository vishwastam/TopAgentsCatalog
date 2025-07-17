import pytest
import uuid
from datetime import datetime
from models import db

# --- Flask app and client fixtures ---
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app

@pytest.fixture
def app():
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
    return app.test_client()

# --- Fixtures ---
@pytest.fixture
def agent_data():
    return {
        "name": "Test Agent",
        "slug": "test-agent",
        "short_desc": "Short description",
        "long_desc": "Long description",
        "creator": "Test Creator",
        "url": "https://test.com",
        "platform": "OpenAI",
        "pricing": "Free",
        "domains": "General",
        "use_cases": "Automation",
        "underlying_model": "GPT-4",
        "deployment": "Cloud",
        "legitimacy": "Verified"
    }

@pytest.fixture
def another_agent_data():
    return {
        "name": "Another Agent",
        "slug": "another-agent",
        "short_desc": "Another short desc",
        "long_desc": "Another long desc",
        "creator": "Another Creator",
        "url": "https://another.com",
        "platform": "Anthropic",
        "pricing": "Paid",
        "domains": "Business",
        "use_cases": "Data Analysis",
        "underlying_model": "Claude",
        "deployment": "API",
        "legitimacy": "Trusted"
    }

# --- Model Creation & Field Validation ---
def test_create_ai_agent(app, agent_data):
    from models import AIAgent
    agent = AIAgent(**agent_data)
    db.session.add(agent)
    db.session.commit()
    assert agent.id is not None
    assert agent.name == agent_data["name"]
    assert agent.slug == agent_data["slug"]
    assert agent.created_at is not None
    assert agent.updated_at is not None

def test_missing_required_fields(app):
    from models import AIAgent
    agent = AIAgent()
    db.session.add(agent)
    with pytest.raises(Exception):
        db.session.commit()

# --- CRUD Operations ---
def test_update_and_delete_ai_agent(app, agent_data):
    from models import AIAgent
    agent = AIAgent(**agent_data)
    db.session.add(agent)
    db.session.commit()
    agent.short_desc = "Updated desc"
    db.session.commit()
    updated = AIAgent.query.filter_by(slug=agent.slug).first()
    assert updated.short_desc == "Updated desc"
    db.session.delete(updated)
    db.session.commit()
    assert AIAgent.query.filter_by(slug=agent.slug).first() is None

def test_query_by_name_and_slug(app, agent_data):
    from models import AIAgent
    agent = AIAgent(**agent_data)
    db.session.add(agent)
    db.session.commit()
    found = AIAgent.query.filter_by(name=agent_data["name"]).first()
    assert found is not None
    found_by_slug = AIAgent.query.filter_by(slug=agent_data["slug"]).first()
    assert found_by_slug is not None

# --- Public Discovery ---
def test_agent_listed_on_repository_page(client, app, agent_data):
    from models import AIAgent
    agent = AIAgent(**agent_data)
    db.session.add(agent)
    db.session.commit()
    response = client.get("/agents")
    assert response.status_code == 200
    assert agent_data["name"].encode() in response.data

def test_agent_detail_page_shows_metadata(client, app, agent_data):
    from models import AIAgent
    agent = AIAgent(**agent_data)
    db.session.add(agent)
    db.session.commit()
    response = client.get(f"/agents/{agent.slug}")
    assert response.status_code == 200
    assert agent_data["long_desc"].encode() in response.data

# --- Recipe Tagging (Many-to-Many) ---
def test_agent_recipe_relationship(app, agent_data):
    from models import AIAgent, Recipe
    agent = AIAgent(**agent_data)
    recipe = Recipe(name="Test Recipe", synopsis="S", detailed_synopsis="D", target_audience="All", why_it_works="W", source_links="L")
    agent.recipes.append(recipe)
    db.session.add(agent)
    db.session.add(recipe)
    db.session.commit()
    assert recipe in agent.recipes
    assert agent in recipe.agents

# --- Admin & Analytics ---
def test_admin_can_create_update_delete_agent(app, agent_data):
    from models import AIAgent, User
    admin = User(id=str(uuid.uuid4()), email="admin@topagents.com", password_hash="x", role="admin", primary_role="admin", roles=["admin"])
    db.session.add(admin)
    db.session.commit()
    agent = AIAgent(**agent_data)
    db.session.add(agent)
    db.session.commit()
    agent.short_desc = "Admin updated desc"
    db.session.commit()
    db.session.delete(agent)
    db.session.commit()
    assert AIAgent.query.filter_by(slug=agent.slug).first() is None

# --- Edge Cases ---
def test_duplicate_agent_slug_fails(app, agent_data):
    from models import AIAgent
    agent1 = AIAgent(**agent_data)
    db.session.add(agent1)
    db.session.commit()
    agent2 = AIAgent(**agent_data)
    db.session.add(agent2)
    with pytest.raises(Exception):
        db.session.commit()

def test_long_and_special_character_fields(app):
    from models import AIAgent
    long_name = "A" * 300
    agent = AIAgent(name=long_name, slug="long-agent", short_desc="S", long_desc="L", creator="C", url="https://x.com", platform="P", pricing="Free", domains="D", use_cases="U", underlying_model="M", deployment="D", legitimacy="L")
    db.session.add(agent)
    db.session.commit()
    assert agent.name == long_name

# --- Relationship Cleanup ---
def test_delete_agent_cleans_up_recipe_relationship(app, agent_data):
    from models import AIAgent, Recipe
    agent = AIAgent(**agent_data)
    recipe = Recipe(name="Cleanup Recipe", synopsis="S", detailed_synopsis="D", target_audience="All", why_it_works="W", source_links="L")
    agent.recipes.append(recipe)
    db.session.add(agent)
    db.session.add(recipe)
    db.session.commit()
    db.session.delete(agent)
    db.session.commit()
    assert agent not in recipe.agents 