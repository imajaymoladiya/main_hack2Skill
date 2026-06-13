document.addEventListener("DOMContentLoaded", () => {
  // --- STATE VARIABLES ---
  let hasApiKey = false;
  let activeExam = "JEE";
  let activeMood = "calm";
  let currentStressLevel = 5;
  let currentTriggers = [];
  let chatHistory = [];
  
  // Timer States
  let pomodoroTimer = null;
  let timerSecondsLeft = 25 * 60;
  let timerTotalDuration = 25 * 60;
  let timerMode = "study"; // study, break
  
  // Breathing States
  let breathingInterval = null;
  let breathingCycle = 1;
  let breathingPhase = 0; // 0: inhale, 1: hold full, 2: exhale, 3: hold empty
  let breathingSeconds = 0;

  // --- SELECTORS ---
  // Status
  const statusBadge = document.getElementById("backend-status-badge");
  
  // Inputs
  const examSelect = document.getElementById("exam-select");
  const moodInputs = document.getElementsByName("mood");
  const journalInput = document.getElementById("journal-text-input");
  const analyzeBtn = document.getElementById("analyze-journal-btn");
  
  // Tabs
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  
  // Analysis Output Views
  const analysisPlaceholder = document.getElementById("analysis-placeholder");
  const analysisLoading = document.getElementById("analysis-loading");
  const analysisReportView = document.getElementById("analysis-report-view");
  const safetyWarningBox = document.getElementById("safety-warning-box");
  const generalReportMetrics = document.getElementById("general-report-metrics");
  
  // Analysis Metric Fields
  const valStressLevel = document.getElementById("val-stress-level");
  const stressGaugeBar = document.getElementById("stress-gauge-bar");
  const valBurnoutRisk = document.getElementById("val-burnout-risk");
  const burnoutBadgeLbl = document.getElementById("burnout-badge-lbl");
  const emotionDistributionBars = document.getElementById("emotion-distribution-bars");
  const triggersList = document.getElementById("triggers-list");
  const patternsList = document.getElementById("patterns-list");
  const insightTextBox = document.getElementById("insight-text-box");
  const motivationTextLbl = document.getElementById("motivation-text-lbl");
  const examTagLbl = document.getElementById("exam-tag-lbl");
  const copingStrategiesContainer = document.getElementById("coping-strategies-container");
  const exerciseNameLbl = document.getElementById("exercise-name-lbl");
  const exerciseInstructionsLbl = document.getElementById("exercise-instructions-lbl");
  const exerciseDurationLbl = document.getElementById("exercise-duration-lbl");
  const safetyMessageText = document.getElementById("safety-message-text");
  const safetyHelplinesList = document.getElementById("safety-helplines-list");
  
  // Chat
  const chatMessagesContainer = document.getElementById("chat-messages-container");
  const chatUserInput = document.getElementById("chat-user-input");
  const chatSendBtn = document.getElementById("chat-send-btn");
  const chatSuggestionChips = document.getElementById("chat-suggestion-chips");
  const chatAvatar = document.querySelector(".chat-avatar");
  
  // Guided Breathing
  const startBreathingBtn = document.getElementById("start-breathing-btn");
  const stopBreathingBtn = document.getElementById("stop-breathing-btn");
  const breathingCircle = document.getElementById("breathing-circle");
  const breathingGuide = document.getElementById("breathing-guide");
  const breathingTimerDisplay = document.getElementById("breathing-timer");
  
  // Pomodoro
  const timerDisplay = document.getElementById("timer-display");
  const timerBadge = document.getElementById("timer-badge");
  const timerProgress = document.getElementById("timer-progress");
  const timerStartBtn = document.getElementById("timer-start-btn");
  const timerBreakBtn = document.getElementById("timer-break-btn");
  const timerResetBtn = document.getElementById("timer-reset-btn");
  
  // History
  const historyCount = document.getElementById("history-count");
  const historyAvgStress = document.getElementById("history-avg-stress");
  const historyTopTrigger = document.getElementById("history-top-trigger");
  const historyLogsList = document.getElementById("history-logs-list");
  const clearHistoryBtn = document.getElementById("clear-history-btn");
  const historyActionsBar = document.getElementById("history-actions-bar");
  
  // Toast
  const toastMessageBox = document.getElementById("toast-message-box");
  const toastText = document.getElementById("toast-text");


  // --- INITIALIZATION ---
  checkServerStatus();
  updateTimelineHistory();
  loadExamAndMoodFromInputs();

  // --- LISTENERS ---
  
  // Inputs sync
  examSelect.addEventListener("change", (e) => {
    activeExam = e.target.value;
    showToast(`Entrance exam updated to ${activeExam}`);
    updateChatHeader();
  });
  
  moodInputs.forEach(input => {
    input.addEventListener("change", (e) => {
      activeMood = e.target.value;
      showToast(`Mood logged: ${activeMood.replace("_", " ")}`);
    });
  });
  
  function loadExamAndMoodFromInputs() {
    activeExam = examSelect.value;
    moodInputs.forEach(input => {
      if (input.checked) {
        activeMood = input.value;
      }
    });
  }

  // Navigation tab switching
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      
      tabButtons.forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      tabContents.forEach(c => c.classList.remove("active"));
      
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      document.getElementById(targetTab).classList.add("active");
      
      if (targetTab === "tab-chat") {
        setTimeout(() => {
          chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        }, 100);
      }
    });
  });

  // Daily Journal submission
  analyzeBtn.addEventListener("click", performJournalAnalysis);

  // Chat message send
  chatSendBtn.addEventListener("click", sendChatMessage);
  chatUserInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendChatMessage();
    }
  });

  // Suggestions chips binding
  chatSuggestionChips.addEventListener("click", (e) => {
    if (e.target.classList.contains("suggestion-chip")) {
      chatUserInput.value = e.target.innerText;
      sendChatMessage();
    }
  });

  // Breathing controls
  startBreathingBtn.addEventListener("click", startBreathingExercise);
  stopBreathingBtn.addEventListener("click", stopBreathingExercise);

  // Pomodoro controls
  timerStartBtn.addEventListener("click", startPomodoroStudy);
  timerBreakBtn.addEventListener("click", startPomodoroBreak);
  timerResetBtn.addEventListener("click", resetPomodoroTimer);

  // Clear history
  clearHistoryBtn.addEventListener("click", clearLocalHistory);


  // --- CORE LOGIC FUNCTIONS ---

  // Check connection status
  async function checkServerStatus() {
    try {
      const response = await fetch("/api/status");
      if (response.ok) {
        const data = await response.json();
        hasApiKey = data.has_api_key;
        if (hasApiKey) {
          statusBadge.innerHTML = `🌟 GenAI Active (${data.model_configured})`;
          statusBadge.style.color = "#10b981";
        } else {
          statusBadge.innerHTML = `⚙️ Local Fallback Mode Active`;
          statusBadge.style.color = "#f59e0b";
          statusBadge.querySelector(".pulse-dot")?.classList.add("fallback");
        }
      }
    } catch (error) {
      console.error("Connection check failed:", error);
      statusBadge.innerHTML = `🔴 Server Offline`;
      statusBadge.style.color = "#ef4444";
    }
  }

  // Toast feedback
  function showToast(message) {
    toastText.innerText = message;
    toastMessageBox.classList.add("show");
    setTimeout(() => {
      toastMessageBox.classList.remove("show");
    }, 2500);
  }

  // Synthesis Audio chime generator (No assets needed!)
  function playPeacefulChime() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      
      // Node 1: E-major chime note
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.type = "sine";
      osc1.frequency.setValueAtTime(659.25, ctx.currentTime); // E5
      
      // Node 2: G# major chime note
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.type = "sine";
      osc2.frequency.setValueAtTime(830.61, ctx.currentTime); // G#5
      
      gain1.gain.setValueAtTime(0.15, ctx.currentTime);
      gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
      
      gain2.gain.setValueAtTime(0.10, ctx.currentTime + 0.1);
      gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.6);
      
      osc1.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 1.6);
      osc2.start(ctx.currentTime + 0.1);
      osc2.stop(ctx.currentTime + 1.7);
    } catch (e) {
      console.log("Audio contexts blocks active due to browser policies:", e);
    }
  }

  // Update companion header
  function updateChatHeader() {
    const subtitle = document.querySelector(".chat-card-container .card-subtitle");
    if (subtitle) {
      subtitle.innerText = `Your empathetic digital companion for ${activeExam} prep support`;
    }
  }


  // --- JOURNAL ANALYSIS PIPELINE ---

  async function performJournalAnalysis() {
    const text = journalInput.value.trim();
    if (!text) {
      alert("Please write a few thoughts in your daily journal before analyzing.");
      return;
    }
    
    // UI Transitions
    analysisPlaceholder.style.display = "none";
    analysisReportView.style.display = "none";
    analysisLoading.style.display = "flex";
    
    // Animate loader checkmarks step by step
    const steps = [
      document.getElementById("step-1"),
      document.getElementById("step-2"),
      document.getElementById("step-3"),
      document.getElementById("step-4")
    ];
    
    steps.forEach(s => s.className = "loading-step");
    steps[0].className = "loading-step active";
    
    let stepTimer1 = setTimeout(() => {
      steps[0].className = "loading-step completed";
      steps[1].className = "loading-step active";
    }, 900);
    
    let stepTimer2 = setTimeout(() => {
      steps[1].className = "loading-step completed";
      steps[2].className = "loading-step active";
    }, 1800);

    let stepTimer3 = setTimeout(() => {
      steps[2].className = "loading-step completed";
      steps[3].className = "loading-step active";
    }, 2700);

    try {
      const response = await fetch("/api/analyze-journal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          journal_text: text,
          mood: activeMood,
          exam: activeExam
        })
      });
      
      // Clear timers
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      
      if (!response.ok) {
        throw new Error("Failed to process journal on server.");
      }
      
      const report = await response.json();
      
      // Render results
      renderAnalysisReport(report, text);
      
    } catch (error) {
      console.error(error);
      alert("Something went wrong connecting to the analysis server. Falling back to local checks.");
      analysisLoading.style.display = "none";
      analysisPlaceholder.style.display = "flex";
    }
  }

  function renderAnalysisReport(report, rawJournalText) {
    analysisLoading.style.display = "none";
    analysisReportView.style.display = "block";
    
    // Safety check redirect
    if (report.is_safety_trigger) {
      safetyWarningBox.style.display = "block";
      generalReportMetrics.style.display = "none";
      safetyMessageText.innerText = report.message;
      
      safetyHelplinesList.innerHTML = "";
      report.helplines.forEach(h => {
        const div = document.createElement("div");
        div.className = "helpline-item";
        div.innerHTML = `
          <div class="helpline-name">${h.name}</div>
          <div class="helpline-contact">${h.contact}</div>
          <div class="helpline-availability">${h.availability}</div>
        `;
        safetyHelplinesList.appendChild(div);
      });
      
      playPeacefulChime();
      return;
    }
    
    // Regular Report Rendering
    safetyWarningBox.style.display = "none";
    generalReportMetrics.style.display = "block";
    
    // 1. Stress Level
    currentStressLevel = report.stress_level;
    valStressLevel.innerText = `${report.stress_level}/10`;
    stressGaugeBar.style.width = `${report.stress_level * 10}%`;
    
    // Set color based on stress
    stressGaugeBar.className = "gauge-fill";
    if (report.stress_level <= 3) {
      valStressLevel.className = "metric-value stress-low";
      stressGaugeBar.style.background = "var(--accent-emerald)";
    } else if (report.stress_level <= 6) {
      valStressLevel.className = "metric-value stress-medium";
      stressGaugeBar.style.background = "var(--accent-amber)";
    } else {
      valStressLevel.className = "metric-value stress-high";
      stressGaugeBar.style.background = "var(--accent-red)";
    }
    
    // 2. Burnout Risk
    valBurnoutRisk.innerText = report.burnout_risk;
    burnoutBadgeLbl.innerText = `${report.burnout_risk} Risk`;
    burnoutBadgeLbl.className = "burnout-badge";
    if (report.burnout_risk.toLowerCase() === "high") {
      burnoutBadgeLbl.style.background = "rgba(239, 68, 68, 0.15)";
      burnoutBadgeLbl.style.color = "var(--accent-red)";
      burnoutBadgeLbl.style.borderColor = "rgba(239, 68, 68, 0.3)";
    } else if (report.burnout_risk.toLowerCase() === "medium") {
      burnoutBadgeLbl.style.background = "rgba(245, 158, 11, 0.15)";
      burnoutBadgeLbl.style.color = "var(--accent-amber)";
      burnoutBadgeLbl.style.borderColor = "rgba(245, 158, 11, 0.3)";
    } else {
      burnoutBadgeLbl.style.background = "rgba(16, 185, 129, 0.15)";
      burnoutBadgeLbl.style.color = "var(--accent-emerald)";
      burnoutBadgeLbl.style.borderColor = "rgba(16, 185, 129, 0.3)";
    }
    
    // 3. Emotional Distribution
    emotionDistributionBars.innerHTML = "";
    const emotions = report.emotional_state_distribution || {};
    
    // Color mapping
    const emotionColors = {
      anxiety: "var(--accent-amber)",
      focus: "var(--accent-indigo)",
      burnout: "var(--accent-red)",
      hopefulness: "var(--accent-emerald)",
      frustration: "#a855f7"
    };
    
    Object.keys(emotions).forEach(emo => {
      const pct = emotions[emo];
      const color = emotionColors[emo] || "var(--accent-teal)";
      const row = document.createElement("div");
      row.className = "emotion-bar-row";
      row.innerHTML = `
        <span class="emotion-bar-label">${emo}</span>
        <div class="emotion-bar-track">
          <div class="emotion-bar-fill" style="width: ${pct}%; background-color: ${color}"></div>
        </div>
        <span class="emotion-bar-pct">${pct}%</span>
      `;
      emotionDistributionBars.appendChild(row);
    });
    
    // 4. Triggers
    currentTriggers = report.primary_triggers || [];
    triggersList.innerHTML = "";
    currentTriggers.forEach(trig => {
      const li = document.createElement("li");
      li.innerText = trig;
      triggersList.appendChild(li);
    });
    
    // 5. Cognitive Patterns
    patternsList.innerHTML = "";
    const patterns = report.detected_cognitive_patterns || [];
    if (patterns.length === 0) {
      const li = document.createElement("li");
      li.innerText = "No severe cognitive biases detected today.";
      patternsList.appendChild(li);
    } else {
      patterns.forEach(pat => {
        const li = document.createElement("li");
        li.innerText = pat;
        patternsList.appendChild(li);
      });
    }
    
    // 6. Insight & Motivation Quote
    insightTextBox.innerText = report.empathetic_insight;
    motivationTextLbl.innerText = report.motivational_boost;
    examTagLbl.innerText = `${activeExam} PREP`;
    
    // 7. Coping strategies
    copingStrategiesContainer.innerHTML = "";
    const strategies = report.actionable_coping_strategies || [];
    strategies.forEach(strategy => {
      const sDiv = document.createElement("div");
      sDiv.className = "coping-card-item";
      sDiv.innerHTML = `
        <div class="coping-card-header">
          <h4 class="coping-card-title">${strategy.title}</h4>
          <span class="coping-time-badge">${strategy.time_required}</span>
        </div>
        <p class="coping-card-desc">${strategy.description}</p>
      `;
      copingStrategiesContainer.appendChild(sDiv);
    });
    
    // 8. Guided mindfulness
    const mindfulness = report.personalized_mindfulness_exercise || {};
    exerciseNameLbl.innerText = mindfulness.name || "Focus Breathing";
    exerciseInstructionsLbl.innerText = mindfulness.instructions || "Focus on your breath.";
    exerciseDurationLbl.innerText = `Suggested Duration: ${mindfulness.duration_minutes || 4} Mins`;
    
    // --- PERSISTENCE TO LOCAL STORAGE ---
    saveWellnessRecordToLocal({
      timestamp: new Date().toISOString(),
      exam: activeExam,
      mood: activeMood,
      stress_level: report.stress_level,
      burnout_risk: report.burnout_risk,
      primary_trigger: currentTriggers[0] || "General Stress",
      journal_text: rawJournalText
    });
    
    showToast("Wellness Log analyzed and saved locally!");
  }


  // --- CONVERSATIONAL AI COMPANION (CHAT) ---

  async function sendChatMessage() {
    const text = chatUserInput.value.trim();
    if (!text) return;
    
    // User message rendering
    appendMessage("user", text);
    chatUserInput.value = "";
    
    // Add temporary companion bubble
    const typingBubble = appendMessage("companion", "🧠 MindBuddy is reflection-typing...");
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    
    // Construct message log
    chatHistory.push({ role: "user", content: text });
    
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: chatHistory,
          exam: activeExam,
          stress_level: currentStressLevel,
          triggers: currentTriggers
        })
      });
      
      // Remove typing bubble
      typingBubble.remove();
      
      if (!response.ok) {
         throw new Error("Chat service failure.");
      }
      
      const replyData = await response.json();
      
      // Update local chat logs
      appendMessage("companion", replyData.reply);
      chatHistory.push({ role: "assistant", content: replyData.reply });
      
      // Load suggestions
      renderSuggestionChips(replyData.suggested_quick_prompts);
      
    } catch (e) {
      typingBubble.remove();
      appendMessage("companion", "I experienced a minor connection hiccup, but I am still here. Let's focus on small study steps. What's on your schedule next?");
      console.error(e);
    }
    
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  }

  function appendMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender === "user" ? "user-message" : "companion-message"}`;
    msgDiv.innerHTML = `
      <div class="message-bubble">${text}</div>
    `;
    chatMessagesContainer.appendChild(msgDiv);
    return msgDiv;
  }

  function renderSuggestionChips(chips) {
    chatSuggestionChips.innerHTML = "";
    if (chips && chips.length > 0) {
      chips.forEach(chip => {
        const btn = document.createElement("button");
        btn.className = "suggestion-chip";
        btn.innerText = chip;
        chatSuggestionChips.appendChild(btn);
      });
    }
  }


  // --- MINDFULNESS BOX BREATHING WIDGET ---

  function startBreathingExercise() {
    if (breathingInterval) return;
    
    breathingCycle = 1;
    breathingPhase = 0;
    breathingSeconds = 0;
    
    startBreathingBtn.disabled = true;
    stopBreathingBtn.disabled = false;
    
    runBreathingPulse();
    breathingInterval = setInterval(runBreathingPulse, 1000);
  }

  function runBreathingPulse() {
    breathingSeconds++;
    
    // phase lengths are strictly 4 seconds in box breathing
    const phaseLimit = 4;
    
    if (breathingSeconds > phaseLimit) {
      breathingSeconds = 1;
      breathingPhase = (breathingPhase + 1) % 4;
      if (breathingPhase === 0) {
        breathingCycle++;
        if (breathingCycle > 4) {
          stopBreathingExercise();
          breathingGuide.innerText = "Complete";
          breathingTimerDisplay.innerText = "4 cycles completed!";
          playPeacefulChime();
          return;
        }
      }
    }
    
    breathingTimerDisplay.innerText = `Cycle ${breathingCycle}/4 • ${breathingSeconds}s`;
    
    // Set circle transitions & text prompt based on phase
    if (breathingPhase === 0) {
      // Inhale
      breathingCircle.className = "breathing-circle-inner inhale";
      breathingGuide.innerText = "Breathe In...";
    } else if (breathingPhase === 1) {
      // Hold full
      breathingCircle.className = "breathing-circle-inner hold-full";
      breathingGuide.innerText = "Hold Breath...";
    } else if (breathingPhase === 2) {
      // Exhale
      breathingCircle.className = "breathing-circle-inner exhale";
      breathingGuide.innerText = "Exhale Slow...";
    } else if (breathingPhase === 3) {
      // Hold empty
      breathingCircle.className = "breathing-circle-inner hold-empty";
      breathingGuide.innerText = "Hold Empty...";
    }
  }

  function stopBreathingExercise() {
    if (breathingInterval) {
      clearInterval(breathingInterval);
      breathingInterval = null;
    }
    
    startBreathingBtn.disabled = false;
    stopBreathingBtn.disabled = true;
    breathingCircle.className = "breathing-circle-inner";
    breathingGuide.innerText = "Paused";
  }


  // --- POMODORO STUDY TIMER ---

  function startPomodoroStudy() {
    stopPomodoroTimer();
    timerMode = "study";
    timerTotalDuration = 25 * 60;
    timerSecondsLeft = timerTotalDuration;
    timerBadge.innerText = "Study Session";
    timerBadge.style.color = "var(--accent-indigo)";
    runPomodoroTick();
    pomodoroTimer = setInterval(runPomodoroTick, 1000);
  }

  function startPomodoroBreak() {
    stopPomodoroTimer();
    timerMode = "break";
    timerTotalDuration = 5 * 60;
    timerSecondsLeft = timerTotalDuration;
    timerBadge.innerText = "Mindfulness Break";
    timerBadge.style.color = "var(--accent-teal)";
    runPomodoroTick();
    pomodoroTimer = setInterval(runPomodoroTick, 1000);
  }

  function runPomodoroTick() {
    if (timerSecondsLeft <= 0) {
      stopPomodoroTimer();
      playPeacefulChime();
      
      if (timerMode === "study") {
        timerDisplay.innerText = "05:00";
        alert("Study session complete! Time to take a relaxing 5-minute breathing break.");
        startPomodoroBreak();
      } else {
        timerDisplay.innerText = "25:00";
        alert("Break complete! Ready to start study session focused and calm?");
        startPomodoroStudy();
      }
      return;
    }
    
    timerSecondsLeft--;
    
    // Formatting
    const min = Math.floor(timerSecondsLeft / 60).toString().padStart(2, "0");
    const sec = (timerSecondsLeft % 60).toString().padStart(2, "0");
    timerDisplay.innerText = `${min}:${sec}`;
    
    // Progress calculation
    const pct = (timerSecondsLeft / timerTotalDuration) * 100;
    timerProgress.style.width = `${pct}%`;
  }

  function stopPomodoroTimer() {
    if (pomodoroTimer) {
      clearInterval(pomodoroTimer);
      pomodoroTimer = null;
    }
  }

  function resetPomodoroTimer() {
    stopPomodoroTimer();
    timerMode = "study";
    timerTotalDuration = 25 * 60;
    timerSecondsLeft = timerTotalDuration;
    timerDisplay.innerText = "25:00";
    timerBadge.innerText = "Study Session";
    timerBadge.style.color = "var(--accent-indigo)";
    timerProgress.style.width = "100%";
  }


  // --- LOCAL HISTORY LOG DATABASE (LOCAL STORAGE) ---

  function saveWellnessRecordToLocal(record) {
    let logs = [];
    try {
      const stored = localStorage.getItem("zenexam_logs");
      if (stored) {
        logs = JSON.parse(stored);
      }
    } catch (e) {
      console.error("Local storage error:", e);
    }
    
    // Insert at front
    logs.unshift(record);
    
    // Keep max 30 records to save browser quota
    if (logs.length > 30) {
      logs = logs.slice(0, 30);
    }
    
    try {
      localStorage.setItem("zenexam_logs", JSON.stringify(logs));
    } catch (e) {
      console.error("Save error:", e);
    }
    
    updateTimelineHistory();
  }

  function updateTimelineHistory() {
    let logs = [];
    try {
      const stored = localStorage.getItem("zenexam_logs");
      if (stored) {
        logs = JSON.parse(stored);
      }
    } catch (e) {
      console.error(e);
    }
    
    historyCount.innerText = logs.length;
    
    if (logs.length === 0) {
      historyAvgStress.innerText = "0/10";
      historyTopTrigger.innerText = "None";
      historyActionsBar.style.display = "none";
      historyLogsList.innerHTML = `
        <div class="empty-history-placeholder">
          <span class="empty-icon">📈</span>
          <p>No historical entries found yet. Complete your first journal analysis under the "Daily Journal" tab to begin tracking patterns over time.</p>
        </div>
      `;
      return;
    }
    
    historyActionsBar.style.display = "flex";
    
    // Calculations
    let totalStress = 0;
    let triggerCounts = {};
    
    historyLogsList.innerHTML = "";
    
    logs.forEach(log => {
      totalStress += log.stress_level;
      
      const tr = log.primary_trigger || "General Stress";
      triggerCounts[tr] = (triggerCounts[tr] || 0) + 1;
      
      // Render timeline element
      const logDate = new Date(log.timestamp).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      const logItem = document.createElement("div");
      logItem.className = "history-item";
      logItem.innerHTML = `
        <div class="history-item-header">
          <span class="history-date-exam">${logDate} — Prep for ${log.exam}</span>
          <span class="history-mood-badge">Mood: ${log.mood}</span>
        </div>
        <div class="history-item-metrics">
          <span>Stress Level: <strong>${log.stress_level}/10</strong></span>
          <span>Burnout Zone: <strong>${log.burnout_risk}</strong></span>
          <span>Stress Trigger: <strong>${log.primary_trigger}</strong></span>
        </div>
        <p class="history-item-text">${log.journal_text}</p>
      `;
      historyLogsList.appendChild(logItem);
    });
    
    // Stress Avg
    const avg = (totalStress / logs.length).toFixed(1);
    historyAvgStress.innerText = `${avg}/10`;
    
    // Top Trigger
    let maxTrigger = "None";
    let maxCount = 0;
    Object.keys(triggerCounts).forEach(tr => {
      if (triggerCounts[tr] > maxCount) {
        maxCount = triggerCounts[tr];
        maxTrigger = tr;
      }
    });
    historyTopTrigger.innerText = maxTrigger;
  }

  function clearLocalHistory() {
    if (confirm("Are you sure you want to delete all historical wellness logs? This action is permanent and cannot be undone.")) {
      localStorage.removeItem("zenexam_logs");
      updateTimelineHistory();
      showToast("Historical logs cleared successfully.");
    }
  }
});
