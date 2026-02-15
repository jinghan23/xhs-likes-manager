#!/bin/bash
# Patch OpenClaw browser to add --remote-allow-origins=* for external CDP access
# Run after each OpenClaw update

CHROME_JS=$(find /opt/homebrew/lib/node_modules/openclaw/dist/ -name 'chrome-*.js' | head -1)
if [ -z "$CHROME_JS" ]; then
  echo "❌ Could not find chrome-*.js in OpenClaw dist"
  exit 1
fi

if grep -q 'remote-allow-origins' "$CHROME_JS"; then
  echo "✅ Patch already applied to $CHROME_JS"
  exit 0
fi

# Add --remote-allow-origins=* after --password-store=basic
sed -i.bak 's/"--password-store=basic"/"--password-store=basic",\n\t\t\t"--remote-allow-origins=*"/' "$CHROME_JS"

if grep -q 'remote-allow-origins' "$CHROME_JS"; then
  echo "✅ Patch applied successfully to $CHROME_JS"
  rm -f "${CHROME_JS}.bak"
else
  echo "❌ Patch failed"
  # Restore backup
  mv "${CHROME_JS}.bak" "$CHROME_JS"
  exit 1
fi
