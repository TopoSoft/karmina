"""Real Chromium acceptance. Requires separately installed Playwright + Chromium."""
import json
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

from karmina.server import make_server


def main():
    with tempfile.TemporaryDirectory() as tmp:
        server = make_server(Path(tmp) / 'browser.sqlite3', 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1440, 'height': 1100})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                expect(page.locator('#hero-title')).to_contain_text('Твоя история')
                for language, heading in [('en', 'Your story'), ('lv', 'Tavs stāsts'), ('ru', 'Твоя история')]:
                    page.locator('#language').select_option(language)
                    expect(page.locator('#hero-title')).to_contain_text(heading)
                page.locator('[data-enter-studio]').first.click()
                for mode in ['animation', 'photorealistic']:
                    page.locator('[name=title]').fill(f'Acceptance {mode}')
                    page.locator('[name=mode]').select_option(mode)
                    page.locator('[name=brief]').fill('Лиса из карандашного рисунка ищет свет в городе.')
                    page.locator('#project-form button').click()
                    expect(page.locator('#project-title')).to_have_text(f'Acceptance {mode}')
                    page.locator('.stage').nth(1).click()
                    expect(page.locator('#draft')).to_be_disabled()
                    page.locator('.stage').first.click()
                    for index in range(6):
                        page.locator('#draft').click()
                        expect(page.locator('#content')).not_to_be_empty()
                        if index == 0:
                            page.locator('#content').fill('Авторская версия брифа. Цель: короткий фильм.')
                            page.locator('#save').click()
                            expect(page.locator('#revision')).to_contain_text('2')
                            page.reload()
                            page.get_by_role('button', name=f'Acceptance {mode}', exact=True).click()
                            expect(page.locator('#content')).to_have_value('Авторская версия брифа. Цель: короткий фильм.')
                        page.locator('#approve').click()
                        expect(page.locator('#progress')).to_contain_text(f'{index + 1} / 6')
                    with page.expect_download() as download_event:
                        page.locator('#export').click()
                    download = download_event.value
                    pack = json.loads(Path(download.path()).read_text())
                    assert len(pack['artifacts']) == 6 and not pack['media_generated']
                    assert pack['mode'] == mode
                    page.locator('.stage').first.click()
                    expect(page.locator('#content')).to_be_disabled()
                    page.locator('#new').click()
                page.set_viewport_size({'width': 390, 'height': 844})
                page.get_by_role('button', name='Acceptance photorealistic', exact=True).click()
                expect(page.locator('#project-title')).to_have_text('Acceptance photorealistic')
                expect(page.locator('.stage')).to_have_count(6)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                assert not errors, errors
                browser.close()
                print('PASS: Chromium EN/LV/RU, both modes, approval gates, revision persistence, JSON downloads, immutable approvals, 390px layout, no page errors')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    main()
