# 🛡️ Password Security Checker

A secure, portable, and 100% local Python tool for checking password strength with an intuitive graphical user interface (Tkinter). Features **automatic language detection** (supports English and German based on your system settings).

## 🚀 Features
* **Automatic Language Detection:** Automatically detects your operating system's language (English or German) and adjusts the user interface accordingly.
* **100% Local:** No internet connection, no telemetry, no cloud storage. Your passwords stay on your computer.
* **Smart Analysis:** Analyzes length, character variety, common patterns, and cross-references passwords with a local database.
* **Load Custom Lists:** Easily add any text files (e.g., password lists from the well-known [SecLists](https://github.com/danielmiessler/SecLists) project) via the integrated button ("Load Custom List").
* **Secure Password Generator:** Generates strong random passwords using the cryptographically secure `secrets` module.

---

## ⚠️ Important Security Notices & Disclaimer

* **No Absolute Protection:** This program serves as a tool and orientation guide to evaluate password quality. A "strong" result is not an absolute guarantee that a password can never be cracked.
* **Software Bugs:** Software can contain bugs. In rare cases, the algorithm may misjudge passwords or overlook patterns.
* **Use at Your Own Risk:** The use of this program is **entirely at your own risk and peril**. The developer assumes no liability for damages, data loss, hacked accounts, or any other consequences arising directly or indirectly from the use of this software or generated passwords.

---

## 📂 Using Custom Password Lists
Want to extend the tool with your own dictionaries? 
1. Click on **"Load Custom List"** at the bottom right in the main window.
2. Select a text file (Format: One password per line).
3. The tool automatically updates and expands the database.

## 📄 License & Credits
Developed by **ABUKICK**. 
Inspired by open-source security projects like [SecLists](https://github.com/danielmiessler/SecLists) by Daniel Miessler.
Published under the MIT License
