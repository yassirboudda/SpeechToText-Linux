async function openRecorder() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const tabId = tab?.id ?? "";
  await chrome.tabs.create({
    url: chrome.runtime.getURL(`recorder.html?tabId=${tabId}`),
    active: true,
  });
  window.close();
}

document.getElementById("openBtn").addEventListener("click", openRecorder);
document.getElementById("settingsBtn").addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});
