#!/usr/bin/env python3
"""Reels d'Uzi (Café Bistro Romain Gary) : page de validation + envoi progressif à David + publication à la validation.
David, 16/11/2026 : « envoie-moi sur WhatsApp dès que c'est prêt, progressivement […] fais que le bouton מאשר marche pour
publication directe, avec bonnes descriptions et hashtags ».
  rg_reels.py tick   (toutes les minutes par launchd) :
   1. nouveaux marqueurs <nom>.ok (contrôle passé) dans REELS_CUISINE_2026-11-16/ et REGGAE_2026-11-14/rendus_v2/
      → code RG-NN, copie de la version légère sur la page, page republiée, vidéo + lien envoyés à David ;
   2. message WhatsApp d'Uzi ou de David contenant « מאשר [RG-NN] » → publication Instagram (publier_reel.py,
      jamais deux fois), légende posée et relue (poser_legende.py), lien envoyé à David.
Hébreu des légendes : uniquement des phrases déjà validées (legendes_he.txt, VERDICT OK) ; hashtags en mots simples."""
import json, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path
H = Path(__file__).parent; MAN = H / 'reels.json'; RG = Path.home() / 'Projects/02-clients/romain-gary-institut'
IG = RG / 'INSTAGRAM_2026-11-12'; LOG = H / 'rg_reels.log'
SRC = [RG / 'REELS_CUISINE_2026-11-16']  # 16/11 : Uzi ne veut plus de reggae sur son fil → la source reggae est coupée
UZI = {'152196528271428@lid'}; DAVID = '972584921492@s.whatsapp.net'; DAVID_JIDS = {DAVID, '149684039512207@lid'}
URL = 'https://uzi.dreamnovamcp.com/oI1NZFp79eCet5JG/'  # page MCP : le bouton מאשר publie directement
TAGS = {'he': '#ירושלים #כשר #ביסטרו #רומןגארי #אוכלכשר #מסעדהכשרה',
        'fr': '#jerusalem #bistrot #cuisinefrancaise #casher #romaingary #jerusalemfood',
        'en': '#jerusalem #kosher #frenchbistro #jerusalemfood #kosherfood #romaingary'}
SIG = {'fr': 'Café Bistro Romain Gary · 35 rue Hillel, Jérusalem', 'en': 'Café Bistro Romain Gary · 35 Hillel St, Jerusalem',
       'he': 'קפה ביסטרו רומן גארי, הלל 35'}

