# LinSticky

Modern sticky notes application built with Python, GTK4, and Libadwaita for Linux.

### **Version**: 2.1.0
_______________

> [!IMPORTANT]
> **This is the new GTK4/Libadwaita version.**  
>  
> ⚠️ **Backward compatibility notice:**  
> This version is **NOT compatible with stickers created in previous versions** (PyQt6 v1.x).  
> Existing stickers **will not be migrated automatically**, so please **save or export any important text in advance** before installing this version.  
>  
> If you are looking for a **legacy version**, please use the original **PyQt6 version (v1.4.1)** available in the  
> 👉 [legacy branch](https://github.com/pavel-glukhov/linsticky/tree/legacy).

_______________

![example of app](https://github.com/pavel-glukhov/linsticky/blob/gtk/pic/example_2.0.0.png)

## 📑 Table of Contents
- [Features](#-features)
- [Installation](#installation)
  - [Snap Store (Upstream)](#snap-store-upstream)
  - [DEB Package](#deb-package)
- [Troubleshooting Localization](#troubleshooting-localization)
- [Credits](#credits)


## ✨ Features

- 📝 Smart Sticky Notes
Create, edit, and organize your notes in a clean, distraction-free interface designed for daily use.
- 🎨 Custom Color Palette
Personalize your notes by choosing colors that match your workflow and mood.
- ✍️ Rich Text Preservation
All text formatting is reliably saved, so your notes always look exactly as intended.
- 🌍 Multilingual Support
Use the app in multiple languages, including:
  - English
  - Русский
  - Español
  - Deutsch
  - Français
  - 简体中文
  - Português (Brasil)
  - Türkçe
  - Қазақша
- 🖥️ Modern GNOME Experience
A refreshed interface that follows current GNOME / Adwaita design guidelines for a native look and feel.
- Support of dark theme.
- Adjustable note transparency: open **Settings**, lower **Note opacity (%)**
  (20–100%), and click **Save Settings**. All open notes update immediately and
  become fully opaque while hovered. The setting is remembered for new notes
  and future sessions; 100% disables transparency.

## Installation

### Snap Store (Upstream)

The upstream LinSticky is available via the Snap Store. This fork's transparency
feature is available in the DEB release below or by running this checkout.

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-black.svg)](https://snapcraft.io/linsticky)

```bash
sudo snap install linsticky
```

### DEB Package

You can download this fork's .deb package from the [Releases page](https://github.com/Rdlenke/linsticky/releases).

```bash
# 1. Download the package
curl -O -L https://github.com/Rdlenke/linsticky/releases/download/v2.1.0/io.linsticky.app_2.1.0_all.deb

# 2. Install dependencies
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gettext

# 3. Install the package
sudo apt install ./io.linsticky.app_2.1.0_all.deb
```

### Run or build from source

After installing the dependencies above, quit any running LinSticky instance and run:

```bash
python3 linsticky/main.py
```

To build a DEB package, install `jq` and run `bash build_deb_package.sh`.
The package is written to `dist/`.

Run the regression tests with `python3 -m unittest discover -s tests -v`.
GTK integration tests require a display (or `xvfb-run -a` in a headless environment).

Releases are published by `.github/workflows/release.yml` when a `v*` tag is pushed.
Update the version in `linsticky/app_info.json`, `snap/snapcraft.yaml`, and this
README, and add `release-notes/<tag>.md` before tagging. The workflow tests the
tagged source and attaches a DEB package and SHA-256 checksum to the GitHub release.

## Troubleshooting Localization

If the app's language doesn't change after selection:
1.  **Install Language Pack:**
    ```sh
    sudo apt install language-pack-[lang_code] 
    ```
2.  **Generate Locale:**
    ```sh
    sudo locale-gen [lang_code].UTF-8 
    ```
3.  **Restart:** Restart the application.

Check available locales: `locale -a`

## Credits

- Author: Pavel Glukhov
- Email: glukhov.p@gmail.com
- License: MIT License
