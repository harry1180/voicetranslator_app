let ws = null;
let mediaRecorder = null;

const logEl = document.getElementById("log");
const notesEl = document.getElementById("notes");
const roomEl = document.getElementById("room");
const modeEl = document.getElementById("mode");
const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");

function log(line) {
  logEl.textContent += `${line}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

function appendNotes(line) {
  notesEl.textContent += line;
  notesEl.scrollTop = notesEl.scrollHeight;
}

async function start() {
  const room = roomEl.value.trim();
  const mode = modeEl.value;
  if (!room) return alert("Enter a room id.");

  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws?room=${encodeURIComponent(room)}&mode=${encodeURIComponent(mode)}`);
  ws.binaryType = "arraybuffer";

  ws.onopen = async () => {
    log("WS connected.");

    if (mode === "speaker") {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Use WebM/Opus (common in Chrome). This is "containerized" audio, so server should NOT set encoding/sample_rate. :contentReference[oaicite:9]{index=9}
      mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });

      mediaRecorder.addEventListener("dataavailable", async (evt) => {
        if (evt.data.size > 0 && ws && ws.readyState === 1) {
          const buf = await evt.data.arrayBuffer();
          ws.send(buf);
        }
      });

      mediaRecorder.start(250);
      log("Mic streaming started.");
    }
  };

  ws.onmessage = (evt) => {
    let msg;
    try { msg = JSON.parse(evt.data); } catch { return; }

    if (msg.type === "status") log(`STATUS: ${msg.status}`);
    if (msg.type === "error") log(`ERROR (${msg.where}): ${msg.message}`);

    if (msg.type === "stt") {
      // Append final utterances to the notes
      if (msg.isFinal && msg.transcript) appendNotes(`${msg.transcript} `);
    }
  };

  ws.onclose = () => log("WS closed.");
  ws.onerror = (e) => log(`WS error: ${e.message || e}`);

  startBtn.disabled = true;
  stopBtn.disabled = false;
}

function stop() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    log("Mic streaming stopped.");
  }
  mediaRecorder = null;

  if (ws && ws.readyState === 1) ws.close();
  ws = null;

  startBtn.disabled = false;
  stopBtn.disabled = true;
}

startBtn.addEventListener("click", start);
stopBtn.addEventListener("click", stop);

