/* ═══════════════════════════════════════════════════════════════
   StudyMate · 课件题目组件（数据契约的唯一出处）
   ═══════════════════════════════════════════════════════════════
   题目从哪来：出题角色写 `lessons/<序号>-<节点id>.quiz.json`（结构 `{"锚点文本": [题, …]}`，
   键与内容文件里 `::: quiz` 的锚点逐字对应），`scripts/render_lesson.py` 把它渲染成页面里的
   题目块：

     <div class="quiz" data-quiz='[
       {"q":"选择题题干","opts":["选项A","选项B","选项C"],"ans":1,"why":"一句解释"},
       {"q":"开放题题干","answer":"参考答案","criteria":"判分要点（学生据此自评）"}
     ]'></div>
     <script src="../assets/quiz.js" defer></script>

   **属性值怎么转义、`data-quiz` 怎么拼，都是渲染器的事**（每个题目块都由它产出）：作者只交
   上面那种 JSON，不写 HTML、也不用知道实体引号的写法。下面这份契约管的是 **JSON 里写什么
   字段、这些字段进页面长什么样**。

   data-quiz 是 JSON 数组，每项是一道题。**四种题型**（词表在 schemas/question.schema.json）；
   可写 `kind` 显式声明（客观题 / 开放题 / 预测验证 / 交付物），不写就按字段推断，
   **各组字段不能混写**：

   题型一 · 选择题（kind: 客观题；页内自动判）
     q     题干（字符串，必填，两种题型都要）
     opts  选项数组（必填，≥2 项，每项都是非空字符串）
     ans   正确选项下标，从 0 开始（必填，必须落在 opts 范围内）
     why   答完显示的一句解释（必填：检查会拦，见 scripts/check_lesson.py）

   题型二 · 开放题（kind: 开放题；学生自评，不贴回会话）
     q         题干（字符串，必填）
     answer    参考答案（必填）
     criteria  判分要点：凭什么算答对了（必填；学生点开对照时看到的就是这两段）

   题型三 · 预测验证（kind: 预测验证；先写预测、再跑起来对照）
     q     题干（必填）：要学生预测什么（"把 i 初值改成 1，循环会跑几次？"）
     预测  参考预测（必填）：出题人给的正确预测
     比对  跑完之后的比对（必填）：实测是什么、与常见错误预测差在哪

   题型四 · 交付物（kind: 交付物；造出可运行的东西）
     q       题干（必填）
     交付物  要造出什么（必填）
     证据    可运行证据（必填）：测试命令 / 断言 / 期望输出——学生自己跑它来验收

   题面里的代码（`q` / `answer` / `criteria` / `why` 四个字段都适用）：
     多行代码写进**围栏**——起止各占一整行，中间照原样写（**缩进与空格全保留**）：

       {"q":"下面这段为什么死循环？\n\n```cpp\nwhile (i <= 100) {\n    ++cnt;\n}\n```\n\n① 哪里出问题？"}

     围栏行的写法是「行首可有缩进 + 三个反引号 + 语言标签」，语言可省（自动识别），
     写 `text` 表示不上色。渲染结果是真代码块（等宽 + 底色 + 自动上色），
     与课件正文里的代码块同款。
     **多行代码不进围栏就会掉缩进**：没有围栏的多行文本按纯文本渲染，只保留换行，
     浏览器会把行首空格折叠掉——靠缩进提问的题（`else` 对齐、嵌套层次）就废了。
     行内的单个反引号是普通字符，不做解析（shell 题面里合法）。
     围栏没闭合检查会拦（`scripts/check_lesson.py`）。

   渲染约定（字段进页面长什么样——**写的是纯文本，不是 Markdown**）：
     - 四个字段都是纯文本，渲染器只认三样排版：`\n` 换行、``` 围栏代码块、
       `$…$` 行内公式（交给离线 KaTeX，判据与课件正文一致；正文里的美元号写 `\$`）。
       **Markdown 与 HTML 标记一律原样显示**：`**加粗**` 会出现星号、`- 列表`/`# 标题`
       不变成列表或标题、行内 `` `code` `` 带反引号、`<b>` 露出尖括号。要强调就用短句
       与空行；要代码就用围栏。检查对这类标记给 WARN（`check_lesson.py`）。
     - 预测验证与交付物的字段（`预测` / `比对` / `交付物` / `证据`）同样是纯文本，规则同上。
     - 每个字段落在哪：`q` 是题干（一组里多道题时自动加「1. 」序号）；`opts` 按数组顺序
       变成可点按钮；`why` 接在「✓ 对／✗ 再想想」后面同一行；`answer` 与 `criteria` 收在
       「想好了，看参考答案」按钮后面，各带「参考答案」「判分要点」小标题。
     - 空行就是空行；围栏前后的空行会被去掉（间距由样式给，别用它凑留白）。

   行为：
   - 预测验证：先只显示题干和一个输入框，学生**写下自己的预测**后"写好了，看实际结果"才可点；
     点开显示「参考预测」「跑完的比对」。预测只留在当前页面，不落盘、不贴回会话
   - 交付物：直接列出「要造出」与「可运行证据」——这是任务，不是答案，做完自己跑证据验收
   - 选择题：点选项立刻给反馈（对/错 + why）；选错的标红、正确的标绿；允许改选，计分只算第一次；
     一组里的选择题全部答完后显示"答对 N / M"，并用 Sayo toast 提示一次（M 只数选择题）
   - 开放题：先只显示题干和"想好了，看参考答案"按钮；点开显示参考答案 + 判分要点；再点一次收起
     （方便隔一会儿重答一遍）。开放题不计分、不判定——它是自测
   - 课件没加载 sayo.js 时自动降级为纯内联反馈（不依赖 Sayo）
   - 题目数据不完整时页面显示提示，不静默吞掉

   出题与判分规范在 <root>/references/layered-practice（题目唯一规范）；
   检查 scripts/check_lesson.py 按上面这套字段做结构校验。
   ═══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  function whenReady(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  /* Sayo toast 是增强项：没有 sayo.js（或调用失败）就静默跳过 */
  function toast(message, type) {
    if (window.Sayo && window.Sayo.toast && typeof window.Sayo.toast.show === 'function') {
      try { window.Sayo.toast.show(message, { type: type }); return true; } catch (e) { /* 忽略 */ }
    }
    return false;
  }

  function questionBlock(item, index, total) {
    return richBlock('quiz__q', item && typeof item.q === 'string' ? item.q : '',
                     total > 1 ? (index + 1) + '. ' : '');
  }

  /* ── 题面/答案里的代码：```lang 围栏渲染成真代码块 ────────────────
     纯文本走 textContent 时，多行代码没有等宽字体、缩进也会被 white-space 折叠掉
     （有的题面恰恰靠缩进提问，学生就看不见了）。围栏里的内容改渲染成 <pre><code>：
     缩进、空格原样保留，底色/边框用 .lesson pre 那套，上色交给 learn-theme.js。
     围栏必须**单独占一行**（行首可缩进）：起一行 ```lang、止一行 ```；行内出现的
     单个反引号是普通字符，不做解析（shell 题面里合法）。语言标签可省（自动识别）。 */
  var FENCE_RE = /^[ \t]*```[ \t]*([A-Za-z0-9+#.-]*)[ \t]*$/;

  /* ── 题面里的公式：`$…$` 交给离线 KaTeX ──────────────────────────
     字段是纯文本（不走 innerHTML，避免注入），所以这里把字符串按 `$…$` 切成
     文本节点 + <span class="math-inline">，再让 lesson-math.js 去排版。
     判据与渲染器 math_close() 一致：开 `$` 后、收 `$` 前都不能是空白，中间不跨行；
     `\$` 是字面美元号。成不了对就按普通字符。 */
  function mathInto(el, text) {
    var body = String(text == null ? '' : text);
    var plain = '';
    var index = 0;
    function flush() {
      if (plain) { el.appendChild(document.createTextNode(plain)); plain = ''; }
    }
    while (index < body.length) {
      var char = body.charAt(index);
      if (char === '\\' && body.charAt(index + 1) === '$') { plain += '$'; index += 2; continue; }
      if (char === '$' && !/\s/.test(body.charAt(index + 1) || '')) {
        var close = -1;
        for (var scan = index + 1; scan < body.length; scan += 1) {
          if (body.charAt(scan) === '\n') break;
          if (body.charAt(scan) === '$' && !/\s/.test(body.charAt(scan - 1))) { close = scan; break; }
        }
        if (close > index + 1) {
          flush();
          var span = document.createElement('span');
          span.className = 'math-inline';
          span.textContent = body.slice(index + 1, close);
          el.appendChild(span);
          index = close + 1;
          continue;
        }
      }
      plain += char;
      index += 1;
    }
    flush();
    return el;
  }

  /* 排版本块里的公式（不是本块里的不管）：结构与 highlight() 同理——
     lesson-math.js 挂在 head，DOMContentLoaded 先于本文件建块，所以这里要再排一次 */
  function typeset(block) {
    if (window.LessonMath && typeof window.LessonMath.render === 'function') {
      try { window.LessonMath.render(block); } catch (e) { /* 忽略 */ }
    }
  }

  function renderRich(el, text) {
    var lines = String(text == null ? '' : text).split(/\r?\n/);
    var prose = [];
    var code = null;

    function flushProse() {
      var body = prose.join('\n').replace(/^\n+|\n+$/g, '');
      if (body) mathInto(el, body);
      prose = [];
    }
    function flushCode() {
      var pre = document.createElement('pre');
      pre.className = 'quiz__code';
      if (code.lang) pre.setAttribute('data-lang', code.lang);
      var inner = document.createElement('code');
      inner.textContent = code.lines.join('\n');
      pre.appendChild(inner);
      el.appendChild(pre);
      code = null;
    }

    lines.forEach(function (line) {
      var fence = FENCE_RE.exec(line);
      if (fence) {
        if (code) flushCode();
        else { flushProse(); code = { lang: fence[1], lines: [] }; }
        return;
      }
      (code ? code.lines : prose).push(line);
    });
    if (code) flushCode();          /* 围栏没闭合：照代码块渲染到结尾（检查会拦这种写法） */
    else flushProse();
  }

  /* 建块（div 而非 p：代码块是 <pre>，不能塞进 p 里） */
  function richBlock(className, text, prefix) {
    var el = document.createElement('div');
    el.className = className;
    if (prefix) el.appendChild(document.createTextNode(prefix));
    renderRich(el, text);
    return el;
  }

  /* 上色是增强项：learn-theme.js 的自动扫描在本文件建块**之前**就跑完了
     （它挂在 head、DOMContentLoaded 先注册），所以这里必须显式再扫一遍自己的块 */
  function highlight(block) {
    if (window.LearnTheme && typeof window.LearnTheme.highlight === 'function') {
      try { window.LearnTheme.highlight(block); } catch (e) { /* 忽略 */ }
    }
  }

  /* ── 选择题：点选项即时反馈 ─────────────────────────────────── */
  function buildChoice(block, item, index, total, state) {
    var question = questionBlock(item, index, total);
    block.appendChild(question);

    var opts = document.createElement('div');
    opts.className = 'quiz__opts';

    var feedback = document.createElement('div');
    feedback.className = 'feedback';
    feedback.hidden = true;

    var firstAnswer = true;

    (item.opts || []).forEach(function (text, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'quiz__opt';
      mathInto(btn, text);

      btn.addEventListener('click', function () {
        var ok = i === item.ans;

        Array.prototype.forEach.call(opts.children, function (other) {
          other.classList.toggle('is-picked', other === btn);
          other.classList.toggle('is-correct', other === btn && ok);
          other.classList.toggle('is-wrong', other === btn && !ok);
        });

        feedback.hidden = false;
        feedback.className = 'feedback ' + (ok ? 'correct' : 'wrong');
        feedback.textContent = '';
        feedback.appendChild(document.createTextNode((ok ? '✓ 对' : '✗ 再想想') + '　'));
        renderRich(feedback, item.why);
        typeset(feedback);
        highlight(feedback);

        if (firstAnswer) {
          firstAnswer = false;
          state.answered += 1;
          if (ok) state.correct += 1;
          if (state.answered === state.total) {
            if (state.scoreEl) {
              state.scoreEl.hidden = false;
              state.scoreEl.textContent = '本题组：答对 ' + state.correct + ' / ' + state.total;
            }
            toast(
              state.correct === state.total ? '全部答对（' + state.total + '/' + state.total + '）'
                                            : '答对 ' + state.correct + ' / ' + state.total,
              state.correct === state.total ? 'success' : 'info'
            );
          }
        }
      });

      opts.appendChild(btn);
    });

    block.appendChild(opts);
    block.appendChild(feedback);
  }

  /* ── 开放题：自己先答，点开对照参考答案与判分要点（不贴回会话）── */
  function buildOpen(block, item, index, total) {
    var question = questionBlock(item, index, total);
    block.appendChild(question);

    var wrap = document.createElement('div');
    wrap.className = 'quiz__open';

    var reveal = document.createElement('button');
    reveal.type = 'button';
    reveal.className = 'quiz__reveal';
    reveal.textContent = '想好了，看参考答案';

    var answer = document.createElement('div');
    answer.className = 'quiz__answer';
    answer.hidden = true;

    var answerLabel = document.createElement('p');
    answerLabel.className = 'quiz__answer-label';
    answerLabel.textContent = '参考答案';
    var answerText = richBlock('quiz__answer-text', item.answer || '');

    var criteriaLabel = document.createElement('p');
    criteriaLabel.className = 'quiz__answer-label';
    criteriaLabel.textContent = '判分要点';
    var criteriaText = richBlock('quiz__criteria', item.criteria || '');

    answer.appendChild(answerLabel);
    answer.appendChild(answerText);
    answer.appendChild(criteriaLabel);
    answer.appendChild(criteriaText);

    reveal.addEventListener('click', function () {
      answer.hidden = !answer.hidden;
      reveal.textContent = answer.hidden ? '想好了，看参考答案' : '收起，再自己答一遍';
    });

    wrap.appendChild(reveal);
    wrap.appendChild(answer);
    block.appendChild(wrap);
  }

  /* ── 两段带小标题的文字（参考答案 / 判分要点 这类） ─────────── */
  function labeled(container, label, text, className) {
    var head = document.createElement('p');
    head.className = 'quiz__answer-label';
    head.textContent = label;
    container.appendChild(head);
    container.appendChild(richBlock(className, text || ''));
  }

  /* ── 预测验证：先写下自己的预测，才能看参考预测与比对 ─────────── */
  function buildPredict(block, item, index, total) {
    block.appendChild(questionBlock(item, index, total));

    var wrap = document.createElement('div');
    wrap.className = 'quiz__open quiz__predict';

    var input = document.createElement('textarea');
    input.className = 'quiz__predict-input';
    input.rows = 2;
    input.placeholder = '先写下你的预测（别先跑）';
    input.setAttribute('aria-label', '你的预测');

    var reveal = document.createElement('button');
    reveal.type = 'button';
    reveal.className = 'quiz__reveal';
    reveal.textContent = '写好了，看实际结果';
    reveal.disabled = true;

    var answer = document.createElement('div');
    answer.className = 'quiz__answer';
    answer.hidden = true;
    labeled(answer, '参考预测', item['预测'], 'quiz__answer-text');
    labeled(answer, '跑完的比对', item['比对'], 'quiz__criteria');

    input.addEventListener('input', function () {
      reveal.disabled = !nonEmptyText(input.value);
    });
    reveal.addEventListener('click', function () {
      if (!nonEmptyText(input.value)) return;     /* 没写预测就等于没做这一层 */
      answer.hidden = !answer.hidden;
      reveal.textContent = answer.hidden ? '写好了，看实际结果' : '收起';
    });

    wrap.appendChild(input);
    wrap.appendChild(reveal);
    wrap.appendChild(answer);
    block.appendChild(wrap);
  }

  /* ── 交付物：要造出什么 + 怎么验收（是任务，不是答案，直接展示）── */
  function buildDeliverable(block, item, index, total) {
    block.appendChild(questionBlock(item, index, total));

    var wrap = document.createElement('div');
    wrap.className = 'quiz__open quiz__deliverable';
    labeled(wrap, '要造出', item['交付物'], 'quiz__answer-text');
    labeled(wrap, '可运行证据（做完自己跑它验收）', item['证据'], 'quiz__criteria');
    block.appendChild(wrap);
  }

  /* ── 数据不完整时的兜底 ─────────────────────────────────────── */
  function buildBroken(block, item, index, total) {
    var question = questionBlock(item, index, total);
    block.appendChild(question);

    var hint = document.createElement('p');
    hint.className = 'feedback wrong';
    hint.textContent = '（这道题的数据不完整：选择题要 opts/ans/why，开放题要 answer/criteria，' +
                       '预测验证要 预测/比对，交付物要 交付物/证据）';
    block.appendChild(hint);
  }

  /* ── 题型判定（与检查、分层规范一致：各组字段不能混写；写了 kind 就必须与字段相符）── */
  function nonEmptyText(value) {
    return typeof value === 'string' && value.trim().length > 0;
  }

  var FIELD_GROUPS = {
    '客观题': ['opts', 'ans', 'why'],
    '开放题': ['answer', 'criteria'],
    '预测验证': ['预测', '比对'],
    '交付物': ['交付物', '证据']
  };

  /* 题目对象 + 没写别的题型的字段 + kind 缺省或等于本题型 */
  function shapedAs(item, kind) {
    if (!item || typeof item !== 'object' || Array.isArray(item) || !nonEmptyText(item.q)) return false;
    if ('kind' in item && item.kind !== kind) return false;
    return Object.keys(FIELD_GROUPS).every(function (other) {
      return other === kind || FIELD_GROUPS[other].every(function (key) { return !(key in item); });
    });
  }

  function isChoiceItem(item) {
    return shapedAs(item, '客观题') && Array.isArray(item.opts) && item.opts.length >= 2 &&
           item.opts.every(nonEmptyText) &&
           typeof item.ans === 'number' && item.ans % 1 === 0 &&
           item.ans >= 0 && item.ans < item.opts.length && nonEmptyText(item.why);
  }

  function isOpenItem(item) {
    return shapedAs(item, '开放题') && nonEmptyText(item.answer) && nonEmptyText(item.criteria);
  }

  function isPredictItem(item) {
    return shapedAs(item, '预测验证') && nonEmptyText(item['预测']) && nonEmptyText(item['比对']);
  }

  function isDeliverableItem(item) {
    return shapedAs(item, '交付物') && nonEmptyText(item['交付物']) && nonEmptyText(item['证据']);
  }

  whenReady(function () {
    var blocks = document.querySelectorAll('.quiz[data-quiz]');

    Array.prototype.forEach.call(blocks, function (block) {
      var items;
      try {
        items = JSON.parse(block.getAttribute('data-quiz') || '[]');
      } catch (e) {
        block.textContent = '（题目数据解析失败：data-quiz 不是合法 JSON）';
        return;
      }
      if (!Array.isArray(items) || items.length === 0) {
        block.textContent = '（这组题还没有内容）';
        return;
      }

      var choiceCount = items.filter(isChoiceItem).length;

      var state = { answered: 0, correct: 0, total: choiceCount };
      if (choiceCount > 1) {
        state.scoreEl = document.createElement('p');
        state.scoreEl.className = 'quiz__score';
        state.scoreEl.hidden = true;
      }

      items.forEach(function (item, index) {
        if (isChoiceItem(item)) buildChoice(block, item, index, items.length, state);
        else if (isOpenItem(item)) buildOpen(block, item, index, items.length);
        else if (isPredictItem(item)) buildPredict(block, item, index, items.length);
        else if (isDeliverableItem(item)) buildDeliverable(block, item, index, items.length);
        else buildBroken(block, item, index, items.length);
      });

      if (state.scoreEl) block.appendChild(state.scoreEl);

      typeset(block);              /* 题面/选项/答案里的公式：建完立刻排（见 typeset 注释） */
      highlight(block);            /* 围栏渲染出的代码块：建完立刻上色（见 highlight 注释） */
    });
  });
})();
