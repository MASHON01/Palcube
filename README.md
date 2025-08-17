# Slack-Jira-GitHub Automation

A production-ready automation system that creates Jira tickets and GitHub repositories from Slack messages, with IBM Watsonx integration.

## 🚀 Features

- **Slack Integration**: Listen for messages and automatically trigger workflows
- **Jira Automation**: Create tickets with intelligent issue type detection
- **GitHub Repository Creation**: Auto-generate repositories with IBM Watsonx integration
- **Smart Keyword Detection**: Automatically determine when to create repositories
- **Multi-branch Setup**: Pre-configured development workflow
- **CI/CD Ready**: GitHub Actions workflow included
- **Docker Support**: Containerized deployment
- **Security**: Environment-based configuration and secrets management

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Slack App with Socket Mode enabled
- Jira Cloud instance with API access
- GitHub account with Personal Access Token
- IBM Watsonx Orchestrate (optional, for enhanced AI features)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd slack-jira-github-automation
```

### 2. Set Up Environment Variables
```bash
cp env.example .env
# Edit .env with your actual credentials
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run with Docker (Recommended)
```bash
docker-compose up -d
```

### 5. Run Locally (Development)
```bash
python slack_listener.py
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | Yes |
| `SLACK_APP_TOKEN` | Slack App-Level Token | Yes |
| `JIRA_URL` | Your Jira instance URL | Yes |
| `JIRA_USERNAME` | Jira username/email | Yes |
| `JIRA_API_TOKEN` | Jira API token | Yes |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes |
| `GITHUB_USERNAME` | GitHub username | Yes |

### Slack App Setup

1. Create a Slack App at https://api.slack.com/apps
2. Enable Socket Mode
3. Add bot token scopes:
   - `chat:write`
   - `app_mentions:read`
   - `channels:history`
4. Subscribe to events:
   - `app_mention`
   - `message.channels`

### Jira Setup

1. Generate API token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Ensure your user has project creation permissions
3. Note your Jira instance URL

### GitHub Setup

1. Create Personal Access Token with `repo` scope
2. Ensure you have repository creation permissions

## 🎯 Usage

### Triggering the Automation

Send a message in Slack mentioning the bot:

```
@Action Agent Need to create a ticket for the new user dashboard feature
```

### What Happens

1. **Slack Message** → Bot detects mention and keywords
2. **Jira Ticket** → Creates ticket with appropriate issue type
3. **GitHub Repository** → Creates repo with IBM Watsonx integration
4. **Jira Update** → Adds GitHub repository link to ticket
5. **Slack Response** → Sends confirmation with all links

### Repository Structure Created

```
repository-name/
├── .github/workflows/ci-cd.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── ibm-watsonx-config.json
└── ibm_watsonx_integration.py
```

## 🔒 Security

- All credentials stored in environment variables
- `.env` file excluded from version control
- Docker runs as non-root user
- Health checks monitor application status
- Comprehensive logging for audit trails

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8080/health
```

### Logs
```bash
# Docker
docker-compose logs -f

# Local
tail -f logs/app.log
```

## 🚀 Deployment

### Production Deployment
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Monitor
docker-compose logs -f
```

### Environment-Specific Configs
- `docker-compose.yml` - Development
- `docker-compose.prod.yml` - Production
- `docker-compose.staging.yml` - Staging

## 🧪 Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
pytest tests/integration/
```

## 📝 API Reference

### Slack Events
- `app_mention` - Triggers automation
- `message.channels` - Processes channel messages

### Jira Integration
- Creates tickets with smart issue type detection
- Updates tickets with GitHub repository links
- Supports multiple project keys

### GitHub Integration
- Creates repositories with IBM Watsonx integration
- Sets up development branches
- Configures CI/CD pipelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the [deployment guide](DEPLOYMENT.md)
- Review the logs for troubleshooting

## 🔄 Changelog

### v1.0.0
- Initial release
- Slack-Jira-GitHub automation
- IBM Watsonx integration
- Docker support
- Production-ready security
