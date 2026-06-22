const MISTRAL_API_URL = "https://api.mistral.ai/v1/audio/transcriptions";
const MISTRAL_MODEL = "voxtral-mini-latest";
const DEFAULT_API_KEY = "xgXbsTF4N7emTwms9JowAKVDHGWNEpJ0";

async function getApiKey() {
  const { mistralApiKey } = await chrome.storage.local.get(["mistralApiKey"]);
  return mistralApiKey || DEFAULT_API_KEY;
}

chrome.runtime.onInstalled.addListener(async () => {
  const existing = await chrome.storage.local.get(["mistralApiKey", "autoTypeAtCursor", "micGranted"]);
  const patch = {};
  if (!existing.mistralApiKey) patch.mistralApiKey = DEFAULT_API_KEY;
  if (existing.autoTypeAtCursor === undefined) patch.autoTypeAtCursor = true;
  if (Object.keys(patch).length) await chrome.storage.local.set(patch);
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    try {
      if (msg.action === "transcribe") {
        const text = await transcribeBase64(msg.base64, msg.mimeType || "audio/webm");
        const { autoTypeAtCursor } = await chrome.storage.local.get(["autoTypeAtCursor"]);
        if (autoTypeAtCursor !== false && msg.tabId) {
          await insertTextInTab(msg.tabId, text);
        }
        sendResponse({ ok: true, text });
        return;
      }

      if (msg.action === "testApiKey") {
        const ok = await testApiKey(msg.apiKey || (await getApiKey()));
        sendResponse({ ok });
        return;
      }

      sendResponse({ ok: false, error: "Unknown action" });
    } catch (err) {
      sendResponse({ ok: false, error: String(err?.message || err) });
    }
  })();
  return true;
});

async function transcribeBase64(base64, mimeType) {
  const apiKey = await getApiKey();
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const blob = new Blob([bytes], { type: mimeType });
  const form = new FormData();
  form.append("file", blob, mimeType.includes("wav") ? "recording.wav" : "recording.webm");
  form.append("model", MISTRAL_MODEL);

  const response = await fetch(MISTRAL_API_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}` },
    body: form,
  });

  if (!response.ok) {
    const detail = (await response.text()).slice(0, 200);
    throw new Error(`Transcription failed (${response.status}): ${detail}`);
  }
  const result = await response.json();
  return (result.text || "").trim();
}

async function testApiKey(apiKey) {
  const response = await fetch("https://api.mistral.ai/v1/models", {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  return response.ok;
}

async function insertTextInTab(tabId, text) {
  if (!text) return;
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: (value) => {
        const active = document.activeElement;
        if (!active) return false;
        if (active.isContentEditable) {
          active.textContent = (active.textContent || "") + value;
          return true;
        }
        if (active.tagName === "TEXTAREA" || active.tagName === "INPUT") {
          const start = active.selectionStart ?? active.value.length;
          const end = active.selectionEnd ?? active.value.length;
          active.value = active.value.slice(0, start) + value + active.value.slice(end);
          active.dispatchEvent(new Event("input", { bubbles: true }));
          active.selectionStart = active.selectionEnd = start + value.length;
          return true;
        }
        return false;
      },
      args: [text],
    });
  } catch {
    // chrome:// pages etc.
  }
}
