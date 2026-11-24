import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import { messages } from '../karmina/web/i18n.js';

test('all supported languages have identical nonempty message keys', () => {
  const keys = Object.keys(messages.en).sort();
  for (const language of ['en', 'lv', 'ru']) {
    assert.deepEqual(Object.keys(messages[language]).sort(), keys);
    for (const value of Object.values(messages[language])) assert.ok(value.trim());
  }
});

test('all static workspace labels have translations', async () => {
  const html = await readFile(new URL('../karmina/web/index.html', import.meta.url), 'utf8');
  for (const [, key] of html.matchAll(/data-t="([^"]+)"/g)) {
    for (const language of ['en', 'lv', 'ru']) assert.ok(messages[language][key], `${language}:${key}`);
  }
});
