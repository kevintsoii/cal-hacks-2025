# 🎮 Live Demo Script
## Step-by-Step Demo Guide for Presentation

**Duration: 2 minutes**

---

## 📝 PRE-DEMO SETUP (Do this 5 minutes before presenting)

### 1. Start All Services
```bash
cd /Users/james/Projects/cal-hacks-2025
docker-compose up -d
```
Wait for all services to be healthy.

### 2. Open Browser Tabs (in this order)
- Tab 1: Dashboard - `http://localhost:3000` (This is what you'll present)
- Tab 2: Backend API - `http://localhost:8000/status` (backup if needed)

### 3. Verify Everything Works
- [ ] Dashboard loads completely
- [ ] "System Active" indicator shows green
- [ ] WebSocket connected (check browser console - no errors)
- [ ] Metrics showing data
- [ ] Can see request log (even if empty)

### 4. Browser Setup
- Close all other tabs
- Set zoom to 100%
- Turn OFF browser notifications
- Turn OFF system notifications (Do Not Disturb mode)
- Full screen the browser (F11 or Cmd+Shift+F)
- Mouse cursor should be visible and easy to follow

### 5. Clear Old Data (Optional - for clean demo)
```bash
# If you want to start fresh
docker-compose down -v
docker-compose up -d
```

---

## 🎬 THE DEMO (2 minutes)

### PART 1: Dashboard Overview (30 seconds)

#### What to Say:
> "Let me show you our dashboard in action. This is our real-time security operations center."

#### What to Do:
1. **Point to the left sidebar** with cursor
   - Say: "Here we have our navigation - Overview, Detections, Endpoints, and Testing tools"

2. **Point to the top header**
   - Say: "You can see our 'System Active' indicator - everything is running live"

3. **Point to the Metrics Overview section**
   - Say: "These are our real-time metrics - total API requests processed, active mitigations currently in effect, and threat analysis"

4. **Point to the Detection Log (if any requests visible)**
   - Say: "And here's our live request feed. Every API request that comes through is shown here in real-time via WebSocket"
   - If empty: "Right now it's quiet, but we're about to change that"

#### Cursor Movement:
- Move cursor **slowly** and **deliberately**
- Circle important areas
- Don't frantically move around

---

### PART 2: Simulate Attack (1 minute)

#### What to Say:
> "Now, let's simulate a real brute force attack - someone trying to break into an account with rapid login attempts."

#### What to Do:

**Step 1: Navigate to Run Tests**
1. Click on **"Run Tests"** in the left sidebar
2. Wait for page to load (should be instant)

**Step 2: Select Test Type**
1. Click on **"Authentication"** tab (should already be selected)
2. Point out the different test types available:
   - Say: "We have multiple attack simulations - brute force, credential stuffing, rapid fire attempts"

**Step 3: Execute Test**
1. **Hover over** the "Run Brute Force Test" button
2. Say: "I'm going to simulate 50 failed login attempts in rapid succession - exactly what a real attacker would do"
3. **Click** "Run Brute Force Test"

**Step 4: Watch the Magic**
1. Logs should start appearing in the test console
2. Point to the logs appearing:
   - Say: "Look at these requests flooding in - POST to /auth/login, all failing, all from the same IP"
3. Point out the count:
   - Say: "50 attempts in about 3 seconds - this is a clear attack pattern"

**Step 5: Wait for AI Processing**
1. Let 5-10 seconds pass (be comfortable with brief silence)
2. Say: "The system is now batching these requests and feeding them to our AI agent pipeline. The orchestrator is routing them to the Auth specialist, which is analyzing the pattern..."

**Timing Note:** Don't rush this. The pause builds anticipation.

---

### PART 3: Show the Detection (30 seconds)

#### What to Say:
> "Now let's see what the AI decided to do."

#### What to Do:

**Step 1: Navigate to Detections**
1. Click **"Detections"** in the left sidebar
2. The "Active Mitigations" tab should be selected by default

**Step 2: Show the New Mitigation**
1. Point to the newly appeared mitigation card
2. Say: "And there it is - the system detected the attack and automatically applied a mitigation"

**Step 3: Explain the Mitigation**
1. Point to the mitigation level (e.g., "Slowdown" or "CAPTCHA"):
   - Say: "Notice it didn't immediately ban the user - it started with a [slowdown/CAPTCHA]. This is our progressive mitigation in action"

2. Point to the IP/User identifier:
   - Say: "This specific IP address is now flagged"

3. Point to the countdown/TTL (if visible):
   - Say: "And this is temporary - it will automatically expire if the suspicious activity stops"

**Step 4: Show AI Reasoning (if available)**
1. Click to expand the mitigation details (if there's an expand button)
2. Point to the reasoning text:
   - Say: "Here's the key - you can see the AI's reasoning. It's not a black box. It explains why it made this decision"
3. Read a snippet of the reasoning if it's visible

---

### PART 4: Explain the Learning (10 seconds - if time permits)

#### What to Say:
> "And here's the best part - this decision is now stored in our semantic memory using ChromaDB. If a similar pattern appears tomorrow, or next week, or next month, the system will recall this decision and adapt its response based on what worked."

#### What to Do:
- You can click on "History" tab to show past mitigations
- Or simply gesture to imply the concept if running low on time

---

### BONUS: Show Chatbot (ONLY if you have extra time)

#### What to Say:
> "As a bonus, we've built an AI chatbot powered by the same agent system."

#### What to Do:
1. Click "Chat" in the sidebar (if you have this feature)
2. Type a quick query like: "Show me recent failed logins"
3. Show the AI responding with data

**Note:** Skip this if you're running out of time. The core demo is more important.

---

## 🔥 DEMO VARIATIONS

### If Demo Breaks (Stay Calm!)

**Option 1: Use Screenshots**
- Have screenshots ready on your computer
- Say: "Let me show you a screenshot of this in action" (confidence!)
- Walk through the screenshot

**Option 2: Switch to Pre-recorded Video**
- Have a 30-second screen recording ready
- Say: "Here's what it looks like when running"
- Play the video

**Option 3: Explain Without Visual**
- Say: "The demo environment isn't loading, but let me explain what you would see..."
- Use your slides to walk through the flow
- **Don't apologize excessively** - it happens in demos

### If Test Doesn't Trigger Mitigation
- Say: "The AI is taking a bit longer to process this batch - it analyzes patterns across time windows. But here's a mitigation from a previous test run"
- Navigate to History tab
- Show a past mitigation

### If Everything is Too Fast
- **Slow down your narration**
- **Pause between actions**
- **Ask rhetorical questions**: "See how fast that was?"

### If Everything is Too Slow
- Fill the time with explanation
- "While this is processing, let me explain what's happening under the hood..."
- Talk about the agent communication

---

## 🎯 KEY POINTS TO EMPHASIZE DURING DEMO

1. **Real-time Nature**: "This is all happening live, via WebSocket"

2. **Speed**: "Notice how fast the mitigation check was - less than 2 milliseconds"

3. **Intelligence**: "The AI isn't just counting requests - it's analyzing patterns, timing, behavior"

4. **Transparency**: "You can see exactly why it made this decision - no black box"

5. **Progressive Approach**: "It didn't ban immediately - it starts gentle and escalates if needed"

6. **Learning**: "This decision is now in memory - the system gets smarter"

7. **Zero Code Changes**: "And remember, this is just middleware - no changes to the application code"

---

## 🎨 PRESENTATION STYLE FOR DEMO

### Body Language:
- Stand to the side of the screen, not in front
- Point with your hand or a pointer
- Make eye contact with judges between actions
- Smile - show you're proud of what you built

### Voice:
- Speak slightly slower than normal
- Pause for effect after key moments
- Show enthusiasm - this is exciting!
- Vary your tone - don't be monotone

### Pacing:
- Don't rush - 2 minutes is longer than you think
- Let actions complete before moving on
- Be comfortable with 2-3 second pauses
- If ahead on time, add more explanation
- If behind on time, skip the bonus features

### Handling Mistakes:
- If you click the wrong thing: "Let me navigate back..."
- If something breaks: Stay calm, use backup
- If you forget a step: "Let me also show you..."
- Never say: "This usually works" or "I don't know why..."

---

## ✅ POST-DEMO ACTIONS

### Immediately After Demo:
1. Say: "Let me return to our slides to wrap up"
2. Navigate back to presentation slides
3. Continue with "Key Innovations" slide

### During Q&A:
- You can return to the dashboard if judges ask
- Be ready to show specific features
- Don't start a new test during Q&A unless asked

---

## 🎬 DEMO SUCCESS CHECKLIST

During demo, make sure you:
- [ ] Showed the dashboard
- [ ] Ran the test
- [ ] Showed requests flooding in
- [ ] Explained what the AI is doing
- [ ] Showed the resulting mitigation
- [ ] Explained the reasoning
- [ ] Mentioned the learning/memory aspect
- [ ] Connected it back to the problem you're solving

---

## 💡 DEMO TIPS FROM HACKATHON WINNERS

1. **Practice the demo 10+ times** - know every click
2. **Have a backup plan** - screenshots, video, or verbal explanation
3. **Narrate everything** - don't assume judges know what they're looking at
4. **Show, don't tell** - let them see it work
5. **Make it visual** - use the cursor to guide eyes
6. **Keep moving** - don't get stuck on one thing
7. **End strong** - finish with a clear takeaway

---

## 🎯 SAMPLE NARRATION (Full Demo)

Here's a complete example narration you can use:

> "Let me show you our dashboard in action. [NAVIGATE TO DASHBOARD]
>
> This is our real-time security operations center, showing live API requests and metrics. [POINT TO SECTIONS]
>
> Now, let's simulate a brute force attack - someone trying to break into an account with rapid login attempts. [CLICK RUN TESTS]
>
> I'm going to run our brute force test - 50 failed login attempts in just a few seconds. [CLICK RUN BRUTE FORCE TEST]
>
> Watch these requests flood in. [POINT TO LOGS] POST to /auth/login, all failing, all from the same IP. This is exactly what a real attacker would do.
>
> [PAUSE 5 SECONDS]
>
> The system is now batching these requests and feeding them to our AI agent pipeline. The orchestrator is routing them to the Auth specialist, which is analyzing the pattern using Groq's LLM and querying historical data from Elasticsearch.
>
> Let's see what it decided. [NAVIGATE TO DETECTIONS]
>
> And there it is - the AI detected the attack pattern and automatically applied a mitigation. [POINT TO MITIGATION CARD]
>
> Notice it started with a slowdown, not an immediate ban. This is our progressive mitigation philosophy in action - proportional response, minimal false positives.
>
> You can see the AI's reasoning here - [POINT/READ REASONING] - it's not a black box. It explains its decision.
>
> And this decision is now stored in our semantic memory. If a similar pattern appears in the future, the system will recall this and adapt its response based on what worked.
>
> The entire process - from attack detection to intelligent mitigation - happened autonomously in under 10 seconds. [SMILE]
>
> Let me return to our slides to wrap up."

---

**You've got this! The demo is where your hard work shines. 🎬🚀**

