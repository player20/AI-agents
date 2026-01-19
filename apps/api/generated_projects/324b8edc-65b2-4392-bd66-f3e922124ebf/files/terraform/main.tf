provider 'aws' {
  region = 'us-east-1'
}

resource 'aws_eks_cluster' 'mira_news_cluster' {
  name     = 'mira-news-cluster'
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = aws_subnet.mira_news_subnet[*].id
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]
}

resource 'aws_iam_role' 'eks_cluster_role' {
  name = 'mira-news-eks-cluster-role'

  assume_role_policy = jsonencode({
    Version = '2012-10-17'
    Statement = [{
      Action = 'sts:AssumeRole'
      Effect = 'Allow'
      Principal = {
        Service = 'eks.amazonaws.com'
      }
    }]
  })
}

resource 'aws_iam_role_policy_attachment' 'eks_cluster_policy' {
  policy_arn = 'arn:aws:iam::aws:policy/AmazonEKSClusterPolicy'
  role       = aws_iam_role.eks_cluster_role.name
}

resource 'aws_vpc' 'mira_news_vpc' {
  cidr_block = '10.0.0.0/16'
  tags = {
    Name = 'mira-news-vpc'
  }
}

resource 'aws_subnet' 'mira_news_subnet' {
  count             = 2
  vpc_id            = aws_vpc.mira_news_vpc.id
  cidr_block        = cidrsubnet(aws_vpc.mira_news_vpc.cidr_block, 8, count.index)
  availability_zone = element(['us-east-1a', 'us-east-1b'], count.index)
  tags = {
    Name = 'mira-news-subnet-${count.index}'
  }
}
