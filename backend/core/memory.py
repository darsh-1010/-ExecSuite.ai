"""
Shared memory system for the agent organization.
Tracks chat history, the shared blackboard, and performs safe file operations.
"""

import logging
import os
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SharedMemory:
    """
    Centralized blackboard, chat history, and filesystem workspace for the agent organization.
    """

    def __init__(self, workspace_dir: str = "workspace") -> None:
        """
        Initialize the SharedMemory manager.

        Args:
            workspace_dir: Path to the workspace directory.
        """
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace_dir, exist_ok=True)

        self.messages: List[Dict[str, Any]] = []
        self.blackboard: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []

        # Callbacks for real-time streaming updates (e.g. SSE to frontend)
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []

        logger.info(f"[MEMORY_INIT] Workspace path: {self.workspace_dir}")

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback function to receive real-time updates.

        Args:
            callback: The callback function to run on update.
        """
        self.callbacks.append(callback)

    def _trigger_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Notify all registered callbacks of an event.

        Args:
            event_type: Type of event triggered.
            data: Payload details of the event.
        """
        payload = {"event": event_type, "data": data}
        for cb in self.callbacks:
            try:
                cb(payload)
            except Exception as ex:
                logger.error(f"[CALLBACK_ERROR] Error: {ex}")

    def add_message(self, sender: str, role: str, content: str) -> None:
        """
        Add a conversation message to history and trigger real-time update.

        Args:
            sender: The name of the sender.
            role: The role of the sender.
            content: The text content of the message.
        """
        msg = {
            "index": len(self.messages),
            "sender": sender,
            "role": role,
            "content": content
        }
        self.messages.append(msg)
        # Content snippet is safe to log as it doesn't contain user/auth secrets in normal flow,
        # but we truncate for log clean-up.
        logger.info(f"[MESSAGE_ADDED] Role: {role} | Sender: {sender} | Content: {content[:100]}...")
        self._trigger_update("message", msg)

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get the full message history.

        Returns:
            List of message dictionaries.
        """
        return self.messages

    def set_blackboard(self, key: str, value: Any) -> None:
        """
        Set a value on the shared blackboard.

        Args:
            key: Blackboard variable name.
            value: Value to assign.
        """
        self.blackboard[key] = value
        self._trigger_update("blackboard", {"key": key, "value": value})

    def get_blackboard(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the shared blackboard.

        Args:
            key: Blackboard variable name.
            default: Default value if key is missing.

        Returns:
            The value associated with the key, or default.
        """
        return self.blackboard.get(key, default)

    def log_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a system/orchestration event (e.g. stage transition).

        Args:
            event_type: The type category of the event.
            message: Descriptive event message.
            details: Extra metadata for the event.
        """
        log_entry = {
            "time": len(self.logs),
            "type": event_type,
            "message": message,
            "details": details or {}
        }
        self.logs.append(log_entry)
        logger.info(f"[EVENT_LOGGED] Event type: {event_type} | Message: {message}")
        self._trigger_update("event", log_entry)

    # --- Safe File Operations ---

    def _safe_path(self, filename: str) -> str:
        """
        Resolve and verify that the path is inside the workspace_dir to prevent path traversal.

        Args:
            filename: Relative or absolute path of the file.

        Returns:
            The resolved absolute path if safe.
        """
        # Clean the filename to prevent relative paths escaping
        # Or allow subdirectories inside the workspace if specified, but verify they resolve under workspace_dir
        target = os.path.abspath(os.path.join(self.workspace_dir, filename))
        if not target.startswith(self.workspace_dir):
            raise PermissionError(
                f"Access denied: Path {target} is outside of the workspace directory {self.workspace_dir}"
            )
        return target

    def write_file(self, filename: str, content: str) -> str:
        """
        Write a file to the workspace safely.

        Args:
            filename: Name of the file inside the workspace.
            content: Text contents of the file.

        Returns:
            The resolved absolute path of the written file.
        """
        filepath = self._safe_path(filename)
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"[FILE_WRITTEN] Filename: {filename}")

        file_info = {
            "filename": filename,
            "size": len(content),
            "action": "write"
        }
        self._trigger_update("file", file_info)
        return filepath

    def read_file(self, filename: str) -> str:
        """
        Read a file from the workspace safely.

        Args:
            filename: Name of the file inside the workspace.

        Returns:
            The contents of the file as a string.
        """
        filepath = self._safe_path(filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filename} not found in workspace.")

        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all files in the workspace with metadata.

        Returns:
            List of dictionaries containing file metadata.
        """
        files_list = []
        for root, _, files in os.walk(self.workspace_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, self.workspace_dir)
                # Skip system or hidden files
                if rel_path.startswith(".") or "node_modules" in rel_path:
                    continue
                try:
                    stat = os.stat(abs_path)
                    files_list.append({
                        "name": rel_path.replace("\\", "/"),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
                except Exception as ex:
                    logger.error(f"[FILE_STAT_ERROR] Path: {rel_path} | Error: {ex}")
        return files_list

    def clear(self) -> None:
        """
        Clear short term conversation history and logs.
        """
        self.messages.clear()
        self.blackboard.clear()
        self.logs.clear()
        logger.info("[MEMORY_CLEARED]")
