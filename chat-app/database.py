import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Get database credentials from environment variables
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")
INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME")

if not all([DB_USER, DB_PASS, DB_NAME, INSTANCE_CONNECTION_NAME]):
    raise ValueError("One or more database environment variables are not set")

print("Attempting to connect via Cloud SQL Unix Socket...")

try:
    # This is the simple, direct connection string.
    # It connects to the socket created by the --add-cloudsql-instances flag.
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@"
        f"/{DB_NAME}?unix_socket=/cloudsql/{INSTANCE_CONNECTION_NAME}"
    )
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print("✅ Database engine created.")

except Exception as e:
    print(f"❌ Failed to create database engine: {e}")
    raise e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# import os
# import pymysql
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
#  # Import dotenv

# # Load environment variables from .env file
# # from dotenv import load_dotenv
# # load_dotenv()

# # Get database credentials
# DB_USER = os.environ.get("DB_USER")
# DB_PASS = os.environ.get("DB_PASS")
# DB_NAME = os.environ.get("DB_NAME")
# DB_HOST = os.environ.get("DB_HOST") 

# # Ensure all variables are present
# if not all([DB_USER, DB_PASS, DB_NAME, DB_HOST]):
#     # Print which one is missing for easier debugging
#     print(f"DEBUG: USER={bool(DB_USER)}, PASS={bool(DB_PASS)}, NAME={bool(DB_NAME)}, HOST={bool(DB_HOST)}")
#     raise ValueError("One or more database environment variables are not set in .env")

# print(f"Attempting to connect to {DB_HOST}...")

# def get_connection():
#     try:
#         return pymysql.connect(
#             host=DB_HOST,
#             user=DB_USER,
#             password=DB_PASS,
#             database=DB_NAME,
#             port=3306, # Standard MySQL port
#             autocommit=True
#         )
#     except Exception as e:
#         print(f"❌ Failed to connect in pymysql.connect: {e}")
#         raise

# try:
#     # Create the engine using the simple connector
#     engine = create_engine(
#         "mysql+pymysql://",
#         creator=get_connection,
#         pool_pre_ping=True,
#     )
#     print("✅ Database engine created.")
# except Exception as e:
#     print(f"❌ Failed to create database engine: {e}")
#     raise e

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()