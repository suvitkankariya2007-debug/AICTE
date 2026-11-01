from alembic import context
from app.db import Base, setup
engine,_=setup()
with engine.connect() as connection:
    context.configure(connection=connection,target_metadata=Base.metadata)
    with context.begin_transaction(): context.run_migrations()
