"""
Passwort-Check, Version 2.6

Prüft lokal, wie leicht ein Passwort zu erraten ist. Nichts wird gespeichert oder gesendet.

Neu in 2.6 (gegenüber 2.5):
- Sprache: Die Anzeigesprache des PCs wird automatisch erkannt (unter Windows die Windows-Anzeigesprache).
  Deutsch bleibt Deutsch, jede andere Sprache bekommt Englisch; ist nichts ermittelbar, gilt Deutsch.
  Alle Texte stehen gesammelt in TEXTE. Die Bewertungslogik selbst ist sprachfrei und liefert nur Schlüssel.
- Fenster: Der mittlere Bereich scrollt, wenn der Bildschirm zu klein ist. Titelzeile und Fußzeile mit
  "Eigene Liste laden" bleiben immer sichtbar.
- Rückmeldungen: Kopieren und Erzeugen melden sich wieder in der Statuszeile (inkl. Hinweis auf die
  automatisch geleerte Zwischenablage).
- Info-Fenster: passt seine Größe dem Inhalt an, die Adresse ist anklickbar, keine Markdown-Sternchen.
- Keine Emojis mehr (werden in Tk je nach Version als Kästchen oder einfarbig dargestellt).
- Die Versionsnummer steht nur noch an einer Stelle (VERSION).
"""

from __future__ import annotations

import math
import os
import re
import secrets
import tkinter as tk
import webbrowser
from dataclasses import dataclass, field
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Set, Tuple

try:  # optional: genauere Mustererkennung
    from zxcvbn import zxcvbn as _ZXCVBN
except Exception:  # ImportError oder defekte Installation
    _ZXCVBN = None

VERSION = "2.6"
STANDARD_SPRACHE = "de"  # gilt, wenn sich die Systemsprache nicht ermitteln lässt
SECLISTS_URL = "https://github.com/danielmiessler/SecLists"

# ----------------------------------------------------------------------------
# Spracherkennung
# ----------------------------------------------------------------------------
LANG_DEUTSCH = 0x07   # Windows-Kennung der Hauptsprache (gilt für alle Varianten wie de-DE, de-AT, de-CH)
LANG_ENGLISCH = 0x09


def _windows_sprachcode() -> Optional[str]:
    """Anzeigesprache von Windows: 'de', 'en' oder 'andere'; None, wenn nicht ermittelbar."""
    try:
        import ctypes
        hauptsprache = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
    except Exception:  # kein Windows oder Aufruf nicht möglich
        return None
    return {LANG_DEUTSCH: "de", LANG_ENGLISCH: "en"}.get(hauptsprache, "andere")


