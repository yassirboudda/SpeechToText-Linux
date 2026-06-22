const $ = (id) => document.getElementById(id);

async function load() {
  const data = await chrome.storage.local.get(["autoTypeAtCursor"]);
  $("autoType").checked = data.autoTypeAtCursor !== false;
}

async function save() {
  await chrome.storage.local.set({ autoTypeAtCursor: $("autoType").checked });
  $("toast").textContent = "Saved";
  setTimeout(() => { $("toast").textContent = ""; }, 2000);
}

$("saveBtn").addEventListener("click", save);
$("testBtn").addEventListener("click", async () => {
  $("toast").textContent = "Testing…";
  const resp = await chrome.runtime.sendMessage({ action: "testApiKey" });
  $("toast").textContent = resp?.ok ? "API key works ✓" : "API key test failed";
});

load();
