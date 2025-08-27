from .base import Base
from .user import User
from .event import EventNormalized
from .detection import Detection

# Alembic will import Base.metadata from here
def get_metadata():
    return Base.metadata