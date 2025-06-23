# client/core/__init__.py

from .network import connect_to_server, send_message, start_listening

__all__ = ["connect_to_server", "send_message", "start_listening"]