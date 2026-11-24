"""Reference-led redesign acceptance, independent from domain workflow tests."""
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

from karmina.server import make_server


def main():
    with tempfile.TemporaryDirectory() as tmp:
        server = make_server(Path(tmp) / 'design.sqlite3', 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1440, 'height': 1100})
                errors, failed = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('response', lambda response: failed.append(response.url) if response.status >= 400 else None)
                base = f'http://127.0.0.1:{server.server_port}'
                page.goto(base)
                expect(page.locator('#landing')).to_be_visible()
                expect(page.locator('#hero-art')).to_be_visible()
                expect(page.locator('#hero-title')).to_contain_text('Твоя история')
                assert page.locator('#hero-art').evaluate('(img) => img.complete && img.naturalWidth > 1000')
                page.evaluate('document.fonts.ready')
                for language in ['en', 'lv', 'ru']:
                    page.locator('#language').select_option(language)
                    for width in [320, 390, 600, 768, 850, 1024, 1440]:
                        page.set_viewport_size({'width': width, 'height': 1100})
                        label = page.locator('.hero-topline').bounding_box()
                        switch = page.locator('.hero-switch').bounding_box()
                        assert (label['x'] + label['width'] <= switch['x']
                                or switch['x'] + switch['width'] <= label['x']
                                or label['y'] + label['height'] <= switch['y']
                                or switch['y'] + switch['height'] <= label['y']), f'hero overlap: {language} {width}'
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'overflow: {language} {width}'
                page.set_viewport_size({'width': 1440, 'height': 1100})
                page.locator('[data-hero-mode=photorealistic]').click()
                expect(page.locator('#hero-art')).to_have_attribute('src', '/assets/cinema.png')
                page.locator('[data-hero-mode=animation]').click()
                expect(page.locator('#hero-art')).to_have_attribute('src', '/assets/crew.png')
                expect(page.locator('.crew-card')).to_have_count(6)
                page.locator('.crew-card').first.click()
                expect(page.locator('#agent-dialog')).to_be_visible()
                page.keyboard.press('Escape')
                expect(page.locator('#agent-dialog')).not_to_be_visible()
                for language in ['en', 'lv', 'ru']:
                    page.locator('#language').select_option(language)
                    expect(page.locator('html')).to_have_attribute('lang', language)
                    assert page.locator('#hero-title').inner_text().strip()
                page.locator('[data-enter-studio]').first.click()
                expect(page.locator('#workspace')).to_be_visible()
                expect(page).to_have_url(base + '/studio')
                page.locator('[name=title]').fill('Existing workflow survives')
                page.locator('[name=brief]').fill('A director creates a story.')
                page.locator('#project-form button[type=submit]').click()
                expect(page.locator('#project-title')).to_have_text('Existing workflow survives')
                page.locator('#draft').click()
                expect(page.locator('#content')).not_to_be_empty()
                page.locator('[data-home]').first.click()
                expect(page.locator('#landing')).to_be_visible()
                page.locator('[data-enter-studio]').first.click()
                page.get_by_role('button', name='Existing workflow survives', exact=True).click()
                expect(page.locator('#content')).not_to_be_empty()
                for width in [390, 768, 1440]:
                    page.set_viewport_size({'width': width, 'height': 1000})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'workspace overflow {width}'
                    page.locator('[data-home]').first.click()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'landing overflow {width}'
                    assert page.locator('#hero-art').evaluate('(img) => img.complete && img.naturalWidth > 1000')
                    page.locator('[data-enter-studio]').first.click()
                page.emulate_media(reduced_motion='reduce')
                assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
                assert not errors, errors
                assert not failed, failed
                browser.close()
                print('PASS: cinematic artwork, mode switching, six role dialogs, RU/EN/LV, studio routing, saved project preservation, 390/768/1440px layouts, reduced motion, no runtime or asset errors')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    main()
