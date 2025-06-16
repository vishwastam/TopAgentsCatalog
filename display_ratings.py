#!/usr/bin/env python3
"""
Simple rating display system for templates
"""

import json
import random
from typing import Dict, Tuple

class DisplayRatings:
    """Simple class to get rating display data for agents"""
    
    def __init__(self):
        self.ratings_cache = {}
        self._load_ratings()
    
    def _load_ratings(self):
        """Load ratings from JSON file"""
        try:
            with open('ratings.json', 'r') as f:
                ratings_data = json.load(f)
            
            # Process ratings by agent
            agent_ratings = {}
            for rating in ratings_data:
                slug = rating['agent_slug']
                if slug not in agent_ratings:
                    agent_ratings[slug] = []
                agent_ratings[slug].append(rating['rating'])
            
            # Calculate averages and counts
            for slug, ratings in agent_ratings.items():
                avg_rating = sum(ratings) / len(ratings)
                self.ratings_cache[slug] = {
                    'average_rating': round(avg_rating, 1),
                    'review_count': len(ratings),
                    'stars_display': self._generate_stars_display(avg_rating)
                }
                
        except Exception as e:
            print(f"Error loading ratings: {e}")
    
    def _generate_stars_display(self, rating: float) -> str:
        """Generate HTML for star display"""
        full_stars = int(rating)
        half_star = rating - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        stars_html = ""
        
        # Full stars
        for _ in range(full_stars):
            stars_html += '<i class="text-yellow-400 text-sm">★</i>'
        
        # Half star
        if half_star:
            stars_html += '<i class="text-yellow-400 text-sm">☆</i>'
        
        # Empty stars
        for _ in range(empty_stars):
            stars_html += '<i class="text-gray-300 text-sm">☆</i>'
        
        return stars_html
    
    def get_agent_rating_display(self, agent_name: str) -> Dict[str, any]:
        """Get rating display data for an agent"""
        slug = agent_name.lower().replace(' ', '-').replace('.', '').replace('(', '').replace(')', '')
        
        if slug in self.ratings_cache:
            return self.ratings_cache[slug]
        
        # Return default if no rating found
        return {
            'average_rating': 0.0,
            'review_count': 0,
            'stars_display': '<i class="text-gray-300 text-sm">☆☆☆☆☆</i>'
        }

# Global instance for use in templates
display_ratings = DisplayRatings()