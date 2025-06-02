#!/usr/bin/env python3
"""
Database migration script to add consultation response fields.
This adds declined_at and response_message columns to the consultations table.
"""

import os
import sys
import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.sql import func
from central_system.models.base import get_db_engine, get_db
from central_system.models.consultation import Consultation, ConsultationStatus
from alembic import op
import sqlalchemy as sa

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def upgrade():
    """
    Upgrade database schema to add new consultation response fields.
    """
    logger.info("Starting database schema upgrade for consultation response fields")
    
    try:
        engine = get_db_engine()
        
        # Check if declined_at column already exists
        inspector = sa.inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('consultations')]
        
        if 'declined_at' not in columns:
            logger.info("Adding declined_at column to consultations table")
            op.add_column('consultations', sa.Column('declined_at', sa.DateTime, nullable=True))
        
        if 'response_message' not in columns:
            logger.info("Adding response_message column to consultations table")
            op.add_column('consultations', sa.Column('response_message', sa.String, nullable=True))
        
        # Update status enum to include new statuses
        # This is trickier as SQLite doesn't support direct enum updates
        # For simplicity, we'll rely on the updated model class to handle this
        # When the application starts with the updated model definitions
        
        logger.info("Schema upgrade completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during schema upgrade: {str(e)}")
        return False

def downgrade():
    """
    Downgrade database schema by removing new consultation response fields.
    """
    logger.info("Starting database schema downgrade to remove consultation response fields")
    
    try:
        # Remove new columns
        op.drop_column('consultations', 'declined_at')
        op.drop_column('consultations', 'response_message')
        
        logger.info("Schema downgrade completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during schema downgrade: {str(e)}")
        return False

def main():
    """
    Main function to run the migration.
    """
    logger.info("Starting consultation response fields migration")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        success = downgrade()
    else:
        success = upgrade()
        
    if success:
        logger.info("Migration completed successfully")
        return 0
    else:
        logger.error("Migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 