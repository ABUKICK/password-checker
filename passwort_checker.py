"""
Passwort-Check (Mit zentriertem Info-Fenster)
"""

from __future__ import annotations

import math
import os
import re
import secrets
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Set, Tuple

try:
    from zxcvbn import zxcvbn as _ZXCVBN
except Exception:
    _ZXCVBN = None

# ----------------------------------------------------------------------------
# Konstanten
# ----------------------------------------------------------------------------
STUFEN = ("Sehr schwach", "Schwach", "Mittel", "Stark", "Sehr stark")
STUFEN_FARBEN = ("#dc2626", "#ea580c", "#ca8a04", "#65a30d", "#16a34a")
STUFEN_SCHWELLEN = (28, 36, 50, 64)

MIN_LAENGE_EMPFOHLEN = 12
BITS_WORT = 2.0
BITS_ZUFALL_BUCHSTABE = 4.3
BITS_ZEICHEN = 3.5
BITS_ERSETZUNG = 2.0
ZUFALL_FAKTOR = 0.8

LEET = {"@": "a", "4": "a", "3": "e", "1": "i", "0": "o", "$": "s", "5": "s", "7": "t"}
TASTATURREIHEN = ("qwertzuiopü", "asdfghjklöä", "yxcvbnm", "qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890")
BUCHSTABEN = "A-Za-zÄÖÜäöüß"
TOKEN_RE = re.compile(f"[{BUCHSTABEN}]+|[^{BUCHSTABEN}]+")
WORT_RE = re.compile(r"[A-ZÄÖÜ]?[a-zäöüß]+|[A-ZÄÖÜ]+|(?:[A-ZÄÖÜ][a-zäöüß]+)+")
BLOCK_RE = re.compile(r"(.{2,}?)\1+", re.S)

ZWISCHENABLAGE_LEEREN_NACH_MS = 30_000
ZUFALL_KLEIN = "abcdefghijkmnopqrstuvwxyz"
ZUFALL_GROSS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
ZUFALL_ZIFFERN = "23456789"
ZUFALL_SONDER = "!@#$%&*?-_=+"

