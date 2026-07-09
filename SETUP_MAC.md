# Setting up Wild Wolves Pulse on your Mac

## One-time setup

### 1. Install Python (if you don't already have it)

Open Terminal and run:

```bash
python3 --version
```

If you get an error or don't have Python 3.9+, install it:

```bash
brew install python
```

(If you don't have Homebrew either, install it first: https://brew.sh)

### 2. Clone the repo

Pick where you want the project to live. For example, in your home folder:

```bash
cd ~
git clone https://github.com/henrysmith23/wild-wolves-pulse.git
cd wild-wolves-pulse
```

### 3. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Install the Chromium browser for Playwright

```bash
python3 -m playwright install chromium
```

### 5. Make the run script executable

```bash
chmod +x run.sh
```

### 6. Test that it works

```bash
./run.sh
```

You should see output like:

```
[date]: Starting collector run
Fetched https://anfield.freeforums.net/... (100000+ chars)
Found last page: 92
...
TOTAL POSTS FOUND: X
NEW POSTS FOUND: Y
Data pushed to GitHub
[date]: Done
```

If this works, move on to step 7. If it fails, stop here and troubleshoot before continuing.

### 7. Set up the scheduled task

This configures your Mac to run the collector every hour while logged in, and once immediately on login.

First, update the plist file with your actual repo path:

```bash
sed -i '' "s|REPO_PATH|$(pwd)|g" com.wildwolves.pulse.plist
```

Create the logs directory:

```bash
mkdir -p logs
```

Copy the plist to where macOS expects it:

```bash
cp com.wildwolves.pulse.plist ~/Library/LaunchAgents/
```

Load and start the scheduled task:

```bash
launchctl load ~/Library/LaunchAgents/com.wildwolves.pulse.plist
```

That's it. The collector will now run:
- Once immediately when you log in
- Every hour while your Mac is awake

## Checking if it's working

### View the log

```bash
cat ~/wild-wolves-pulse/logs/collector.log
```

(Replace the path if you cloned it somewhere else.)

### Check recent git history

```bash
cd ~/wild-wolves-pulse
git log --oneline -5
```

You should see "update pulse data" commits appearing.

## Stopping or removing the scheduled task

To temporarily stop:

```bash
launchctl unload ~/Library/LaunchAgents/com.wildwolves.pulse.plist
```

To restart it later:

```bash
launchctl load ~/Library/LaunchAgents/com.wildwolves.pulse.plist
```

To remove it entirely:

```bash
launchctl unload ~/Library/LaunchAgents/com.wildwolves.pulse.plist
rm ~/Library/LaunchAgents/com.wildwolves.pulse.plist
```

## Troubleshooting

**"command not found: python3"** — Install Python via `brew install python`.

**"No module named playwright"** — Run `pip3 install -r requirements.txt` again.

**"Executable doesn't exist" from Playwright** — Run `python3 -m playwright install chromium`.

**Git push fails with "rejected"** — Someone else pushed. Run `git pull --rebase` then `./run.sh` again.

**"Got Cloudflare challenge page"** — Unusual from a home IP. Try again in a few minutes; if persistent, the forum may have tightened security further.
