"""
JSON file manager for persisting conversation sessions
"""

import os
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Union

from simpleaihelper.session import Session

class JSONManager:
    """
    A manager for persisting conversation sessions in JSON files.
    
    This class provides methods for storing, retrieving, and managing
    conversation sessions in a JSON file.
    """
    
    def __init__(
        self, 
        json_path: str, 
        client, 
        session_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the JSON manager.
        
        Args:
            json_path: Path to the JSON file
            client: The AI client instance
            session_id: Optional session ID to load
            **kwargs: Additional parameters
        """
        self.json_path = json_path
        self.client = client
        self.kwargs = kwargs
        
        # Create the JSON file if it doesn't exist
        self._init_json()
        
        # Set or load the session
        self.current_session_id = session_id
        self.current_session = None
        
        if session_id:
            self.load_session(session_id)
    
    def _init_json(self) -> None:
        """
        Initialize the JSON file if it doesn't exist.
        """
        # Create the directory if it doesn't exist
        json_dir = os.path.dirname(self.json_path)
        if json_dir and not os.path.exists(json_dir):
            os.makedirs(json_dir)
        
        # Create the JSON file if it doesn't exist
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump({"sessions": {}}, f, ensure_ascii=False, indent=2)
    
    def _load_data(self) -> Dict[str, Any]:
        """
        Load data from the JSON file.
        
        Returns:
            The loaded data
        """
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If the file is empty or corrupted, create a new data structure
            return {"sessions": {}}
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """
        Save data to the JSON file.
        
        Args:
            data: The data to save
        """
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def view_sessions(self) -> List[Dict[str, Any]]:
        """
        View all available sessions.
        
        Returns:
            List of session information dictionaries
        """
        data = self._load_data()
        
        sessions = []
        for session_id, session_data in data.get("sessions", {}).items():
            sessions.append({
                "session_id": session_id,
                "created_at": session_data.get("created_at", 0),
                "updated_at": session_data.get("updated_at", 0),
                "system_prompt": session_data.get("system_prompt", ""),
                "message_count": len(session_data.get("messages", []))
            })
        
        # Sort by updated_at in descending order
        sessions.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        
        return sessions
    
    def view_session_messages(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        View all messages in a specific session.
        
        Args:
            session_id: ID of the session to view, or current session if None
            
        Returns:
            List of message dictionaries
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return []
        
        data = self._load_data()
        session_data = data.get("sessions", {}).get(session_id, {})
        
        return session_data.get("messages", [])
    
    def load_session(self, session_id: str, update: bool = False) -> "Session":
        """
        Load a session from the JSON file.
        
        Args:
            session_id: ID of the session to load
            update: Whether to generate a new session ID
            
        Returns:
            The loaded Session object
        """
        from ..session import Session
        
        data = self._load_data()
        
        if session_id not in data.get("sessions", {}):
            raise ValueError(f"Session with ID {session_id} not found")
        
        session_data = data["sessions"][session_id]
        
        # Create a new session
        system_prompt = session_data.get("system_prompt", "")
        self.current_session = Session(self.client, system_prompt, **self.kwargs)
        
        # If update is True, generate a new session ID
        if update:
            self.current_session_id = self.current_session.session_id
        else:
            self.current_session_id = session_id
            self.current_session.session_id = session_id
            
        # Set the session creation time
        self.current_session.created_at = session_data.get("created_at", time.time())
        
        # Set the messages
        self.current_session.messages = session_data.get("messages", [])
        
        return self.current_session
    
    def save_session(self, session) -> None:
        """
        Save a session to the JSON file.
        
        Args:
            session: The Session object to save
        """
        data = self._load_data()
        
        # Ensure sessions dict exists
        if "sessions" not in data:
            data["sessions"] = {}
        
        now = time.time()
        
        # Extract system prompt
        system_prompt = ""
        if session.messages and session.messages[0]["role"] == "system":
            system_prompt = session.messages[0]["content"]
        
        # Update the session data
        data["sessions"][session.session_id] = {
            "created_at": session.created_at,
            "updated_at": now,
            "system_prompt": system_prompt,
            "messages": session.messages
        }
        
        # Save the data
        self._save_data(data)
        
        # Update the current session ID
        self.current_session_id = session.session_id
        self.current_session = session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from the JSON file.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if successful, False otherwise
        """
        data = self._load_data()
        
        if "sessions" not in data or session_id not in data["sessions"]:
            return False
        
        # Delete the session
        del data["sessions"][session_id]
        
        # Save the data
        self._save_data(data)
        
        # Reset current session if it was deleted
        if self.current_session_id == session_id:
            self.current_session_id = None
            self.current_session = None
            
        return True 