# megarover_description Jazzy単独表示の確認結果

2026-10-14、Ubuntu 24.04 / ROS 2 Jazzy / CycloneDDS / ROS_DOMAIN_ID=100 / VNC :1で、独立ビルドとモデル表示を確認した。実行したソースはcleanな`4c691b8bc0710b6fd9601756ab99af90c45aa684`。親のmegarover3_bringupをROS環境に追加していない。

## 変更と原因

- display.launch.pyが本パッケージ自身の補助ノードを起動するようにした。モデルとRViz設定の選択は維持した。
- SDK joint publisherを利用するGUI有無の入口で、import中の終了要求を記録し、nativeのROS/DDS初期化中だけSIGINT/SIGTERMを保留する。初期化後は元のmaskを復元し、worker/node/contextを順に終了する。
- RVizは初期化中のcloseを保留し、実際のmain windowの出現後もcloseを送る。表示layoutの未保存確認を省略し、Qt/ROSの終了順を保持した。File → Save Configは残る。
- 必要な依存関係・インストール対象をpackage.xml/CMakeに追加した。package.xmlの要素順、Apacheライセンス記載、標準lintの書式を修正した。
- GLXのXlib macroとQtの競合を避けるため、QtをGLXより先にincludeする。
- READMEにJazzyの導入・3機種・GUI有無・終了・オプションの手順を記載した。

失敗と原因の記録はDESCRIPTION-JOINT-GUI-001、DESCRIPTION-RVIZ-CONTEXT-001、DESCRIPTION-RVIZ-WINDOW-001、DESCRIPTION-JSP-SIGNAL-001、DESCRIPTION-JSP-IMPORT-001、DESCRIPTION-GLX-QT-ORDER-001、DESCRIPTION-DDS-BIND-SIGNAL-001に保持した。最終確認途中で発生したUDP bindのEINTRも、終了コード0を理由に合格へ変更していない。

## 同一artifactの実行結果

固定したDESCRIPTION-STANDALONE-001の基準で[15条件すべて合格](./qualified-20261014/qualified-summary.json)。各result.jsonに実行commit・clean状態・command・PID・cwd・実行ファイル/model/configのSHA-256・停止結果を保存した。実行前後のinstalled artifactも同一だった。

| 機種 | 表示完了後Ctrl+C：GUIあり/なし | 初期化中Ctrl+C：GUIあり/なし | GUI再起動 |
| --- | --- | --- | --- |
| mega3 | 2/2合格 | 2/2合格 | 合格 |
| f120a | 2/2合格 | 2/2合格 | 合格 |
| s40a_lb | 2/2合格 | 2/2合格 | 合格 |

表示完了後はrobot_description、joint_states、全URDF jointに対応するTF、mesh実ファイルを確認して12秒観測した。初期化中の条件は所有RViz出現から0.15秒後にSIGINT。終了時間は1.118～1.419秒で、Traceback/ERROR/FATAL、強制終了、所有プロセスの残留は0件。指令publisherは作成していない。

VNC画像は3機種ともモデルと関節GUIが表示され、Global Status: Okであることを画像で確認した。

- [mega3](./qualified-20261014/qualified-candidate-13-mega3-true-restart/desktop.png)
- [f120a](./qualified-20261014/qualified-candidate-14-f120a-true-restart/desktop.png)
- [s40a_lb](./qualified-20261014/qualified-candidate-15-s40a_lb-true-restart/desktop.png)

bind中SIGINTの追加診断は修正後3/3合格、errno=4なし。これは原因の追加診断で、通常の15条件は診断libraryなしで実行した。

## ビルドと標準チェック

[build](./qualified-20261014/qualified-standard-build.log)、[colcon test](./qualified-20261014/qualified-standard-tests.log)、[test-result](./qualified-20261014/qualified-standard-results.log)は合格。8種の標準チェック、37テスト、error/failure/skipはすべて0。cppcheckはこの環境の既定スキップを避けるため、検証条件としてAMENT_CPPCHECK_ALLOW_SLOW_VERSIONS=1で実行した。

[rosdep check](./qualified-20261014/final-rosdep-check.log)も依存関係充足。[実行platform](./qualified-20261014/final-platform.json)と[manifest](./qualified-20261014/qualified-standard-manifest.json)を保存した。証拠転送後に[index](./qualified-20261014/index.json)の187ファイルのSHA-256を照合した。

## モデルとオプション

上流モデルcommit`eb4f4443112d1d708e5b019c67db0c4a335b0276`から、URDF/mesh/RViz/controllers・relay YAMLの28ファイルはbyte単位で同一。[照合結果](./qualified-20261014/qualified-model-invariance.json)を保存した。TG30のincludeは全3モデルでコメントのまま。

TG30、バンパー、カメラステー＋D435iの18組合せは、別の検証用xacroで展開・mesh参照・TF tree構造を確認した。証拠はDESCRIPTION-JSP-IMPORT-001/controlled-candidate/options-qualificationに保持した。モデル定義が同一のため、この結果は現在のモデルにも対応する。オプション上流は確認したcommit`932a710473d1e68b86d78ab919a8442f457ee79f`のmasterを使用する。

## 確認範囲

この結果はモデル表示と終了処理のJazzy動作確認。実機走行、実機センサー統合、物理特性の実測、AMIR 740、legacy Gazebo定義の単独起動は未確認。Gazebo Harmonicの変換・走行は親リポジトリのmegarover3_gazebo側の別検証で扱う。上流の公式Jazzyサポート保証には当たらない。ユーザー確認前のためcandidate branchに保持し、main/上流への昇格は行っていない。
