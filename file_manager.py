# file_manager.py

import os
from database import Database
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import threading

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_manager):
        self.file_manager = file_manager

    def on_moved(self, event):
        if not event.is_directory:
            # Check if the old path exists in our database
            old_path = event.src_path
            new_path = event.dest_path
            self.file_manager.update_file_path(old_path, new_path)

class FileManager:
    def __init__(self, db: Database):
        """
        Handles adding, listing, and removing files in the database.
        """
        self.db = db
        self.observer = None
        self.monitoring = False
        self.start_file_monitoring()

    def start_file_monitoring(self):
        """
        Start monitoring file system changes
        """
        if not self.monitoring:
            self.observer = Observer()
            event_handler = FileChangeHandler(self)
            # Monitor the root directory of all files in the database
            paths_to_watch = self._get_watched_directories()
            for path in paths_to_watch:
                self.observer.schedule(event_handler, path, recursive=False)
            self.observer.start()
            self.monitoring = True

    def stop_file_monitoring(self):
        """
        Stop monitoring file system changes
        """
        if self.monitoring and self.observer:
            self.observer.stop()
            self.observer.join()
            self.monitoring = False

    def _get_watched_directories(self):
        """
        Get unique directories of all files in the database
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT file_path FROM files")
        paths = cursor.fetchall()
        directories = set()
        for (path,) in paths:
            dir_path = os.path.dirname(path)
            if dir_path and os.path.exists(dir_path):
                directories.add(dir_path)
        return directories

    def update_file_path(self, old_path: str, new_path: str):
        """
        Update the file path in the database when a file is moved
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE files 
            SET file_path = ?, name = ?
            WHERE file_path = ?
        """, (new_path, os.path.basename(new_path), old_path))
        conn.commit()
        self.log_action(f"Updated file path from {old_path} to {new_path}")

    def verify_file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists at the given path
        """
        return os.path.exists(file_path)

    def verify_all_files(self):
        """
        Verify all files in the database and update paths if needed.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, file_path FROM files")
        files = cursor.fetchall()
        
        for file_id, file_path in files:
            if not os.path.exists(file_path):
                # Try to find the file in the same directory
                filename = os.path.basename(file_path)
                directory = os.path.dirname(file_path)
                if os.path.exists(os.path.join(directory, filename)):
                    new_path = os.path.join(directory, filename)
                    cursor.execute(
                        "UPDATE files SET file_path=? WHERE id=?",
                        (new_path, file_id)
                    )
                    conn.commit()

    def add_file(self, file_path: str, metadata: str = "") -> int:
        """
        Add a new file to the database.
        Returns the ID of the newly added file.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (name, file_path, metadata) VALUES (?, ?, ?)",
            (os.path.basename(file_path), file_path, metadata)
        )
        conn.commit()
        return cursor.lastrowid

    def remove_file(self, file_id: int):
        """
        Remove a file from the database.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE id=?", (file_id,))
        conn.commit()

    def list_files(self) -> list:
        """
        List all files in the database.
        Returns a list of tuples (id, name, file_path, metadata).
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, file_path, metadata FROM files")
        return cursor.fetchall()

    def get_file(self, file_id: int) -> tuple:
        """
        Get file information by ID.
        Returns a tuple (id, name, file_path, metadata) or None if not found.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, file_path, metadata FROM files WHERE id=?",
            (file_id,)
        )
        return cursor.fetchone()

    def log_action(self, action: str):
        """
        Helper method to log actions to the 'logs' table.
        """
        conn = self.db.get_connection()
        conn.execute("INSERT INTO logs (action) VALUES (?)", (action,))
        conn.commit()
