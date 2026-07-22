from app import app, db, Signup, Post, Friends, Contact, Likes, Comments
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

def migrate_database():
    # 1. Connect to Local MySQL
    local_uri = 'mysql+pymysql://root:@localhost/socialmd'
    print("Connecting to local MySQL database...")
    try:
        local_engine = create_engine(local_uri)
        LocalSession = sessionmaker(bind=local_engine)
        local_session = LocalSession()
    except Exception as e:
        print(f"Error connecting to local DB: {e}")
        sys.exit(1)

    print("Fetching local data...")
    # Fetch all data
    users = local_session.query(Signup).all()
    posts = local_session.query(Post).all()
    comments = local_session.query(Comments).all()
    friends = local_session.query(Friends).all()
    contacts = local_session.query(Contact).all()
    likes = local_session.query(Likes).all()

    # Detach objects from local session so they can be pushed to Neon
    all_data = [users, posts, comments, friends, contacts, likes]
    for dataset in all_data:
        for item in dataset:
            local_session.expunge(item)

    print(f"Found: {len(users)} users, {len(posts)} posts, {len(comments)} comments, {len(likes)} likes.")

    local_session.close()

    # 2. Ask for Neon URL
    print("\n-------------------------------------------------")
    print("Please paste your Neon PostgreSQL Connection String.")
    print("It looks like: postgresql://username:password@ep-cold-surf...aws.neon.tech/neondb")
    print("-------------------------------------------------")
    neon_uri = input("Neon URL: ").strip()

    if not neon_uri:
        print("No URL provided. Exiting.")
        sys.exit(1)

    # Neon requires PostgreSQL URL to start with postgresql:// not just postgres:// for SQLAlchemy
    if neon_uri.startswith("postgres://"):
        neon_uri = neon_uri.replace("postgres://", "postgresql://", 1)

    # 3. Connect to Neon and Insert
    print("\nConnecting to Neon Database...")
    try:
        neon_engine = create_engine(neon_uri)
        print("Creating tables in Neon...")
        # Drop existing tables to fix the phone column type issue
        db.metadata.drop_all(neon_engine)
        # Create all tables on the new Neon engine
        db.metadata.create_all(neon_engine)

        print("Migrating data to Neon...")
        NeonSession = sessionmaker(bind=neon_engine)
        neon_session = NeonSession()

        for dataset in all_data:
            for item in dataset:
                neon_session.merge(item)
        
        neon_session.commit()
        print("\n✅ MIGRATION SUCCESSFUL! All your local data is now in Neon.")
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")

if __name__ == '__main__':
    migrate_database()
