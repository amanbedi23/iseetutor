#!/bin/bash
# Check PostgreSQL setup for ISEE Tutor

echo "=== Checking PostgreSQL Setup ==="
echo ""

# Run from /tmp to avoid permission issues
cd /tmp

echo "1. PostgreSQL Users:"
sudo -u postgres psql -c "\du" | grep -E "Role name|iseetutor|---"

echo ""
echo "2. Databases:"
sudo -u postgres psql -c "\l" | grep -E "Name|iseetutor|---"

echo ""
echo "3. Testing connection:"
PGPASSWORD=iseetutor123 psql -U iseetutor -d iseetutor_db -h localhost -c "SELECT 'Connection successful!' as status;" 2>&1

echo ""
echo "4. Redis status:"
redis-cli ping && echo "Redis is running" || echo "Redis is not running"