"""The password-protected internal page at /intern/.

The site is static and its repository is public, so a password check alone
would protect nothing. Instead the content is encrypted here, at build time,
and the page decrypts it in the browser with the password the visitor types.
Only the ciphertext (intern/data.bin) is committed and served.

Sources (outside this repository, never committed here):
    ../Swinder/docs/questions.md, plan.md, research.md
    ../Swinder/prototype/index.html

Password: environment variable KL_INTERN_PASSWORD, or the first line of the
gitignored file .intern-password in the repository root. Never commit it.

Without the password or the sources, the existing intern/data.bin is kept.
Without any data.bin, the page and the footer link are left out.

Format of data.bin: 16 bytes salt, then AES-256-CBC ciphertext (PKCS#7).
Key (32 bytes) and IV (16 bytes) are PBKDF2-HMAC-SHA256(password, salt, ITER).
The plaintext starts with MAGIC, which is how the page recognises a wrong
password. The salt is derived from password and content, so an unchanged
build gives an unchanged file.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import pathlib
import re
import subprocess

ITER = 310_000
MAGIC = "KLINTERN1\n"

DOCS = [
    # id, file, tab label
    ("questions", "questions.md", "Fragen"),
    ("plan", "plan.md", "Plan"),
    ("research", "research.md", "Recherche"),
]


# --------------------------------------------------------------------------
# Markdown, the small subset the documents use: headings, paragraphs, flat
# lists with wrapped lines, tables, rules, bold, italics, code, links.
# --------------------------------------------------------------------------

_ITEM = re.compile(r"^([-*]|\d+\.)\s+(.*)$")


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    def link(m: re.Match) -> str:
        text, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://")):
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
        for doc_id, name, _ in DOCS:
            if url.split("#")[0].endswith(name):
                return f'<a href="#{doc_id}" data-tab="{doc_id}">{text}</a>'
        return text

    s = re.sub(r"`([^`]+)`", stash, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(
        r"&lt;(https?://[^\s&]+)&gt;",
        lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>',
        s,
    )
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def markdown(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            flush()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
            i += 1
            continue
        if re.match(r"^-{3,}$", line):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            head, body = _cells(rows[0]), rows[1:]
            if body and re.match(r"^\|[\s:|-]+\|?$", body[0]):
                body = body[1:]
            t = '<div class="iv-table"><table><thead><tr>'
            t += "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
            for r in body:
                t += "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in _cells(r)) + "</tr>"
            out.append(t + "</tbody></table></div>")
            continue
        m = _ITEM.match(line)
        if m and not para:
            ordered = m.group(1)[0].isdigit()
            start = m.group(1).rstrip(".") if ordered else ""
            items: list[list[str]] = []
            while i < len(lines):
                cur = lines[i].rstrip()
                m = _ITEM.match(cur)
                if m and m.group(1)[0].isdigit() == ordered:
                    items.append([m.group(2)])
                elif cur.startswith(" ") and cur.strip():
                    items[-1].append(cur.strip())
                elif not cur.strip():
                    nxt = lines[i + 1] if i + 1 < len(lines) else ""
                    nm = _ITEM.match(nxt)
                    if nm and nm.group(1)[0].isdigit() == ordered:
                        pass
                    elif nxt.startswith(" ") and nxt.strip():
                        items[-1].append("\x01")
                    else:
                        break
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            attr = f' start="{start}"' if ordered and start != "1" else ""
            lis = "".join(
                "<li>" + _inline(" ".join(it)).replace(" \x01 ", "<br><br>").replace("\x01", "") + "</li>"
                for it in items
            )
            out.append(f"<{tag}{attr}>{lis}</{tag}>")
            continue
        para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


# --------------------------------------------------------------------------
# Encryption
# --------------------------------------------------------------------------


def _password(root: pathlib.Path) -> str | None:
    pw = os.environ.get("KL_INTERN_PASSWORD")
    if pw:
        return pw
    f = root / ".intern-password"
    if f.exists():
        lines = f.read_text(encoding="utf-8").splitlines()
        return lines[0].strip() if lines and lines[0].strip() else None
    return None


def _payload(swinder: pathlib.Path) -> str:
    docs = []
    for doc_id, name, label in DOCS:
        docs.append({"id": doc_id, "label": label, "html": markdown((swinder / "docs" / name).read_text(encoding="utf-8"))})
    proto = (swinder / "prototype" / "index.html").read_text(encoding="utf-8")
    # The local build offers own test photos through custom-items.js; not here.
    proto = proto.replace('<script src="custom-items.js"></script>\n', "")
    return json.dumps({"proto_label": "Prototyp", "proto": proto, "docs": docs}, ensure_ascii=False)


def _encrypt(plain: bytes, password: str) -> bytes:
    salt = hashlib.sha256(b"kl-intern-salt\0" + password.encode() + b"\0" + plain).digest()[:16]
    bits = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITER, 48)
    res = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-nosalt", "-K", bits[:32].hex(), "-iv", bits[32:].hex()],
        input=plain, capture_output=True, check=True,
    )
    return salt + res.stdout


def build_data(root: pathlib.Path) -> str | None:
    """Refresh intern/data.bin if possible. Returns its version tag, or None if there is no data."""
    out = root / "intern" / "data.bin"
    swinder = root.parent / "Swinder"
    pw = _password(root)
    have_sources = all((swinder / "docs" / d[1]).exists() for d in DOCS) and (swinder / "prototype" / "index.html").exists()
    if pw and have_sources:
        data = _encrypt((MAGIC + _payload(swinder)).encode("utf-8"), pw)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or out.read_bytes() != data:
            out.write_bytes(data)
            print("wrote intern/data.bin (encrypted)")
    elif out.exists():
        print("intern: no password or sources, keeping the existing intern/data.bin")
    else:
        print("intern: no password or sources and no data.bin, page left out")
        return None
    return hashlib.sha256(out.read_bytes()).hexdigest()[:10]


# --------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------

STYLE = """<style>
.iv-lock { min-height: 72vh; display: grid; place-items: center; padding: 120px var(--gutter) 64px; }
.iv-lock form { width: min(420px, 100%); text-align: center; }
.iv-lock .eyebrow { justify-content: center; }
.iv-lock h1 { font-size: clamp(28px, 5vw, 38px); margin: 14px 0 10px; }
.iv-lock p { color: var(--muted); margin: 0 0 22px; }
.iv-lock input { width: 100%; font: inherit; font-size: 17px; color: var(--text); background: var(--surface);
  border: 1px solid var(--line-2); border-radius: var(--radius-sm); padding: 14px 16px; margin-bottom: 12px; }
