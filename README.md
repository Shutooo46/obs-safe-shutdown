# obs-safe-shutdown

PCシャットダウン時に OBS Studio を安全に終了させ、設定を確実に保存する OBS Python スクリプトです。

## 解決する問題

Windows をシャットダウンする際に OBS を先に閉じないと、次回起動時にマイクが認識されないことがあります。  
これは OBS が強制終了されることで音声デバイスの設定が保存されないために起こります。

このスクリプトを導入すると、シャットダウン通知を受け取った時点で自動的に OBS の設定を保存するため、問題が解消されます。

## 動作の仕組み

| 状況 | 動作 |
|------|------|
| Windows シャットダウン / 再起動 / ログオフ | `WM_QUERYENDSESSION` を検知し即座に設定保存 |
| OBS を手動で閉じる | `OBS_FRONTEND_EVENT_EXIT` イベントで設定保存 |

## 動作環境

- **OS**: Windows 10 / 11（メイン対応）
- **OBS Studio**: 28.0 以降
- **Python**: OBS 内蔵の Python インタープリタ（別途インストール不要）

> macOS / Linux では `OBS_FRONTEND_EVENT_EXIT` イベントでの保存のみ動作します。

## インストール方法

1. [Releases](https://github.com/Shutooo46/obs-safe-shutdown/releases) から `safe-shutdown.py` をダウンロード

2. OBS Studio を起動し、メニューから **ツール → スクリプト** を開く

3. **「+」ボタン** をクリックし、ダウンロードした `safe-shutdown.py` を選択

4. スクリプト一覧に `safe-shutdown.py` が表示されれば導入完了

## 確認方法

OBS のログ（**ヘルプ → ログファイル → 現在のログを表示**）に以下のメッセージが出力されていれば正常に動作しています。

```
[obs-safe-shutdown] Loaded (v0.1.0)
[obs-safe-shutdown] Windows shutdown handler installed (HWND=0x...)
```

シャットダウン時には：

```
[obs-safe-shutdown] WM_QUERYENDSESSION — saving before shutdown
[obs-safe-shutdown] Settings saved successfully.
```

## アンインストール

**ツール → スクリプト** から `safe-shutdown.py` を選択し、**「-」ボタン** で削除してください。

## ライセンス

MIT License
