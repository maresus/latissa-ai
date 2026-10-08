(function() {
  'use strict';

  var _scriptEl = document.currentScript || document.querySelector('script[src*="widget.js"]');
  var _apiUrl = ((_scriptEl && _scriptEl.getAttribute('data-api-base')) || window.location.origin) + '/chat';

  const CONFIG = {
    apiUrl: _apiUrl,
    brandColor: '#3a322e',
    brandColorHover: '#2a2420',
    accentColor: '#b9a89c',
    bgColor: '#f6ece4',
    title: 'Latissa home&decor',
    subtitle: 'Kako vam lahko pomagam?',
    placeholder: 'Vprašajte karkoli...',
    welcomeMessage: 'Pozdravljeni! Sem Latissin digitalni pomočnik. Z veseljem vam pomagam najti pravi kotiček za vaš dom ali odgovorim na vprašanja o naročilu.',
    mobileBreakpoint: 768,
    maxStoredMessages: 50
  };

  const styles = `
    #la-widget-container * {
      box-sizing: border-box;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    #la-launcher {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999999;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 10px;
      pointer-events: none;
    }
    #la-launcher > * { pointer-events: all; }

    #la-widget-bubble {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: ${CONFIG.brandColor};
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s, box-shadow 0.2s;
      border: none;
      padding: 0;
      touch-action: manipulation;
      -webkit-tap-highlight-color: transparent;
      flex-shrink: 0;
      position: relative;
    }
    #la-widget-bubble:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 24px rgba(0,0,0,0.25);
    }
    #la-widget-bubble svg { width: 28px; height: 28px; fill: white; }

    #la-widget-panel {
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 420px;
      height: 600px;
      max-height: calc(100vh - 120px);
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.18);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      z-index: 999998;
      opacity: 0;
      visibility: hidden;
      transform: translateY(8px);
      transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s;
    }
    #la-widget-panel.la-open {
      opacity: 1;
      visibility: visible;
      transform: translateY(0);
    }

    @media (max-width: ${CONFIG.mobileBreakpoint}px) {
      #la-widget-panel {
        position: fixed !important;
        inset: 0 !important;
        width: 100% !important;
        height: auto !important;
        max-height: none !important;
        border-radius: 0 !important;
        margin: 0 !important;
      }
      #la-widget-panel.la-open {
        opacity: 1 !important;
        visibility: visible !important;
        transform: translateY(0) !important;
      }
      #la-widget-header {
        padding-top: max(16px, env(safe-area-inset-top)) !important;
      }
      #la-widget-input-area {
        padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
      }
      #la-widget-input { font-size: 16px !important; }
    }

    #la-widget-header {
      background: ${CONFIG.brandColor};
      color: #fff;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }

    #la-widget-header-icon {
      width: 40px;
      height: 40px;
      background: rgba(255,255,255,0.15);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    #la-widget-header-icon svg { width: 22px; height: 22px; fill: white; }

    #la-widget-header-text { flex: 1; }
    #la-widget-header-text h3 {
      margin: 0;
      font-size: 15px;
      font-weight: 600;
      color: #fff;
    }
    #la-widget-header-text p {
      margin: 2px 0 0;
      font-size: 12px;
      color: rgba(255,255,255,0.75);
    }

    .la-header-btn {
      background: rgba(255,255,255,0.15);
      border: none;
      color: #fff;
      cursor: pointer;
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      border-radius: 8px;
      transition: background 0.15s;
    }
    .la-header-btn:hover { background: rgba(255,255,255,0.25); }
    .la-header-btn svg { width: 18px; height: 18px; fill: white; display: block; }

    #la-widget-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: ${CONFIG.bgColor};
    }

    .la-message { margin-bottom: 12px; display: flex; flex-direction: column; }
    .la-message.la-bot { align-items: flex-start; }
    .la-message.la-user { align-items: flex-end; }

    .la-message-bubble {
      max-width: 85%;
      padding: 11px 15px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
    }
    .la-bot .la-message-bubble {
      background: white;
      color: #2a2420;
      border-bottom-left-radius: 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .la-user .la-message-bubble {
      background: ${CONFIG.brandColor};
      color: white;
      border-bottom-right-radius: 4px;
    }

    .la-typing { display: flex; gap: 4px; padding: 12px 16px; }
    .la-typing span {
      width: 8px; height: 8px;
      background: ${CONFIG.accentColor};
      border-radius: 50%;
      animation: la-bounce 1.2s infinite;
    }
    .la-typing span:nth-child(2) { animation-delay: 0.2s; }
    .la-typing span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes la-bounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-6px); }
    }

    #la-widget-input-area {
      padding: 12px 16px;
      background: white;
      border-top: 1px solid #e8ddd5;
      display: flex;
      gap: 10px;
      flex-shrink: 0;
    }

    #la-widget-input {
      flex: 1;
      border: 1px solid #d2c4b8;
      border-radius: 24px;
      padding: 11px 18px;
      font-size: 16px;
      outline: none;
      transition: border-color 0.15s;
      background: #fdf9f6;
    }
    #la-widget-input:focus { border-color: ${CONFIG.brandColor}; background: #fff; }

    #la-widget-send {
      width: 44px; height: 44px;
      border-radius: 50%;
      background: ${CONFIG.brandColor};
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.15s;
      flex-shrink: 0;
    }
    #la-widget-send:hover { background: ${CONFIG.brandColorHover}; }
    #la-widget-send:disabled { background: #ccc; cursor: not-allowed; }
    #la-widget-send svg { width: 20px; height: 20px; fill: white; }

    #la-widget-disclaimer {
      font-size: 11px;
      color: #aaa;
      line-height: 1.4;
      padding: 5px 14px 2px;
      background: white;
      text-align: center;
    }
    #la-widget-disclaimer a { color: ${CONFIG.accentColor}; text-decoration: none; }
    #la-widget-powered {
      text-align: center;
      font-size: 11px;
      color: #ccc;
      padding: 2px 0 6px;
      background: white;
    }
    #la-widget-powered a { color: #bbb; text-decoration: none; }
    #la-widget-powered a:hover { color: ${CONFIG.brandColor}; }
  `;

  const icons = {
    chat: '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>',
    home: '<svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
    close: '<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    send: '<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>',
    refresh: '<svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>'
  };

  let sessionId = localStorage.getItem('la_widget_session') || _genId();
  localStorage.setItem('la_widget_session', sessionId);

  let storedMessages = [];
  try {
    const s = sessionStorage.getItem('la_widget_messages');
    if (s) storedMessages = JSON.parse(s);
  } catch(e) { storedMessages = []; }

  function _genId() {
    return 'la_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  function _saveMessages() {
    try {
      sessionStorage.setItem('la_widget_messages', JSON.stringify(storedMessages.slice(-CONFIG.maxStoredMessages)));
    } catch(e) {}
  }

  function _clearConversation() {
    storedMessages = [];
    try { sessionStorage.removeItem('la_widget_messages'); } catch(e) {}
    sessionId = _genId();
    localStorage.setItem('la_widget_session', sessionId);
    document.getElementById('la-widget-messages').innerHTML = '';
    _addMessage(CONFIG.welcomeMessage, 'bot', false);
  }

  function _createWidget() {
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);

    const launcher = document.createElement('div');
    launcher.id = 'la-launcher';

    // Greeting kartice
    var cardStyle = [
      'display:block','background:#ffffff','color:' + CONFIG.brandColor,
      'font-size:14px','font-family:-apple-system,BlinkMacSystemFont,sans-serif',
      'font-weight:600','padding:10px 16px','border-radius:18px 18px 4px 18px',
      'box-shadow:0 2px 12px rgba(0,0,0,0.13)','cursor:pointer',
      'border:1px solid rgba(58,50,46,0.18)','max-width:240px',
      'text-align:right','touch-action:manipulation',
      '-webkit-tap-highlight-color:transparent','margin-bottom:8px','line-height:1.4',
    ].join(';');

    var closeStyle = [
      'display:block','background:#fff','color:' + CONFIG.brandColor,
      'border:1px solid rgba(58,50,46,0.2)','border-radius:50%',
      'width:24px','height:24px','font-size:13px','cursor:pointer',
      'touch-action:manipulation','-webkit-tap-highlight-color:transparent',
      'margin-bottom:6px','margin-left:auto','line-height:22px',
      'text-align:center','padding:0',
    ].join(';');

    const greetingCards = document.createElement('div');
    greetingCards.id = 'la-greeting-cards';
    greetingCards.setAttribute('style', [
      'position:fixed','bottom:90px','right:0','z-index:2147483647',
      'display:none','flex-direction:column','align-items:flex-end','padding-right:0',
    ].join(';'));

    var xBtn = document.createElement('button');
    xBtn.setAttribute('style', closeStyle + ';margin-right:6px');
    xBtn.textContent = '✕';
    xBtn.onclick = function(e) { e.stopPropagation(); e.preventDefault(); _hideCards(); };
    greetingCards.appendChild(xBtn);

    ['Pozdravljeni! 👋', 'Pomagam vam najti pravi kotiček.', 'Kaj iščete?'].forEach(function(text) {
      var btn = document.createElement('button');
      btn.setAttribute('style', cardStyle);
      btn.textContent = text;
      btn.onclick = function(e) { e.stopPropagation(); e.preventDefault(); setTimeout(_openPanel, 0); };
      greetingCards.appendChild(btn);
    });

    const bubble = document.createElement('button');
    bubble.id = 'la-widget-bubble';
    bubble.setAttribute('aria-label', 'Odpri Latissin digitalni pomočnik');
    bubble.innerHTML = icons.home;
    bubble.onclick = function(e) { e.stopPropagation(); e.preventDefault(); setTimeout(_togglePanel, 0); };

    const panel = document.createElement('div');
    panel.id = 'la-widget-panel';
    panel.innerHTML = `
      <div id="la-widget-header">
        <div id="la-widget-header-icon">${icons.home}</div>
        <div id="la-widget-header-text">
          <h3>${CONFIG.title}</h3>
          <p>${CONFIG.subtitle}</p>
        </div>
        <button class="la-header-btn" id="la-widget-refresh" title="Nov pogovor" aria-label="Nov pogovor">${icons.refresh}</button>
        <button class="la-header-btn" id="la-widget-close" title="Zapri" aria-label="Zapri pomočnika">${icons.close}</button>
      </div>
      <div id="la-widget-messages" role="log" aria-live="polite" aria-label="Pogovor z digitalnim pomočnikom"></div>
      <div id="la-widget-input-area">
        <input type="text" id="la-widget-input" placeholder="${CONFIG.placeholder}" aria-label="Vnesite vprašanje">
        <button id="la-widget-send" aria-label="Pošlji">${icons.send}</button>
      </div>
      <div id="la-widget-disclaimer">🤖 Ta asistent je umetna inteligenca (AI) — EU AI Act čl. 50. Odgovori so informativne narave. Za naročila obiščite <a href="https://latissa.si" target="_blank">latissa.si</a>.</div>
      <div id="la-widget-powered">built by: <a href="https://spoznaj-ai.si" target="_blank">spoznaj-ai.si</a></div>
    `;

    launcher.appendChild(bubble);
    document.body.appendChild(launcher);
    document.body.appendChild(greetingCards);
    document.body.appendChild(panel);

    panel.addEventListener('click', function(e) { e.stopPropagation(); });
    greetingCards.addEventListener('click', function(e) { e.stopPropagation(); });
    launcher.addEventListener('click', function(e) { e.stopPropagation(); });

    document.getElementById('la-widget-close').onclick = _closePanel;
    document.getElementById('la-widget-refresh').onclick = _clearConversation;
    document.getElementById('la-widget-send').onclick = _sendMessage;
    document.getElementById('la-widget-input').onkeypress = function(e) {
      if (e.key === 'Enter') _sendMessage();
    };
    document.getElementById('la-widget-input').addEventListener('focus', function() {
      var msgs = document.getElementById('la-widget-messages');
      if (!msgs) return;
      setTimeout(function() { msgs.scrollTo({ top: msgs.scrollHeight, behavior: 'smooth' }); }, 350);
    });

    if (storedMessages.length > 0) {
      storedMessages.forEach(function(m) { _addMessageToUI(m.text, m.sender, false); });
    } else {
      _addMessageToUI(CONFIG.welcomeMessage, 'bot', false);
    }

    setTimeout(function() { if (!_panelOpen) _showCards(); }, 800);
  }

  var _panelOpen = false;

  function _showCards() {
    var c = document.getElementById('la-greeting-cards');
    if (c) c.style.display = 'flex';
  }
  function _hideCards() {
    var c = document.getElementById('la-greeting-cards');
    if (c) c.style.display = 'none';
  }
  function _togglePanel() { if (_panelOpen) _closePanel(); else _openPanel(); }

  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', _onResize);
    window.visualViewport.addEventListener('scroll', _onResize);
  }
  function _onResize() {
    if (!_panelOpen || window.innerWidth > CONFIG.mobileBreakpoint) return;
    var vv = window.visualViewport;
    if (!vv) return;
    var p = document.getElementById('la-widget-panel');
    p.style.top = vv.offsetTop + 'px';
    p.style.height = vv.height + 'px';
    p.style.bottom = 'auto';
  }

  function _openPanel() {
    if (_panelOpen) return;
    _panelOpen = true;
    var p = document.getElementById('la-widget-panel');
    p.classList.add('la-open');
    if (window.innerWidth <= CONFIG.mobileBreakpoint) {
      p.style.position = 'fixed'; p.style.inset = '0';
      p.style.width = '100%'; p.style.height = 'auto';
      p.style.maxHeight = 'none'; p.style.borderRadius = '0';
      document.body.style.overflow = 'hidden';
      if (window.visualViewport) _onResize();
    }
    _hideCards();
    document.getElementById('la-widget-input').focus();
    localStorage.setItem('la_widget_open', 'true');
  }

  function _closePanel() {
    if (!_panelOpen) return;
    _panelOpen = false;
    var p = document.getElementById('la-widget-panel');
    p.classList.remove('la-open');
    document.body.style.overflow = '';
    localStorage.setItem('la_widget_open', 'false');
    _showCards();
  }

  function _addMessageToUI(text, sender, autoScroll) {
    if (autoScroll === undefined) autoScroll = true;
    var messages = document.getElementById('la-widget-messages');
    var msg = document.createElement('div');
    msg.className = 'la-message la-' + sender;
    msg.innerHTML = '<div class="la-message-bubble">' + (sender === 'bot' ? _renderMd(text) : _escHtml(text)) + '</div>';
    messages.appendChild(msg);
    if (!autoScroll) return;
    if (sender === 'user') {
      msg.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      var allUser = messages.querySelectorAll('.la-user');
      var last = allUser[allUser.length - 1];
      if (last) last.scrollIntoView({ behavior: 'smooth', block: 'start' });
      else msg.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function _addMessage(text, sender, save) {
    if (save === undefined) save = true;
    _addMessageToUI(text, sender);
    if (save) {
      storedMessages.push({ text: text, sender: sender, time: Date.now() });
      _saveMessages();
    }
  }

  function _showTyping() {
    var messages = document.getElementById('la-widget-messages');
    var t = document.createElement('div');
    t.id = 'la-typing-indicator';
    t.className = 'la-message la-bot';
    t.innerHTML = '<div class="la-message-bubble la-typing"><span></span><span></span><span></span></div>';
    messages.appendChild(t);
    t.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function _hideTyping() {
    var t = document.getElementById('la-typing-indicator');
    if (t) t.remove();
  }

  function _escHtml(text) {
    var d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML.replace(/\n/g, '<br>');
  }

  function _outsideTags(html, fn) {
    return html.split(/(<a\b[^>]*>[\s\S]*?<\/a>)/gi).map(function(part, i) {
      return (i % 2 === 0) ? fn(part) : part;
    }).join('');
  }

  function _sanitize(html) {
    var ALLOWED = {P:1,BR:1,STRONG:1,EM:1,A:1,UL:1,LI:1};
    var tmp = document.createElement('div');
    tmp.innerHTML = html;
    (function walk(node) {
      for (var i = node.children.length - 1; i >= 0; i--) {
        var el = node.children[i];
        if (!ALLOWED[el.tagName]) {
          node.replaceChild(document.createTextNode(el.textContent), el);
        } else {
          Array.from(el.attributes || []).forEach(function(a) {
            if (/^on/i.test(a.name)) el.removeAttribute(a.name);
          });
          if (el.tagName === 'A') {
            var h = el.getAttribute('href') || '';
            if (!/^(?:https?:|mailto:|tel:)/.test(h)) {
              node.replaceChild(document.createTextNode(el.textContent), el);
              continue;
            }
          }
          walk(el);
        }
      }
    })(tmp);
    return tmp.innerHTML;
  }

  function _renderMd(text) {
    var _ls = 'color:' + CONFIG.brandColor + ';text-decoration:underline;';
    var e = (function(t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; })(text);
    e = e.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    e = e.replace(/\b([\w.+%-]+@[\w-]+\.[a-z]{2,6})\b/gi, function(m, addr) {
      return '<a href="mailto:' + addr + '" style="' + _ls + '">' + addr + '</a>';
    });
    e = e.replace(/\b(0\d{2}[\s ]?\d{3}[\s ]?\d{3})\b/g, function(m, num) {
      return '<a href="tel:' + num.replace(/[\s ]/g, '') + '" style="' + _ls + '">' + num + '</a>';
    });
    e = e.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="' + _ls + '">$1</a>');
    e = _outsideTags(e, function(txt) {
      return txt.replace(/(https?:\/\/[^\s<>"')\]]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" style="' + _ls + '">$1</a>');
    });
    e = e.replace(/((?:^|\n)- [^\n]+)+/g, function(block) {
      var items = block.trim().split(/\n/).map(function(line) { return '<li>' + line.replace(/^- /, '') + '</li>'; }).join('');
      return '<ul style="margin:6px 0 6px 16px;padding:0;">' + items + '</ul>';
    });
    e = e.replace(/\n\n+/g, '</p><p style="margin:6px 0;">');
    e = e.replace(/\n/g, '<br>');
    return _sanitize('<p style="margin:0;">' + e + '</p>');
  }

  async function _sendMessage() {
    var input = document.getElementById('la-widget-input');
    var sendBtn = document.getElementById('la-widget-send');
    var text = input.value.trim();
    if (!text) return;

    _addMessage(text, 'user');
    input.value = '';
    sendBtn.disabled = true;
    _showTyping();

    try {
      var response = await fetch(CONFIG.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });
      _hideTyping();
      if (!response.ok) throw new Error('API error');
      var data = await response.json();
      _addMessage(data.reply || 'Oprostite, prišlo je do napake.', 'bot');
    } catch(err) {
      _hideTyping();
      _addMessage('Oprostite, trenutno ni mogoče vzpostaviti povezave. Pokličite nas na 070 733 390.', 'bot');
    }

    sendBtn.disabled = false;
    input.focus();
  }

  function _init() {
    if (document.getElementById('la-launcher')) return;
    _createWidget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _init);
  } else {
    requestAnimationFrame(_init);
  }
})();
