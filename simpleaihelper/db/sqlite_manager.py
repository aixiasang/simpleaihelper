"""
SQLite database manager for persisting conversation sessions
"""

import os
import json
import sqlite3
import time
from typing import List, Dict, Any, Optional, Tuple, Union

from simpleaihelper.session import Session

class SQLiteManager:
    """
    A manager for persisting conversation sessions in SQLite.
    
    This class provides methods for storing, retrieving, and managing
    conversation sessions in a SQLite database.
    """
    
    def __init__(
        self, 
        db_path: str, 
        client, 
        table: str = "ai_message", 
        session_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the SQLite manager.
        
        Args:
            db_path: Path to the SQLite database file
            client: The AI client instance
            table: Name of the table to use
            session_id: Optional session ID to load
            **kwargs: Additional parameters
        """
        self.db_path = db_path
        self.client = client
        self.table = table
        self.kwargs = kwargs
        
        # Create the database and table if they don't exist
        self._init_db()
        
        # Set or load the session
        self.current_session_id = session_id
        self.current_session = None
        
        if session_id:
            self.load_session(session_id)
    
    def _init_db(self) -> None:
        """
        Initialize the database and create tables if they don't exist.
        """
        # Create the directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create the sessions table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at REAL,
            updated_at REAL,
            system_prompt TEXT
        )
        ''')
        
        # Create the messages table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {self.table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def view_sessions(self) -> List[Dict[str, Any]]:
        """
        View all available sessions.
        
        Returns:
            List of session information dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
        SELECT id, created_at, updated_at, system_prompt FROM sessions
        ORDER BY updated_at DESC
        ''')
        
        sessions = []
        for row in cursor.fetchall():
            session_id, created_at, updated_at, system_prompt = row
            
            # Count messages in this session
            cursor.execute(f'''
            SELECT COUNT(*) FROM {self.table} WHERE session_id = ?
            ''', (session_id,))
            message_count = cursor.fetchone()[0]
            
            sessions.append({
                "session_id": session_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "system_prompt": system_prompt,
                "message_count": message_count
            })
        
        conn.close()
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
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
        SELECT role, content, created_at FROM {self.table}
        WHERE session_id = ?
        ORDER BY id
        ''', (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            role, content, created_at = row
            messages.append({
                "role": role,
                "content": content,
                "created_at": created_at
            })
        
        conn.close()
        return messages
    
    def load_session(self, session_id: str, update: bool = False) -> "Session":
        """
        Load a session from the database.
        
        Args:
            session_id: ID of the session to load
            update: Whether to generate a new session ID
            
        Returns:
            The loaded Session object
        """
        from ..session import Session
        
        # Get session details
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
        SELECT system_prompt FROM sessions
        WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Session with ID {session_id} not found")
            
        system_prompt = row[0]
        
        # Get messages
        cursor.execute(f'''
        SELECT role, content FROM {self.table}
        WHERE session_id = ?
        ORDER BY id
        ''', (session_id,))
        
        messages = [{"role": role, "content": content} for role, content in cursor.fetchall()]
        
        conn.close()
        
        # Create a new session
        self.current_session = Session(self.client, system_prompt, **self.kwargs)
        
        # If update is True, generate a new session ID
        if update:
            self.current_session_id = self.current_session.session_id
        else:
            self.current_session_id = session_id
            self.current_session.session_id = session_id
            
        # Set the messages
        self.current_session.messages = messages
        
        return self.current_session
    
    def save_session(self, session) -> None:
        """
        Save a session to the database.
        
        Args:
            session: The Session object to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = time.time()
        
        # Check if the session exists
        cursor.execute(f'''
        SELECT id FROM sessions WHERE id = ?
        ''', (session.session_id,))
        
        if cursor.fetchone():
            # Update the session
            cursor.execute(f'''
            UPDATE sessions
            SET updated_at = ?
            WHERE id = ?
            ''', (now, session.session_id))
        else:
            # Insert a new session
            system_prompt = ""
            if session.messages and session.messages[0]["role"] == "system":
                system_prompt = session.messages[0]["content"]
                
            cursor.execute(f'''
            INSERT INTO sessions (id, created_at, updated_at, system_prompt)
            VALUES (?, ?, ?, ?)
            ''', (session.session_id, session.created_at, now, system_prompt))
        
        # Delete existing messages for this session
        cursor.execute(f'''
        DELETE FROM {self.table} WHERE session_id = ?
        ''', (session.session_id,))
        
        # Insert messages
        for message in session.messages:
            cursor.execute(f'''
            INSERT INTO {self.table} (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            ''', (session.session_id, message["role"], message["content"], now))
        
        conn.commit()
        conn.close()
        
        # Update the current session ID
        self.current_session_id = session.session_id
        self.current_session = session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from the database.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete messages
            cursor.execute(f'''
            DELETE FROM {self.table} WHERE session_id = ?
            ''', (session_id,))
            
            # Delete session
            cursor.execute(f'''
            DELETE FROM sessions WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
            
            # Reset current session if it was deleted
            if self.current_session_id == session_id:
                self.current_session_id = None
                self.current_session = None
                
            return True
            
        except Exception as e:
            conn.rollback()
            return False
            
        finally:
            conn.close() 