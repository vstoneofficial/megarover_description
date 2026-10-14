# Jazzy成果ブランチの統合

対象はYOSHIDA-V/megarover_description-jazzy。Jazzyの成果ブランチをjazzyに統一し、READMEと親submoduleの参照もこの名前へ揃える。上流vstoneofficialのリポジトリは変更しない。

基点は表示15条件・標準チェック8種37テストが合格したc024f0f0d38ba750ab95e384a1450cd4a5888597。元のmain（64e5525）の履歴は、この確認済みcheckpointに含まれる。productionコード、モデル、mesh、設定は基点と同一であることをgit diffで確認する。TG30のincludeは3機種ともコメントのまま。

中断直前のc6a337eは未実行の速度リレー用fixtureとcontractを追加しただけで、productionコードはc024f0fと同一。未検証のfixtureは成果ブランチへ追加せず、旧ブランチ全体をarchive tagへ保持した。TG30有効化ブランチもオプション設定の履歴として保持し、公開初期状態は無効を維持する。

| 旧リモートブランチ | 先端commit | 保存済みarchive tag |
| --- | --- | --- |
| main | 64e5525268d4df9aea50462e81e0d15acb3823ef | archive/consolidation-20261014/original-main |
| codex/jazzy-description-default | eb4f4443112d1d708e5b019c67db0c4a335b0276 | archive/consolidation-20261014/description-default |
| codex/jazzy-standalone-display | c6a337e698f4783c2c112387aa43f399292785ab | archive/consolidation-20261014/standalone-display |
| codex/jazzy-tg30-option | 8b091896ba4d54717e520cdc5cd8c220cfbf7fc3 | archive/consolidation-20261014/tg30-option |

タグをremoteへ保存し、完全履歴のローカルbundleも検証してから整理する。対象リポジトリにopen PRは0件、旧4ブランチに保護設定はないことを事前に確認した。jazzyをpushし、default branchを切り替えてから、記録した旧SHAに対するleaseを付けて旧ブランチを削除する。

2026-10-14 09:22 JST、削除後の[参照状態](./verified-refs.json)を確認した。GitHubとローカルのheadsはjazzyだけで、GitHubのdefault branchもjazzy。productionと検証fixtureは確認済みc024f0fと同一。このJSONは証拠commitを追加する前の参照snapshotである。

これはブランチと参照の整理であり、未確認の実機制御・AMIR 740・同梱速度リレー単独実行の成功を意味しない。確認済みのモデル表示と終了処理の成果・失敗証拠はすべて保持する。
