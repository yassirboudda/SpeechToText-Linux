import {
  MAX_DURATION_SEC,
  blobToBase64,
  formatTime,
  openExtensionSettings,
  pickMimeType,
  queryMicState,
  requestMicrophoneStream,
} from "./mic.js";

const $ = (id) => document.getElementById(id);

let recording = false;
let timer = null;
let currentTabId = null;
let mediaRecorder = null;
let mediaStream = null;
let chunks = [];

async function init() {
  const params = new URLSearchParams(location.search);
  const tabId = Number(params.get("tabId"));
  if (Number.isFinite(tabId)) currentTabId = tabId;
  else {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTabId = tab?.id || null;
  }

  $("allowBtn").addEventListener("click", grantMicrophone);
  $("settingsBtn").addEventListener("click", openExtensionSettings);
  $("recordBtn").addEventListener("click", toggleRecording);
  $("copyBtn").addEventListener("click", copyText);
  $("clearBtn").addEventListener("click", () => { $("output").value = ""; });

  const state = await queryMicState();
  if (state === "granted") {
    try {
      mediaStream = await requestMicrophoneStream();
      showRecorder();
      return;
    } catch {
      // fall through to permission UI
    }
  }

  if (state === "denied") {
    showDenied();
  }
}

function showDenied() {
  setPermStatus("Microphone is blocked for this extension.");
  $("allowBtn").classList.add("hidden");
  $("settingsBtn").classList.remove("hidden");
}

function setPermStatus(text) {
  $("permPanel").querySelector("p").textContent = text;
}

async function grantMicrophone() {
  $("allowBtn").disabled = true;
  setPermStatus("Waiting for Chrome permission prompt…");

  try {
    mediaStream = await requestMicrophoneStream();
    await chrome.storage.local.set({ micGranted: true });
    showRecorder();
  } catch (err) {
    $("allowBtn").disabled = false;
    const name = err?.name || "";
    if (name === "NotAllowedError" || name === "PermissionDeniedError") {
      showDenied();
      setPermStatus(
        "Microphone access was blocked. Open extension settings, set Microphone to Allow, then reload this page."
      );
    } else if (name === "NotFoundError") {
      setPermStatus("No microphone found on this device.");
    } else {
      setPermStatus(err?.message || "Could not access microphone.");
    }
  }
}

function showRecorder() {
  $("permPanel").classList.add("hidden");
  $("recPanel").classList.remove("hidden");
  setStatus("Ready to record");
}

async function toggleRecording() {
  if (recording) await stop();
  else await start();
}

async function start() {
  try {
    if (!mediaStream || !mediaStream.active) {
      mediaStream = await requestMicrophoneStream();
    }

    chunks = [];
    const mimeType = pickMimeType();
    mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorder.start(250);
    recording = true;
    $("recordBtn").textContent = "⏹ Stop & Transcribe";
    $("recordBtn").classList.add("recording");
    $("hint").textContent = "Recording… keep this tab open";

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
      setStatus("Microphone lost — reload this page and allow access again");
      $("permPanel").classList.remove("hidden");
      $("recPanel").classList.add("hidden");
      showDenied();
    } else {
      setStatus(err?.message || "Could not start recording");
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
  $("hint").textContent = "Speak clearly, then click Stop & Transcribe";
}

function setStatus(text) {
  $("status").textContent = text;
}

async function copyText() {
  const text = $("output").value.trim();
  if (!text) return;
  await navigator.clipboard.writeText(text);
  setStatus("Copied to clipboard");
}

init();
