/* ═══════════════════════════════════════════════════════════════
   StudyMate · 共享行为层（主题 + 代码块高亮）
   ═══════════════════════════════════════════════════════════════
   根主页、科目主页、课件三个页面共用这一份，不要在页面里各写一套。
   两件事：主题（apply/set/toggle/current/wire）、代码块高亮（highlight，加载即自动跑）。

   用法（三步）：

     <!-- 1) <head> 里尽早应用主题，避免首帧闪白/闪黑 -->
     <script src="…/learn-theme.js"></script>
     <script>LearnTheme.apply();</script>

     <!-- 2) 页面里放一个 Sayo 主题开关 -->
     <label class="syo-toggle syo-toggle--theme">
       <input type="checkbox" id="theme-checkbox">
       <span class="syo-toggle-track"></span>
       <span class="syo-toggle-knob"> …日/月图标… </span>
     </label>

     // 3) 页面脚本末尾绑定它
     LearnTheme.wire(document.getElementById('theme-checkbox'));

   主题取值规则（apply 时）：
     URL 上的 ?theme=dark|light  →  优先，且不写入偏好（方便预览）
     localStorage['le-theme']    →  其次（学生在任何页面切过都记住）
     都没有                      →  亮色（我们的暖色系；暗色是 Sayo 的 Primer 暗色）

   约定：只用一个 data-theme 属性；**不要**用 Sayo 自带的 data-syo-theme，两套属性会打架。

   代码块高亮：课件里的 <pre><code> 和 .syo-editor 会自动上色，讲解角色写纯文本即可；
   要指定语言就在容器上写 data-lang="python|sh|powershell|html|js|json|sql|cpp|yaml|term"（text = 不上色）。
   页面加载了 Prism（课件页）时：上色交给 Prism，并在代码块右上角挂语言角标 + 复制按钮；
   没加载 Prism（主页）时退回下方的自研正则。
   ═══════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  var KEY = 'le-theme';
  var root = document.documentElement;

  function readSaved() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* file:// 下可能不可用 */ }
    return (saved === 'dark' || saved === 'light') ? saved : null;
  }

  function fromQuery() {
    var q = null;
    try { q = new URLSearchParams(global.location.search).get('theme'); } catch (e) {}
    return (q === 'dark' || q === 'light') ? q : null;
  }

  function current() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  /* 应用主题：可选传 'light'/'dark' 强制指定；不传则按上面的优先级推断 */
  function apply(theme) {
    var next = theme || fromQuery() || readSaved() || 'dark';
    root.setAttribute('data-theme', next === 'dark' ? 'dark' : 'light');
    return current();
  }

  /* 切换并记住（persist=false 时只改不记） */
  function set(theme, persist) {
    var next = theme === 'dark' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    if (persist !== false) {
      try { localStorage.setItem(KEY, next); } catch (e) {}
    }
    return next;
  }

  function toggle() {
    return set(current() === 'dark' ? 'light' : 'dark');
  }

  /* 把页面上的 Sayo 主题开关接上：勾选 = 亮色 */
  function wire(checkbox) {
    if (!checkbox) return;
    checkbox.checked = current() === 'light';
    checkbox.addEventListener('change', function () {
      set(checkbox.checked ? 'light' : 'dark');
    });
  }

  /* ═══════════════════════════════════════════════════════════════
     代码块高亮（课件里的 pre>code 与 .syo-editor 自动上色）

     思路与 sayo-ui 文档页一致：正则逐个 token 染色，染之前先换成占位符，
     免得插进去的 <span> 被后面的规则二次匹配。token 类沿用 Sayo 的 .syn-*，
     颜色由 sayo.css（暗色）+ learn-theme.css（亮色）给，这里不碰颜色。

     作用对象：<pre><code>…</code></pre> 与 .syo-editor-code 里的 .line 行。
     语言：容器上写 data-lang="cpp|sh|bash|shell|term|html|js|javascript|ts|typescript|json|python|py" 指定
           （text／plain／markdown／md／http／yaml／yml／toml／sql／ini／diff／mermaid／powershell／java = 不上色），
           不写就按内容猜；猜不出的（普通输出、题面文字）原样不动。
     已手写过 .syn-* 的块整块跳过——手工优先，自动不覆盖。
     ═══════════════════════════════════════════════════════════════ */
  var LANGS = {
    /* C++：课件里的源码、题解代码 */
    cpp: function (html, t) {
      html = html.replace(/("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|\/\/[^\n]*|\/\*[\s\S]*?\*\/)/g,
        function (m) { return t(m[0] === '/' ? 'syn-comment' : 'syn-string', m); });
      html = html.replace(/(^|\n)([ \t]*)(#[ \t]*[a-z]+)/g, function (m, a, b, c) { return a + b + t('syn-macro', c); });
      html = html.replace(/\b(if|else|for|while|do|switch|case|default|break|continue|return|goto|try|catch|throw|new|delete|using|namespace|template|typename|class|struct|union|enum|public|private|protected|virtual|static|const|constexpr|inline|explicit|friend|operator|sizeof|typedef|auto|nullptr|true|false|this|override|noexcept|mutable|extern)\b/g, function (m) { return t('syn-keyword', m); });
      html = html.replace(/\b(int|long|short|char|float|double|void|bool|unsigned|signed|size_t|string|vector|map|set|unordered_map|unordered_set|pair|queue|stack|deque|priority_queue|array|tuple|list|bitset|istream|ostream|iostream|ifstream|ofstream|stringstream|iterator|int32_t|int64_t|uint32_t|uint64_t|cout|cin|cerr|endl)\b/g, function (m) { return t('syn-type', m); });
      html = html.replace(/(&lt;&lt;|&gt;&gt;|&lt;=|&gt;=|==|!=|&amp;&amp;|\|\||\+\+|--|\+=|-=|\*=|\/=|->|::)/g, function (m) { return t('syn-operator', m); });
      html = html.replace(/(?<!&#)\b(\d+(?:\.\d+)?[fFlLuU]*)\b/g, function (m) { return t('syn-number', m); });
      html = html.replace(/\b([A-Za-z_]\w*)(?=\s*\()/g, function (m) { return t('syn-func', m); });
      return html;
    },

    /* shell：课件里的命令、脚本（命令行为紫色，选项为蓝色，变量为橙色） */
    sh: function (html, t) {
      html = html.replace(/("(?:[^"\\\n]|\\.)*"|'[^'\n]*'|(^|[ \t])(#[^\n]*))/gm,
        function (m, token, space, comment) { return comment ? space + t('syn-comment', comment) : t('syn-string', m); });
      html = html.replace(/(^|\n)([ \t]*)((?:\.{0,2}\/|~\/)?[A-Za-z_][\w.+-]*)/g, function (m, a, b, c) { return a + b + t('syn-func', c); });
      html = html.replace(/(&amp;&amp;|\|\||(?<!&[a-z]{1,6});|\|)([ \t]*)((?:\.{0,2}\/|~\/)?[A-Za-z_][\w.+-]*)/g, function (m, a, b, c) { return a + b + t('syn-func', c); });
      html = html.replace(/([ \t])(-{1,2}[A-Za-z][\w-]*)/g, function (m, a, b) { return a + t('syn-operator', b); });
      html = html.replace(/(\$\{[^}\n]*\}|\$[A-Za-z_]\w*|\$\?)/g, function (m) { return t('syn-type', m); });
      html = html.replace(/(?<!&#)\b(\d+(?:\.\d+)?)\b/g, function (m) { return t('syn-number', m); });
      return html;
    },

    /* 终端 / 编译器输出：着色 error、warning、文件名:行:列、引号里的内容 */
    term: function (html, t) {
      html = html.replace(/\b(error|错误|failed|失败)\b/g, function (m) { return t('syn-keyword', m); });
      html = html.replace(/\b(warning|note|警告|提示)\b/g, function (m) { return t('syn-macro', m); });
      html = html.replace(/([\w./-]+\.(?:cpp|cc|cxx|c|h|hpp|ts|tsx|js|mjs|json|py|rs|sh|html):\d+(?::\d+)?)/g, function (m) { return t('syn-func', m); });
      html = html.replace(/("(?:[^"\\\n]|\\.)*"|'[^'\n]*'|‘[^’\n]*’|“[^”\n]*”)/g, function (m) { return t('syn-string', m); });
      html = html.replace(/(?<!&#)\b(\d+(?:\.\d+)?)\b/g, function (m) { return t('syn-number', m); });
      return html;
    },

    /* HTML */
    html: function (html, t) {
      html = html.replace(/(&lt;!--[\s\S]*?--&gt;)/g, function (m) { return t('syn-comment', m); });
      html = html.replace(/(&lt;\/?)([A-Za-z][\w-]*)/g, function (m, a, b) { return a + t('syn-type', b); });
      html = html.replace(/([ \t])([\w-]+)(?==(?:"|&quot;))/g, function (m, a, b) { return a + t('syn-func', b); });
      html = html.replace(/(?:&quot;|")([^"\n]*)(?:&quot;|")/g, function (m) { return t('syn-string', m); });
      return html;
    },

    /* JS / TS */
    js: function (html, t) {
      html = html.replace(/("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`|\/\/[^\n]*|\/\*[\s\S]*?\*\/)/g,
        function (m) { return t(m[0] === '/' ? 'syn-comment' : 'syn-string', m); });
      html = html.replace(/\b(const|let|var|function|return|if|else|for|while|do|of|in|await|async|class|extends|super|new|this|typeof|instanceof|true|false|null|undefined|import|export|from|default|switch|case|break|continue|try|catch|finally|throw|yield|static|get|set|interface|type|enum|implements|public|private|readonly|declare|as|satisfies)\b/g, function (m) { return t('syn-keyword', m); });
      html = html.replace(/(?<!&#)\b(\d+(?:\.\d+)?)\b/g, function (m) { return t('syn-number', m); });
      html = html.replace(/\b([A-Za-z_$][\w$]*)(?=\s*\()/g, function (m) { return t('syn-func', m); });
      return html;
    },

    /* JSON */
    json: function (html, t) {
      html = html.replace(/("(?:[^"\\\n]|\\.)*")(\s*:)/g, function (m, a, b) { return t('syn-func', a) + b; });
      html = html.replace(/("(?:[^"\\\n]|\\.)*")/g, function (m) { return t('syn-string', m); });
      html = html.replace(/\b(true|false|null)\b/g, function (m) { return t('syn-keyword', m); });
      html = html.replace(/\b(-?\d+(?:\.\d+)?)\b/g, function (m) { return t('syn-number', m); });
      return html;
    },

    /* Python：课件里的脚本与库调用 */
    python: function (html, t) {
      html = html.replace(/((?:[rbfuRBFU]{0,2})"""[\s\S]*?"""|(?:[rbfuRBFU]{0,2})'''[\s\S]*?'''|(?:[rbfuRBFU]{0,2})"(?:[^"\\\n]|\\.)*"|(?:[rbfuRBFU]{0,2})'(?:[^'\\\n]|\\.)*'|#[^\n]*)/g,
        function (m) { return t(m[0] === '#' ? 'syn-comment' : 'syn-string', m); });
      html = html.replace(/(^|\n)([ \t]*)(@[A-Za-z_][\w.]*)/g,
        function (m, a, b, c) { return a + b + t('syn-macro', c); });
      html = html.replace(/\b(def|class|return|if|elif|else|for|while|break|continue|pass|import|from|as|with|try|except|finally|raise|lambda|global|nonlocal|assert|del|yield|await|async|in|is|not|and|or|True|False|None)\b/g,
        function (m) { return t('syn-keyword', m); });
      html = html.replace(/\b(int|float|str|bytes|bool|list|tuple|dict|set|frozenset|complex|object|type|range|enumerate|zip|len|print|min|max|sum|abs|round|sorted|reversed|open|isinstance|self|cls|Exception|ValueError|TypeError|IndexError|KeyError|RuntimeError|StopIteration)\b/g,
        function (m) { return t('syn-type', m); });
      html = html.replace(/(?<!&#)\b(\d+(?:\.\d+)?)\b/g, function (m) { return t('syn-number', m); });
      html = html.replace(/\b([A-Za-z_]\w*)(?=\s*\()/g, function (m) { return t('syn-func', m); });
      return html;
    },

    /* 围栏里的常见别名：`py` 与 `bash` 指的是同一套配色 */
    py: function (html, t) { return LANGS.python(html, t); },
    bash: function (html, t) { return LANGS.sh(html, t); },
    /* 围栏里常见的同义写法 */
    shell: function (html, t) { return LANGS.sh(html, t); },
    javascript: function (html, t) { return LANGS.js(html, t); },
    ts: function (html, t) { return LANGS.js(html, t); },
    typescript: function (html, t) { return LANGS.js(html, t); }
  };

  /* 按内容猜语言；猜不出返回 null（原样不动，普通输出不该被染色） */
  var SH_KNOWN = /^(g\+\+|gcc|clang(\+\+)?|make|cmake|mkdir|cd|ls|cat|echo|rm|cp|mv|touch|chmod|chown|export|npm|npx|pnpm|yarn|node|git|python3?|pip3?|curl|wget|apt(-get)?|sudo|head|tail|wc|grep|find|which|sort|uniq|diff|tree|tar|zip|unzip|ln|stat|sleep|printf|test|time|awk|sed|xargs|tee|env|source|bash|sh|zsh|file|du|df|ps|kill|less|more|man)$/;

  function firstLine(text) {
    var lines = text.split('\n');
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim()) return lines[i].trim();
    }
    return '';
  }

  function detect(text) {
    if (/Traceback \(most recent call last\)|\b(error|warning|note):|[\w./-]+\.\w+:\d+(?::\d+)?:/.test(text)) return 'term';
    /* 首行像命令（$、#!、命令名）就以 shell 为准：heredoc 里嵌着代码也算 shell 会话 */
    var head = firstLine(text);
    if (/^PS [A-Za-z]:\\|^[A-Z][a-z]+-[A-Z][A-Za-z]+\b/.test(head)) return 'powershell';
    if (/^(\$|#!)/.test(head) || SH_KNOWN.test(head.split(/[\s;|&]+/)[0])) return 'sh';
    /* Python 放在 js 之前：`import x` 两边都有，Python 的 def/class 冒号、from…import、self. 更有辨识度 */
    if (/(^|\n)[ \t]*(def [A-Za-z_]\w*\s*\(|class [A-Za-z_]\w*\s*[:(]|from [\w.]+ import |import [\w.]+(\s+as\s+\w+)?[ \t]*(\n|$)|if __name__\s*==|@dataclass|with open\(|try:|except\b[^\n]*:)/.test(text) || /\bself\.\w+|\bprint\(/.test(text)) return 'python';
    if (/#[ \t]*include\b|\bstd::|\bint\s+main\s*\(|\bcout\b|\bcin\b|\bendl\b|\b(?:vector|string|map|set|pair|queue|stack)\s*<|\bnullptr\b|\bconstexpr\b|\b(int|double|void|char|long|float|bool|auto)\s+\w+\s*[=;(]/.test(text)) return 'cpp';
    if (/<(!doctype|html|head|body|div|span|nav|section|article|ul|ol|li|table|tr|td|th|h[1-6]|script|link|meta|button|input|form|img|pre|code|a)\b/i.test(text)) return 'html';
    if (/(^|\n)\s*[[{][\s\S]*"\s*:/.test(text)) return 'json';
    if (/\b(const|let|var|function|import|export|require|console\.|await|async|interface|enum|implements|readonly|declare|satisfies)\b|=>|\btype\s+\w+\s*=/.test(text)) return 'js';
    if (/(^|\n)\s*(\$|#|(?:\.{0,2}\/|~\/|\/)\S)/.test(text) || /&&|\|\||\|\s|\$\(|`|>>|2>&1/.test(text)) return 'sh';
    if (/(^|\n|\s)(g\+\+|gcc|clang|make|cmake|mkdir|cd|ls|cat|echo|rm|cp|mv|touch|chmod|export|npm|npx|node|pnpm|git|python3?|pip3?|curl|wget|apt|sudo|head|tail|wc|grep|find|which|sort|diff|tree|tar|ln|stat|sleep|printf|test|time|awk|sed|xargs|tee|env|source|bash|sh)\b/.test(text)) return 'sh';
    return null;
  }

  function highlightBlock(el, lang) {
    var tokens = [];
    function tok(cls, text) {
      tokens.push('<span class="' + cls + '">' + text + '</span>');
      return '\u0000K' + (tokens.length - 1) + '\u0000';
    }
    var html = LANGS[lang](el.innerHTML, tok);
    // 后生成的 token 可能包含早先的占位符，先还原外层才能完整还原原文。
    for (var i = tokens.length - 1; i >= 0; i--) {
      html = html.split('\u0000K' + i + '\u0000').join(tokens[i]);
    }
    el.innerHTML = html;
  }

  /* ── 语言名归一：data-lang 的写法 → 规范 id ──
     规范 id 优先对上 Prism 的语法名（python/bash/powershell/markup/…）；
     Prism 没有的（term）或 Prism 没加载时，退回上面 LANGS 的自研正则（sh/html/js 是它的名字）。 */
  var ALIAS = {
    py: 'python', python: 'python', python3: 'python',
    sh: 'bash', bash: 'bash', shell: 'bash', zsh: 'bash', console: 'bash',
    ps: 'powershell', ps1: 'powershell', powershell: 'powershell', pwsh: 'powershell',
    html: 'markup', xml: 'markup', markup: 'markup', svg: 'markup',
    js: 'javascript', javascript: 'javascript', ts: 'javascript',
    json: 'json', css: 'css', sql: 'sql', sqlite: 'sql',
    cpp: 'cpp', 'c++': 'cpp', c: 'c', yaml: 'yaml', yml: 'yaml',
    term: 'term', text: 'text', txt: 'text', plain: 'text', output: 'text'
  };
  /* 规范 id → 自研正则引擎的名字（Prism 缺席时的兜底） */
  var LEGACY = { bash: 'sh', markup: 'html', javascript: 'js', json: 'json', cpp: 'cpp', c: 'cpp', term: 'term' };
  /* 角标上显示的名字（Obsidian 式：右上角写语言名） */
  var LABEL = {
    python: 'Python', bash: 'Shell', powershell: 'PowerShell', markup: 'HTML', javascript: 'JavaScript',
    json: 'JSON', css: 'CSS', sql: 'SQL', cpp: 'C++', c: 'C', yaml: 'YAML', term: '终端输出', text: '文本'
  };

  /* 语言从最近的 data-lang 容器上取（归一成规范 id）；没写就猜；猜不出返回 null */
  function langOf(block, holder) {
    var scope = block.closest('[data-lang]') || holder.closest('[data-lang]');
    var attr = scope && scope.getAttribute('data-lang');
    if (attr) {
      var key = attr.toLowerCase();
      return Object.prototype.hasOwnProperty.call(ALIAS, key) ? ALIAS[key] : 'text';   /* 未知值 = 不上色 */
    }
    var guess = detect(holder.textContent || '');
    return guess ? ALIAS[guess] : null;
  }

  /* ── Prism 接入 ──
     上色：Prism 的 token 类（keyword/string/…）经 wrap 钩子追加成 Sayo 的 .syn-*，
           于是配色仍由 sayo.css（暗）+ learn-theme.css（亮）给，不引入 Prism 主题。
     工具栏：Prism 官方插件 toolbar + show-language（语言角标）+ copy-to-clipboard（复制按钮），
           按钮只显示图标（样式照 VitePress，见 learn-theme.css），文案经 <html data-prismjs-copy*> 写成中文、只给读屏。 */
  var SYN = {
    comment: 'syn-comment', prolog: 'syn-comment', doctype: 'syn-macro', cdata: 'syn-comment',
    keyword: 'syn-keyword', boolean: 'syn-keyword', important: 'syn-keyword', atrule: 'syn-keyword', constant: 'syn-keyword',
    string: 'syn-string', char: 'syn-string', 'attr-value': 'syn-string', regex: 'syn-string',
    'triple-quoted-string': 'syn-string', 'template-string': 'syn-string', url: 'syn-string',
    'function': 'syn-func', 'attr-name': 'syn-func', property: 'syn-func',
    'class-name': 'syn-type', builtin: 'syn-type', tag: 'syn-type', selector: 'syn-type', variable: 'syn-type', namespace: 'syn-type',
    decorator: 'syn-macro', annotation: 'syn-macro', directive: 'syn-macro', macro: 'syn-macro', shebang: 'syn-macro',
    operator: 'syn-operator', number: 'syn-number'
  };
  var prismReady = false;
  function setupPrism() {
    var P = global.Prism;
    if (!P || !P.plugins || !P.plugins.toolbar) return null;
    if (prismReady) return P;
    prismReady = true;
    P.hooks.add('wrap', function (env) {
      var names = [env.type].concat(env.alias || []);
      for (var i = 0; i < names.length; i++) {
        var cls = SYN[names[i]];
        if (cls && env.classes.indexOf(cls) < 0) { env.classes.push(cls); break; }
      }
    });
    var html = document.documentElement;
    if (!html.hasAttribute('data-prismjs-copy')) {
      html.setAttribute('data-prismjs-copy', '复制代码');   /* 只给读屏：按钮视觉上只有图标 */
      html.setAttribute('data-prismjs-copy-success', '已复制');
      html.setAttribute('data-prismjs-copy-error', '按 Ctrl+C 复制');
      html.setAttribute('data-prismjs-copy-timeout', '2000');   /* 与 VitePress 一致：2 秒后图标复原 */
    }
    return P;
  }

  var SYN_ANY = '.syn-comment, .syn-keyword, .syn-string, .syn-func, .syn-type, .syn-macro, .syn-operator, .syn-number';

  function decorate(code, P) {
    var pre = code.parentNode;
    if (pre.parentNode && pre.parentNode.classList && pre.parentNode.classList.contains('code-toolbar')) return;  /* 已处理过（幂等） */
    var handwritten = !!code.querySelector(SYN_ANY);
    var lang = langOf(code, pre);
    var id = lang || 'text';
    pre.setAttribute('data-language', LABEL[id] || id);
    if (!handwritten && lang && P.languages[lang]) {
      code.classList.add('language-' + lang);
      P.highlightElement(code);            /* 'complete' 钩子里 toolbar 插件自动挂上角标与复制按钮 */
      return;
    }
    /* Prism 没有的语法（term）或手写过 .syn-* 的块：颜色走自研正则或保留手写，只挂工具栏 */
    if (!handwritten && lang && LEGACY[lang]) highlightBlock(code, LEGACY[lang]);
    P.plugins.toolbar.hook({ element: code, language: id });
  }

  function highlightAll(scope) {
    var root = scope || document;
    var P = setupPrism();

    var codes = root.querySelectorAll('pre > code');
    for (var i = 0; i < codes.length; i++) {
      var code = codes[i];
      if (P && !code.closest('.syo-editor')) { decorate(code, P); continue; }   /* 编辑器块自带标题栏，不挂工具栏 */
      if (code.querySelector(SYN_ANY)) continue;
      var lang = langOf(code, code.parentNode);
      if (lang && LEGACY[lang]) highlightBlock(code, LEGACY[lang]);
    }

    /* .syo-editor（带标题栏与行号的编辑器块）逐行上色，仍走自研正则 */
    var editors = root.querySelectorAll('.syo-editor-code');
    for (var j = 0; j < editors.length; j++) {
      var box = editors[j];
      if (box.querySelector('[class^="syn-"]')) continue;
      var lines = box.querySelectorAll('.line');
      if (!lines.length) continue;
      var elang = langOf(box, box.closest('.syo-editor') || box);
      if (!elang || !LEGACY[elang]) continue;
      for (var k = 0; k < lines.length; k++) highlightBlock(lines[k], LEGACY[elang]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { highlightAll(); });
  } else {
    highlightAll();
  }

  global.LearnTheme = {
    KEY: KEY,
    apply: apply,
    set: set,
    toggle: toggle,
    current: current,
    wire: wire,
    highlight: highlightAll
  };
})(window);
