Screenshots were not captured in the build environment because the browser download failed. To capture four real application screens locally:

```bash
python -m pip install playwright
python -m playwright install chromium
# In another terminal, run the seeded app using the main README.
python scripts/capture_screenshots.py
```

The capture script expects the seeded demo project with ID 1 and does not modify records.
