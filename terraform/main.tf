terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "windows_ai" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "windows-ai-vpc"
  }
}

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.windows_ai.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "windows-ai-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.windows_ai.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "windows-ai-private-${count.index + 1}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "windows_ai" {
  vpc_id = aws_vpc.windows_ai.id

  tags = {
    Name = "windows-ai-igw"
  }
}

# RDS PostgreSQL Database
resource "aws_rds_cluster" "windows_ai" {
  cluster_identifier      = "windows-ai-cluster"
  engine                  = "aurora-postgresql"
  engine_version          = "15.2"
  database_name           = "windows_ai"
  master_username         = var.db_username
  master_password         = var.db_password
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  skip_final_snapshot     = false

  db_subnet_group_name            = aws_db_subnet_group.windows_ai.name
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.windows_ai.name
  vpc_security_group_ids          = [aws_security_group.db.id]

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "windows-ai-db"
  }
}

resource "aws_rds_cluster_instance" "windows_ai" {
  count              = 2
  cluster_identifier = aws_rds_cluster.windows_ai.id
  instance_class     = "db.t3.medium"
  engine              = aws_rds_cluster.windows_ai.engine
  engine_version      = aws_rds_cluster.windows_ai.engine_version

  tags = {
    Name = "windows-ai-db-instance-${count.index + 1}"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "windows_ai" {
  cluster_id           = "windows-ai-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  security_group_ids   = [aws_security_group.cache.id]

  subnet_group_name = aws_elasticache_subnet_group.windows_ai.name

  tags = {
    Name = "windows-ai-cache"
  }
}

# S3 Bucket for Storage
resource "aws_s3_bucket" "windows_ai" {
  bucket = "windows-ai-storage-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "windows-ai-storage"
  }
}

resource "aws_s3_bucket_versioning" "windows_ai" {
  bucket = aws_s3_bucket.windows_ai.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "windows_ai" {
  name = "windows-ai-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "windows-ai-cluster"
  }
}

# ECR Repository
resource "aws_ecr_repository" "windows_ai" {
  name                 = "windows-ai"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "windows-ai-repo"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "windows_ai" {
  family                   = "windows-ai"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name      = "windows-ai"
    image     = "${aws_ecr_repository.windows_ai.repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "ENVIRONMENT"
        value = "production"
      },
      {
        name  = "DATABASE_URL"
        value = "postgresql://${var.db_username}:${var.db_password}@${aws_rds_cluster.windows_ai.endpoint}:5432/windows_ai"
      },
      {
        name  = "REDIS_URL"
        value = "redis://${aws_elasticache_cluster.windows_ai.cache_nodes[0].address}:6379"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.windows_ai.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  tags = {
    Name = "windows-ai-task"
  }
}

# ECS Service
resource "aws_ecs_service" "windows_ai" {
  name            = "windows-ai-service"
  cluster         = aws_ecs_cluster.windows_ai.id
  task_definition = aws_ecs_task_definition.windows_ai.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.windows_ai.arn
    container_name   = "windows-ai"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.windows_ai]

  tags = {
    Name = "windows-ai-service"
  }
}

# Application Load Balancer
resource "aws_lb" "windows_ai" {
  name               = "windows-ai-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "windows-ai-alb"
  }
}

resource "aws_lb_target_group" "windows_ai" {
  name        = "windows-ai-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.windows_ai.id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name = "windows-ai-tg"
  }
}

resource "aws_lb_listener" "windows_ai" {
  load_balancer_arn = aws_lb.windows_ai.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.windows_ai.arn
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "windows_ai" {
  name              = "/ecs/windows-ai"
  retention_in_days = 7

  tags = {
    Name = "windows-ai-logs"
  }
}

# Auto Scaling
resource "aws_autoscaling_target" "windows_ai" {
  max_capacity       = 4
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.windows_ai.name}/${aws_ecs_service.windows_ai.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_autoscaling_policy" "windows_ai_cpu" {
  name               = "windows-ai-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_autoscaling_target.windows_ai.resource_id
  scalable_dimension = aws_autoscaling_target.windows_ai.scalable_dimension
  service_namespace  = aws_autoscaling_target.windows_ai.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "windows-ai-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.windows_ai.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "windows-ai-alb-sg"
  }
}

resource "aws_security_group" "app" {
  name        = "windows-ai-app-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.windows_ai.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "windows-ai-app-sg"
  }
}

resource "aws_security_group" "db" {
  name        = "windows-ai-db-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.windows_ai.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "windows-ai-db-sg"
  }
}

resource "aws_security_group" "cache" {
  name        = "windows-ai-cache-sg"
  description = "Security group for ElastiCache"
  vpc_id      = aws_vpc.windows_ai.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "windows-ai-cache-sg"
  }
}

# IAM Roles
resource "aws_iam_role" "ecs_task_execution" {
  name = "windows-ai-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "windows-ai-ecs-task-execution"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Database and Cache subnet groups
resource "aws_db_subnet_group" "windows_ai" {
  name       = "windows-ai-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "windows-ai-db-subnet-group"
  }
}

resource "aws_elasticache_subnet_group" "windows_ai" {
  name       = "windows-ai-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "windows-ai-cache-subnet-group"
  }
}

# RDS parameter group
resource "aws_rds_cluster_parameter_group" "windows_ai" {
  family      = "aurora-postgresql15"
  name        = "windows-ai-params"
  description = "Parameter group for Windows AI"

  tags = {
    Name = "windows-ai-params"
  }
}
