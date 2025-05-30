"""
Test suite for AID-001-F: Initial Database Migration

This test verifies that the initial database migration works correctly,
including table creation, relationships, and data integrity.
"""

import os
import sys
import unittest
import tempfile
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Ensure __init__.py files exist
(backend_dir / "app" / "__init__.py").touch()
(backend_dir / "app" / "core" / "__init__.py").touch()
(backend_dir / "app" / "models" / "__init__.py").touch()

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from alembic.config import Config
    from alembic import command
    from app.core.database import Base
    from app.models import (
        User, RefreshToken, Role, Department, 
        LLMConfiguration, DepartmentQuota, UsageLog
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the backend directory and virtual environment is activated")
    sys.exit(1)


class TestAID001F(unittest.TestCase):
    """Test case for Initial Database Migration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and run migration"""
        cls.test_db_name = "aidock_test_python"
        cls.test_db_url = f"postgresql://aidock:aidock@localhost:5432/{cls.test_db_name}"
        
        # Create test database
        try:
            subprocess.run(['createdb', cls.test_db_name], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Database might already exist, drop and recreate
            subprocess.run(['dropdb', cls.test_db_name], capture_output=True)
            subprocess.run(['createdb', cls.test_db_name], check=True, capture_output=True)
        
        # Create test engine
        cls.engine = create_engine(cls.test_db_url)
        cls.SessionClass = sessionmaker(bind=cls.engine)
        
        # Run Alembic migration
        cls.run_migration()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        cls.engine.dispose()
        try:
            subprocess.run(['dropdb', cls.test_db_name], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass  # Database might not exist
    
    @classmethod
    def run_migration(cls):
        """Run the Alembic migration"""
        # Create temporary alembic.ini for testing
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", "alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", cls.test_db_url)
        
        try:
            # Generate migration if not exists
            command.revision(alembic_cfg, autogenerate=True, message="Test initial tables")
            # Apply migration
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            print(f"Migration error: {e}")
            raise
    
    def setUp(self):
        """Set up test session"""
        self.session = self.SessionClass()
    
    def tearDown(self):
        """Clean up test session"""
        self.session.rollback()
        self.session.close()
    
    def test_01_database_connection(self):
        """Test that we can connect to the test database"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            self.assertEqual(result.fetchone()[0], 1)
    
    def test_02_all_tables_exist(self):
        """Test that all expected tables were created"""
        with self.engine.connect() as conn:
            # Get list of tables
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'users', 'refresh_tokens', 'roles', 'departments',
                'llm_configurations', 'department_quotas', 'usage_logs',
                'alembic_version'
            ]
            
            for table in expected_tables:
                self.assertIn(table, tables, f"Table '{table}' not found in database")
    
    def test_03_users_table_structure(self):
        """Test users table structure"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            columns = {row[0]: (row[1], row[2]) for row in result.fetchall()}
            
            # Check required columns exist
            required_columns = ['id', 'username', 'email', 'hashed_password', 'is_active']
            for col in required_columns:
                self.assertIn(col, columns, f"Column '{col}' not found in users table")
            
            # Check data types
            self.assertEqual(columns['username'][0], 'character varying')
            self.assertEqual(columns['email'][0], 'character varying')
            self.assertEqual(columns['is_active'][0], 'boolean')
    
    def test_04_foreign_key_relationships(self):
        """Test that foreign key relationships are properly created"""
        with self.engine.connect() as conn:
            # Check foreign keys in users table
            result = conn.execute(text("""
                SELECT 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'users'
            """))
            
            foreign_keys = list(result.fetchall())
            self.assertGreater(len(foreign_keys), 0, "No foreign keys found in users table")
    
    def test_05_create_sample_data(self):
        """Test creating sample data in all tables"""
        try:
            # Create role
            role = Role(name="test_admin", description="Test admin role", permissions=["*"])
            self.session.add(role)
            self.session.flush()
            
            # Create department
            department = Department(name="test_dept", description="Test department")
            self.session.add(department)
            self.session.flush()
            
            # Create user
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password_here",
                role_id=role.id,
                department_id=department.id
            )
            self.session.add(user)
            self.session.flush()
            
            # Create LLM configuration
            llm_config = LLMConfiguration(
                model_name="test-gpt-4",
                provider="openai",
                enabled=True,
                config_json={"temperature": 0.7}
            )
            self.session.add(llm_config)
            self.session.flush()
            
            # Create department quota
            quota = DepartmentQuota(
                department_id=department.id,
                llm_config_id=llm_config.id,
                monthly_limit_tokens=100000,
                current_usage_tokens=0
            )
            self.session.add(quota)
            self.session.flush()
            
            # Create refresh token
            refresh_token = RefreshToken(
                user_id=user.id,
                token_hash="test_token_hash",
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            self.session.add(refresh_token)
            self.session.flush()
            
            # Create usage log
            usage_log = UsageLog(
                user_id=user.id,
                department_id=department.id,
                llm_config_id=llm_config.id,
                tokens_prompt=50,
                tokens_completion=100,
                cost_estimated=0.0025
            )
            self.session.add(usage_log)
            
            # Commit all changes
            self.session.commit()
            
            # Verify data was created
            self.assertIsNotNone(user.id)
            self.assertIsNotNone(role.id)
            self.assertIsNotNone(department.id)
            self.assertIsNotNone(llm_config.id)
            self.assertIsNotNone(quota.id)
            self.assertIsNotNone(refresh_token.id)
            self.assertIsNotNone(usage_log.id)
            
        except Exception as e:
            self.session.rollback()
            self.fail(f"Failed to create sample data: {e}")
    
    def test_06_model_relationships(self):
        """Test that model relationships work correctly"""
        # Create test data first
        role = Role(name="test_role", permissions=["read"])
        department = Department(name="test_dept")
        user = User(
            username="testuser2",
            email="test2@example.com", 
            hashed_password="hash",
            role=role,
            department=department
        )
        
        self.session.add_all([role, department, user])
        self.session.commit()
        
        # Test relationships
        self.assertEqual(user.role.name, "test_role")
        self.assertEqual(user.department.name, "test_dept")
        self.assertIn(user, role.users)
        self.assertIn(user, department.users)
    
    def test_07_model_methods(self):
        """Test model utility methods"""
        role = Role(name="admin", permissions=["*"])
        department = Department(name="IT")
        user = User(
            username="admin_user",
            email="admin@example.com",
            hashed_password="hash",
            role=role,
            department=department,
            is_superuser=True
        )
        
        self.session.add_all([role, department, user])
        self.session.commit()
        
        # Test user methods
        self.assertTrue(user.is_admin())
        self.assertTrue(user.can_access_model("gpt-4"))
        self.assertTrue(user.has_permission("any_permission"))
        self.assertEqual(user.display_name, "admin_user")
        self.assertTrue(user.is_department_member)
    
    def test_08_refresh_token_methods(self):
        """Test RefreshToken utility methods"""
        user = User(
            username="token_user",
            email="token@example.com",
            hashed_password="hash"
        )
        self.session.add(user)
        self.session.flush()
        
        # Create non-expired token
        token = RefreshToken(
            user_id=user.id,
            token_hash="valid_token",
            expires_at=datetime.utcnow() + timedelta(days=7),
            remember_me=True
        )
        self.session.add(token)
        self.session.commit()
        
        # Test token methods
        self.assertFalse(token.is_expired())
        self.assertTrue(token.is_valid())
        self.assertTrue(token.is_remember_me_token)
        self.assertGreater(token.days_until_expiry, 0)
        
        # Test revoke
        token.revoke()
        self.assertFalse(token.is_valid())
    
    def test_09_indexes_exist(self):
        """Test that important indexes were created"""
        with self.engine.connect() as conn:
            # Check for indexes on important columns
            result = conn.execute(text("""
                SELECT indexname, tablename, indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND tablename IN ('users', 'refresh_tokens', 'usage_logs')
            """))
            
            indexes = list(result.fetchall())
            self.assertGreater(len(indexes), 0, "No indexes found on key tables")
            
            # Check for specific indexes (username, email should be indexed)
            index_definitions = [idx[2] for idx in indexes]
            index_string = ' '.join(index_definitions)
            self.assertIn('username', index_string)
            self.assertIn('email', index_string)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAID001F)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 60)
    print("AID-001-F: Initial Database Migration - Python Test Suite")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n🎉 All Python tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some Python tests failed!")
        sys.exit(1)
