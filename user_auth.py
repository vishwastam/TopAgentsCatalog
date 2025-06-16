"""
User authentication system with Google SSO and email/password
Stores user data in JSON files for easy migration to database later
"""

import json
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

class UserAuth:
    def __init__(self, users_file: str = "users.json", sessions_file: str = "user_sessions.json"):
        self.users_file = users_file
        self.sessions_file = sessions_file
        self.users = self._load_users()
        self.sessions = self._load_sessions()
    
    def _load_users(self) -> List[Dict]:
        """Load users from JSON file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"Error loading users: {e}")
            return []
    
    def _save_users(self):
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Error saving users: {e}")
    
    def _load_sessions(self) -> Dict:
        """Load active sessions from JSON file"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading sessions: {e}")
            return {}
    
    def _save_sessions(self):
        """Save sessions to JSON file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Error saving sessions: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def _verify_password(self, password: str, hash_string: str) -> bool:
        """Verify password against hash"""
        try:
            salt, pwd_hash = hash_string.split(':')
            return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() == pwd_hash
        except Exception:
            return False
    
    def create_user(self, email: str, password: Optional[str] = None, google_id: Optional[str] = None, 
                    first_name: str = "", last_name: str = "", profile_image: str = "") -> Dict:
        """Create a new user account"""
        
        # Check if user already exists
        existing_user = self.get_user_by_email(email)
        if existing_user:
            return {"success": False, "error": "User already exists"}
        
        user_id = secrets.token_urlsafe(16)
        user_data = {
            "id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "profile_image": profile_image,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True,
            "auth_method": "google" if google_id else "email",
            "google_id": google_id,
            "password_hash": self._hash_password(password) if password else "",
            "email_verified": bool(google_id),  # Google emails are pre-verified
            "role": "user",
            "preferences": {
                "notifications": True,
                "theme": "light",
                "language": "en"
            }
        }
        
        self.users.append(user_data)
        self._save_users()
        
        return {"success": True, "user": user_data, "is_new_user": True}
    
    def authenticate_user(self, email: str, password: str) -> Dict:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return {"success": False, "error": "User not found"}
        
        if not user["is_active"]:
            return {"success": False, "error": "Account is deactivated"}
        
        if user["auth_method"] == "google":
            return {"success": False, "error": "Please sign in with Google"}
        
        if not user["password_hash"] or not self._verify_password(password, user["password_hash"]):
            return {"success": False, "error": "Invalid password"}
        
        # Update last login
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        return {"success": True, "user": user}
    
    def authenticate_google_user(self, google_id: str, email: str, first_name: str = "", 
                                last_name: str = "", profile_image: str = "") -> Dict:
        """Authenticate or create user with Google SSO"""
        
        # Try to find existing user by Google ID
        user = self.get_user_by_google_id(google_id)
        if user:
            # Update last login and profile info
            user["last_login"] = datetime.now().isoformat()
            user["first_name"] = first_name or user["first_name"]
            user["last_name"] = last_name or user["last_name"]
            user["profile_image"] = profile_image or user["profile_image"]
            self._save_users()
            return {"success": True, "user": user}
        
        # Try to find by email (user might have signed up with email first)
        user = self.get_user_by_email(email)
        if user:
            # Link Google account to existing user
            user["google_id"] = google_id
            user["auth_method"] = "both"  # Can use both methods
            user["email_verified"] = True
            user["last_login"] = datetime.now().isoformat()
            user["first_name"] = first_name or user["first_name"]
            user["last_name"] = last_name or user["last_name"]
            user["profile_image"] = profile_image or user["profile_image"]
            self._save_users()
            return {"success": True, "user": user}
        
        # Create new user with Google
        return self.create_user(
            email=email,
            google_id=google_id,
            first_name=first_name,
            last_name=last_name,
            profile_image=profile_image
        )
    
    def create_session(self, user_id: str) -> str:
        """Create a new session for user"""
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        self.sessions[session_token] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "last_used": datetime.now().isoformat()
        }
        
        self._save_sessions()
        return session_token
    
    def get_user_from_session(self, session_token: str) -> Optional[Dict]:
        """Get user from session token"""
        if not session_token or session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            del self.sessions[session_token]
            self._save_sessions()
            return None
        
        # Update last used time
        session["last_used"] = datetime.now().isoformat()
        self._save_sessions()
        
        # Get user
        user = self.get_user_by_id(session["user_id"])
        return user if user and user["is_active"] else None
    
    def logout_session(self, session_token: str):
        """Remove session (logout)"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            self._save_sessions()
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        for user in self.users:
            if user["email"].lower() == email.lower():
                return user
        return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict]:
        """Get user by Google ID"""
        for user in self.users:
            if user.get("google_id") == google_id:
                return user
        return None
    
    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Don't allow updating certain fields
        protected_fields = ["id", "created_at", "password_hash"]
        for field in protected_fields:
            updates.pop(field, None)
        
        user.update(updates)
        self._save_users()
        return True
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        if user["auth_method"] == "google":
            return {"success": False, "error": "Cannot change password for Google accounts"}
        
        if not self._verify_password(old_password, user["password_hash"]):
            return {"success": False, "error": "Current password is incorrect"}
        
        user["password_hash"] = self._hash_password(new_password)
        self._save_users()
        
        return {"success": True}
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin function)"""
        return self.users
    
    def clean_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_tokens = []
        
        for token, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session["expires_at"])
            if now > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.sessions[token]
        
        if expired_tokens:
            self._save_sessions()

# Initialize global auth instance
user_auth = UserAuth()