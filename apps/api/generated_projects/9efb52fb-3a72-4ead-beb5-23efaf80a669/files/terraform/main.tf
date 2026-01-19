provider "aws" {
  region = var.aws_region
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "18.26.6"
  cluster_name    = var.cluster_name
  cluster_version = "1.21"
  subnets         = module.vpc.private_subnets
  vpc_id          = module.vpc.vpc_id

  node_groups = {
    general = {
      desired_capacity = 2
      max_capacity     = 3
      min_capacity     = 1
      instance_types   = ["t3.small"]
    }
  }
}

module "vpc" {
  source               = "terraform-aws-modules/vpc/aws"
  version              = "3.14.2"
  name                 = "mira-news-vpc"
  cidr                 = "10.0.0.0/16"
  azs                  = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets      = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets       = ["10.0.101.0/24", "10.0.102.0/24"]
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
}

resource "aws_secretsmanager_secret" "mira_news_secrets" {
  name = "mira-news-secrets"
}

resource "aws_secretsmanager_secret_version" "mira_news_secrets_version" {
  secret_id     = aws_secretsmanager_secret.mira_news_secrets.id
  secret_string = jsonencode({
    database-url    = var.database_url
    redis-url       = var.redis_url
    jwt-secret-key  = var.jwt_secret_key
  })
}