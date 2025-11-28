"""
Cloud Function for daily contest automation tasks.
Triggered by Cloud Scheduler to:
1. Calculate and finalize daily contest winners
2. Reset vote counters for new day
3. Archive old submissions
"""

import os
import functions_framework
from datetime import datetime, timedelta
from google.cloud import secretmanager
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def get_db_connection():
    """Create database connection using Cloud SQL."""
    db_user = os.environ.get('DB_USER', 'art_everyday_user')
    db_name = os.environ.get('DB_NAME', 'art_everyday')
    db_socket_dir = os.environ.get('DB_SOCKET_DIR', '/cloudsql')
    cloud_sql_connection_name = os.environ['CLOUD_SQL_CONNECTION_NAME']
    
    # Get password from Secret Manager
    project_id = os.environ.get('GCP_PROJECT')
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/db-password/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    db_pass = response.payload.data.decode('UTF-8')
    
    # Create engine
    engine = create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={"unix_sock": f"{db_socket_dir}/{cloud_sql_connection_name}/.s.PGSQL.5432"}
        ),
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
    )
    
    return engine


@functions_framework.http
def finalize_daily_contest(request):
    """
    HTTP Cloud Function to finalize daily contest results.
    Expected to be triggered by Cloud Scheduler at end of day.
    """
    try:
        engine = get_db_connection()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get yesterday's date
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Query submissions from yesterday
        query = text("""
            SELECT id, user_id, score, first_place_votes, second_place_votes, third_place_votes
            FROM submission
            WHERE DATE(contest_date) = :contest_date
            ORDER BY score DESC
            LIMIT 3
        """)
        
        results = session.execute(query, {"contest_date": yesterday}).fetchall()
        
        if len(results) > 0:
            # Update user win counters
            for i, result in enumerate(results):
                user_id = result[1]
                
                if i == 0:  # First place
                    update_query = text("""
                        UPDATE user 
                        SET first_place_wins = first_place_wins + 1
                        WHERE id = :user_id
                    """)
                elif i == 1:  # Second place
                    update_query = text("""
                        UPDATE user 
                        SET second_place_wins = second_place_wins + 1
                        WHERE id = :user_id
                    """)
                elif i == 2:  # Third place
                    update_query = text("""
                        UPDATE user 
                        SET third_place_wins = third_place_wins + 1
                        WHERE id = :user_id
                    """)
                
                session.execute(update_query, {"user_id": user_id})
            
            session.commit()
            
            return {
                "status": "success",
                "message": f"Finalized contest for {yesterday}",
                "winners_count": len(results)
            }, 200
        else:
            return {
                "status": "no_submissions",
                "message": f"No submissions found for {yesterday}"
            }, 200
            
    except Exception as e:
        print(f"Error finalizing contest: {e}")
        return {
            "status": "error",
            "message": str(e)
        }, 500
    finally:
        if session:
            session.close()


@functions_framework.http
def cleanup_old_data(request):
    """
    HTTP Cloud Function to clean up old data.
    Can be triggered periodically to archive or delete old submissions.
    """
    try:
        engine = get_db_connection()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Delete votes older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        delete_query = text("""
            DELETE FROM vote
            WHERE contest_date < :cutoff_date
        """)
        
        result = session.execute(delete_query, {"cutoff_date": cutoff_date})
        deleted_count = result.rowcount
        session.commit()
        
        return {
            "status": "success",
            "message": f"Cleaned up old data",
            "deleted_votes": deleted_count
        }, 200
        
    except Exception as e:
        print(f"Error cleaning up data: {e}")
        return {
            "status": "error",
            "message": str(e)
        }, 500
    finally:
        if session:
            session.close()