def log(m): open(LOG, 'a').write(f"{time.strftime('%F %T')} {m}\n")
def wa(to, text=None, path=None):
    tok = open(Path.home() / '.nova/wa_token').read().strip()
    body = {'to': to, 'text': text} if path is None else {'to': to, 'path': str(path), **({'caption': text} if text else {})}
    r = urllib.request.Request('http://127.0.0.1:3010' + ('/send' if path is None else '/send-doc'), json.dumps(body).encode(),
                               {'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(r, timeout=120).read())
def load(): return json.loads(MAN.read_text()) if MAN.exists() else {'reels': []}
def save(m): MAN.write_text(json.dumps(m, ensure_ascii=False, indent=1))

def legende(e):
    l = e['langue']; base = e.get('legende', '').strip()
    he_ok = [x.strip() for x in (IG / 'legendes_he.txt').read_text(encoding='utf-8').splitlines() if x.strip()]
    if l == 'he' and base not in he_ok and base not in ('ערב רגאיי ברומן גארי', 'קפה ביסטרו רומן גארי, הלל 35'):
        base = he_ok[1]  # phrase hébraïque non validée → on la remplace par une validée (jamais d'hébreu non relu en ligne)
    sig = '' if SIG[l] in base else '\n' + SIG[l]
    return f"{base}{sig}\n\n{TAGS[l]}"

def build_page(m):
    def b(lbl, txt): return f'<a class="b" href="https://wa.me/972584921492?text={urllib.parse.quote(txt)}">{lbl}</a>'
    cards = ''
    for e in m['reels']:
        act = (f'<div class="pub">✅ פורסם · <a href="https://www.instagram.com{e["lien"]}">Instagram</a></div>' if e.get('lien')
               else f'<div class="r">{b("✅ מאשר", f"מאשר [{e["code"]}] {e["titre"]}")}{b("✏️ לתקן", f"לתקן [{e["code"]}] {e["titre"]} — ")}</div>')
        media = f'<video controls playsinline preload="metadata" poster="v/{e["code"]}.jpg" src="v/{e["code"]}.mp4"></video>' if e.get('type', 'reel') == 'reel' else f'<img src="v/{e["code"]}.jpg">'
        cards += f'<div class="c">{media}<h2>{e["code"]} · {e["titre"]}</h2>{act}</div>'
    html = f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>קפה ביסטרו רומן גארי · Reels</title>
<style>body{{margin:0;background:#141210;color:#f3ece1;font-family:-apple-system,Helvetica,Arial;text-align:center}}h1{{font-size:24px;margin:28px 12px 4px;color:#e8c46a}}p{{opacity:.7;margin:0 12px 20px}}.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px;max-width:1150px;margin:auto;padding:0 16px 40px}}.c{{background:#1e1b18;border-radius:16px;padding:12px}}video,img{{width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:12px;background:#000}}h2{{font-size:16px;margin:10px 0}}.r{{display:flex;gap:10px}}.b{{flex:1;padding:12px;border-radius:12px;background:#2c2721;color:#f3ece1;text-decoration:none;font-weight:600}}.b:first-child{{background:#e8c46a;color:#141210}}.pub{{padding:12px;color:#9be39b}}.pub a{{color:#9be39b}}</style></head>
<body><h1>קפה ביסטרו רומן גארי</h1><p>Reels · DreamNova</p><div class="g">{cards}</div></body></html>'''
    (H / 'index.html').write_text(html)
    subprocess.run(['git', '-C', str(H), 'add', '-A'], check=True)
    if subprocess.run(['git', '-C', str(H), 'diff', '--cached', '--quiet']).returncode:
        subprocess.run(['git', '-C', str(H), 'commit', '-q', '-m', 'maj reels'], check=True)
        subprocess.run(['git', '-C', str(H), 'push', '-q'], check=True)

def ajouter(m):
    vus = {e.get('marqueur') for e in m['reels']}; neufs = []
    for d in SRC:
        for ok in sorted(d.glob('*.ok')) if d.exists() else []:
            if str(ok) in vus: continue
            try: e = json.loads(ok.read_text().strip().splitlines()[0])
            except Exception as x: log(f'marqueur illisible {ok}: {x}'); continue
            code = f"RG-{len(m['reels']) + 1:02d}"; e.update(code=code, marqueur=str(ok), type=e.get('type', 'reel'))
            if e['type'] == 'reel':
                tel = Path(e['tel']); assert tel.exists() and tel.stat().st_size < 30e6, tel
                shutil.copy(tel, H / 'v' / f'{code}.mp4')
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '2', '-i', str(tel), '-frames:v', '1', '-vf', 'scale=540:-2', '-q:v', '4', str(H / 'v' / f'{code}.jpg')], check=True)
            else:
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', e['images'][0], '-vf', 'scale=540:-2', '-q:v', '4', str(H / 'v' / f'{code}.jpg')], check=True)
            m['reels'].append(e); neufs.append(e); log(f'ajouté {code} {e["titre"]}')
    if neufs:
        save(m); build_page(m)
        for e in neufs:
            f = e['tel'] if e['type'] == 'reel' else e['images'][0]
            wa(DAVID, f"🎬 Nouveau pour Uzi · {e['code']} · {e['titre']} ({e['langue']})", Path(f)); time.sleep(2)
        wa(DAVID, f"Page de validation d'Uzi mise à jour ({len(neufs)} nouveau(x)) :"); time.sleep(1); wa(DAVID, URL)

def valider(m):
    st = H / 'wa_vu.json'; vu = set(json.loads(st.read_text())) if st.exists() else set()
    depuis = time.time() - 6 * 3600; codes = []
    for l in open(Path.home() / '.nova/wa_recent.jsonl', errors='ignore'):
        if '"ts":17' not in l: continue
        d = json.loads(l)
        if d['ts'] < depuis or d['id'] in vu: continue
        txt = d.get('text') or ''
        if d['jid'] in UZI or d['jid'] in DAVID_JIDS:
            mm = re.search(r'מאשר\s*\[(RG-\d+)\]', txt)
            if mm: codes.append(mm.group(1)); vu.add(d['id'])
    st.write_text(json.dumps(sorted(vu)))
    for c in dict.fromkeys(codes): publier(m, c, 'WhatsApp')

def publier(m, c, source):
    """Publie le livrable <c> (une seule fois), pose et relit la légende, prévient David. Renvoie le lien ou None."""
    e = next((x for x in m['reels'] if x['code'] == c), None)
    if not e: return None
    if e.get('lien'): return e['lien']
    lf = H / f'leg_{c}.txt'; lf.write_text(legende(e), encoding='utf-8')
    f = e['complet'] if e['type'] == 'reel' else e['images'][0]
    r = subprocess.run([sys.executable, str(IG / 'publier_reel.py'), f'uzi_{c}', f, str(lf)], capture_output=True, text=True, timeout=900, cwd=IG)
    lien = (re.search(r'(/romain\.gary\.cafe\.bistro/(?:reel|p)/[^/\s]+/)', r.stdout) or [None, None])[1]
    if not lien:
        log(f'publication {c} échouée : {r.stdout[-300:]} {r.stderr[-300:]}'); wa(DAVID, f'⚠️ Publication {c} échouée ({source}), je regarde.'); return None
    p2 = subprocess.run([sys.executable, str(IG / 'poser_legende.py'), 'https://www.instagram.com' + lien, str(lf)], capture_output=True, text=True, timeout=600, cwd=IG)
    e['lien'] = lien; e['legende_ok'] = 'LÉGENDE PRÉSENTE' in p2.stdout; e['valide_par'] = source; save(m); build_page(m)
    log(f'publié {c} {lien} légende={e["legende_ok"]} via {source}')
    wa(DAVID, f"✅ Uzi a validé · publié sur Instagram · {c} · {e['titre']}" + ('' if e['legende_ok'] else ' (légende à revérifier)')); time.sleep(1)
    wa(DAVID, 'https://www.instagram.com' + lien)
    return lien

if __name__ == '__main__':
    m = load()
    if sys.argv[1:] == ['tick']:
        for f in (ajouter, valider):
            try: f(m)
            except Exception as x: log(f'{f.__name__} erreur : {x}')
    elif sys.argv[1:] == ['build']: build_page(m)
