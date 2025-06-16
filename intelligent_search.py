"""
Intelligent search functionality using fuzzy matching and semantic understanding
"""

from fuzzywuzzy import fuzz, process
from typing import List, Dict, Any, Tuple
import re


class IntelligentSearch:
    """Enhanced search with fuzzy matching and natural language understanding"""
    
    def __init__(self):
        # Keywords mapped to categories and use cases
        self.category_keywords = {
            'chatbot': ['chat', 'conversation', 'messaging', 'talk', 'dialogue', 'communicate'],
            'coding': ['code', 'programming', 'development', 'developer', 'software', 'github', 'coding', 'programming'],
            'writing': ['write', 'content', 'text', 'blog', 'article', 'copy', 'editor', 'writing'],
            'design': ['design', 'ui', 'ux', 'graphics', 'visual', 'creative', 'logo', 'branding'],
            'productivity': ['productivity', 'workflow', 'automation', 'organize', 'task', 'management'],
            'analytics': ['analytics', 'data', 'insights', 'reporting', 'metrics', 'dashboard'],
            'customer_service': ['customer', 'support', 'service', 'help', 'assistance'],
            'marketing': ['marketing', 'advertising', 'promotion', 'campaign', 'social media'],
            'voice': ['voice', 'speech', 'audio', 'sound', 'speak', 'talk', 'dictation'],
            'image': ['image', 'photo', 'picture', 'visual', 'art', 'generate', 'create'],
            'video': ['video', 'movie', 'film', 'animation', 'editing'],
            'research': ['research', 'analysis', 'study', 'investigation', 'explore'],
            'education': ['education', 'learning', 'teaching', 'tutorial', 'training'],
            'translation': ['translate', 'language', 'multilingual', 'localization'],
            'automation': ['automation', 'workflow', 'process', 'auto', 'schedule'],
            'email': ['email', 'mail', 'message', 'communication', 'inbox'],
            'sales': ['sales', 'crm', 'lead', 'prospect', 'revenue', 'selling'],
            'finance': ['finance', 'financial', 'money', 'budget', 'accounting', 'investment'],
            'legal': ['legal', 'law', 'contract', 'compliance', 'regulation'],
            'healthcare': ['health', 'medical', 'doctor', 'patient', 'medicine'],
            'gaming': ['game', 'gaming', 'play', 'entertainment', 'interactive'],
            'search': ['search', 'find', 'discover', 'explore', 'lookup'],
            'scheduling': ['schedule', 'calendar', 'appointment', 'meeting', 'time'],
            'ai_framework': ['framework', 'ai', 'machine learning', 'ml', 'neural', 'model'],
            'web3': ['web3', 'blockchain', 'crypto', 'nft', 'defi', 'ethereum'],
            'digital_worker': ['worker', 'employee', 'assistant', 'virtual', 'digital'],
            'agents': ['agent', 'ai agent', 'autonomous', 'intelligent']
        }
        
        # Platform keywords
        self.platform_keywords = {
            'web': ['web', 'browser', 'online', 'website', 'internet'],
            'api': ['api', 'integration', 'connect', 'endpoint'],
            'desktop': ['desktop', 'computer', 'pc', 'software'],
            'mobile': ['mobile', 'phone', 'app', 'ios', 'android'],
            'cloud': ['cloud', 'saas', 'service', 'hosted'],
            'open_source': ['open source', 'github', 'free', 'community'],
            'enterprise': ['enterprise', 'business', 'corporate', 'professional']
        }
        
        # Use case keywords
        self.use_case_keywords = {
            'content_creation': ['content', 'create', 'generate', 'write', 'produce'],
            'data_analysis': ['data', 'analysis', 'analytics', 'insights', 'report'],
            'customer_support': ['support', 'help', 'customer', 'service', 'assistance'],
            'automation': ['automation', 'automate', 'workflow', 'process'],
            'research': ['research', 'study', 'investigate', 'analyze'],
            'communication': ['communication', 'chat', 'message', 'talk'],
            'development': ['development', 'coding', 'programming', 'software'],
            'design': ['design', 'creative', 'visual', 'graphics'],
            'education': ['education', 'learning', 'teaching', 'training'],
            'entertainment': ['entertainment', 'fun', 'game', 'play']
        }
    
    def extract_intent(self, query: str) -> Dict[str, List[str]]:
        """Extract user intent from natural language query"""
        query_lower = query.lower().strip()
        intent = {
            'categories': [],
            'platforms': [],
            'use_cases': [],
            'keywords': []
        }
        
        # Extract categories
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent['categories'].append(category)
                    break
        
        # Extract platforms
        for platform, keywords in self.platform_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent['platforms'].append(platform)
                    break
        
        # Extract use cases
        for use_case, keywords in self.use_case_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent['use_cases'].append(use_case)
                    break
        
        # Extract individual keywords (remove common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must'}
        words = re.findall(r'\b\w+\b', query_lower)
        intent['keywords'] = [word for word in words if word not in common_words and len(word) > 2]
        
        return intent
    
    def calculate_relevance_score(self, agent: Any, query: str, intent: Dict[str, List[str]]) -> float:
        """Calculate relevance score for an agent based on query and intent"""
        score = 0.0
        
        # Direct name matching (highest weight)
        name_score = fuzz.partial_ratio(query.lower(), agent.name.lower()) / 100.0
        score += name_score * 3.0
        
        # Creator matching
        creator_score = fuzz.partial_ratio(query.lower(), agent.creator.lower()) / 100.0
        score += creator_score * 1.5
        
        # Description matching
        desc_score = fuzz.partial_ratio(query.lower(), agent.short_desc.lower()) / 100.0
        score += desc_score * 2.0
        
        # Long description matching
        long_desc_score = fuzz.partial_ratio(query.lower(), agent.long_desc.lower()) / 100.0
        score += long_desc_score * 1.0
        
        # Category intent matching
        agent_domains = agent.domains.lower().split(',')
        for category in intent['categories']:
            for domain in agent_domains:
                if category in domain or fuzz.partial_ratio(category, domain) > 70:
                    score += 1.5
        
        # Use case intent matching
        agent_use_cases = agent.use_cases.lower().split(',')
        for use_case in intent['use_cases']:
            for agent_use_case in agent_use_cases:
                if use_case in agent_use_case or fuzz.partial_ratio(use_case, agent_use_case) > 70:
                    score += 1.2
        
        # Platform intent matching
        for platform in intent['platforms']:
            if platform in agent.platform.lower() or fuzz.partial_ratio(platform, agent.platform.lower()) > 70:
                score += 1.0
        
        # Keyword matching
        searchable_text = f"{agent.name} {agent.creator} {agent.short_desc} {agent.long_desc} {agent.domains} {agent.use_cases} {agent.platform}".lower()
        for keyword in intent['keywords']:
            if keyword in searchable_text:
                score += 0.8
            else:
                # Fuzzy match for keywords
                words_in_text = re.findall(r'\b\w+\b', searchable_text)
                best_match = process.extractOne(keyword, words_in_text)
                if best_match and best_match[1] > 75:
                    score += 0.5
        
        # Boost score for exact matches in key fields
        if query.lower() in agent.name.lower():
            score += 2.0
        if query.lower() in agent.creator.lower():
            score += 1.0
        
        return score
    
    def search(self, agents: List[Any], query: str, threshold: float = 0.1) -> List[Any]:
        """Perform intelligent search on agents"""
        if not query or not query.strip():
            return agents
        
        query = query.strip()
        intent = self.extract_intent(query)
        
        # Calculate relevance scores
        scored_agents = []
        for agent in agents:
            relevance_score = self.calculate_relevance_score(agent, query, intent)
            if relevance_score > threshold:
                scored_agents.append((agent, relevance_score))
        
        # Sort by relevance score (descending)
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        # Return only the agents (without scores)
        results = [agent for agent, score in scored_agents]
        
        # If no results above threshold, try a more lenient search
        if not results:
            # Try fuzzy matching on names only with lower threshold
            name_matches = []
            for agent in agents:
                name_score = fuzz.partial_ratio(query.lower(), agent.name.lower())
                creator_score = fuzz.partial_ratio(query.lower(), agent.creator.lower())
                if name_score > 50 or creator_score > 60:
                    name_matches.append((agent, max(name_score, creator_score)))
            
            if name_matches:
                name_matches.sort(key=lambda x: x[1], reverse=True)
                results = [agent for agent, score in name_matches[:10]]  # Limit to top 10
        
        return results


# Global instance for use in routes
intelligent_search = IntelligentSearch()