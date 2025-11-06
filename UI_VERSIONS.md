# Lock In - UI Versions

The Lock In app has **two UI versions** available. Both use the same core functionality (app blocking, session management, statistics) but with different visual frameworks.

---

## 🎨 Available Versions

### 1. PyQt6 Version (main.py) - **DEFAULT**
**Framework:** PyQt6 (Qt 6)
**Design:** Desktop-native, premium dark theme with card-based design
**Best for:** Traditional desktop experience, maximum performance

**To Run:**
```bash
python main.py
```

**Features:**
- Native OS integration
- Card-based design with shadows
- Emerald green accent color (#10b981)
- Charcoal dark theme
- Running apps shown first with ● indicator
- 60/40 split between available and whitelisted apps
- Visible timer spinner arrows
- Large progress indicators

---

### 2. Flet Version (main_flet.py) - **EXPERIMENTAL**
**Framework:** Flet (Flutter/Material Design)
**Design:** Modern Material Design, responsive
**Best for:** Cross-platform consistency, mobile-like experience

**To Run:**
```bash
python main_flet.py
```

**Features:**
- Material Design components
- Responsive layout
- Cross-platform consistency
- Quick preset buttons (Pomodoro, Deep Work, Ultra Focus)
- Cards with elevation
- Smooth animations (framework-level)
- Web deployment ready (can be deployed as web app)

---

## 📊 Comparison

| Feature | PyQt6 (main.py) | Flet (main_flet.py) |
|---------|----------------|---------------------|
| **Performance** | ⚡ Excellent | ✅ Good |
| **Native Look** | ✅ Yes | ❌ Material Design only |
| **File Size** | 📦 Larger | 📦 Smaller |
| **Startup Time** | ⚡ Fast | ⏱️ Moderate |
| **Customization** | 🎨 Full CSS control | 🎨 Material theming |
| **Mobile-like Feel** | ❌ No | ✅ Yes |
| **Web Deployment** | ❌ No | ✅ Yes (future) |
| **Complexity** | 🔧 More code | 🔧 Less code |

---

## 🚀 Installation

**For PyQt6 version:**
```bash
pip install PyQt6 PyQt6-Qt6 psutil python-dateutil matplotlib
```

**For Flet version:**
```bash
pip install flet psutil python-dateutil matplotlib
```

**For both:**
```bash
pip install -r requirements.txt
```

---

## 🔄 Switching Between Versions

Both versions share the same:
- ✅ Core logic (`core/` folder)
- ✅ Database (`database/` folder)
- ✅ Session data
- ✅ Statistics

You can run either version and they'll use the same data!

---

## 🎯 Which Should I Use?

**Choose PyQt6 (main.py) if:**
- You want maximum performance
- You prefer native desktop look and feel
- You're only targeting desktop platforms
- You want the most stable, tested version

**Choose Flet (main_flet.py) if:**
- You like Material Design aesthetics
- You want a more mobile-app-like experience
- You're interested in future web deployment
- You prefer simpler, more declarative code

---

## 🐛 Known Issues

### PyQt6 Version
- None currently

### Flet Version
- Timer doesn't update in real-time (needs threading implementation)
- App blocking runs in background but UI doesn't reflect it
- Emergency exit may not immediately reflect in UI
- Session progress bar is static

---

## 🔮 Future Plans

- **PyQt6**: Continue as primary, stable version
- **Flet**: Experimental, may add real-time updates and web deployment
- Both will maintain feature parity where possible

---

## 💡 Contributing

If you want to improve either version:
1. PyQt6 improvements go in `main.py` and `ui/` folder
2. Flet improvements go in `main_flet.py`
3. Core logic improvements go in `core/` folder (benefits both!)

---

**Last Updated:** 2025-11-06
**Current Recommended Version:** PyQt6 (main.py)