def _umgebungs_sprachcode(env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """Sprachcode aus den Umgebungsvariablen (Linux/macOS), z. B. 'de' aus 'de_DE.UTF-8'."""
    env = os.environ if env is None else env
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        wert = env.get(name, "").split(":")[0].strip()  # LANGUAGE kann "de:en" lauten
        if not wert or wert in ("C", "POSIX") or wert.startswith("C."):
            continue
        return re.split(r"[_.@-]", wert)[0].lower()
    return None


def erkenne_sprache() -> str:
    """'de' oder 'en' passend zur Anzeigesprache des PCs."""
    code = _windows_sprachcode() if os.name == "nt" else None
    if code is None:
        code = _umgebungs_sprachcode()
    if code is None:
        return STANDARD_SPRACHE
    return "de" if code == "de" else "en"


# ----------------------------------------------------------------------------
# Texte (alle sichtbaren Texte stehen hier; die Logik weiter unten kennt keine Sprache)
# ----------------------------------------------------------------------------
TEXTE: Dict[str, Dict] = {
    "de": {
        "titel": "Passwort-Check",
        "untertitel": "100% lokale Ausführung. Keine Internetverbindung.",
        "info_btn": "Info",
        "passwort_label": "Passwort",
        "leeren": "Leeren",
        "anzeigen": "Anzeigen",
        "verbergen": "Verbergen",
        "stufen": ("Sehr schwach", "Schwach", "Mittel", "Stark", "Sehr stark"),
        "zusammenfassung": (
            "Sehr leicht zu erraten. Bitte nicht verwenden.",
            "Leicht zu erraten. Wähle ein längeres, weniger vorhersehbares Passwort.",
            "Brauchbar, aber ausbaufähig.",
            "Gut gewählt.",
            "Sehr gut gewählt.",
        ),
        "treffer_text": "Entspricht dem häufigen Passwort „{wort}“.",
        "eingabe_aufforderung": "Tippe ein Passwort ein, um es zu prüfen.",
        "nichts_eingegeben": "Noch nichts eingegeben",
        "merkmale_titel": "Merkmale",
        "merkmale": {
            "laenge": "Mindestens {n} Zeichen",
            "gross_klein": "Groß- und Kleinbuchstaben",
            "zahlen": "Zahlen",
            "sonder": "Sonderzeichen oder Leerzeichen",
            "nicht_haeufig": "Kein häufiges Passwort",
        },
        "tipps_titel": "So wird es besser",
        "tipps_leer": "Die Tipps erscheinen bei der Eingabe.",
        "hinweise": {
            "treffer": "Komplett ändern: Dieses Passwort oder eine leichte Abwandlung steht in Listen häufiger "
                       "Passwörter.",
            "block": "Ein Teil wiederholt sich. Wiederholungen bringen kaum zusätzlichen Schutz.",
            "wiederholung": "Gleiche Zeichen hintereinander erhöhen die Sicherheit kaum.",
            "folge": "Folgen wie abc, 1234 oder qwertz sind leicht zu erraten.",
            "wort_zahl": "Ein Wort mit angehängter Zahl ist ein sehr typisches Muster.",
            "zu_kurz": "Länger ist besser: ab {n} Zeichen.",
            "ein_konto": "Verwende es nur für ein einziges Konto.",
            "mehr_zufall": "Mehr Länge und mehr Zufall machen es stärker.",
        },
        "generator_titel": "Zufallspasswort",
        "laenge": "Länge",
        "erzeugen": "Erzeugen",
        "kopieren": "Kopieren",
        "erzeugt": "Zufallspasswort erzeugt und oben eingetragen. Speichere es in einem Passwortmanager, "
                   "bevor du das Fenster schließt.",
        "kopiert": "Kopiert. Die Zwischenablage wird in {s} Sekunden geleert (der Windows-Zwischenablageverlauf "
                   "Win+V kann trotzdem eine Kopie behalten).",
        "datenbank_status": "Datenbank: {n} Passwörter aktiv.",
        "liste_laden_btn": "Eigene Liste laden (.txt)",
        "dialog_titel": "Passwort-Liste auswählen",
        "dateityp_text": "Textdateien",
        "dateityp_alle": "Alle Dateien",
        "erfolg_titel": "Erfolg",
        "erfolg_text": "Die Liste wurde erfolgreich geladen!\nAktuell aktive Passwörter: {n}",
        "fehler_titel": "Fehler",
        "fehler_text": "Die Datei konnte nicht gelesen werden:\n{fehler}",
        "info_titel": "Über das Projekt & Copyright",
        "info_entwickler": "Entwickelt von: ABUKICK",
        "info_text_oben": (
            "Dieses Tool läuft zu 100 % lokal auf deinem Computer. Es findet keinerlei Datenübertragung oder "
            "Telemetrie statt.\n\n"
            "Quellen & Open-Source-Hinweis:\n"
            "Ein Teil der integrierten Passwort-Referenzlisten basiert auf offenen Sicherheits- und "
            "Forschungsprojekten, insbesondere dem weltweit bekannten Open-Source-Repository SecLists von "
            "Daniel Miessler:"
        ),
        "info_text_unten": (
            "Bedienung:\n"
            "Über den Button „Eigene Liste laden“ unten rechts kannst du jederzeit beliebige Textdateien "
            "(z. B. aus SecLists) mit einem Klick einlesen."
        ),
        "schliessen": "Schließen",
    },
    "en": {
        "titel": "Password Check",
        "untertitel": "100% local execution. No internet connection.",
        "info_btn": "Info",
        "passwort_label": "Password",
        "leeren": "Clear",
        "anzeigen": "Show",
        "verbergen": "Hide",
        "stufen": ("Very weak", "Weak", "Medium", "Strong", "Very strong"),
        "zusammenfassung": (
            "Very easy to guess. Please do not use.",
            "Easy to guess. Choose a longer, less predictable password.",
            "Usable, but can be improved.",
            "Well chosen.",
            "Very well chosen.",
        ),
        "treffer_text": "Matches the common password “{wort}”.",
        "eingabe_aufforderung": "Type a password to check it.",
        "nichts_eingegeben": "Nothing entered yet",
        "merkmale_titel": "Characteristics",
        "merkmale": {
            "laenge": "At least {n} characters",
            "gross_klein": "Uppercase and lowercase letters",
            "zahlen": "Numbers",
            "sonder": "Special characters or spaces",
            "nicht_haeufig": "Not a common password",
        },
        "tipps_titel": "How to improve",
        "tipps_leer": "Tips will appear as you type.",
        "hinweise": {
            "treffer": "Change completely: This password or a slight variation appears in common password lists.",
            "block": "A part repeats itself. Repetitions provide hardly any additional protection.",
            "wiederholung": "Consecutive identical characters add little security.",
            "folge": "Sequences like abc, 1234 or qwertz are easy to guess.",
            "wort_zahl": "A word with an appended number is a very typical pattern.",
            "zu_kurz": "Longer is better: starting from {n} characters.",
            "ein_konto": "Use this password for a single account only.",
            "mehr_zufall": "More length and randomness make it stronger.",
        },
        "generator_titel": "Random Password",
        "laenge": "Length",
        "erzeugen": "Generate",
        "kopieren": "Copy",
        "erzeugt": "Random password generated and entered above. Save it in a password manager before closing "
                   "the window.",
        "kopiert": "Copied. The clipboard will be cleared in {s} seconds (the Windows clipboard history Win+V "
                   "may still keep a copy).",
        "datenbank_status": "Database: {n} passwords active.",
        "liste_laden_btn": "Load custom list (.txt)",
        "dialog_titel": "Select Password List",
        "dateityp_text": "Text files",
        "dateityp_alle": "All files",
        "erfolg_titel": "Success",
        "erfolg_text": "The list was loaded successfully!\nCurrently active passwords: {n}",
        "fehler_titel": "Error",
        "fehler_text": "The file could not be read:\n{fehler}",
        "info_titel": "About & Copyright",
        "info_entwickler": "Developed by: ABUKICK",
        "info_text_oben": (
            "This tool runs 100% locally on your computer. No data transmission or telemetry takes place.\n\n"
            "Sources & Open Source Notice:\n"
            "Part of the integrated password reference lists is based on open security and research projects, "
            "particularly the world-renowned open-source repository SecLists by Daniel Miessler:"
        ),
        "info_text_unten": (
            "Usage:\n"
            "Use the 'Load custom list' button at the bottom right to import any text files "
            "(e.g., from SecLists) with a single click."
        ),
        "schliessen": "Close",
    },
}

# ----------------------------------------------------------------------------
# Konstanten
# ----------------------------------------------------------------------------
STUFEN_FARBEN = ("#dc2626", "#ea580c", "#ca8a04", "#65a30d", "#16a34a")
STUFEN_SCHWELLEN = (28, 36, 50, 64)  # Bit-Grenzen zwischen den fünf Stufen

MIN_LAENGE_EMPFOHLEN = 12
BITS_WORT = 2.0               # pro Buchstabe in wortartigem Text (≈ 11 Bit je Wort)
BITS_ZUFALL_BUCHSTABE = 4.3   # pro Buchstabe bei zufälliger Groß-/Kleinschreibung
BITS_ZEICHEN = 3.5            # pro Ziffer/Sonderzeichen
BITS_ERSETZUNG = 2.0          # pro Ersetzung wie @ → a
ZUFALL_FAKTOR = 0.8           # Abschlag bei Zeichenpool-Schätzung (Menschen sind nie ganz zufällig)

LEET = {"@": "a", "4": "a", "3": "e", "1": "i", "0": "o", "$": "s", "5": "s", "7": "t"}
TASTATURREIHEN = ("qwertzuiopü", "asdfghjklöä", "yxcvbnm", "qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890")
BUCHSTABEN = "A-Za-zÄÖÜäöüß"
TOKEN_RE = re.compile(f"[{BUCHSTABEN}]+|[^{BUCHSTABEN}]+")
WORT_RE = re.compile(r"[A-ZÄÖÜ]?[a-zäöüß]+|[A-ZÄÖÜ]+|(?:[A-ZÄÖÜ][a-zäöüß]+)+")
BLOCK_RE = re.compile(r"(.{2,}?)\1+", re.S)
VOKALE = frozenset("aeiouyäöü")

MERKMAL_SCHLUESSEL = ("laenge", "gross_klein", "zahlen", "sonder", "nicht_haeufig")

ZWISCHENABLAGE_LEEREN_NACH_MS = 30_000
ZUFALL_KLEIN = "abcdefghijkmnopqrstuvwxyz"   # ohne l
ZUFALL_GROSS = "ABCDEFGHJKLMNPQRSTUVWXYZ"    # ohne I und O
ZUFALL_ZIFFERN = "23456789"                  # ohne 0 und 1
ZUFALL_SONDER = "!@#$%&*?-_=+"

# Häufige Passwörter. Erweiterbar über haeufige_passwoerter.txt neben diesem Skript
# oder im Programm über "Eigene Liste laden".
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
# Bewertungslogik (reine Funktionen ohne Oberfläche und ohne Sprache, daher testbar)
# ----------------------------------------------------------------------------
def entleet(s: str) -> Tuple[str, int]:
    """Macht typische Ersetzungen rückgängig (p@ssw0rd → password). Nur innerhalb von Wörtern.

    Gibt (neuer_Text, Anzahl_Ersetzungen) zurück. Angehängte Ziffern (Password1) bleiben unverändert.
    """
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
    """Normalisiert die Wortliste: klein geschrieben. Zuordnung Suchform → ursprünglicher Listeneintrag.

    Zu jedem Eintrag wird auch die Variante ohne Ersetzungen aufgenommen (p@ssw0rd → password).
    """
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
    """Eingebaute Liste plus optionale Datei 'haeufige_passwoerter.txt' neben dem Skript."""
    woerter = _HAEUFIGE_TEXT.split()
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haeufige_passwoerter.txt")
    try:
        with open(pfad, encoding="utf-8", errors="ignore") as f:
            woerter.extend(f.read().splitlines())
    except OSError:
        pass
    return bereite_liste_vor(woerter)


def finde_treffer(passwort: str, haeufige: Mapping[str, str]) -> Optional[str]:
    """Findet den Listeneintrag, dem die Eingabe entspricht oder auf dem sie aufbaut (sonst None)."""
    if not passwort:
        return None
    low = passwort.lower()
    kandidaten = {low, entleet(low)[0]}
    for k in kandidaten:
        if k in haeufige:
            return haeufige[k]
    for k in kandidaten:  # Wort mit angehängten oder vorangestellten Zahlen/Zeichen (summer2024!)
        basis = re.sub(r"^[^a-zäöüß]+", "", re.sub(r"[^a-zäöüß]+$", "", k))
        if len(basis) >= 4 and basis in haeufige:
            return haeufige[basis]
    return None


def wiederholter_block(passwort: str) -> Optional[str]:
    """'Hallo1!Hallo1!' → 'Hallo1!'; None, wenn sich nichts wiederholt."""
    m = BLOCK_RE.fullmatch(passwort)
    return m.group(1) if m else None


def wortaehnlich(tok: str) -> bool:
    """Grobe Prüfung, ob ein Buchstabenblock wie ein Wort aussieht (genug Vokale, keine langen Konsonantenfolgen)."""
    if not WORT_RE.fullmatch(tok):
        return False
    low = tok.lower()
    if sum(c in VOKALE for c in low) * 4 < len(low):
        return False
    return re.search(r"[^aeiouyäöü]{5,}", low) is None


def gewichte(low: str) -> List[float]:
    """Gewicht je Zeichen: Wiederholungen (aaa) zählen 0, Folgen (abc, 4321) und Tastaturreihen 0,25, sonst 1."""
    n = len(low)
    w = [1.0] * n
    for i in range(2, n):  # ab dem dritten gleichen Zeichen in Folge (Doppelbuchstaben wie in "Wasser" sind normal)
        if low[i] == low[i - 1] == low[i - 2]:
            w[i] = 0.0
    i = 0
    while i < n - 1:  # Folgen mit mindestens 3 Zeichen
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
    for reihe in TASTATURREIHEN:  # Tastaturmuster ab 4 Zeichen, vorwärts und rückwärts
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
    """Größe des Zeichenvorrats, aus dem das Passwort gebaut ist (Klein, Groß, Ziffern, Sonderzeichen)."""
    pool = 0
    if any(c.islower() for c in passwort):
        pool += 26
    if any(c.isupper() for c in passwort):
        pool += 26
    if any(c.isdigit() for c in passwort):
        pool += 10
    if any(not c.isalnum() for c in passwort):
        pool += 33
    return max(pool, 10)


def schaetze_bits(passwort: str) -> Tuple[float, Set[str]]:
    """Grobe Schätzung des Rateaufwands in Bit plus erkannte Muster ('wiederholung', 'folge', 'wort_zahl')."""
    if not passwort:
        return 0.0, set()
    w = gewichte(passwort.lower())
    norm, ersetzt = entleet(passwort)
    muster: Set[str] = set()
    if any(w[i] == 0.0 for i in range(1, len(w))):
        muster.add("wiederholung")
    if any(0.0 < x < 1.0 for x in w):
        muster.add("folge")

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

    if wortartig == 0:  # kein erkennbares Wort: wie ein Zufallspasswort schätzen
        bits = max(bits, sum(w) * math.log2(pool_groesse(passwort)) * ZUFALL_FAKTOR)
    elif woerter == 1 and sonstige >= 1:
        muster.add("wort_zahl")
    return bits, muster


def stufe_aus_bits(bits: float) -> int:
    return sum(bits >= grenze for grenze in STUFEN_SCHWELLEN)


@dataclass
class Ergebnis:
    stufe: int                                   # 0 (sehr schwach) bis 4 (sehr stark)
    bits: float
    treffer: Optional[str] = None                # Eintrag der Liste häufiger Passwörter
    merkmale: List[Tuple[str, bool]] = field(default_factory=list)   # (Schlüssel, erfüllt)
    hinweise: List[str] = field(default_factory=list)                # Schlüssel der Tipps


def baue_merkmale(passwort: str, treffer: Optional[str]) -> List[Tuple[str, bool]]:
    """Merkmale als (Schlüssel, erfüllt); die Beschriftung kommt aus TEXTE[sprache]['merkmale']."""
    return [
        ("laenge", len(passwort) >= MIN_LAENGE_EMPFOHLEN),
        ("gross_klein", any(c.islower() for c in passwort) and any(c.isupper() for c in passwort)),
        ("zahlen", any(c.isdigit() for c in passwort)),
        ("sonder", any(not c.isalnum() for c in passwort)),
        ("nicht_haeufig", treffer is None),
    ]


def baue_hinweise(passwort: str, treffer: Optional[str], block: Optional[str],
                  muster: Set[str], stufe: int) -> List[str]:
    """Schlüssel der passenden Tipps (Texte in TEXTE[sprache]['hinweise']), höchstens vier."""
    h: List[str] = []
    if treffer:
        h.append("treffer")
    if block:
        h.append("block")
    elif "wiederholung" in muster:
        h.append("wiederholung")
    if "folge" in muster:
        h.append("folge")
    if "wort_zahl" in muster:
        h.append("wort_zahl")
    if len(passwort) < MIN_LAENGE_EMPFOHLEN:
        h.append("zu_kurz")
    if not h:
        h.append("ein_konto" if stufe >= 3 else "mehr_zufall")
    return h[:4]


def bewerte(passwort: str, haeufige: Mapping[str, str],
            zxcvbn_fn: Optional[Callable] = _ZXCVBN) -> Ergebnis:
    """Bewertet ein Passwort. Ohne Eingabe: Stufe 0 und keine Hinweise."""
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
            pass  # optionale Hilfe darf die Prüfung nie stören
    return Ergebnis(stufe=stufe, bits=bits, treffer=treffer,
                    merkmale=baue_merkmale(passwort, treffer),
                    hinweise=baue_hinweise(passwort, treffer, block, muster, stufe))


def erzeuge_passwort(haeufige: Mapping[str, str], laenge: int = 18) -> str:
    """Zufallspasswort mit kryptografisch sicherem Zufall; enthält alle vier Zeichenarten."""
    laenge = max(12, min(int(laenge), 64))
    alle = ZUFALL_KLEIN + ZUFALL_GROSS + ZUFALL_ZIFFERN + ZUFALL_SONDER
    gruppen = (ZUFALL_KLEIN, ZUFALL_GROSS, ZUFALL_ZIFFERN, ZUFALL_SONDER)
    ziel = 4 if laenge >= 13 else 3  # mit 12 Zeichen ist "Stark" die höchste Stufe, die die Schätzung vergibt
    bester, beste_bits = "", -1.0
    for _ in range(200):
        pw = "".join(secrets.choice(alle) for _ in range(laenge))
        if not all(any(c in g for c in pw) for g in gruppen):
            continue
        erg = bewerte(pw, haeufige, None)
        # Verwirft zufällig entstandene Wörter oder Folgen (z. B. "abcd"), damit die Anzeige zur Länge passt
        if erg.stufe >= ziel:
            return pw
        if erg.bits > beste_bits:
            bester, beste_bits = pw, erg.bits
    return bester  # praktisch nie erreicht: das beste der Kandidaten


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
FONT_LINK = ("Segoe UI", 9, "underline")
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_STUFE = ("Segoe UI", 16, "bold")


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
    """Passt den Zeilenumbruch eines Labels an die Breite seines Containers an."""
    container.bind("<Configure>", lambda e: label.config(wraplength=max(e.width - margin, 150)), add="+")


class ScrollBereich(tk.Frame):
    """Senkrecht scrollbarer Bereich. Die Bildlaufleiste erscheint nur, wenn der Inhalt höher ist als das Fenster."""

    def __init__(self, parent: tk.Misc, bg: str) -> None:
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.leiste = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.leiste.set)
        self.inhalt = tk.Frame(self.canvas, bg=bg)
        self.fenster_id = self.canvas.create_window((0, 0), window=self.inhalt, anchor="nw")
        self.leiste_sichtbar = False
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.inhalt.bind("<Configure>", lambda e: self.aktualisiere())
        self.canvas.bind("<Configure>", self.breite_anpassen)

    def breite_anpassen(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.fenster_id, width=event.width)
        self.aktualisiere()

    def aktualisiere(self) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        noetig = self.inhalt.winfo_reqheight() > self.canvas.winfo_height()
        if noetig and not self.leiste_sichtbar:
            self.leiste.pack(side=tk.RIGHT, fill=tk.Y)
            self.leiste_sichtbar = True
        elif not noetig and self.leiste_sichtbar:
            self.leiste.pack_forget()
            self.leiste_sichtbar = False
            self.canvas.yview_moveto(0)

    def scroll_einheiten(self, anzahl: int) -> None:
        if self.leiste_sichtbar:
            self.canvas.yview_scroll(anzahl, "units")

    def mausrad(self, event: tk.Event) -> None:
        delta = event.delta
        self.scroll_einheiten(-int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1))

    def mausrad_binden(self, root: tk.Misc) -> None:
        root.bind_all("<MouseWheel>", self.mausrad)
        root.bind_all("<Button-4>", lambda e: self.scroll_einheiten(-1))  # Linux
        root.bind_all("<Button-5>", lambda e: self.scroll_einheiten(1))


