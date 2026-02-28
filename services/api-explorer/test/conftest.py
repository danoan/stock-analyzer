import os

# Use an in-memory database for tests
os.environ["DB_PATH"] = ":memory:"
