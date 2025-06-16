# Top Agents - AI Agents Marketplace

A comprehensive B2B AI agents marketplace platform that enables enterprise teams to discover, collaborate, and deploy internal tools through an intuitive, socially-driven interface.

## 🌟 Features

### 🚀 Core Platform
- **143+ AI Agents Directory** with detailed profiles and ratings
- **Advanced Search & Filtering** by domain, platform, pricing model
- **User Authentication** with Google SSO demo and email/password
- **Team Collaboration** through Stories & Recipes Hub
- **Enterprise Integration** architecture documentation

### 🔐 Authentication System
- Secure user registration and login
- Google SSO integration (demo mode)
- Session management with token-based authentication
- Post-signup welcome flow with team outreach messaging

### 📊 Agent Management
- Comprehensive agent profiles with ratings and reviews
- Category-based filtering (Productivity, Customer Service, Coding, etc.)
- Platform filtering (Web-based, API, Desktop, Mobile)
- Pricing model filtering (Free, Freemium, Paid, Enterprise)
- User-generated content and reviews

### 🏢 Enterprise Features
- **Dashboard** for team leaders with agent management
- **Stories Hub** for employee discovery and knowledge sharing
- **Enterprise Integration** page with 5-step architecture flow
- **API Documentation** for seamless integrations

### 📱 Design & UX
- Mobile-responsive design with Tailwind CSS
- Clean, modern interface optimized for B2B use
- Dual-layer UX: admin dashboard + employee discovery
- Professional styling with consistent branding

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Flask and dependencies (see `pyproject.toml`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/vishwastam/ai-agents-directory.git
cd ai-agents-directory
```

2. Install dependencies:
```bash
pip install -r dependencies.txt
# or if using uv:
uv sync
```

3. Set up environment variables:
```bash
export DATABASE_URL="your_postgresql_url"
export SESSION_SECRET="your_secret_key"
export GITHUB_TOKEN="your_github_token"  # Optional, for discovery system
```

4. Run the application:
```bash
python main.py
# or with gunicorn:
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

5. Visit `http://localhost:5000` to see the directory

## 📊 Database Schema

The application uses a PostgreSQL database with the following key data:

- **Agents**: Stored in CSV format (`combined_ai_agents_directory.csv`)
- **User Ratings**: JSON-based storage (`ratings.json`)
- **User Submissions**: JSON-based storage (`user_agents.json`)

## 🤖 Automated Discovery System

The directory includes an automated system to discover new AI agents:

```bash
# Run manual discovery
python agent_discovery_system.py

# Set up automated scheduling
python scheduler.py
```

### Discovery Features
- Web scraping from curated sources
- Duplicate detection and validation
- Confidence scoring for new agents
- Automated integration with manual review

## 🛠️ Architecture

### Backend (Python/Flask)
- `main.py`: Application entry point
- `app.py`: Flask application setup
- `routes.py`: URL routing and view logic
- `models.py`: Data models and structures
- `data_loader.py`: Agent data management
- `rating_system.py`: User rating functionality

### Frontend (HTML/CSS/JavaScript)
- Responsive design with Tailwind CSS
- Interactive filtering and search
- Star rating system
- Mobile-optimized interface

### Discovery System
- `agent_discovery_system.py`: Core discovery logic
- `comprehensive_user_research.py`: User feedback research
- `scheduler.py`: Automated scheduling
- `merge_agents.py`: Data integration utilities

## 📝 User Submission Management

### Pending Review System
User-submitted agents are saved for review before being added to the main directory:

1. **Submission Process**: Users submit agents through the web form
2. **Pending Status**: Submissions are saved with `status: 'pending_review'`
3. **Review Queue**: Check `user_agents.json` for pending submissions
4. **Approval Process**: Manually change status to `'approved'` to publish

### Managing Submissions
View pending submissions:
```bash
python -c "
import json
with open('user_agents.json', 'r') as f:
    data = json.load(f)
pending = [agent for agent in data if agent.get('status') == 'pending_review']
print(f'Pending submissions: {len(pending)}')
for agent in pending:
    print(f'- {agent[\"name\"]} by {agent.get(\"creator\", \"Unknown\")}')
"
```

Approve a submission:
```python
import json
with open('user_agents.json', 'r') as f:
    data = json.load(f)

# Find and approve agent by name
for agent in data:
    if agent['name'] == 'Agent Name' and agent['status'] == 'pending_review':
        agent['status'] = 'approved'
        break

with open('user_agents.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## 🔧 Configuration

### Discovery System Configuration
Create `discovery_config.json`:
```json
{
  "sources": [
    "https://example.com/ai-tools",
    "https://another-source.com/agents"
  ],
  "filters": {
    "min_confidence": 0.7,
    "exclude_keywords": ["demo", "test"]
  }
}
```

### Scheduler Configuration
Create `scheduler_config.json`:
```json
{
  "frequency": "daily",
  "time": "02:00",
  "max_new_agents": 10,
  "backup_retention_days": 30
}
```

## 📈 Usage Examples

### Adding New Agents
Users can submit agents through the web interface or programmatically:

```python
from data_loader import DataLoader

loader = DataLoader()
agent_data = {
    "name": "New AI Agent",
    "creator": "Company Name",
    "url": "https://example.com",
    "description": "Agent description",
    "domains": "Category",
    "pricing": "Free"
}
loader.add_user_agent(agent_data)
```

### Rating Agents
```python
from rating_system import RatingSystem

rating_system = RatingSystem()
rating_system.add_rating(
    agent_slug="agent-name",
    rating=5,
    feedback="Excellent agent for coding tasks!"
)
```

## 🔍 Search & Filtering

The directory supports:
- **Natural language search**: "coding assistants for Python"
- **Category filtering**: Software Development, Writing, Marketing, etc.
- **Use case filtering**: Code completion, Content writing, etc.
- **Pricing filters**: Free, Freemium, Paid
- **Platform filters**: Web, API, Desktop, Mobile

## 📱 Mobile Optimization

- Responsive grid layouts
- Touch-friendly interfaces
- Optimized search and filtering
- Mobile-specific navigation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Adding New Agents
To add agents to the directory:

1. Use the web interface "Add Agent" button
2. Or run the automated discovery system
3. Or submit a pull request with agent data

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🔗 Links

- **Live Demo**: [Deployed on Replit](https://your-repl-url.replit.app)
- **Repository**: [GitHub](https://github.com/vishwastam/ai-agents-directory)
- **Issues**: [GitHub Issues](https://github.com/vishwastam/ai-agents-directory/issues)

## 📞 Support

For questions, feature requests, or bug reports:
- Open an issue on GitHub
- Contact through the repository discussions

---

Built with ❤️ for the AI community