class PasswortCheckerApp:
    def __init__(self, root: tk.Tk, sprache: str = STANDARD_SPRACHE) -> None:
        self.root = root
        self.sprache = sprache if sprache in TEXTE else STANDARD_SPRACHE
        self.t = TEXTE[self.sprache]
        root.title(f"{self.t['titel']} v{VERSION}")
        self.setup_window()
        apply_theme(root)

        self.haeufige = lade_basis_liste()

        self.var_pw = tk.StringVar()
        self.var_laenge = tk.IntVar(value=18)
        self.sichtbar = False
        self.stufe: Optional[int] = None
        self.status_text = ""
        self.kopier_status = ""

        self.baue_oberflaeche()
        self.var_pw.trace_add("write", lambda *args: self.aktualisieren())
        self.aktualisieren()
        self.entry.focus_set()

    def setup_window(self) -> None:
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = min(580, int(sw * 0.9)), min(840, int(sh * 0.9))
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{max((sh - h) // 2 - 20, 0)}")
        # Mindestgröße nie größer als das Fenster selbst, sonst wird es auf kleinen Bildschirmen abgeschnitten
        self.root.minsize(min(480, w), min(420, h))

    # ---------------- Aufbau ----------------
    def baue_oberflaeche(self) -> None:
        t = self.t
        # Reihenfolge ist wichtig: Titel (oben) und Fuß (unten) reservieren zuerst ihren Platz,
        # der scrollbare Bereich bekommt den Rest.
        kopf = tk.Frame(self.root, bg=BG)
        kopf.pack(side=tk.TOP, fill=tk.X, padx=28, pady=(16, 6))
        titel_rahmen = tk.Frame(kopf, bg=BG)
        titel_rahmen.pack(fill=tk.X)
        tk.Label(titel_rahmen, text=t["titel"], font=FONT_TITLE, fg=TEXT, bg=BG).pack(side=tk.LEFT)
        ttk.Button(titel_rahmen, text=t["info_btn"], command=self.zeige_info_fenster).pack(side=tk.RIGHT)
        tk.Label(kopf, text=t["untertitel"], font=FONT_SMALL, fg=MUTED, bg=BG, anchor="w",
                 justify="left").pack(anchor="w", pady=(2, 0))

        fuss = tk.Frame(self.root, bg=BG)
        fuss.pack(side=tk.BOTTOM, fill=tk.X, padx=28, pady=(6, 12))
        self.lbl_info = tk.Label(fuss, text="", font=FONT_SMALL, fg=MUTED, bg=BG, anchor="w", justify="left")
        self.lbl_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        auto_wrap(self.lbl_info, fuss, 230)
        ttk.Button(fuss, text=t["liste_laden_btn"], command=self.eigene_liste_laden).pack(side=tk.RIGHT)

        self.bereich = ScrollBereich(self.root, BG)
        self.bereich.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.bereich.mausrad_binden(self.root)
        self.inhalt = self.bereich.inhalt

        self.baue_eingabe_karte()
        self.baue_merkmale_karte()
        self.baue_tipps_karte()
        self.baue_generator_karte()
        self.zeige_standard_status()

    def baue_eingabe_karte(self) -> None:
        t = self.t
        karte = make_card(self.inhalt)
        karte.pack(fill=tk.X, padx=28, pady=4)
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=12)

        tk.Label(innen, text=t["passwort_label"], font=FONT_BOLD, fg=TEXT, bg=CARD, anchor="w").pack(fill=tk.X)
        zeile = tk.Frame(innen, bg=CARD)
        zeile.pack(fill=tk.X, pady=(6, 0))
        self.entry = tk.Entry(zeile, textvariable=self.var_pw, show="•", font=("Segoe UI", 13), relief="flat", bd=0,
                              bg="#ffffff", fg=TEXT, insertbackground=TEXT, highlightthickness=1,
                              highlightbackground=BORDER, highlightcolor=ACCENT)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        ttk.Button(zeile, text=t["leeren"], command=self.leeren).pack(side=tk.RIGHT, padx=(8, 0))
        self.btn_anzeigen = ttk.Button(zeile, text=t["anzeigen"], command=self.sichtbarkeit_umschalten)
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
        karte = make_card(self.inhalt)
        karte.pack(fill=tk.X, padx=28, pady=4)
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(innen, text=self.t["merkmale_titel"], font=FONT_BOLD, fg=TEXT, bg=CARD,
                 anchor="w").pack(fill=tk.X, pady=(0, 2))
        self.lbl_merkmale: List[tk.Label] = []
        for _ in MERKMAL_SCHLUESSEL:
            lbl = tk.Label(innen, text="", font=FONT_SMALL, bg=CARD, anchor="w")
            lbl.pack(fill=tk.X, pady=1)
            self.lbl_merkmale.append(lbl)

    def baue_tipps_karte(self) -> None:
        karte = make_card(self.inhalt)
        karte.pack(fill=tk.X, padx=28, pady=4)
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(innen, text=self.t["tipps_titel"], font=FONT_BOLD, fg=TEXT, bg=CARD, anchor="w").pack(fill=tk.X)
        self.lbl_tipps = tk.Label(innen, text="", font=FONT_SMALL, fg=TEXT, bg=CARD, anchor="w", justify="left")
        self.lbl_tipps.pack(fill=tk.X, pady=(4, 0))
        auto_wrap(self.lbl_tipps, innen, 10)

    def baue_generator_karte(self) -> None:
        t = self.t
        karte = make_card(self.inhalt)
        karte.pack(fill=tk.X, padx=28, pady=(4, 12))
        innen = tk.Frame(karte, bg=CARD)
        innen.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(innen, text=t["generator_titel"], font=FONT_BOLD, fg=TEXT, bg=CARD, anchor="w").pack(fill=tk.X)
        zeile = tk.Frame(innen, bg=CARD)
        zeile.pack(fill=tk.X, pady=(6, 0))
        tk.Label(zeile, text=t["laenge"], font=FONT, fg=TEXT, bg=CARD).pack(side=tk.LEFT)
        ttk.Spinbox(zeile, from_=12, to=40, width=5, textvariable=self.var_laenge).pack(side=tk.LEFT, padx=(8, 12))
        ttk.Button(zeile, text=t["erzeugen"], style="Primary.TButton", command=self.erzeugen).pack(side=tk.LEFT)
        ttk.Button(zeile, text=t["kopieren"], command=self.kopieren).pack(side=tk.LEFT, padx=(8, 0))

    # ---------------- Statuszeile ----------------
    def zeige_status(self, text: str) -> None:
        self.status_text = text
        self.lbl_info.config(text=text)

    def zeige_standard_status(self) -> None:
        self.zeige_status(self.t["datenbank_status"].format(n=len(self.haeufige)))

    # ---------------- Anzeige ----------------
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

    def merkmal_text(self, schluessel: str) -> str:
        return self.t["merkmale"][schluessel].format(n=MIN_LAENGE_EMPFOHLEN)

    def aktualisieren(self) -> None:
        t = self.t
        pw = self.var_pw.get()
        if not pw:
            self.stufe = None
            self.lbl_stufe.config(text=t["nichts_eingegeben"], fg=MUTED)
            self.lbl_text.config(text=t["eingabe_aufforderung"])
            for lbl, schluessel in zip(self.lbl_merkmale, MERKMAL_SCHLUESSEL):
                lbl.config(text=f"○   {self.merkmal_text(schluessel)}", fg=MUTED)
            self.lbl_tipps.config(text=t["tipps_leer"], fg=MUTED)
            self.zeichne_balken()
            return

        erg = bewerte(pw, self.haeufige)
        self.stufe = erg.stufe
        self.lbl_stufe.config(text=t["stufen"][erg.stufe], fg=STUFEN_FARBEN[erg.stufe])
        text = t["treffer_text"].format(wort=erg.treffer) if erg.treffer else t["zusammenfassung"][erg.stufe]
        self.lbl_text.config(text=text)
        for lbl, (schluessel, erfuellt) in zip(self.lbl_merkmale, erg.merkmale):
            lbl.config(text=f"{'✓' if erfuellt else '○'}   {self.merkmal_text(schluessel)}",
                       fg=OK_COLOR if erfuellt else MUTED)
        tipps = "\n".join(f"•  {t['hinweise'][k].format(n=MIN_LAENGE_EMPFOHLEN)}" for k in erg.hinweise)
        self.lbl_tipps.config(text=tipps, fg=TEXT)
        self.zeichne_balken()

    # ---------------- Aktionen ----------------
    def wende_sichtbarkeit_an(self) -> None:
        self.entry.config(show="" if self.sichtbar else "•")
        self.btn_anzeigen.config(text=self.t["verbergen"] if self.sichtbar else self.t["anzeigen"])

    def sichtbarkeit_umschalten(self) -> None:
        self.sichtbar = not self.sichtbar
        self.wende_sichtbarkeit_an()

    def leeren(self) -> None:
        self.var_pw.set("")
        self.zeige_standard_status()
        self.entry.focus_set()

    def erzeugen(self) -> None:
        try:
            laenge = int(self.var_laenge.get())
        except (tk.TclError, ValueError):
            laenge = 18
        self.var_pw.set(erzeuge_passwort(self.haeufige, laenge))
        self.sichtbar = True
        self.wende_sichtbarkeit_an()
        self.zeige_status(self.t["erzeugt"])

    def kopieren(self) -> None:
        pw = self.var_pw.get()
        if not pw:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(pw)
        self.kopier_status = self.t["kopiert"].format(s=ZWISCHENABLAGE_LEEREN_NACH_MS // 1000)
        self.zeige_status(self.kopier_status)
        self.root.after(ZWISCHENABLAGE_LEEREN_NACH_MS, lambda: self.zwischenablage_leeren(pw))

    def zwischenablage_leeren(self, pw: str) -> None:
        try:
            if self.root.clipboard_get() == pw:
                self.root.clipboard_clear()
        except tk.TclError:
            pass  # Zwischenablage leer oder nicht lesbar
        if self.status_text == self.kopier_status:  # nur zurücksetzen, wenn nicht inzwischen etwas Neueres steht
            self.zeige_standard_status()

    def eigene_liste_laden(self) -> None:
        t = self.t
        dateipfad = filedialog.askopenfilename(
            title=t["dialog_titel"],
            filetypes=[(t["dateityp_text"], "*.txt"), (t["dateityp_alle"], "*.*")])
        if not dateipfad:
            return
        try:
            with open(dateipfad, encoding="utf-8", errors="ignore") as f:
                neue_woerter = f.read().splitlines()

            basis_woerter = _HAEUFIGE_TEXT.split()
            basis_woerter.extend(neue_woerter)
            self.haeufige = bereite_liste_vor(basis_woerter)

            self.zeige_standard_status()
            messagebox.showinfo(t["erfolg_titel"], t["erfolg_text"].format(n=len(self.haeufige)))
            self.aktualisieren()
        except Exception as e:
            messagebox.showerror(t["fehler_titel"], t["fehler_text"].format(fehler=e))

    def zeige_info_fenster(self) -> None:
        t = self.t
        fenster = tk.Toplevel(self.root, bg=CARD)
        fenster.title(t["info_titel"])
        fenster.resizable(False, False)

        inhalt = tk.Frame(fenster, bg=CARD)
        inhalt.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        breite = 430  # Textbreite in Pixeln; die Höhe ergibt sich aus dem Inhalt

        tk.Label(inhalt, text=f"{t['titel']} v{VERSION}", font=FONT_BOLD, fg=TEXT, bg=CARD).pack(anchor="w")
        tk.Label(inhalt, text=t["info_entwickler"], font=FONT_SMALL, fg=ACCENT, bg=CARD).pack(anchor="w", pady=(2, 14))
        tk.Label(inhalt, text=t["info_text_oben"], font=FONT_SMALL, fg=TEXT, bg=CARD, justify="left", anchor="w",
                 wraplength=breite).pack(anchor="w", fill=tk.X)
        link = tk.Label(inhalt, text=SECLISTS_URL, font=FONT_LINK, fg=ACCENT, bg=CARD, cursor="hand2", anchor="w")
        link.pack(anchor="w", pady=(2, 12))
        link.bind("<Button-1>", lambda e: webbrowser.open(SECLISTS_URL))
        tk.Label(inhalt, text=t["info_text_unten"], font=FONT_SMALL, fg=TEXT, bg=CARD, justify="left", anchor="w",
                 wraplength=breite).pack(anchor="w", fill=tk.X)
        ttk.Button(inhalt, text=t["schliessen"], command=fenster.destroy).pack(anchor="e", pady=(16, 0))

        # Größe aus dem Inhalt, mittig über dem Hauptfenster
        fenster.update_idletasks()
        fw, fh = fenster.winfo_reqwidth(), fenster.winfo_reqheight()
        x = self.root.winfo_x() + (self.root.winfo_width() - fw) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - fh) // 2
        fenster.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        fenster.transient(self.root)
        fenster.grab_set()


def main() -> None:
    root = tk.Tk()
    PasswortCheckerApp(root, erkenne_sprache())
    root.mainloop()


if __name__ == "__main__":
    main()
