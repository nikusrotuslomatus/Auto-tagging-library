# database.py

import os
import sqlite3
import threading

class Database:
    def __init__(self, db_path=None):
        """
        Manages the SQLite connection and schema.
        If no db_path is given, store 'library.db' in the same folder as this file.
        """
        if db_path:
            self.db_path = db_path
        else:
            base_dir = os.path.dirname(__file__)
            self.db_path = os.path.join(base_dir, "library.db")
        self._local = threading.local()

    def get_connection(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.execute("PRAGMA foreign_keys = ON;")
        return self._local.conn

    def connect(self):
        """
        Opens a connection to the SQLite database for the main thread.
        """
        self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._local.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self):
        """
        Commits changes and closes the database connection if open (main thread only).
        """
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.commit()
            self._local.conn.close()
            self._local.conn = None

    def init_schema(self):
        """
        Create or update the schema for the digital library:
         - Files table (with 'name' column)
         - Tags table
         - File-Tags association
         - Logs table
        """
        conn = self.get_connection()
        with conn:
            # Files table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    name TEXT,
                    metadata TEXT
                );
            """)

            # Tags table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT CHECK(type IN ('boolean', 'numeric', 'string')) NOT NULL
                );
            """)

            # Association table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_tags (
                    file_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    value TEXT,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                    PRIMARY KEY (file_id, tag_id)
                );
            """)

            # Logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
