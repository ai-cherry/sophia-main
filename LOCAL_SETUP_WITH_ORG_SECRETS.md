# Local Setup with Organization Secrets

Your organization secrets are configured and ready for deployment! Here's how to use them:

## 🚀 Automated Deployment (Recommended)

Your push to `main` has triggered the deployment workflow. Check the status:
https://github.com/ai-cherry/sophia-main/actions

The workflow will automatically:
1. ✅ Use your organization secrets
2. ✅ Create the .env file
3. ✅ Deploy to Lambda Labs
4. ✅ Deploy frontend to Vercel

## 💻 Local Development Setup

Since organization secrets are secure and only available during GitHub Actions, you need to set up your local environment manually:

### Quick Setup with Your Existing .env

Your `.env` is already configured from our earlier setup. Let's verify it has the essentials:

```bash
# Check if your .env has the required keys
grep -E "OPENAI_API_KEY|ANTHROPIC_API_KEY|PORTKEY_API_KEY|OPENROUTER_API_KEY" .env
```

### Essential Keys for Local Development

At minimum, you need:

```env
# One of these AI providers:
OPENAI_API_KEY=sk-...  # Your OpenAI key
# OR
ANTHROPIC_API_KEY=sk-ant-...  # Your Anthropic key
# OR (Recommended)
PORTKEY_API_KEY=...  # Your Portkey key
OPENROUTER_API_KEY=...  # Your OpenRouter key

# Database (using Docker)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sophia
POSTGRES_PASSWORD=sophia_pass
POSTGRES_DB=sophia_payready

REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=<generate-random-key>
ADMIN_PASSWORD=<your-password>
```

### Start Development

1. **Start databases:**
   ```bash
   docker-compose up -d sophia-postgres sophia-redis
   ```

2. **Run the app:**
   ```bash
   cd backend
   python3 app/main.py
   ```

3. **Access the app:**
   - API: http://localhost:5000/api/
   - Health: http://localhost:5000/api/health

## 🔐 Security Notes

- Organization secrets are **never exposed** in logs or outputs
- They're only available during GitHub Actions runs
- For local dev, use a separate set of development keys
- Never commit `.env` files

## 📊 Monitor Deployments

1. **GitHub Actions:** https://github.com/ai-cherry/sophia-main/actions
2. **Container Registry:** https://github.com/ai-cherry/sophia-main/packages
3. **Lambda Labs Dashboard:** (check your Lambda Labs account)
4. **Vercel Dashboard:** (check your Vercel account)

## 🆘 Troubleshooting

If deployment fails:
1. Check the Actions tab for error logs
2. Verify organization secrets are properly named
3. Ensure secrets have correct values (no extra spaces/quotes)

Your organization-level secrets are more secure and easier to manage than repository secrets. They're perfect for a production setup! 