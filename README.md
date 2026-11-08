# 🛡️ Password Security Checker (v2.6)

A secure, portable, and 100% local Python tool for checking password strength with an intuitive graphical user interface (Tkinter). Features **automatic language detection** (supporting English and German based on your system settings) and a responsive, scrollable layout.

## 🚀 What's New in Version 2.6?
* **Language Detection:** The PC's display language is automatically detected (on Windows via the Windows UI language). German remains German, any other language defaults to English; if nothing can be determined, German is used. All UI texts are collected centrally in `TEXTE`, while the evaluation logic itself remains language-free and returns keys only.
* **Scrollable Layout:** The middle area scrolls automatically if the screen is too small. The title bar and footer with the "Load custom list" button always remain visible.
* **Enhanced Feedback:** Copy and generate actions report back in the status bar (including a notice about the automatically cleared clipboard).
* **Improved Info Window:** Dynamically adjusts its size to fit the content, the SecLists URL is clickable, and Markdown asterisks have been removed.
* **No More Emojis:** Removed all emojis to prevent rendering issues (such as boxes or monochrome display) depending on the Tk version.
* **Centralized Versioning:** The version number is now maintained in a single place (`VERSION`).

## 🌟 Core Features
* **100% Local Execution:** No internet connection, no telemetry, no cloud storage. Your passwords stay strictly on your computer.
* **Smart Analysis:** Analyzes length, character variety, common patterns, and cross-references passwords with a local database.
* **Load Custom Lists:** Easily add any text files (e.g., password lists from the well-known [SecLists](https://github.com/danielmiessler/SecLists) project[cite: 1]) via the integrated button ("Load custom list (.txt)")[cite: 1].
* **Secure Password Generator:** Generates strong random passwords using the cryptographically secure `secrets` module.
* **Clipboard Protection:** Copied passwords are automatically cleared from the clipboard after 30 seconds.

---

## ⚠️ Important Security Notices & Disclaimer

* **No Absolute Protection:** This program serves as a tool and orientation guide to evaluate password quality. A "strong" result is not an absolute guarantee that a password can never be cracked.
* **Software Bugs:** Software can contain bugs. In rare cases, the algorithm may misjudge passwords or overlook patterns.
* **Use at Your Own Risk:** The use of this program is **entirely at your own risk and peril**. The developer assumes no liability for damages, data loss, hacked accounts, or any other consequences arising directly or indirectly from the use of this software or generated passwords.

---

## 📂 Using Custom Password Lists
Want to extend the tool with your own dictionaries? 
1. Click on **"Load custom list (.txt)"** at the bottom right in the main window.
2. Select a text file (Format: One password per line).
3. The tool automatically updates and expands the database.

## 📄 License & Credits
Developed by **ABUKICK**. 
Inspired by open-source security projects like [SecLists](https://github.com/danielmiessler/SecLists) by Daniel Miessler[cite: 1].
Published under the MIT License – see the [LICENSE](LICENSE) file for more details.
