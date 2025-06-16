"""
Rating system for AI agents with star ratings and text feedback
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

class RatingSystem:
    """Handles ratings and reviews for AI agents"""
    
    def __init__(self, ratings_file: str = "ratings.json"):
        self.ratings_file = ratings_file
        self.ratings = self._load_ratings()
    
    def _load_ratings(self) -> List[Dict[str, Any]]:
        """Load ratings from JSON file"""
        try:
            if os.path.exists(self.ratings_file):
                with open(self.ratings_file, 'r') as f:
                    ratings_data = json.load(f)
                    return ratings_data if isinstance(ratings_data, list) else []
            return []
        except Exception as e:
            logging.error(f"Error loading ratings: {e}")
            return []
    
    def _save_ratings(self):
        """Save ratings to JSON file"""
        try:
            with open(self.ratings_file, 'w') as f:
                json.dump(self.ratings, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Error saving ratings: {e}")
    
    def add_rating(self, agent_slug: str, rating: int, feedback: str = "", 
                   user_identifier: str = "") -> bool:
        """Add a new rating for an agent"""
        try:
            # Validate rating
            if not (1 <= rating <= 5):
                return False
            
            # Create rating entry
            rating_entry = {
                'agent_slug': agent_slug,
                'rating': rating,
                'feedback': feedback.strip(),
                'timestamp': datetime.now().isoformat(),
                'user_identifier': user_identifier or 'anonymous'
            }
            
            self.ratings.append(rating_entry)
            self._save_ratings()
            
            logging.info(f"Added rating {rating}/5 for agent {agent_slug}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding rating: {e}")
            return False
    
    def get_agent_ratings(self, agent_slug: str) -> Dict[str, Any]:
        """Get all ratings data for a specific agent"""
        agent_ratings = [r for r in self.ratings if r['agent_slug'] == agent_slug]
        
        if not agent_ratings:
            return {
                'average_rating': 0,
                'total_ratings': 0,
                'ratings_breakdown': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'recent_reviews': []
            }
        
        # Calculate statistics
        ratings_values = [r['rating'] for r in agent_ratings]
        average_rating = sum(ratings_values) / len(ratings_values)
        
        # Ratings breakdown - handle decimal ratings by rounding to nearest integer
        breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings_values:
            rounded_rating = round(rating)
            if rounded_rating in breakdown:
                breakdown[rounded_rating] += 1
        
        # Recent reviews with feedback
        recent_reviews = [
            r for r in sorted(agent_ratings, key=lambda x: x['timestamp'], reverse=True)
            if r['feedback'].strip()
        ][:5]  # Last 5 reviews with feedback
        
        return {
            'average_rating': round(average_rating, 1),
            'total_ratings': len(agent_ratings),
            'ratings_breakdown': breakdown,
            'recent_reviews': recent_reviews
        }
    
    def get_top_rated_agents(self, min_ratings: int = 3, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-rated agents with minimum number of ratings"""
        agent_stats = {}
        
        # Calculate stats for each agent
        for rating in self.ratings:
            slug = rating['agent_slug']
            if slug not in agent_stats:
                agent_stats[slug] = []
            agent_stats[slug].append(rating['rating'])
        
        # Filter and sort by average rating
        top_agents = []
        for slug, ratings_list in agent_stats.items():
            if len(ratings_list) >= min_ratings:
                avg_rating = sum(ratings_list) / len(ratings_list)
                top_agents.append({
                    'agent_slug': slug,
                    'average_rating': round(avg_rating, 1),
                    'total_ratings': len(ratings_list)
                })
        
        # Sort by average rating, then by number of ratings
        top_agents.sort(key=lambda x: (x['average_rating'], x['total_ratings']), reverse=True)
        
        return top_agents[:limit]
    
    def get_recent_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent reviews with feedback"""
        reviews_with_feedback = [
            r for r in self.ratings 
            if r['feedback'].strip()
        ]
        
        # Sort by timestamp (newest first)
        reviews_with_feedback.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return reviews_with_feedback[:limit]