# Eingebaute Basis-Liste
_HAEUFIGE_TEXT = """
0 101010 10203 102030 10203040 1111 11111 111111 1111111 11111111 111111111 1111111111 11112222
112233 11223344 1122334455 1212 121212 12121212 123123 123123123 1234 12341234 12344321 12345
1234512345 1234554321 123456 1234567 12345678 123456788 123456789 1234567890 12345678900 12345678901
1234567891 12345678910 1234567899 123456789a 123456789aA@ 12345678@ 12345678a 12345679 1234567a
123456a 123456aa 123456aA@ 1234abcd 1234qwer 123654 123abc 123admin 123qwe 123qweasd 124578 12qwaszx
1313 131313 135790 147258369 1q2w3e4r 1q2w3e4r5t 1qaz2wsx 1qazxsw2 2000 202020 2112 2222 222222
22446688 232323 246810 3333 4128 4321 4444 5150 54321 5555 555555 654321 6666 666666 6969 696969
7654321 7777 777777 7777777 8675309 87654321 888888 88888888 987654 987654321 999999 999999999
a123456 a1234567 a12345678 a123456789 a123456a a1b2c3d4 aa102030 aa112233 aa123123 aa123456
aa1234567 aa12345678 aa123456789 aa@12345 aa@123456 aa@1234567 aa@123456789 aaa111 aaaa aaaa1111
aaaaaa aabb1122 ab123456 abc123 abc12345 abc123456 abc@123 abc@1234 abc@12345 abcd1234 abcd1234@
abcd@123 abcd@1234 abgrtyu aboy1234 access access14 action admin admin1 admin123 admin1234
admin12345 admin123456 admin@123 admin@1234 adminadmin adminisp administrator admintelecom albert
alex alexis amanda amateur andrew angel angela angels animal anthony apollo apple apples arsenal
arthur asdasd asdf asdf1234 asdfgh asdfghjkl ashley asshole august austin azerty azerty123 baby
badboy bailey banana barney baseball batman beach bear beaver beavis beer bigcock bigdaddy bigdick
bigdog bigtits bill billy bismillah bitch bitches biteme black blazer blonde blondes blowjob blowme
blue bond007 bonnie booboo boobs booger boomer booty boston brandon brandy braves brazil brian
bronco broncos bubba bulldog buster butter butthead calvin camaro cameron canada captain carlos
carter casper changeme charles charlie cheese chelsea chester chevy chicago chicken cisco cocacola
coffee college compaq computer contraseña cool cooper corvette cowboy cowboys cream crystal cumming
cumshot cunt dakota dallas daniel danielle dave david debbie demo@123 dennis diablo diamond dick
dirty doctor doggie dolphin dolphins donald dragon dreams driver eagle eagle1 eagles edward einstein
enter eric erotic extreme falcon fender ferrari fire firebird fish fishing florida flower flyers
football football1 ford forever frank fred freddy freedom fuck fucked fucker fucking fuckme fuckyou
gandalf gatekeeper gateway gators gemini george ghost giants ginger girl girls global123@ golden
golf golfer gordon great gregory guest guitar gunner guru123456 hammer hannah happy hardcore harley
heather hello helpme hentai heslo1234 hockey hooters horney horny hotdog house hunter hunting iceman
iloveyou india@123 internet iwantu jack jackie jackson jaguar jake james japan jason jasper jennifer
jeremy jessica john johnny johnson jordan joseph joshua juice junior justin kapler123 kevin killer
king kitty knight ladies lakers lauren leather legend letmein little lol123456 london love lover
lovers lucky madison maggie magic magnum makeit marine mark marlboro martin marvin master matrix
matthew maverick maxwell melissa member mercedes merlin michael michelle mickey midnight mike miller
mine minecraft mistress monica monkey monster morgan mother mountain movie muffin murphy music
mustang naked nascar nathan naughty ncc1701 newyork nicholas nicole nipple nipples orange ou812
p@$$w0rd p@55w0rd p@ssw0rd packers pakistan pakistan123 panties paris parker pass pass@123 pass@1234
pass@12345 passw0rd password password1 password123 password@1 password@123 patrick paul peaches
peanut penis pepper peter phantom phoenix player please pookie porn porno porsche power prince
princess private pussies pussy q1w2e3r4 q1w2e3r4t5 qazwsx qwer1234 qwer4321 qwert qwerty qwerty123
qwerty1234 qwerty12345 qwerty123456 qwerty@123 qwertyui qwertyuiop rabbit rachel raiders rainbow
ranger rangers rebecca redskins redsox redwings richard robert rock rocket rosebud runner rush2112
russia samantha sammy samson sandra saturn scooby scooter scorpio scorpion scott secret sexsex sexy
shadow shannon shaved shit sierra silver skippy slayer slut smith smokey snoopy soccer sophie spanky
sparky spider squirt srinivas star stars startrek starwars steelers steve steven sticky stupid
success suckit summer sunshine super superman surfer swimming sydney taylor teens tennis teresa test
test123 test1234 test@123 tester testing theman theworldinyourhand thomas thunder thx1138 tiffany
tiger tigers tigger time tits tomcat topgun toyota travis trouble trustno1 tucker turktelekom turtle
united user1234 vagina victor victoria video viking viper vodafone voodoo voyager walter warrior
welcome welcome1 welcome@123 whatever white william willie wilson winner winston winter wizard wolf
women xavier xxxx xxxxx xxxxxx xxxxxxxx yamaha yankee yankees yellow young zxcvbn zxcvbnm zxcvbnm123
zzzzzz
"""

