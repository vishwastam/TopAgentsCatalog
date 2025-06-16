# Top Agents - AI Agents Marketplace Setup

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file or set environment variables:
```
SESSION_SECRET=your_secure_session_secret_here
```

### 3. Run the Application
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## Features Overview

- **143+ AI Agents Directory** with detailed profiles and ratings
- **User Authentication** with Google SSO demo and email/password
- **Dashboard** for team leaders with agent management
- **Team Stories & Recipes Hub** for employee collaboration
- **Enterprise Integration** architecture documentation
- **Mobile-responsive design** with Tailwind CSS

## Application Structure

### Core Files
- `main.py` - Application entry point
- `app.py` - Flask application setup
- `routes.py` - All application routes
- `user_auth.py` - Authentication system
- `models.py` - Data models
- `data_loader.py` - Agent data management
- `recipe_loader.py` - Recipe data management

### Data Files
- `combined_ai_agents_directory.csv` - Agent database (143 agents)
- `recipes_full_content.csv` - Recipe database (24 recipes)
- `ratings.json` - User ratings data
- `users.json` - User accounts (empty initially)
- `user_sessions.json` - User sessions (empty initially)

### Templates
- All HTML templates in `templates/` directory
- Responsive design with mobile-first approach
- Clean B2B interface optimized for enterprise use

## Environment Variables

Required:
- `SESSION_SECRET` - Secure random string for session management

Optional:
- `DATABASE_URL` - PostgreSQL connection string (if using database instead of JSON files)

## Authentication

The application includes:
- Email/password registration and login
- Google SSO demo functionality
- Session-based authentication with secure tokens
- Post-signup welcome flow with team outreach messaging

## Production Deployment

For production deployment:
1. Set secure SESSION_SECRET
2. Configure proper database (PostgreSQL recommended)
3. Set up SSL/HTTPS
4. Configure proper domain and DNS
5. Set up monitoring and logging

## Support

For questions or issues, contact: support@topagents.com