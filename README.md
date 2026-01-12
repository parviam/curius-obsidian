# Curius to Obsidian Sync
Automatically sync your [Curius](https://curius.app) bookmarks to your Obsidian vault with AI-generated summaries.

## AI USAGE
I spent about an hour total on this project, and ~95% of the code was written by Claude. Do not use in super sensitive settings, your mileage may vary, this is not medical advice, etc. etc. Please feel free to reach out if anything is wrong.

## Meta note
Probably, the easiest way to set this up is just asking Claude to read this.

## Features

- Fetches all saved links from your Curius account
- Generates concise summaries using your choice of LLM provider (OpenRouter or Groq)
- Preserves highlights and comments from Curius
- Creates well-formatted Markdown files with YAML frontmatter
- Tracks processed links to avoid duplicates
- Supports scheduled automation (Windows Task Scheduler, Mac/Linux cron)

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
- **LLM API key** - Choose one:
  - [OpenRouter](https://openrouter.ai/keys) - Access to many models (Claude, GPT-4, etc.)
  - [Groq](https://console.groq.com/keys) - Free, fast (LLaMA 3.3 70B)
- **Curius account** - Your saved links at [curius.app](https://curius.app)
- **Obsidian vault** - Where your notes will be saved

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/curius-obsidian.git
cd curius-obsidian
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Edit `.env` with your values:

```env
# Choose ONE LLM provider:
# Option 1: OpenRouter (if both are set, OpenRouter is preferred)
OPENROUTER_API_KEY=your_openrouter_api_key_here
# OPENROUTER_MODEL=google/gemini-flash-1.5  # optional, this is the default (free)

# Option 2: Groq (free)
# GROQ_API_KEY=your_groq_api_key_here

# Required settings
CURIUS_USER_ID=12345

# Windows:
VAULT_PATH=C:\Users\YourName\Documents\Obsidian\curius
# Mac/Linux:
VAULT_PATH=/Users/yourname/Documents/Obsidian/curius
```

## LLM Provider Options

The script auto-detects which provider to use based on which API key is set.

### OpenRouter
- **Pros**: Access to many models (Claude, GPT-4, Gemini, etc.), includes free models
- **Setup**: Get an API key at [openrouter.ai/keys](https://openrouter.ai/keys)
- **Default model**: `google/gemini-flash-1.5` (fast and free)
- **Custom model**: Set `OPENROUTER_MODEL` in your `.env` file
- **Browse models**: [openrouter.ai/models](https://openrouter.ai/models) (filter by "free" for free options)

### Groq
- **Pros**: Free tier, very fast inference
- **Setup**: Get an API key at [console.groq.com/keys](https://console.groq.com/keys)
- **Model**: LLaMA 3.3 70B Versatile

If both API keys are set, OpenRouter is used.

### Finding Your Curius User ID

The Curius API requires your numeric user ID (not your username). To find it:

1. Go to your Curius profile page (e.g., `curius.app/your-username`)
2. Open browser DevTools (`F12` or right-click > Inspect)
3. Go to the **Network** tab
4. Refresh the page
5. Look for API requests to `/api/users/{number}/links`
6. The number in the URL is your user ID

## Usage

### Manual Run

```bash
uv run python main.py
```

### Automated Daily Sync (Windows Task Scheduler)

#### Method 1: Using the Setup Script (Recommended)

1. Open **PowerShell as Administrator** (right-click > Run as Administrator)
2. Navigate to the project directory:
   ```powershell
   cd "C:\path\to\curius-obsidian"
   ```
3. Run the setup script:
   ```powershell
   .\setup_task.ps1
   ```

The task will run daily at 6:00 AM, or when your computer wakes up if it was off.

#### Method 2: Manual Task Scheduler Setup

1. Press `Win + S` and search for **Task Scheduler**, open it
2. Click **Create Basic Task...** in the right panel
3. Configure the task:
   - **Name**: `CuriusObsidianSync`
   - **Description**: `Sync Curius bookmarks to Obsidian daily`
   - **Trigger**: Daily, at your preferred time (e.g., 6:00 AM)
   - **Action**: Start a program
   - **Program/script**: Browse to `run_sync.bat` in this project folder
   - **Start in**: The full path to this project folder (e.g., `C:\path\to\curius-obsidian`)
4. Click **Finish**

**Important: Configure these additional settings** (edit the task after creation):

1. Right-click the task > **Properties**
2. **General** tab:
   - Check "Run whether user is logged on or not" (optional, for headless operation)
3. **Conditions** tab:
   - **Uncheck** "Start only if the computer is on AC power" (allows running on battery)
4. **Settings** tab:
   - **Check** "Run task as soon as possible after a scheduled start is missed" (runs on wake if laptop was off)

#### Removing the Scheduled Task

PowerShell (as Administrator):
```powershell
Unregister-ScheduledTask -TaskName "CuriusObsidianSync" -Confirm:$false
```

Or manually delete it from Task Scheduler.

### Automated Daily Sync (Mac/Linux - cron)

1. Make the script executable:
   ```bash
   chmod +x run_sync.sh
   ```

2. Open your crontab:
   ```bash
   crontab -e
   ```

3. Add this line to run daily at 6 AM:
   ```
   0 6 * * * /path/to/curius-obsidian/run_sync.sh
   ```
   Replace `/path/to/curius-obsidian` with the actual path to your project folder.

4. Save and exit. The cron job is now active.

#### Removing the cron job

```bash
crontab -e
# Delete the line you added, then save and exit
```

#### Viewing logs

```bash
tail -f /path/to/curius-obsidian/sync_log.txt
```

## Output Format

Each synced link creates a Markdown file like this:

```markdown
---
url: https://example.com/article
author: John Doe
date_saved: 2024-01-15
curius_id: 12345
favorite: false
---

# Article Title

## Summary

AI-generated summary of the article content...

## Highlights

> "Highlighted text from the article"

## Comments

- Your comment on this link

## Source

[Original Article](https://example.com/article)
```

## Files Overview

| File | Purpose |
|------|---------|
| `main.py` | Core sync logic |
| `run_sync.bat` | Windows batch file for scheduled execution |
| `run_sync.sh` | Mac/Linux shell script for scheduled execution |
| `setup_task.ps1` | Windows PowerShell script to create scheduled task |
| `.env` | Your configuration (not committed) |
| `.env.example` | Template for configuration |
| `processed_links.json` | Tracks synced links (not committed) |
| `sync_log.txt` | Execution logs (not committed) |

## Troubleshooting

### "No LLM API key found" Error

Set at least one of the following in your `.env` file:
- `OPENROUTER_API_KEY` - Get one at [openrouter.ai/keys](https://openrouter.ai/keys)
- `GROQ_API_KEY` - Get one at [console.groq.com/keys](https://console.groq.com/keys)

### "Missing required environment variable" Error

Ensure your `.env` file exists and contains all required variables:
- `OPENROUTER_API_KEY` or `GROQ_API_KEY` (at least one)
- `CURIUS_USER_ID`
- `VAULT_PATH`

### Vault folder not created

The script will create the vault folder automatically if it doesn't exist. Make sure the parent directory exists and you have write permissions.

### Task Scheduler not running (Windows)

1. Open Task Scheduler and check the task's **History** tab (enable history from the View menu if needed)
2. Verify `run_sync.bat` path is correct in the task's Actions
3. Ensure `uv` is in your system PATH
4. Check `sync_log.txt` in the project folder for error messages

### Cron job not running (Mac/Linux)

1. Check if cron is running: `pgrep cron` or `systemctl status cron`
2. Make sure `run_sync.sh` is executable: `chmod +x run_sync.sh`
3. Ensure `uv` is available in cron's PATH - you may need to use the full path to `uv` in `run_sync.sh`
4. Check `sync_log.txt` for error messages
5. View cron logs: `grep CRON /var/log/syslog` (Linux) or check Console.app (Mac)

### API rate limits

The script includes retry logic with exponential backoff. If you have many links, the initial sync may take a while. Subsequent runs only process new links.

## Contact
Say hi to me at [parvmahajan.com](https://www.parvmahajan.com)! If this brought you sufficient joy, consider donating $5 (or more!) to the [Malaria Consortium](https://www.givewell.org/charities/malaria-consortium) through GiveWell!

## License
Check out [LICENSE](/LICENSE)
