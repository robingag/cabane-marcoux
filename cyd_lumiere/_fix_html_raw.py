"""
Ajouter affichage bassins + raw + dompeur + temp dans la page HTML locale
"""

path = r"C:\Users\ryb086\OneDrive - Groupe R.Y. Beaudoin\Bureau\CLAUDE_CODE\cyd_lumiere\src\main.cpp"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_html = """  .status {
    margin-top: 20px;
    font-size: 12px;
    color: #666;
  }
</style>
</head>
<body>
  <h2>CYD Controleur (Local)</h2>
  <div class="light" id="light"></div>
  <button class="btn off" id="btn" onclick="toggle()">ON</button>
  <div class="status" id="status">Connecte</div>
<script>
  let state = false;
  function updateUI(on) {
    state = on;
    const light = document.getElementById('light');
    const btn = document.getElementById('btn');
    if (on) {
      light.classList.add('on');
      btn.textContent = 'OFF';
      btn.className = 'btn on';
    } else {
      light.classList.remove('on');
      btn.textContent = 'ON';
      btn.className = 'btn off';
    }
  }
  function toggle() {
    fetch('/toggle').then(r => r.json()).then(d => updateUI(d.on));
  }
  setInterval(() => {
    fetch('/state').then(r => r.json()).then(d => updateUI(d.on));
  }, 500);
</script>"""

new_html = """  .status {
    margin-top: 10px;
    font-size: 12px;
    color: #666;
  }
  .data-grid {
    width: 90%; max-width: 400px;
    margin-top: 20px;
  }
  .data-row {
    display: flex; justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid #2a2a4e;
  }
  .data-label { color: #66bbff; font-size: 14px; }
  .data-val { color: #00ffff; font-size: 14px; font-weight: bold; }
  .data-raw { color: #808080; font-size: 11px; }
  .bar-bg {
    width: 100%; height: 12px;
    background: #333; border-radius: 6px;
    margin-top: 4px; overflow: hidden;
  }
  .bar-fill {
    height: 100%; border-radius: 6px;
    transition: width 0.3s;
  }
</style>
</head>
<body>
  <h2>CYD Controleur (Local)</h2>
  <div class="light" id="light"></div>
  <button class="btn off" id="btn" onclick="toggle()">ON</button>
  <div class="data-grid">
    <div class="data-row">
      <span class="data-label">Dompeur</span>
      <span class="data-val" id="dompeur">--:--</span>
    </div>
    <div class="data-row">
      <span class="data-label">Temperature</span>
      <span class="data-val" id="temp">--</span>
    </div>
    <div class="data-row" style="flex-direction:column">
      <div style="display:flex;justify-content:space-between">
        <span class="data-label">Bassin 1</span>
        <span><span class="data-val" id="b1">0</span>% <span class="data-raw" id="r1"></span></span>
      </div>
      <div class="bar-bg"><div class="bar-fill" id="bar1" style="width:0%;background:#44ff44"></div></div>
    </div>
    <div class="data-row" style="flex-direction:column">
      <div style="display:flex;justify-content:space-between">
        <span class="data-label">Bassin 2</span>
        <span><span class="data-val" id="b2">0</span>% <span class="data-raw" id="r2"></span></span>
      </div>
      <div class="bar-bg"><div class="bar-fill" id="bar2" style="width:0%;background:#44ff44"></div></div>
    </div>
    <div class="data-row" style="flex-direction:column">
      <div style="display:flex;justify-content:space-between">
        <span class="data-label">Bassin 3</span>
        <span><span class="data-val" id="b3">0</span>% <span class="data-raw" id="r3"></span></span>
      </div>
      <div class="bar-bg"><div class="bar-fill" id="bar3" style="width:0%;background:#44ff44"></div></div>
    </div>
  </div>
  <div class="status" id="status">Connecte</div>
<script>
  let state = false;
  function barColor(v) { return v >= 50 ? '#ff4444' : v >= 25 ? '#ffff44' : '#44ff44'; }
  function updateUI(d) {
    state = d.on;
    const light = document.getElementById('light');
    const btn = document.getElementById('btn');
    if (d.on) {
      light.classList.add('on');
      btn.textContent = 'OFF';
      btn.className = 'btn on';
    } else {
      light.classList.remove('on');
      btn.textContent = 'ON';
      btn.className = 'btn off';
    }
    if (d.dompeur !== undefined) document.getElementById('dompeur').textContent = d.dompeur;
    if (d.temp !== undefined) document.getElementById('temp').textContent = d.temp + ' C';
    for (let i = 1; i <= 3; i++) {
      let v = d['basin' + i];
      if (v !== undefined) {
        document.getElementById('b' + i).textContent = v;
        let bar = document.getElementById('bar' + i);
        bar.style.width = v + '%';
        bar.style.background = barColor(v);
      }
      let r = d['raw' + i];
      if (r !== undefined) document.getElementById('r' + i).textContent = '(' + r + ' cm)';
    }
  }
  function toggle() {
    fetch('/toggle').then(r => r.json()).then(d => updateUI(d));
  }
  setInterval(() => {
    fetch('/state').then(r => r.json()).then(d => updateUI(d));
  }, 500);
</script>"""

if old_html in code:
    code = code.replace(old_html, new_html, 1)
    print("[OK] HTML updated")
else:
    print("[FAIL] HTML not found")

with open(path, "w", encoding="utf-8") as f:
    f.write(code)
