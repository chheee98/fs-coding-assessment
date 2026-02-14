# Models package — import all models so SQLAlchemy resolves relationships at startup.
from app.models.user import User  # noqa: F401
from app.models.todo import Todo  # noqa: F401
