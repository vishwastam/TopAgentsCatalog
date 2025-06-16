import pandas as pd
import os
import json
from models import Agent
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime, timedelta
import time
from intelligent_search import IntelligentSearch
from rating_system import RatingSystem

class DataLoader:
    """Class to handle loading and processing agent data from CSV"""
    
    def __init__(self, csv_path: str = "combined_ai_agents_directory.csv"):
        self.csv_path = csv_path
        self.user_agents_path = "user_agents.json"
        self.agents = []
        self.user_agents = []
        self.intelligent_search = IntelligentSearch()
        self.rating_system = RatingSystem()
        self._load_data()
    
    def _load_data(self):
        """Load agent data from CSV file"""
        try:
            if not os.path.exists(self.csv_path):
                logging.error(f"CSV file not found: {self.csv_path}")
                return
            
            df = pd.read_csv(self.csv_path)
            logging.info(f"Loaded {len(df)} agents from CSV")
            
            # Convert DataFrame rows to Agent objects
            for _, row in df.iterrows():
                try:
                    agent = Agent(
                        name=str(row.get('name', '')),
                        domains=str(row.get('domains', '')),
                        use_cases=str(row.get('use_cases', '')),
                        short_desc=str(row.get('short_desc', '')),
                        long_desc=str(row.get('long_desc', '')),
                        creator=str(row.get('creator', '')), 
                        url=str(row.get('url', '')),
                        platform=str(row.get('platform', '')),
                        pricing=str(row.get('pricing', '')),
                        underlying_model=str(row.get('underlying_model', '')),
                        deployment=str(row.get('deployment', '')),
                        legitimacy=str(row.get('legitimacy', '')),
                        what_users_think=str(row.get('what_users_think', ''))
                    )
                    self.agents.append(agent)
                except Exception as e:
                    logging.error(f"Error creating agent from row: {e}")
                    continue
            
            # Load user-submitted agents
            self._load_user_agents()
                    
        except Exception as e:
            logging.error(f"Error loading CSV data: {e}")
    
    def _load_user_agents(self):
        """Load approved user-submitted agents from JSON file"""
        try:
            if os.path.exists(self.user_agents_path):
                with open(self.user_agents_path, 'r') as f:
                    user_agents_data = json.load(f)
                
                approved_count = 0
                for agent_data in user_agents_data:
                    # Only load approved agents into main display
                    if agent_data.get('status') == 'approved':
                        agent = Agent(
                            name=agent_data['name'],
                            domains=agent_data.get('domains', ''),
                            use_cases=agent_data.get('use_cases', ''),
                            short_desc=agent_data['short_desc'],
                            long_desc=agent_data.get('long_desc', ''),
                            creator=agent_data.get('creator', 'User Submitted'),
                            url=agent_data.get('url', ''),
                            platform=agent_data.get('platform', 'Web'),
                            pricing=agent_data.get('pricing', 'Unknown'),
                            underlying_model=agent_data.get('underlying_model', ''),
                            deployment=agent_data.get('deployment', ''),
                            legitimacy=agent_data.get('legitimacy', 'User Submitted')
                        )
                        self.agents.append(agent)
                        approved_count += 1
                
                if approved_count > 0:
                    logging.info(f"Loaded {approved_count} approved user-submitted agents")
        except Exception as e:
            logging.error(f"Error loading user agents: {e}")
    
    def add_user_agent(self, agent_data: Dict[str, str]) -> bool:
        """Add a new user-submitted agent for review (not directly to main list)"""
        try:
            # Load existing submissions first
            existing_submissions = []
            if os.path.exists(self.user_agents_path):
                with open(self.user_agents_path, 'r') as f:
                    existing_submissions = json.load(f)
            
            # Create submission record with pending status
            submission = {
                'id': f"user_{int(time.time())}_{len(existing_submissions) + 1}",
                'name': agent_data['name'],
                'domains': agent_data.get('domains', ''),
                'use_cases': agent_data.get('use_cases', ''),
                'short_desc': agent_data['short_desc'],
                'long_desc': agent_data.get('long_desc', ''),
                'creator': agent_data.get('creator', 'User Submitted'),
                'url': agent_data.get('url', ''),
                'platform': agent_data.get('platform', 'Web'),
                'pricing': agent_data.get('pricing', 'Unknown'),
                'underlying_model': agent_data.get('underlying_model', ''),
                'deployment': agent_data.get('deployment', ''),
                'legitimacy': 'User Submitted',
                'status': 'pending_review',
                'submitted_date': datetime.now().isoformat(),
                'reviewed': False
            }
            
            # Add new submission
            existing_submissions.append(submission)
            
            # Save updated submissions
            with open(self.user_agents_path, 'w') as f:
                json.dump(existing_submissions, f, indent=2)
            
            logging.info(f"Added new user agent submission for review: {agent_data['name']}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding user agent submission: {e}")
            return False
    
    def _save_user_agents(self):
        """Save user-submitted agents to JSON file"""
        try:
            # Get only user-submitted agents
            user_agents = [agent for agent in self.agents if agent.legitimacy == 'User Submitted']
            
            # Convert to dictionaries for JSON serialization
            agents_data = []
            for agent in user_agents:
                agents_data.append({
                    'name': agent.name,
                    'domains': agent.domains,
                    'use_cases': agent.use_cases,
                    'short_desc': agent.short_desc,
                    'long_desc': agent.long_desc,
                    'creator': agent.creator,
                    'url': agent.url,
                    'platform': agent.platform,
                    'pricing': agent.pricing,
                    'underlying_model': agent.underlying_model,
                    'deployment': agent.deployment,
                    'legitimacy': agent.legitimacy
                })
            
            with open(self.user_agents_path, 'w') as f:
                json.dump(agents_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving user agents: {e}")
    
    def get_all_agents(self) -> List[Agent]:
        """Get all loaded agents"""
        return self.agents
    
    def get_agent_by_slug(self, slug: str) -> Agent:
        """Get a specific agent by its slug"""
        for agent in self.agents:
            if agent.slug == slug:
                return agent
        raise ValueError(f"Agent with slug '{slug}' not found")
    
    def get_filter_options(self) -> Dict[str, Any]:
        """Get all available filter options for the UI"""
        if not self.agents:
            return {}
        
        # Collect all unique values for filters
        domains = set()
        use_cases = set()
        platforms = set()
        pricing_options = set()
        models = set()
        creators = set()
        
        for agent in self.agents:
            domains.update(agent.domain_list)
            use_cases.update(agent.use_case_list)
            platforms.update(agent.platform_list)
            pricing_options.add(agent.pricing_clean)
            if agent.underlying_model.strip():
                models.add(agent.underlying_model.strip())
            if agent.creator.strip():
                creators.add(agent.creator.strip())
        
        return {
            'domains': sorted(list(domains)),
            'use_cases': sorted(list(use_cases)),
            'platforms': sorted(list(platforms)),
            'pricing': sorted(list(pricing_options)),
            'models': sorted(list(models)),
            'creators': sorted(list(creators))
        }
    
    def search_agents(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Agent]:
        """Search and filter agents based on query and filters"""
        if filters is None:
            filters = {}
        
        results = self.agents.copy()
        
        # Apply intelligent search
        if query:
            results = self.intelligent_search.search(results, query)
        
        # Apply filters
        if filters.get('domain'):
            results = [
                agent for agent in results
                if filters['domain'] in agent.domain_list
            ]
        
        if filters.get('use_case'):
            results = [
                agent for agent in results
                if filters['use_case'] in agent.use_case_list
            ]
        
        if filters.get('platform'):
            results = [
                agent for agent in results
                if filters['platform'] in agent.platform_list
            ]
        

        
        if filters.get('model'):
            results = [
                agent for agent in results
                if filters['model'].lower() in agent.underlying_model.lower()
            ]
        
        if filters.get('creator'):
            results = [
                agent for agent in results
                if filters['creator'].lower() in agent.creator.lower()
            ]
        
        return results
    
    def get_last_updated_time(self) -> str:
        """Get a human-readable timestamp for when the directory was last updated"""
        try:
            # Check the modification time of the main CSV file
            if os.path.exists(self.csv_path):
                csv_mtime = os.path.getmtime(self.csv_path)
            else:
                csv_mtime = 0
            
            # Check the modification time of user agents file
            if os.path.exists(self.user_agents_path):
                user_mtime = os.path.getmtime(self.user_agents_path)
            else:
                user_mtime = 0
            
            # Use the most recent modification time
            last_modified = max(csv_mtime, user_mtime)
            
            if last_modified == 0:
                return "Recently"
            
            # Calculate time difference
            now = datetime.now()
            last_update = datetime.fromtimestamp(last_modified)
            diff = now - last_update
            
            # Format the time difference
            if diff.days > 0:
                if diff.days == 1:
                    return "Updated 1 day ago"
                return f"Updated {diff.days} days ago"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                if hours == 1:
                    return "Updated 1 hour ago"
                return f"Updated {hours} hours ago"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                if minutes == 1:
                    return "Updated 1 minute ago"
                return f"Updated {minutes} minutes ago"
            else:
                return "Updated just now"
                
        except Exception as e:
            logging.error(f"Error getting last updated time: {e}")
            return "Recently updated"

# Global data loader instance
data_loader = DataLoader()
