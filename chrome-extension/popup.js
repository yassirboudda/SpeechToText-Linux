const $ = (id) => document.getElementById(id);
const MAX_DURATION_SEC = 70; // 1:10

let recording = false;
let timer = null;
let currentTabId = null;
let mediaRecorder = null;
let mediaStream = null;
let chunks = [];

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTabId = tab?.id || null;
  $("recordBtn").addEventListener("click", toggleRecording);
  $("copyBtn").addEventListener("click", copyText);
  $("clearBtn").addEventListener("click", () => { $("output").value = ""; });
  $("settingsBtn").addEventListener("click", () => chrome.runtime.openOptionsPage());

  const { micGranted } = await chrome.storage.local.get(["micGranted"]);
  if (!micGranted) {
    setStatus("Click Start — Chrome will ask to use your microphone");
  }
}

async function toggleRecording() {
  if (recording) await stop();
  else await start();
}

function pickMimeType() {
  const types = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return "";
}

async function requestMicrophone() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Microphone API not available in this browser");
  }
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
  await chrome.storage.local.set({ micGranted: true });
  return stream;
}

async function start() {
  try {
    setStatus("Requesting microphone access…");
    $("recordBtn").disabled = true;

    if (!mediaStream) {
      mediaStream = await requestMicrophone();
    }

    chunks = [];
    const mimeType = pickMimeType();
    mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorder.start(250);
    recording = true;
    $("recordBtn").disabled = false;
    $("recordBtn").textContent = "⏹ Stop & Transcribe";
    $("recordBtn").classList.add("recording");
    $("hint").textContent = "Keep this popup open while recording";

    let elapsed = 0;
    setStatus(`Recording… ${formatTime(elapsed)} / ${formatTime(MAX_DURATION_SEC)}`);
    timer = setInterval(async () => {
      elapsed += 1;
      setStatus(`Recording… ${formatTime(elapsed)} / ${formatTime(MAX_DURATION_SEC)}`);
      if (elapsed >= MAX_DURATION_SEC) await stop();
    }, 1000);
  } catch (err) {
    resetUi();
    const name = err?.name || "";
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      setStatus("Microphone blocked — click the lock icon in the address bar and allow mic, then retry");
    } else if (name === "NotFoundError") {
      setStatus("No microphone found on this device");
    } else {
      setStatus(err?.message || "Could not access microphone");
    }
  }
}

async function stop() {
  if (timer) { clearInterval(timer); timer = null; }
  recording = false;
  $("recordBtn").disabled = true;
  $("recordBtn").textContent = "Transcribing…";
  $("hint").textContent = "";
  setStatus("Sending audio to Mistral Voxtral…");

  try {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      throw new Error("No active recording");
    }

    const blob = await new Promise((resolve, reject) => {
      mediaRecorder.onstop = () => {
        resolve(new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" }));
      };
      mediaRecorder.onerror = () => reject(new Error("Recording error"));
      mediaRecorder.stop();
    });

    if (blob.size < 1000) {
      throw new Error("Recording too short — speak louder or longer");
    }

    const base64 = await blobToBase64(blob);
    const resp = await chrome.runtime.sendMessage({
      action: "transcribe",
      base64,
      mimeType: blob.type,
      tabId: currentTabId,
    });

    resetUi();

    if (!resp?.ok) {
      setStatus(resp?.error || "Transcription failed");
      return;
    }

    $("output").value = resp.text || "";
    setStatus(resp.text ? "Done — copied to clipboard" : "No speech detected");
    if (resp.text) {
      try { await navigator.clipboard.writeText(resp.text); } catch {}
    }
  } catch (err) {
    resetUi();
    setStatus(err?.message || "Transcription failed");
  }
}

function resetUi() {
  recording = false;
  $("recordBtn").disabled = false;
  $("recordBtn").textContent = "🎙 Start Recording";
  $("recordBtn").classList.remove("recording");
  $("hint").textContent = "Microphone permission is requested when you click Start";
}

function setStatus(text) {
  $("status").textContent = text;
}

function formatTime(sec) {
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function copyText() {
  const text = $("output").value.trim();
  if (!text) return;
  await navigator.clipboard.writeText(text);
  setStatus("Copied to clipboard");
}

init();