# ----------------------------------------------------------------------------
# Bewertungslogik
# ----------------------------------------------------------------------------
def entleet(s: str) -> Tuple[str, int]:
    out = list(s)
    n = len(s)
    ersetzt = 0
    def wortzeichen(c: str) -> bool:
        return c.isalpha() or c in LEET
    for i, ch in enumerate(s):
        if ch not in LEET:
            continue
        innen = (0 < i < n - 1 and wortzeichen(out[i - 1]) and wortzeichen(s[i + 1])
                 and (out[i - 1].isalpha() or s[i + 1].isalpha()))
        anfang = i == 0 and ch in "@$" and n > 1 and wortzeichen(s[1])
        if innen or anfang:
            out[i] = LEET[ch]
            ersetzt += 1
    return "".join(out), ersetzt

def bereite_liste_vor(woerter: Iterable[str]) -> Dict[str, str]:
    bereinigt = []
    for wort in woerter:
        wort = wort.strip().lower()
        if wort and not wort.startswith("#"):
            bereinigt.append(wort)
    zuordnung: Dict[str, str] = {wort: wort for wort in bereinigt}
    for wort in bereinigt:
        zuordnung.setdefault(entleet(wort)[0], wort)
    return zuordnung

def lade_basis_liste() -> Dict[str, str]:
    woerter = _HAEUFIGE_TEXT.split()
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haeufige_passwoerter.txt")
    try:
        with open(pfad, encoding="utf-8", errors="ignore") as f:
            woerter.extend(f.read().splitlines())
    except OSError:
        pass
    return bereite_liste_vor(woerter)

def finde_treffer(passwort: str, haeufige: Mapping[str, str]) -> Optional[str]:
    if not passwort:
        return None
    low = passwort.lower()
    kandidaten = {low, entleet(low)[0]}
    for k in kandidaten:
        if k in haeufige:
            return haeufige[k]
    for k in kandidaten:
        basis = re.sub(r"^[^a-zäöüß]+", "", re.sub(r"[^a-zäöüß]+$", "", k))
        if len(basis) >= 4 and basis in haeufige:
            return haeufige[basis]
    return None

def wiederholter_block(passwort: str) -> Optional[str]:
    m = BLOCK_RE.fullmatch(passwort)
    return m.group(1) if m else None

VOKALE = frozenset("aeiouyäöü")

def wortaehnlich(tok: str) -> bool:
    if not WORT_RE.fullmatch(tok):
        return False
    low = tok.lower()
    if sum(c in VOKALE for c in low) * 4 < len(low):
        return False
    return re.search(r"[^aeiouyäöü]{5,}", low) is None

def gewichte(low: str) -> List[float]:
    n = len(low)
    w = [1.0] * n
    for i in range(2, n):
        if low[i] == low[i - 1] == low[i - 2]:
            w[i] = 0.0
    i = 0
    while i < n - 1:
        d = ord(low[i + 1]) - ord(low[i])
        if d in (1, -1):
            j = i + 1
            while j < n - 1 and ord(low[j + 1]) - ord(low[j]) == d:
                j += 1
            if j - i >= 2:
                for k in range(i + 1, j + 1):
                    w[k] = min(w[k], 0.25)
            i = j
        else:
            i += 1
    for reihe in TASTATURREIHEN:
        for r in (reihe, reihe[::-1]):
            for start in range(len(r) - 3):
                teil = r[start:start + 4]
                pos = low.find(teil)
                while pos != -1:
                    for k in range(pos + 1, pos + 4):
                        w[k] = min(w[k], 0.25)
                    pos = low.find(teil, pos + 1)
    return w

def pool_groesse(passwort: str) -> int:
    pool = 0
    if any(c.islower() for c in passwort): pool += 26
    if any(c.isupper() for c in passwort): pool += 26
    if any(c.isdigit() for c in passwort): pool += 10
    if any(not c.isalnum() for c in passwort): pool += 33
    return max(pool, 10)

