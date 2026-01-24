# Icon Placeholders

Die Extension benötigt Icons in folgenden Größen:

- icon16.png (16x16)
- icon32.png (32x32)
- icon48.png (48x48)
- icon128.png (128x128)

## Temporäre Lösung

Für Development kannst du einfache Placeholder-Icons erstellen:

### Option 1: Online Icon Generator

1. Gehe zu https://www.favicon-generator.org/
2. Lade ein Logo hoch oder erstelle ein einfaches Icon
3. Generiere die verschiedenen Größen
4. Lade die PNG-Dateien herunter und benenne sie entsprechend

### Option 2: Mit SVG und Browser

Erstelle eine SVG-Datei `icon.svg` mit folgendem Inhalt:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" fill="#667eea"/>
  <text x="64" y="80" font-size="60" text-anchor="middle" fill="white" font-family="Arial">🎯</text>
</svg>
```

Dann öffne die SVG im Browser, mache einen Screenshot und skaliere auf die benötigten Größen.

### Option 3: Python Script (empfohlen für Production)

```python
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    # Erstelle ein Icon mit Farbverlauf
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)

    # Zeichne ein einfaches Symbol (z.B. "🎯" oder "SPO")
    font_size = int(size * 0.6)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    text = "🎯"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) / 2
    y = (size - text_height) / 2

    draw.text((x, y), text, font=font, fill='white')
    img.save(filename, 'PNG')

# Generiere alle benötigten Größen
create_icon(16, 'icon16.png')
create_icon(32, 'icon32.png')
create_icon(48, 'icon48.png')
create_icon(128, 'icon128.png')
```

## Finales Icon Design

Für Production sollte ein professionelles Icon erstellt werden, das:

- Das SPO-Branding widerspiegelt
- Auf allen Größen gut erkennbar ist
- Einen eindeutigen Wiedererkennungswert hat
- Im Chrome Web Store gut aussieht

Mögliche Design-Elemente:

- Shopping-Bag Icon
- Stern (für Bonusprogramme)
- Prozentzeichen (für Cashback)
- SPO-Logo
- Kombination aus Einkaufswagen + Sterne
