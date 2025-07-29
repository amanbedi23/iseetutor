#!/bin/bash

# Database Initialization Script for ISEE Tutor
# This script initializes the RDS PostgreSQL database with schema and seed data

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-dev}"
PROJECT_NAME="iseetutor"

# Functions
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Get database connection details
get_db_connection() {
    cd ../environments/${ENVIRONMENT}
    
    DB_ENDPOINT=$(terraform output -raw db_instance_endpoint 2>/dev/null || echo "")
    DB_NAME=$(terraform output -raw db_instance_name 2>/dev/null || echo "iseetutor")
    DB_USERNAME=$(terraform output -raw db_instance_username 2>/dev/null || echo "iseetutor_admin")
    DB_PASSWORD=$(aws ssm get-parameter \
        --name "/${PROJECT_NAME}/${ENVIRONMENT}/rds/password" \
        --with-decryption \
        --query 'Parameter.Value' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$DB_ENDPOINT" ] || [ -z "$DB_PASSWORD" ]; then
        print_error "Could not retrieve database connection details"
        exit 1
    fi
    
    # Extract host and port
    DB_HOST=$(echo $DB_ENDPOINT | cut -d: -f1)
    DB_PORT=$(echo $DB_ENDPOINT | cut -d: -f2)
    
    export PGPASSWORD=$DB_PASSWORD
    print_status "Retrieved database connection details"
}

# Create database schemas
create_schemas() {
    print_info "Creating database schemas..."
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME << EOF
-- Create schemas
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS content;

-- Set default search path
ALTER DATABASE $DB_NAME SET search_path TO app, public;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Grant permissions
GRANT ALL ON SCHEMA app TO $DB_USERNAME;
GRANT ALL ON SCHEMA analytics TO $DB_USERNAME;
GRANT ALL ON SCHEMA content TO $DB_USERNAME;

-- Create custom types
DO \$\$ BEGIN
    CREATE TYPE user_role AS ENUM ('student', 'parent', 'teacher', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END \$\$;

DO \$\$ BEGIN
    CREATE TYPE question_type AS ENUM ('multiple_choice', 'essay', 'fill_blank', 'true_false');
EXCEPTION
    WHEN duplicate_object THEN null;
END \$\$;

DO \$\$ BEGIN
    CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard');
EXCEPTION
    WHEN duplicate_object THEN null;
END \$\$;

DO \$\$ BEGIN
    CREATE TYPE subject_type AS ENUM ('math', 'reading', 'writing', 'verbal');
EXCEPTION
    WHEN duplicate_object THEN null;
END \$\$;

COMMIT;
EOF
    
    print_status "Database schemas created"
}

# Create indexes for performance
create_indexes() {
    print_info "Creating performance indexes..."
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME << EOF
-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON app.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON app.users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON app.users(role);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON app.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON app.sessions(created_at);

-- Progress indexes
CREATE INDEX IF NOT EXISTS idx_progress_user_id ON app.progress(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_subject ON app.progress(subject);
CREATE INDEX IF NOT EXISTS idx_progress_updated_at ON app.progress(updated_at);

-- Question indexes
CREATE INDEX IF NOT EXISTS idx_questions_subject ON app.questions(subject);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON app.questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_type ON app.questions(question_type);

-- Quiz indexes
CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON app.quizzes(user_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_created_at ON app.quizzes(created_at);

-- Full text search indexes
CREATE INDEX IF NOT EXISTS idx_questions_content_search ON app.questions USING gin(to_tsvector('english', question_text));
CREATE INDEX IF NOT EXISTS idx_content_search ON app.content USING gin(to_tsvector('english', content));

COMMIT;
EOF
    
    print_status "Performance indexes created"
}

# Create initial data
seed_initial_data() {
    print_info "Seeding initial data..."
    
    # Create Python script for seeding
    cat > /tmp/seed_data.py << 'EOF'
import os
import sys
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
import bcrypt

# Database connection
conn_params = {
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT'),
    'database': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USERNAME'),
    'password': os.environ.get('PGPASSWORD')
}

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    # Create default admin user
    admin_password = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    cur.execute("""
        INSERT INTO app.users (username, email, full_name, hashed_password, role, is_active, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    """, ('admin', 'admin@iseetutor.com', 'System Administrator', admin_password, 'admin', True, Json({})))
    
    # Create demo student
    student_password = bcrypt.hashpw(b'student123', bcrypt.gensalt()).decode('utf-8')
    cur.execute("""
        INSERT INTO app.users (username, email, full_name, hashed_password, role, is_active, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
        RETURNING id
    """, ('demo_student', 'student@iseetutor.com', 'Demo Student', student_password, 'student', True, 
          Json({'age': 12, 'grade': 7, 'avatar': 'avatar1'})))
    
    student_id = cur.fetchone()
    
    # Create sample questions
    sample_questions = [
        {
            'subject': 'math',
            'question_type': 'multiple_choice',
            'difficulty': 'easy',
            'question_text': 'What is 15 + 27?',
            'choices': ['32', '42', '52', '62'],
            'correct_answer': '42',
            'explanation': '15 + 27 = 42. You can solve this by adding the ones place (5+7=12, carry 1) and tens place (1+2+1=4).'
        },
        {
            'subject': 'reading',
            'question_type': 'multiple_choice',
            'difficulty': 'medium',
            'question_text': 'What is the main idea of a paragraph?',
            'choices': [
                'The first sentence',
                'The last sentence',
                'The central point the author is making',
                'The longest sentence'
            ],
            'correct_answer': 'The central point the author is making',
            'explanation': 'The main idea is the central point or message that the author wants to convey in the paragraph.'
        },
        {
            'subject': 'verbal',
            'question_type': 'multiple_choice',
            'difficulty': 'medium',
            'question_text': 'Choose the word that best completes the analogy: Book is to Reading as Fork is to ___',
            'choices': ['Kitchen', 'Eating', 'Metal', 'Spoon'],
            'correct_answer': 'Eating',
            'explanation': 'A book is used for reading, just as a fork is used for eating. This is a tool-to-action relationship.'
        }
    ]
    
    for q in sample_questions:
        cur.execute("""
            INSERT INTO app.questions (
                subject, question_type, difficulty, question_text, 
                choices, correct_answer, explanation, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (q['subject'], q['question_type'], q['difficulty'], q['question_text'],
              Json(q['choices']), q['correct_answer'], q['explanation'], Json({})))
    
    # Create sample educational content
    sample_content = [
        {
            'title': 'Introduction to ISEE',
            'content_type': 'article',
            'content': 'The Independent School Entrance Examination (ISEE) is an admission test...',
            'subject': 'general',
            'metadata': {'tags': ['overview', 'introduction']}
        },
        {
            'title': 'Math Problem Solving Strategies',
            'content_type': 'guide',
            'content': 'When solving math problems on the ISEE, follow these strategies...',
            'subject': 'math',
            'metadata': {'tags': ['strategies', 'tips']}
        }
    ]
    
    for c in sample_content:
        cur.execute("""
            INSERT INTO app.content (title, content_type, content, subject, metadata)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (c['title'], c['content_type'], c['content'], c['subject'], Json(c['metadata'])))
    
    conn.commit()
    print("Initial data seeded successfully")
    
except Exception as e:
    print(f"Error seeding data: {e}")
    sys.exit(1)
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
EOF

    # Export environment variables
    export DB_HOST=$DB_HOST
    export DB_PORT=$DB_PORT
    export DB_NAME=$DB_NAME
    export DB_USERNAME=$DB_USERNAME
    
    # Run seed script
    python3 /tmp/seed_data.py
    
    # Clean up
    rm /tmp/seed_data.py
    
    print_status "Initial data seeded"
}

# Run Alembic migrations
run_migrations() {
    print_info "Running database migrations..."
    
    # Use ECS task to run migrations
    CLUSTER_NAME="${PROJECT_NAME}-${ENVIRONMENT}-cluster"
    TASK_DEFINITION="${PROJECT_NAME}-${ENVIRONMENT}-backend"
    
    # Get subnet and security group
    SUBNET_ID=$(aws ec2 describe-subnets \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-private-subnet-1" \
        --query 'Subnets[0].SubnetId' \
        --output text)
    
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-ecs-tasks-sg" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    
    if [ -z "$SUBNET_ID" ] || [ -z "$SECURITY_GROUP_ID" ]; then
        print_error "Could not find required network configuration"
        exit 1
    fi
    
    # Run migration task
    TASK_ARN=$(aws ecs run-task \
        --cluster $CLUSTER_NAME \
        --task-definition $TASK_DEFINITION \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SECURITY_GROUP_ID]}" \
        --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","upgrade","head"]}]}' \
        --query 'tasks[0].taskArn' \
        --output text)
    
    if [ "$TASK_ARN" != "None" ]; then
        print_info "Waiting for migrations to complete..."
        aws ecs wait tasks-stopped --cluster $CLUSTER_NAME --tasks $TASK_ARN
        
        # Check exit code
        EXIT_CODE=$(aws ecs describe-tasks \
            --cluster $CLUSTER_NAME \
            --tasks $TASK_ARN \
            --query 'tasks[0].containers[0].exitCode' \
            --output text)
        
        if [ "$EXIT_CODE" -eq 0 ]; then
            print_status "Database migrations completed"
        else
            print_error "Database migrations failed with exit code $EXIT_CODE"
            exit 1
        fi
    else
        print_error "Failed to start migration task"
        exit 1
    fi
}