def schaetze_bits(passwort: str) -> Tuple[float, Set[str]]:
    if not passwort:
        return 0.0, set()
    w = gewichte(passwort.lower())
    norm, ersetzt = entleet(passwort)
    muster: Set[str] = set()
    if any(w[i] == 0.0 for i in range(1, len(w))): muster.add("wiederholung")
    if any(0.0 < x < 1.0 for x in w): muster.add("folge")

    bits = ersetzt * BITS_ERSETZUNG
    wortartig = 0
    woerter = 0
    sonstige = 0
    for m in TOKEN_RE.finditer(norm):
        a, b = m.span()
        eff = sum(w[a:b])
        tok = m.group()
        if tok[0].isalpha():
            if len(tok) >= 3 and wortaehnlich(tok):
                bits += eff * BITS_WORT
                woerter += 1
                wortartig += len(tok) >= 4
            else:
                bits += eff * BITS_ZUFALL_BUCHSTABE
        else:
            bits += eff * BITS_ZEICHEN
            sonstige += 1

    if wortartig == 0:
        bits = max(bits, sum(w) * math.log2(pool_groesse(passwort)) * ZUFALL_FAKTOR)
    elif woerter == 1 and sonstige >= 1:
        muster.add("wort_zahl")
    return bits, muster

def stufe_aus_bits(bits: float) -> int:
    return sum(bits >= grenze for grenze in STUFEN_SCHWELLEN)

@dataclass
class Ergebnis:
    stufe: int
    bits: float
    treffer: Optional[str] = None
    merkmale: List[Tuple[str, bool]] = field(default_factory=list)
    hinweise: List[str] = field(default_factory=list)

def baue_merkmale(passwort: str, treffer: Optional[str]) -> List[Tuple[str, bool]]:
    return [
        (f"Mindestens {MIN_LAENGE_EMPFOHLEN} Zeichen", len(passwort) >= MIN_LAENGE_EMPFOHLEN),
        ("Groß- und Kleinbuchstaben", any(c.islower() for c in passwort) and any(c.isupper() for c in passwort)),
        ("Zahlen", any(c.isdigit() for c in passwort)),
        ("Sonderzeichen oder Leerzeichen", any(not c.isalnum() for c in passwort)),
        ("Kein häufiges Passwort", treffer is None),
    ]

def baue_hinweise(passwort: str, treffer: Optional[str], block: Optional[str],
                  muster: Set[str], stufe: int) -> List[str]:
    h: List[str] = []
    if treffer:
        h.append("Komplett ändern: Dieses Passwort oder eine leichte Abwandlung steht in Listen häufiger Passwörter.")
    if block:
        h.append("Ein Teil wiederholt sich. Wiederholungen bringen kaum zusätzlichen Schutz.")
    elif "wiederholung" in muster:
        h.append("Gleiche Zeichen hintereinander erhöhen die Sicherheit kaum.")
    if "folge" in muster:
        h.append("Folgen wie abc, 1234 oder qwertz sind leicht zu erraten.")
    if "wort_zahl" in muster:
        h.append("Ein Wort mit angehängter Zahl ist ein sehr typisches Muster.")
    if len(passwort) < MIN_LAENGE_EMPFOHLEN:
        h.append(f"Länger ist besser: ab {MIN_LAENGE_EMPFOHLEN} Zeichen.")
    if not h:
        if stufe >= 3:
            h.append("Verwende es nur für ein einziges Konto.")
        else:
            h.append("Mehr Länge und mehr Zufall machen es stärker.")
    return h[:4]

def bewerte(passwort: str, haeufige: Mapping[str, str],
            zxcvbn_fn: Optional[Callable] = _ZXCVBN) -> Ergebnis:
    if not passwort:
        return Ergebnis(stufe=0, bits=0.0)
    treffer = finde_treffer(passwort, haeufige)
    block = wiederholter_block(passwort)
    bits, muster = schaetze_bits(block or passwort)
    if treffer:
        bits = 0.0
    stufe = stufe_aus_bits(bits)
    if zxcvbn_fn and not treffer:
        try:
            stufe = min(stufe, int(zxcvbn_fn(passwort[:72])["score"]))
        except Exception:
            pass
    return Ergebnis(stufe=stufe, bits=bits, treffer=treffer,
                    merkmale=baue_merkmale(passwort, treffer),
                    hinweise=baue_hinweise(passwort, treffer, block, muster, stufe))

