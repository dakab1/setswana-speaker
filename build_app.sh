#!/bin/sh
# Build "Setswana Speaker.app" into ~/Applications. The bundle is a thin launcher:
# it runs desktop.py from this folder, so code changes here need no rebuild.
set -e
cd "$(dirname "$0")"
PROJECT="$(pwd)"
APP="$HOME/Applications/Setswana Speaker.app"

# Icon: Botswana flag (pula blue, white, black) on a macOS-style rounded square.
.venv/bin/python - <<'EOF'
from AppKit import NSBezierPath, NSBitmapImageRep, NSColor, NSImage, NSPNGFileType, NSMakeRect
S = 1024
img = NSImage.alloc().initWithSize_((S, S))
img.lockFocus()
NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(100, 100, 824, 824), 185, 185).addClip()
def band(y, h, rgb):
    NSColor.colorWithSRGBRed_green_blue_alpha_(*rgb, 1).set()
    NSBezierPath.fillRect_(NSMakeRect(0, y, S, h))
band(0, S, (0.427, 0.663, 0.847))      # pula blue
band(392, 240, (1, 1, 1))              # white edges
band(432, 160, (0, 0, 0))              # black band
img.unlockFocus()
rep = NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
rep.representationUsingType_properties_(NSPNGFileType, None).writeToFile_atomically_("icon.png", True)
EOF

ICONSET="$(mktemp -d)/icon.iconset"
mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s icon.png --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  sips -z $((s * 2)) $((s * 2)) icon.png --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/icon.icns"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Setswana Speaker</string>
  <key>CFBundleDisplayName</key><string>Setswana Speaker</string>
  <key>CFBundleIdentifier</key><string>local.setswana-speaker</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>setswana-speaker</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>LSArchitecturePriority</key><array><string>arm64</string></array>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
EOF

cat > "$APP/Contents/MacOS/setswana-speaker" <<EOF
#!/bin/sh
cd "$PROJECT" && set -a && . ./.env && set +a
exec arch -arm64 .venv/bin/python -W default desktop.py >> "\$HOME/Library/Logs/SetswanaSpeaker.log" 2>&1
EOF
chmod +x "$APP/Contents/MacOS/setswana-speaker"
touch "$APP"
echo "Built $APP"
