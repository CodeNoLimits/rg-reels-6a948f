#!/usr/bin/env python3
"""Page de validation d'Uzi sur uzi.dreamnovamcp.com (tunnel Cloudflare → 127.0.0.1:8852), lien privé /<clé>/.
« ✅ מאשר » → POST /<clé>/api/valider → publication Instagram directe (rg_reels.publier), sans WhatsApp (David, 16/11).
« ✏️ לתקן » → POST /<clé>/api/corriger avec son commentaire → transmis à David. La page se rafraîchit seule."""
import json, os, secrets, threading, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import rg_reels as R
H = Path(__file__).parent; KF = H / '.cle_uzi'
if not KF.exists(): KF.write_text(secrets.token_urlsafe(12))
KEY = KF.read_text().strip(); VERROU = threading.Lock(); EN_COURS = set()

def page():
    m = R.load(); cartes = ''
    for e in m['reels']:
        c = e['code']
        if e.get('lien'): act = f'<div class="pub">✅ פורסם · <a href="https://www.instagram.com{e["lien"]}" target="_blank">Instagram</a></div>'
        elif c in EN_COURS: act = '<div class="pub">⏳ מתפרסם…</div>'
        else: act = (f'<div class="r"><button class="b ok" onclick="ok(\'{c}\')">✅ מאשר</button>'
                     f'<button class="b" onclick="fix(\'{c}\')">✏️ לתקן</button></div>')
        media = (f'<video controls playsinline preload="metadata" poster="v/{c}.jpg" src="v/{c}.mp4"></video>' if e.get('type', 'reel') == 'reel'
                 else f'<img src="v/{c}.jpg">')
        cartes += f'<div class="c" id="{c}">{media}<h2>{c} · {e["titre"]} · {e["langue"].upper()}</h2>{act}</div>'
    return f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>קפה ביסטרו רומן גארי · Reels</title>
<style>body{{margin:0;background:#141210;color:#f3ece1;font-family:-apple-system,Helvetica,Arial;text-align:center}}h1{{font-size:24px;margin:28px 12px 4px;color:#e8c46a}}p{{opacity:.7;margin:0 12px 20px}}.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px;max-width:1150px;margin:auto;padding:0 16px 40px}}.c{{background:#1e1b18;border-radius:16px;padding:12px}}video,img{{width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:12px;background:#000}}h2{{font-size:15px;margin:10px 0}}.r{{display:flex;gap:10px}}.b{{flex:1;padding:13px;border:0;border-radius:12px;background:#2c2721;color:#f3ece1;font-size:16px;font-weight:600}}.ok{{background:#e8c46a;color:#141210}}.pub{{padding:12px;color:#9be39b}}.pub a{{color:#9be39b}}</style></head>
<body><h1>קפה ביסטרו רומן גארי</h1><p>Reels · DreamNova</p><div class="g">{cartes}</div>
<script>
async function post(u,d){{const r=await fetch(u,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});return r.json();}}
async function ok(c){{const x=document.querySelector('#'+c+' .r');x.innerHTML='<div class="pub">⏳ מתפרסם…</div>';await post('api/valider',{{code:c}});}}
async function fix(c){{const t=prompt('מה לתקן?');if(t){{await post('api/corriger',{{code:c,texte:t}});alert('✓');}}}}
setInterval(async()=>{{const r=await fetch('api/etat');const s=await r.json();for(const[c,l] of Object.entries(s)){{const el=document.querySelector('#'+c+' .r, #'+c+' .pub');if(l&&el&&!el.innerHTML.includes('Instagram'))location.reload();}}}},8000);
</script></body></html>'''

def lancer(c):
    with VERROU:
        try: R.publier(R.load(), c, 'page uzi.dreamnovamcp.com')
        except Exception as x: R.log(f'publier {c} erreur : {x}'); R.wa(R.DAVID, f'⚠️ Publication {c} échouée, je regarde.')
        finally: EN_COURS.discard(c)

class Hd(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body, ct='text/html; charset=utf-8'):
        b = body if isinstance(body, bytes) else body.encode(); self.send_response(code)
        self.send_header('Content-Type', ct); self.send_header('Content-Length', str(len(b))); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)
    def _chemin(self):
        p = urllib.parse.urlparse(self.path).path
        if not p.startswith(f'/{KEY}/'): return None
        return p[len(KEY) + 2:]
    def do_GET(self):
        p = self._chemin()
        if p is None: return self._send(404, 'introuvable')
        if p in ('', 'index.html'): return self._send(200, page())
        if p == 'api/etat': return self._send(200, json.dumps({e['code']: e.get('lien') for e in R.load()['reels']}), 'application/json')
        f = (H / p).resolve()
        if p.startswith('v/') and f.is_file() and H in f.parents:
            ct = 'video/mp4' if f.suffix == '.mp4' else 'image/jpeg'; data = f.read_bytes()
            rng = self.headers.get('Range')
            if rng and ct == 'video/mp4':  # lecture vidéo sur téléphone : réponses partielles
                a, _, b = rng.replace('bytes=', '').partition('-'); a = int(a or 0); b = int(b) if b else len(data) - 1
                self.send_response(206); self.send_header('Content-Type', ct); self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Content-Range', f'bytes {a}-{b}/{len(data)}'); self.send_header('Content-Length', str(b - a + 1)); self.end_headers(); self.wfile.write(data[a:b + 1]); return
            return self._send(200, data, ct)
        self._send(404, 'introuvable')
    def do_POST(self):
        p = self._chemin(); n = int(self.headers.get('Content-Length') or 0)
        try: d = json.loads(self.rfile.read(n) or b'{}')
        except Exception: d = {}
        c = str(d.get('code', ''))
        if p is None or not any(e['code'] == c for e in R.load()['reels']): return self._send(404, '{}', 'application/json')
        if p == 'api/valider':
            if c not in EN_COURS: EN_COURS.add(c); threading.Thread(target=lancer, args=(c,), daemon=True).start()
            R.log(f'validation {c} depuis la page'); return self._send(200, '{"ok":true}', 'application/json')
        if p == 'api/corriger':
            t = str(d.get('texte', ''))[:500]; R.log(f'correction {c} : {t}')
            R.wa(R.DAVID, f'✏️ Uzi demande une correction sur {c} : {t}'); return self._send(200, '{"ok":true}', 'application/json')
        self._send(404, '{}', 'application/json')

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8852), Hd).serve_forever()