def erzeuge_passwort(haeufige: Mapping[str, str], laenge: int = 18) -> str:
    laenge = max(12, min(int(laenge), 64))
    alle = ZUFALL_KLEIN + ZUFALL_GROSS + ZUFALL_ZIFFERN + ZUFALL_SONDER
    gruppen = (ZUFALL_KLEIN, ZUFALL_GROSS, ZUFALL_ZIFFERN, ZUFALL_SONDER)
    ziel = 4 if laenge >= 13 else 3
    bester, beste_bits = "", -1.0
    for _ in range(200):
        pw = "".join(secrets.choice(alle) for _ in range(laenge))
        if not all(any(c in g for c in pw) for g in gruppen):
            continue
        erg = bewerte(pw, haeufige, None)
        if erg.stufe >= ziel:
            return pw
        if erg.bits > beste_bits:
            bester, beste_bits = pw, erg.bits
    return bester

# ----------------------------------------------------------------------------
# Design & GUI
# ----------------------------------------------------------------------------
BG, CARD, BORDER = "#f4f5f7", "#ffffff", "#d8dce2"
TEXT, MUTED = "#1f2937", "#6b7280"
ACCENT, ACCENT_DARK = "#2563eb", "#1d4ed8"
OK_COLOR = "#16a34a"
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_STUFE = ("Segoe UI", 16, "bold")

ZUSAMMENFASSUNG = (
    "Sehr leicht zu erraten. Bitte nicht verwenden.",
    "Leicht zu erraten. Wähle ein längeres, weniger vorhersehbares Passwort.",
    "Brauchbar, aber ausbaufähig.",
    "Gut gewählt.",
    "Sehr gut gewählt.",
)

def apply_theme(root: tk.Tk) -> None:
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", background=BG, foreground=TEXT, font=FONT)
    style.configure("TButton", padding=(12, 6), font=FONT, background="#e5e7eb", foreground=TEXT,
                    borderwidth=0, focusthickness=0, relief="flat")
    style.map("TButton", background=[("disabled", "#eceef1"), ("active", "#d9dde3")],
              foreground=[("disabled", "#9ca3af")])
    style.configure("Primary.TButton", background=ACCENT, foreground="white", font=FONT_BOLD)
    style.map("Primary.TButton", background=[("disabled", "#93b4f0"), ("active", ACCENT_DARK)],
              foreground=[("disabled", "white")])

def make_card(parent: tk.Misc) -> tk.Frame:
    return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER)

def auto_wrap(label: tk.Label, container: tk.Misc, margin: int = 30) -> None:
    container.bind("<Configure>", lambda e: label.config(wraplength=max(e.width - margin, 150)), add="+")


class PasswortCheckerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Passwort-Checker v2.3")
        self.setup_window()
        apply_theme(root)

        self.haeufige = lade_basis_liste()
        
        self.var_pw = tk.StringVar()
        self.var_laenge = tk.IntVar(value=18)
        self.sichtbar = False
        self.stufe: Optional[int] = None

        self.baue_oberflaeche()
        self.var_pw.trace_add("write", lambda *args: self.aktualisieren())
        self.aktualisieren()
        self.entry.focus_set()

    def setup_window(self) -> None:
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = min(580, int(sw * 0.9)), min(840, int(sh * 0.92))
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.root.minsize(520, 720)

    def baue_oberflaeche(self) -> None:
        kopf = tk.Frame(self.root, bg=BG)
        kopf.pack(fill=tk.X, padx=28, pady=(16, 6))
        
        titel_rahmen = tk.Frame(kopf, bg=BG)
        titel_rahmen.pack(fill=tk.X)
        tk.Label(titel_rahmen, text="Passwort-Check", font=FONT_TITLE, fg=TEXT, bg=BG).pack(side=tk.LEFT)
        
        btn_info = ttk.Button(titel_rahmen, text="ℹ️ Info", command=self.zeige_info_fenster)
        btn_info.pack(side=tk.RIGHT)

        tk.Label(kopf, text="100% lokale Ausführung. Keine Internetverbindung.",
                 font=FONT_SMALL, fg=MUTED, bg=BG, anchor="w", justify="left").pack(anchor="w", pady=(2, 0))

        self.baue_eingabe_karte()
        self.baue_merkmale_karte()
        self.baue_tipps_karte()
        self.baue_generator_karte()

        fuss_rahmen = tk.Frame(self.root, bg=BG)
        fuss_rahmen.pack(fill=tk.X, padx=28, pady=(6, 12))

        self.lbl_info = tk.Label(fuss_rahmen, text="", font=FONT_SMALL, fg=MUTED, bg=BG, anchor="w", justify="left")
        self.lbl_info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_liste_laden = ttk.Button(fuss_rahmen, text="📂 Eigene Liste laden (.txt)", command=self.eigene_liste_laden)
        btn_liste_laden.pack(side=tk.RIGHT)

        self.aktualisiere_status()

    def baue_eingabe_karte(self) -> None:
        karte = make_card(self.root)
        karte.pack(fill=tk.X, padx=28, pady=4)
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=12)

        tk.Label(innen, text="Passwort", font=FONT_BOLD, fg=TEXT, bg=CARD, anchor="w").pack(fill=tk.X)
        zeile = tk.Frame(innen, bg=CARD)
        zeile.pack(fill=tk.X, pady=(6, 0))
        self.entry = tk.Entry(zeile, textvariable=self.var_pw, show="•", font=("Segoe UI", 13), relief="flat", bd=0,
                              bg="#ffffff", fg=TEXT, insertbackground=TEXT, highlightthickness=1,
                              highlightbackground=BORDER, highlightcolor=ACCENT)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        ttk.Button(zeile, text="Leeren", command=self.leeren).pack(side=tk.RIGHT, padx=(8, 0))
        self.btn_anzeigen = ttk.Button(zeile, text="Anzeigen", command=self.sichtbarkeit_umschalten)
        self.btn_anzeigen.pack(side=tk.RIGHT, padx=(8, 0))

        self.balken = tk.Canvas(innen, height=8, bg=CARD, highlightthickness=0, bd=0)
        self.balken.pack(fill=tk.X, pady=(10, 6))
        self.balken.bind("<Configure>", lambda e: self.zeichne_balken())

        self.lbl_stufe = tk.Label(innen, text="", font=FONT_STUFE, bg=CARD, anchor="w")
        self.lbl_stufe.pack(fill=tk.X)
        self.lbl_text = tk.Label(innen, text="", font=FONT, fg=MUTED, bg=CARD, anchor="w", justify="left")
        self.lbl_text.pack(fill=tk.X, pady=(2, 0))
        auto_wrap(self.lbl_text, innen, 10)

    def baue_merkmale_karte(self) -> None:
        karte = make_card(self.root)
        karte.pack(fill=tk.X, padx=28, pady=4)
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(innen, text="Merkmale", font=FONT_BOLD, fg=TEXT, bg=CARD, anchor="w").pack(fill=tk.X, pady=(0, 2))
        self.lbl_merkmale: List[tk.Label] = []
        for _ in range(5):
            lbl = tk.Label(innen, text="", font=FONT_SMALL, bg=CARD, anchor="w")
            lbl.pack(fill=tk.X, pady=1)
            self.lbl_merkmale.append(lbl)

    def baue_tipps_karte(self) -> None:
        karte = make_card(self.root)
        karte.pack(fill=tk.X, padx=28, pady=4)
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(innen, text="So wird es besser", font=FONT_BOLD, fg=TEXT, bg=CARD, anchor="w").pack(fill=tk.X)
        self.lbl_tipps = tk.Label(innen, text="", font=FONT_SMALL, fg=TEXT, bg=CARD, anchor="w", justify="left")
        self.lbl_tipps.pack(fill=tk.X, pady=(4, 0))
        auto_wrap(self.lbl_tipps, innen, 10)

    def baue_generator_karte(self) -> None:
        karte = make_card(self.root)
        karte.pack(fill=tk.X, padx=28, pady=4)
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(innen, text="Zufallspasswort", font=FONT_BOLD, fg=TEXT, bg=CARD, anchor="w").pack(fill=tk.X)
        zeile = tk.Frame(innen, bg=CARD)
        zeile.pack(fill=tk.X, pady=(6, 0))
        tk.Label(zeile, text="Länge", font=FONT, fg=TEXT, bg=CARD).pack(side=tk.LEFT)
        ttk.Spinbox(zeile, from_=12, to=40, width=5, textvariable=self.var_laenge).pack(side=tk.LEFT, padx=(8, 12))
        ttk.Button(zeile, text="Erzeugen", style="Primary.TButton", command=self.erzeugen).pack(side=tk.LEFT)
        ttk.Button(zeile, text="Kopieren", command=self.kopieren).pack(side=tk.LEFT, padx=(8, 0))

    def aktualisiere_status(self) -> None:
        anzahl = len(self.haeufige)
        self.lbl_info.config(text=f"Datenbank: {anzahl} Passwörter aktiv.")

    def zeichne_balken(self) -> None:
        self.balken.delete("all")
        breite = max(self.balken.winfo_width(), 100)
        luecke = 6
        seg = (breite - 4 * luecke) / 5
        for i in range(5):
            aktiv = self.stufe is not None and i <= self.stufe
            farbe = STUFEN_FARBEN[self.stufe] if aktiv else "#e5e7eb"
            x0 = i * (seg + luecke)
            self.balken.create_rectangle(x0, 0, x0 + seg, 8, fill=farbe, outline="")

    def aktualisieren(self) -> None:
        pw = self.var_pw.get()
        if not pw:
            self.stufe = None
            self.lbl_stufe.config(text="Noch nichts eingegeben", fg=MUTED)
            self.lbl_text.config(text="Tippe ein Passwort ein, um es zu prüfen.")
            for lbl, name in zip(self.lbl_merkmale, [m[0] for m in baue_merkmale("", None)]):
                lbl.config(text=f"○   {name}", fg=MUTED)
            self.lbl_tipps.config(text="Die Tipps erscheinen bei der Eingabe.", fg=MUTED)
            self.zeichne_balken()
            return

        erg = bewerte(pw, self.haeufige)
        self.stufe = erg.stufe
        self.lbl_stufe.config(text=STUFEN[erg.stufe], fg=STUFEN_FARBEN[erg.stufe])
        if erg.treffer:
            text = f"Entspricht dem häufigen Passwort „{erg.treffer}“."
        else:
            text = ZUSAMMENFASSUNG[erg.stufe]
        self.lbl_text.config(text=text)
        for lbl, (name, erfuellt) in zip(self.lbl_merkmale, erg.merkmale):
            lbl.config(text=f"{'✓' if erfuellt else '○'}   {name}", fg=OK_COLOR if erfuellt else MUTED)
        self.lbl_tipps.config(text="\n".join(f"•  {h}" for h in erg.hinweise), fg=TEXT)
        self.zeichne_balken()

    def wende_sichtbarkeit_an(self) -> None:
        self.entry.config(show="" if self.sichtbar else "•")
        self.btn_anzeigen.config(text="Verbergen" if self.sichtbar else "Anzeigen")

    def sichtbarkeit_umschalten(self) -> None:
        self.sichtbar = not self.sichtbar
        self.wende_sichtbarkeit_an()

    def leeren(self) -> None:
        self.var_pw.set("")
        self.entry.focus_set()

    def erzeugen(self) -> None:
        try:
            laenge = int(self.var_laenge.get())
        except (tk.TclError, ValueError):
            laenge = 18
        self.var_pw.set(erzeuge_passwort(self.haeufige, laenge))
        self.sichtbar = True
        self.wende_sichtbarkeit_an()

    def kopieren(self) -> None:
        pw = self.var_pw.get()
        if not pw:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(pw)
        self.root.after(ZWISCHENABLAGE_LEEREN_NACH_MS, lambda: self.zwischenablage_leeren(pw))

    def zwischenablage_leeren(self, pw: str) -> None:
        try:
            if self.root.clipboard_get() == pw:
                self.root.clipboard_clear()
        except tk.TclError:
            pass

    def eigene_liste_laden(self) -> None:
        dateipfad = filedialog.askopenfilename(
            title="Passwort-Liste auswählen",
            filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        if not dateipfad:
            return
        try:
            with open(dateipfad, encoding="utf-8", errors="ignore") as f:
                neue_woerter = f.read().splitlines()
            
            basis_woerter = _HAEUFIGE_TEXT.split()
            basis_woerter.extend(neue_woerter)
            self.haeufige = bereite_liste_vor(basis_woerter)
            
            self.aktualisiere_status()
            messagebox.showinfo("Erfolg", f"Die Liste wurde erfolgreich geladen!\nAktuell aktive Passwörter: {len(self.haeufige)}")
            self.aktualisieren()
        except Exception as e:
            messagebox.showerror("Fehler", f"Die Datei konnte nicht gelesen werden:\n{e}")

    def zeige_info_fenster(self) -> None:
        fenster = tk.Toplevel(self.root)
        fenster.title("Über das Projekt & Copyright")
        fenster.geometry("460x410")
        fenster.resizable(False, False)
        fenster.configure(bg=CARD)

        # NEU: Zentriert das Info-Fenster exakt über dem Hauptfenster
        fenster.update_idletasks()
        mw = self.root.winfo_width()
        mh = self.root.winfo_height()
        mx = self.root.winfo_x()
        my = self.root.winfo_y()
        
        fw = 460
        fh = 410
        fx = mx + (mw - fw) // 2
        fy = my + (mh - fh) // 2
        fenster.geometry(f"{fw}x{fh}+{fx}+{fy}")

        # Damit das Fenster im Vordergrund bleibt und den Fokus behält
        fenster.transient(self.root)
        fenster.grab_set()

        inhalt = tk.Frame(fenster, bg=CARD)
        inhalt.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(inhalt, text="Passwort-Sicherheits-Tool", font=FONT_BOLD, fg=TEXT, bg=CARD).pack(anchor="w", pady=(0, 5))
        tk.Label(inhalt, text="Entwickelt von: [ABUKICK / Passwort Checker]", font=FONT_SMALL, fg=ACCENT, bg=CARD).pack(anchor="w", pady=(0, 15))

        text = (
            "Dieses Tool läuft zu 100 % lokal auf deinem Computer. "
            "Es findet keinerlei Datenübertragung oder Telemetrie statt.\n\n"
            "Quellen & Open-Source-Hinweis:\n"
            "Ein Teil der integrierten Passwort-Referenzlisten basiert auf "
            "offenen Sicherheits- und Forschungsprojekten, insbesondere dem "
            "weltweit bekannten Open-Source-Repository **SecLists** von Daniel Miessler "
            "(https://github.com/danielmiessler/SecLists)[cite: 1].\n\n"
            "Bedienung:\n"
            "Über den Button „Eigene Liste laden“ unten rechts kannst du jederzeit "
            "beliebige Textdateien (z. B. aus SecLists) mit einem Klick einlesen."
        )
        lbl = tk.Label(inhalt, text=text, font=FONT_SMALL, fg=TEXT, bg=CARD, justify="left", anchor="w")
        lbl.pack(anchor="w", fill=tk.X)
        auto_wrap(lbl, inhalt, 40)

        ttk.Button(inhalt, text="Schließen", command=fenster.destroy).pack(anchor="e", pady=(15, 0))


def main() -> None:
    root = tk.Tk()
    PasswortCheckerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
