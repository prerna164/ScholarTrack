"""Optional: pip install playwright; python -m playwright install chromium.
Start the seeded app first, then: python scripts/capture_screenshots.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).resolve().parent.parent/'screenshots'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    for filename,url in [('dashboard','/'),('projects','/projects?q=water'),('detail','/projects/1')]:
        page.goto('http://127.0.0.1:8000'+url)
        page.screenshot(path=str(out/f'{filename}.png'),full_page=True)
    page.goto('http://127.0.0.1:8000/proposal')
    page.fill('[name=title]','Water quality sensor network')
    page.fill('[name=summary]','Monitor river water quality with sensors measuring pH and turbidity to detect pollution events.')
    page.click('button')
    page.wait_for_load_state('networkidle')
    page.screenshot(path=str(out/'proposal.png'),full_page=True)
    browser.close()
print('Saved four screenshots in',out)