.iv-lock input:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
.iv-lock button { width: 100%; justify-content: center; cursor: pointer; font: inherit; font-weight: 700; }
.iv-lock button[disabled] { opacity: .6; cursor: progress; }
.iv-err { min-height: 1.5em; margin: 12px 0 0 !important; color: var(--rose) !important; }
#iv { display: none; }
body.iv-open .site-header, body.iv-open .site-footer, body.iv-open .iv-lock, body.iv-open .skip { display: none; }
body.iv-open #iv { display: block; }
.iv-bar { position: sticky; top: 0; z-index: 5; height: 52px; display: flex; align-items: center; gap: 6px;
  padding: 0 max(12px, env(safe-area-inset-right)) 0 max(12px, env(safe-area-inset-left));
  background: rgba(7, 10, 18, .92); backdrop-filter: blur(12px); border-bottom: 1px solid var(--line);
  overflow-x: auto; scrollbar-width: none; }
.iv-bar::-webkit-scrollbar { display: none; }
.iv-bar a.iv-home { display: flex; flex: none; margin-right: 6px; }
.iv-bar button { flex: none; font: inherit; font-size: 15px; font-weight: 600; color: var(--muted); background: none;
  border: 0; border-radius: 999px; padding: 8px 14px; cursor: pointer; white-space: nowrap; }
