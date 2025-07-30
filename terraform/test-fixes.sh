#!/bin/bash

echo "Testing Terraform fixes..."
echo "========================"

cd /Users/amanbedi/VSCode/iseetutor/terraform/environments/dev

# Initialize Terraform
echo "1. Initializing Terraform..."
terraform init

# Validate configuration
echo -e "\n2. Validating configuration..."
terraform validate

# Plan to check for errors
echo -e "\n3. Running terraform plan to check for errors..."
terraform plan -var="domain_name=" -var="certificate_arn=" -no-color | grep -E "(Error:|Warning:|will be created|will be updated|will be destroyed)" || echo "No errors found in plan"

echo -e "\nDone!"