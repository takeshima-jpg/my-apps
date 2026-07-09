#!/usr/bin/env node
/*
 * pre-commit 用のスクリプト抽出ヘルパー（node のみで動作）。
 *
 *   node tools/extract_scripts.js <input.html> <outDir>
 *
 * <outDir>/vanilla.js  … src属性なし・type="text/babel"以外の <script> を連結
 * <outDir>/babel.jsx   … type="text/babel" の <script>（存在する時だけ生成）
 *
 * ブラウザでは各 <script> が同一グローバルを共有するため、連結して node --check
 * にかけるのは実際の実行環境に近い妥当な構文チェックになる。
 */
'use strict';
const fs = require('fs');
const path = require('path');

const [, , inPath, outDir] = process.argv;
if (!inPath || !outDir) {
  console.error('usage: node extract_scripts.js <input.html> <outDir>');
  process.exit(2);
}

const html = fs.readFileSync(inPath, 'utf8');
const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;

const vanilla = [];
const babel = [];
let m;
while ((m = re.exec(html)) !== null) {
  const attrs = m[1] || '';
  const body = m[2] || '';
  if (/\bsrc\s*=/i.test(attrs)) continue;              // 外部読み込みは対象外
  if (/type\s*=\s*["']text\/babel["']/i.test(attrs)) {
    babel.push(body);
  } else {
    vanilla.push(body);
  }
}

fs.writeFileSync(path.join(outDir, 'vanilla.js'), vanilla.join('\n;\n'), 'utf8');
if (babel.length) {
  fs.writeFileSync(path.join(outDir, 'babel.jsx'), babel.join('\n;\n'), 'utf8');
}
