from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

class Env(ABC):
    """Base class for agent environments."""
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the list of tool definitions for this environment."""
        pass
    
    @abstractmethod
    def get_handlers(self) -> Dict[str, callable]:
        """Return a dictionary mapping tool names to handler functions."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this environment."""
        pass
    
    @abstractmethod
    def get_agent_folder(self) -> str:
        """Return the folder path for this environment."""
        pass
    
    def initialize(self):
        """Initialize the environment (create folders, etc.)."""
        folder = self.get_agent_folder()
        if folder:  # Only create folder if path is not empty
            folder_path = Path(folder)
            if not folder_path.exists():
                folder_path.mkdir(parents=True)
            return folder_path
        return None
    
    def get_name(self) -> str:
        """Return a human-readable name for this environment."""
        return self.__class__.__name__