.iv-bar button[aria-selected="true"] { color: #10131c; background: var(--amber); }
.iv-bar button:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
.iv-panel[hidden] { display: none; }
.iv-proto { height: calc(100vh - 52px); height: calc(100dvh - 52px); display: grid; place-items: center; padding: 16px; }
.iv-phone { height: min(844px, 100%); aspect-ratio: 390 / 844; max-width: 100%; border: 10px solid #1a2132;
  border-radius: 44px; overflow: hidden; background: #000; box-shadow: 0 30px 80px rgba(0, 0, 0, .55), 0 0 0 1px var(--line-2); }
.iv-phone iframe { display: block; width: 100%; height: 100%; border: 0; background: #fff; }
@media (max-width: 560px) {
  .iv-proto { padding: 0; }
  .iv-bar { gap: 2px; }
  .iv-bar a.iv-home { margin-right: 2px; }
  .iv-bar button { font-size: 14px; padding: 7px 10px; }
  .iv-phone { width: 100%; height: 100%; aspect-ratio: auto; border: 0; border-radius: 0; box-shadow: none; }
}
.iv-doc { max-width: 860px; margin: 0 auto; padding: 32px var(--gutter) 96px; line-height: 1.65; overflow-wrap: break-word; }
.iv-doc h1 { font-size: clamp(28px, 5vw, 40px); line-height: 1.15; margin: 0 0 20px; }
.iv-doc h2 { font-size: clamp(22px, 3.6vw, 28px); margin: 48px 0 12px; padding-top: 20px; border-top: 1px solid var(--line); }
.iv-doc h3 { font-size: 19px; margin: 32px 0 8px; }
.iv-doc h4 { font-size: 16px; margin: 24px 0 6px; }
.iv-doc p, .iv-doc li { color: #d5dbe7; }
.iv-doc li { margin: 6px 0; }
.iv-doc ul, .iv-doc ol { padding-left: 22px; }
.iv-doc a { color: var(--amber); }
.iv-doc code { font-size: .9em; background: var(--surface-2); padding: 1px 5px; border-radius: 6px; }
.iv-doc hr { border: 0; border-top: 1px solid var(--line); margin: 36px 0; }
.iv-table { overflow-x: auto; margin: 18px 0; border: 1px solid var(--line); border-radius: var(--radius-sm); }
.iv-table table { border-collapse: collapse; width: 100%; font-size: 14.5px; line-height: 1.5; }
.iv-table th, .iv-table td { text-align: left; vertical-align: top; padding: 10px 12px; border-bottom: 1px solid var(--line); min-width: 110px; }
.iv-table th { color: var(--text); background: var(--surface); white-space: nowrap; }
.iv-table td { color: #d5dbe7; }
.iv-table tr:last-child td { border-bottom: 0; }
</style>
"""

SCRIPT = """<script>
(function () {
  var ITER = __ITER__, MAGIC = __MAGIC__, DATA = "/intern/data.bin?v=__VERSION__";
  var form = document.getElementById("iv-form"), input = document.getElementById("iv-pw"),
      err = document.getElementById("iv-err"), btn = document.getElementById("iv-go"), root = document.getElementById("iv");

  function decrypt(pw) {
    var enc = new TextEncoder(), buf;
    return fetch(DATA).then(function (r) {
      if (!r.ok) throw new Error("load");
      return r.arrayBuffer();
    }).then(function (b) {
      buf = new Uint8Array(b);
      return crypto.subtle.importKey("raw", enc.encode(pw), "PBKDF2", false, ["deriveBits"]);
    }).then(function (km) {
      return crypto.subtle.deriveBits({ name: "PBKDF2", salt: buf.slice(0, 16), iterations: ITER, hash: "SHA-256" }, km, 384);
    }).then(function (bits) {
      bits = new Uint8Array(bits);
      return crypto.subtle.importKey("raw", bits.slice(0, 32), "AES-CBC", false, ["decrypt"]).then(function (key) {
        return crypto.subtle.decrypt({ name: "AES-CBC", iv: bits.slice(32, 48) }, key, buf.slice(16));
      });
    }).then(function (plain) {
      var text = new TextDecoder().decode(plain);
      if (text.slice(0, MAGIC.length) !== MAGIC) throw new Error("wrong");
      return JSON.parse(text.slice(MAGIC.length));
    }, function (e) {
      throw new Error(e && e.message === "load" ? "load" : "wrong");
    });
  }

  function show(data) {
    var bar = document.createElement("div"), panels = {}, tabs = {};
    bar.className = "iv-bar";
    bar.setAttribute("role", "tablist");
    bar.innerHTML = '<a class="iv-home" href="/de/" aria-label="Kroess Labs Startseite"><img src="/assets/img/logo.svg" alt="" width="28" height="28"></a>';
    root.appendChild(bar);

    function add(id, label, node) {
      var b = document.createElement("button");
      b.type = "button"; b.textContent = label;
      b.setAttribute("role", "tab");
      b.addEventListener("click", function () { select(id); });
      bar.appendChild(b); tabs[id] = b;
      node.className = "iv-panel " + node.className; node.hidden = true;
      node.setAttribute("role", "tabpanel");
      root.appendChild(node); panels[id] = node;
    }
    function select(id) {
      if (!panels[id]) return;
      Object.keys(panels).forEach(function (k) {
        panels[k].hidden = k !== id;
        tabs[k].setAttribute("aria-selected", k === id ? "true" : "false");
      });
      window.scrollTo(0, 0);
    }

    var proto = document.createElement("div");
    proto.className = "iv-proto";
    var phone = document.createElement("div"), frame = document.createElement("iframe");
    phone.className = "iv-phone";
    frame.title = data.proto_label;
    // No allow-same-origin: the prototype cannot reach this site and cannot
    // store anything in the browser. Its state lives until the page reloads.
    frame.setAttribute("sandbox", "allow-scripts");
    frame.srcdoc = data.proto;
    phone.appendChild(frame); proto.appendChild(phone);
    add("proto", data.proto_label, proto);

    data.docs.forEach(function (d) {
      var el = document.createElement("article");
      el.className = "iv-doc";
      el.innerHTML = d.html;
      add(d.id, d.label, el);
    });
    root.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[data-tab]");
      if (a) { e.preventDefault(); select(a.getAttribute("data-tab")); }
    });
    document.body.classList.add("iv-open");
    select("proto");
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!window.crypto || !crypto.subtle) { err.textContent = "Dieser Browser kann die Seite nicht entschlüsseln."; return; }
    err.textContent = ""; btn.disabled = true;
    decrypt(input.value).then(function (data) {
      input.value = "";
      show(data);
    }, function (e) {
      btn.disabled = false;
      err.textContent = e.message === "load" ? "Die Inhalte konnten nicht geladen werden." : "Das Passwort stimmt nicht.";
      input.select();
    });
  });
})();
</script>
"""

MAIN = """<section class="iv-lock">
  <form id="iv-form" autocomplete="off">
    <span class="eyebrow">Intern</span>
    <h1>Nur mit Passwort</h1>
    <p>Dieser Bereich ist für Leute, die wir eingeladen haben.</p>
    <input id="iv-pw" type="password" aria-label="Passwort" placeholder="Passwort" autocomplete="off" autocapitalize="off" spellcheck="false" required>
    <button id="iv-go" class="btn btn-primary" type="submit">Öffnen</button>
    <p id="iv-err" class="iv-err" role="alert"></p>
  </form>
</section>
<div id="iv"></div>
<noscript><p style="text-align:center;padding:0 16px 64px">Für diesen Bereich muss JavaScript eingeschaltet sein.</p></noscript>"""


def page_parts(version: str) -> tuple[str, str]:
    """Returns (extra head HTML, main HTML) for the page."""
    script = SCRIPT.replace("__ITER__", str(ITER)).replace("__MAGIC__", json.dumps(MAGIC)).replace("__VERSION__", version)
    return STYLE, MAIN + "\n" + script
