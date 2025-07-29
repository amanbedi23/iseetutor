terraform {
  cloud {
    organization = "iseetutor"  # Replace with your actual Terraform Cloud org name
    
    workspaces {
      name = "iseetutor-dev"
    }
  }
  
  required_version = ">= 1.5.0"
}