# Create read-only user for analytics
create_readonly_user() {
    print_info "Creating read-only analytics user..."
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USERNAME -d $DB_NAME << EOF
-- Create read-only user
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'iseetutor_readonly') THEN
        CREATE USER iseetutor_readonly WITH PASSWORD 'readonly_password_here';
    END IF;
END
\$\$;

-- Grant connect privilege
GRANT CONNECT ON DATABASE $DB_NAME TO iseetutor_readonly;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA app TO iseetutor_readonly;
GRANT USAGE ON SCHEMA analytics TO iseetutor_readonly;
GRANT USAGE ON SCHEMA content TO iseetutor_readonly;

-- Grant select on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA app TO iseetutor_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO iseetutor_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA content TO iseetutor_readonly;

-- Grant select on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO iseetutor_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO iseetutor_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA content GRANT SELECT ON TABLES TO iseetutor_readonly;

COMMIT;
EOF
    
    print_status "Read-only user created"
}

# Main execution
main() {
    echo "🗄️  ISEE Tutor Database Initialization"
    echo "====================================="
    echo "Environment: ${ENVIRONMENT}"
    echo ""
    
    get_db_connection
    create_schemas
    run_migrations
    create_indexes
    seed_initial_data
    create_readonly_user
    
    echo ""
    echo -e "${GREEN}Database initialization complete!${NC}"
    echo ""
    echo "Database connection details:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  Username: $DB_USERNAME"
    echo ""
    echo "Demo users created:"
    echo "  Admin: admin@iseetutor.com / admin123"
    echo "  Student: student@iseetutor.com / student123"
    echo ""
}

# Run main function
main