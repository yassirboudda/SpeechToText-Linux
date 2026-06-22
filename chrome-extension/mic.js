export const MAX_DURATION_SEC = 70;

export function extensionSettingsUrl() {
  const site = `chrome-extension://${chrome.runtime.id}/`;
  return `chrome://settings/content/siteDetails?site=${encodeURIComponent(site)}`;
}

export function openExtensionSettings() {
  chrome.tabs.create({ url: extensionSettingsUrl() });
}

export async function queryMicState() {
  try {
    const perm = await navigator.permissions.query({ name: "microphone" });
    return perm.state;
  } catch {
    return "prompt";
  }
}

export async function requestMicrophoneStream() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Microphone API not available in this browser");
  }
  return navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
}

export function pickMimeType() {
  const types = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return "";
}

export function formatTime(sec) {
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
}

export function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
