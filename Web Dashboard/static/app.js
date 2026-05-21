/* ============================================================
   Radar Web Dashboard — client
   Live SSE -> radar canvas + metrics + trend + DB table
   ============================================================ */
(() => {
  "use strict";

  const MAX_RANGE = 100;        // cm shown on the radar
  const BUZZ_RANGE = 30;        // cm proximity alert
  const TRAIL_MS = 1600;        // sweep persistence
  const TREND_POINTS = 200;

  // ---- live state from server ----
  let live = { angle: 90, distance: -1, mode: 0, buzzer: 0, source: "STARTING" };
  let lastServerAngle = 90;
  // smoothed angle so the sweep glides between samples
  let drawAngle = 90;
  const blips = [];             // {angle, distance, t}
  const trend = [];             // {distance, t}

  // ---------------------------------------------------------
  // SSE connection
  // ---------------------------------------------------------
  function connect() {
    const es = new EventSource("/api/stream");
    es.onmessage = (e) => {
      const d = JSON.parse(e.data);
      live = d;
      applyState(d);
    };
    es.onerror = () => {
      setStatus("error", "STREAM LOST", "reconnecting…");
      es.close();
      setTimeout(connect, 1500);
    };
  }

  // ---------------------------------------------------------
  // Apply a reading to metrics / status / data buffers
  // ---------------------------------------------------------
  const $ = (id) => document.getElementById(id);

  function applyState(d) {
    lastServerAngle = d.angle;

    // metrics
    $("mAngle").textContent = d.angle;
    $("mDist").textContent = d.distance === -1 ? "--" : d.distance;
    $("angleBar").style.width = (d.angle / 180 * 100) + "%";
    const distPct = d.distance === -1 ? 0 : Math.min(d.distance, MAX_RANGE) / MAX_RANGE * 100;
    $("distBar").style.width = distPct + "%";

    // mode chip
    const modeChip = $("modeChip");
    $("mMode").textContent = d.mode === 1 ? "MANUAL" : "AUTO";
    modeChip.classList.toggle("is-manual", d.mode === 1);

    // buzzer chip
    const buzzChip = $("buzzChip");
    const buzzing = d.buzzer === 1;
    $("mBuzz").textContent = buzzing ? "ALERT" : "OFF";
    buzzChip.classList.toggle("is-alert", buzzing);
    buzzChip.classList.toggle("is-on", !buzzing && d.distance !== -1);

    // proximity card
    const rc = $("rangeCard");
    const rt = $("rangeText");
    rc.classList.remove("safe", "warn", "danger");
    if (d.distance === -1) {
      rt.textContent = "No echo · out of range";
    } else if (d.distance < BUZZ_RANGE) {
      rc.classList.add("danger");
      rt.textContent = `⚠ Object ${d.distance} cm — within alert zone`;
    } else if (d.distance < 60) {
      rc.classList.add("warn");
      rt.textContent = `Object detected at ${d.distance} cm`;
    } else {
      rc.classList.add("safe");
      rt.textContent = `Clear · nearest ${d.distance} cm`;
    }

    // status pill
    const map = {
      LIVE:     ["live", "LIVE", `${d.port} @ ${d.baud}`],
      SIM:      ["sim", "SIMULATION", d.reason || "no live serial data"],
      PORT_BUSY:["error", "PORT BUSY", d.reason || "serial port in use"],
      NO_DATA:  ["error", "NO DATA", d.reason || "port open, no packets"],
      STARTING: ["idle", "CONNECTING…", d.reason || ""],
    };
    const [cls, txt, meta] = map[d.source] || map.STARTING;
    setStatus(cls, txt, meta);

    $("footStats").textContent =
      `readings ${d.total_readings} · logged ${d.logged_rows}`;

    // buffers for radar blips + trend
    const now = performance.now();
    if (d.distance > 0 && d.distance <= MAX_RANGE) {
      blips.push({ angle: d.angle, distance: d.distance, t: now });
    }
    trend.push({ distance: d.distance, t: Date.now() });
    if (trend.length > TREND_POINTS) trend.shift();
  }

  function setStatus(cls, text, meta) {
    const pill = $("statusPill");
    pill.className = "pill pill--" + cls;
    $("statusText").textContent = text;
    $("sourceMeta").textContent = meta || "—";
  }

  // ---------------------------------------------------------
  // Radar canvas
  // ---------------------------------------------------------
  const radar = $("radar");
  const rx = radar.getContext("2d");

  function drawRadar() {
    const W = radar.width, H = radar.height;
    const cx = W / 2, cy = H - 24;
    const R = Math.min(W / 2 - 30, H - 50);

    rx.clearRect(0, 0, W, H);

    // glow base
    const bg = rx.createRadialGradient(cx, cy, 0, cx, cy, R);
    bg.addColorStop(0, "rgba(43,255,158,0.05)");
    bg.addColorStop(1, "rgba(43,255,158,0)");
    rx.fillStyle = bg;
    rx.beginPath(); rx.arc(cx, cy, R, Math.PI, 2 * Math.PI); rx.fill();

    // range rings
    rx.lineWidth = 1;
    rx.font = "11px JetBrains Mono, monospace";
    rx.textAlign = "center";
    for (let i = 1; i <= 5; i++) {
      const r = R * i / 5;
      rx.strokeStyle = "rgba(43,255,158,0.16)";
      rx.beginPath(); rx.arc(cx, cy, r, Math.PI, 2 * Math.PI); rx.stroke();
      rx.fillStyle = "rgba(43,255,158,0.45)";
      rx.fillText(i * 20 + "cm", cx + r - 16, cy + 14);
    }

    // angle spokes + labels
    for (let a = 0; a <= 180; a += 30) {
      const rad = a * Math.PI / 180;
      const ex = cx + R * Math.cos(Math.PI - rad);
      const ey = cy - R * Math.sin(rad);
      rx.strokeStyle = "rgba(43,255,158,0.12)";
      rx.beginPath(); rx.moveTo(cx, cy); rx.lineTo(ex, ey); rx.stroke();
      rx.fillStyle = "rgba(43,255,158,0.5)";
      rx.fillText(a + "°", cx + (R + 16) * Math.cos(Math.PI - rad), cy - (R + 16) * Math.sin(rad) + 4);
    }

    // smooth the sweep toward latest server angle
    drawAngle += (lastServerAngle - drawAngle) * 0.25;
    const sweepRad = drawAngle * Math.PI / 180;
    const sx = cx + R * Math.cos(Math.PI - sweepRad);
    const sy = cy - R * Math.sin(sweepRad);

    // sweep trail (a wedge fading behind the beam)
    const trail = rx.createRadialGradient(cx, cy, 0, cx, cy, R);
    trail.addColorStop(0, "rgba(43,255,158,0.28)");
    trail.addColorStop(1, "rgba(43,255,158,0)");
    rx.fillStyle = trail;
    rx.beginPath();
    rx.moveTo(cx, cy);
    rx.arc(cx, cy, R, Math.PI - sweepRad, Math.PI - sweepRad + 0.34);
    rx.closePath();
    rx.fill();

    // sweep beam
    rx.strokeStyle = "rgba(43,255,158,0.9)";
    rx.lineWidth = 2;
    rx.shadowColor = "rgba(43,255,158,0.8)";
    rx.shadowBlur = 12;
    rx.beginPath(); rx.moveTo(cx, cy); rx.lineTo(sx, sy); rx.stroke();
    rx.shadowBlur = 0;

    // blips with fade
    const now = performance.now();
    for (let i = blips.length - 1; i >= 0; i--) {
      const b = blips[i];
      const age = now - b.t;
      if (age > TRAIL_MS) { blips.splice(i, 1); continue; }
      const life = 1 - age / TRAIL_MS;
      const rad = b.angle * Math.PI / 180;
      const pr = (b.distance / MAX_RANGE) * R;
      const px = cx + pr * Math.cos(Math.PI - rad);
      const py = cy - pr * Math.sin(rad);
      const danger = b.distance < BUZZ_RANGE;
      const col = danger ? "255,77,87" : "43,255,158";
      rx.fillStyle = `rgba(${col},${life})`;
      rx.shadowColor = `rgba(${col},${life})`;
      rx.shadowBlur = 14 * life;
      rx.beginPath(); rx.arc(px, py, 5 * life + 2, 0, 2 * Math.PI); rx.fill();
      rx.shadowBlur = 0;
    }

    requestAnimationFrame(drawRadar);
  }

  // ---------------------------------------------------------
  // Trend chart (hand-drawn, no deps)
  // ---------------------------------------------------------
  const trendC = $("trend");
  const tx = trendC.getContext("2d");

  function drawTrend() {
    const W = trendC.width, H = trendC.height;
    const pad = 26;
    tx.clearRect(0, 0, W, H);

    // gridlines + y labels (0..100cm)
    tx.font = "10px JetBrains Mono, monospace";
    tx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const y = pad + (H - 2 * pad) * i / 4;
      tx.strokeStyle = "rgba(255,255,255,0.05)";
      tx.beginPath(); tx.moveTo(pad, y); tx.lineTo(W - 6, y); tx.stroke();
      tx.fillStyle = "rgba(120,160,150,0.6)";
      tx.fillText((100 - i * 25) + "", pad - 6, y + 3);
    }

    if (trend.length < 2) { requestAnimationFrame(drawTrend); return; }

    const n = trend.length;
    const xAt = (i) => pad + (W - pad - 6) * (i / (TREND_POINTS - 1));
    const yAt = (d) => {
      const v = d === -1 ? 0 : Math.min(d, MAX_RANGE);
      return pad + (H - 2 * pad) * (1 - v / MAX_RANGE);
    };

    // area fill
    const grad = tx.createLinearGradient(0, pad, 0, H - pad);
    grad.addColorStop(0, "rgba(43,255,158,0.30)");
    grad.addColorStop(1, "rgba(43,255,158,0)");
    tx.beginPath();
    tx.moveTo(xAt(0), H - pad);
    trend.forEach((p, i) => tx.lineTo(xAt(i), yAt(p.distance)));
    tx.lineTo(xAt(n - 1), H - pad);
    tx.closePath();
    tx.fillStyle = grad; tx.fill();

    // line
    tx.beginPath();
    trend.forEach((p, i) => { const fn = i ? "lineTo" : "moveTo"; tx[fn](xAt(i), yAt(p.distance)); });
    tx.strokeStyle = "rgba(43,255,158,0.95)";
    tx.lineWidth = 2;
    tx.shadowColor = "rgba(43,255,158,0.6)"; tx.shadowBlur = 8;
    tx.stroke();
    tx.shadowBlur = 0;

    // head dot
    const hx = xAt(n - 1), hy = yAt(trend[n - 1].distance);
    tx.fillStyle = "#eafff5";
    tx.beginPath(); tx.arc(hx, hy, 3, 0, 2 * Math.PI); tx.fill();

    requestAnimationFrame(drawTrend);
  }

  // ---------------------------------------------------------
  // Database log table (polls persisted rows)
  // ---------------------------------------------------------
  async function refreshLog() {
    try {
      const res = await fetch("/api/history?limit=40");
      const rows = await res.json();
      const body = $("logBody");
      if (!rows.length) return;
      body.innerHTML = rows.map((r) => {
        const t = (r.timestamp || "").replace("T", " ").slice(11, 19);
        const dist = r.distance === -1 ? "OUT" : r.distance + " cm";
        const mode = r.mode === 1 ? "MANUAL" : "AUTO";
        const buzz = r.buzzer_active === 1
          ? '<td class="alert">ON</td>' : "<td>off</td>";
        return `<tr><td>${t}</td><td>${r.angle}°</td><td>${dist}</td><td>${mode}</td>${buzz}</tr>`;
      }).join("");
    } catch (_) { /* keep last view on transient errors */ }
  }

  // ---------------------------------------------------------
  // boot
  // ---------------------------------------------------------
  connect();
  requestAnimationFrame(drawRadar);
  requestAnimationFrame(drawTrend);
  refreshLog();
  setInterval(refreshLog, 2000);
})();
