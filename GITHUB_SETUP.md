# GitHub Authentication Setup - Manual Steps Required

## Complete GitHub CLI Authentication

Since GitHub CLI requires interactive authentication, please follow these steps in your terminal:

### Step 1: Run the GitHub Login Command

```bash
cd "d:/SIT-CSM-Learning/4.Module 4 - Ethical Computing & Data Analysis/ICT 1506C - Computing Systems/Project 3"
export PATH="/c/Program Files/GitHub CLI:$PATH"
gh auth login
```

### Step 2: Select Authentication Method

When prompted, choose:

- **Protocol**: HTTPS (recommended)
- **Credential**: Paste your GitHub token (see below) or authenticate via browser

### Step 3: Generate Personal Access Token (if needed)

If you don't have a token:

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: `cctv-system-repo`
4. Scopes needed:
   - ✓ repo (Full control of private repositories)
   - ✓ admin:repo_hook (Admin access to hooks)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. Paste it into the `gh auth login` prompt

### Alternative: Browser-based Login

If you prefer, let `gh auth login` open your browser to authenticate directly.

---

## After Authentication is Complete

Once you see "Logged in as [your-username]", run these commands:

```bash
# Create private GitHub repository
gh repo create cctv-system --private --source=. --remote=origin --push

# Verify push was successful
git log --oneline origin/main
```

---

## Troubleshooting

### "gh: command not found"

```bash
export PATH="/c/Program Files/GitHub CLI:$PATH"
```

### Token expiration

Generate a new token at: https://github.com/settings/tokens

### Rate limiting

Wait a few minutes before trying again.

### Cannot push

Verify authentication:

```bash
gh auth status
```

---

## Your Repository Will Be Created With:

- **Name**: cctv-system
- **Visibility**: Private
- **Branches**: main (with all your code)
- **Files**: 35 commited files, 6,967 lines added

**Once complete, your repository will be at**: `https://github.com/YOUR_USERNAME/cctv-system`

---

**Need help?** Run: `gh auth login --help`
