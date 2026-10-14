# DESCRIPTION-JOINT-GUI-001

問題：単独displayのジョイントGUIがSIGINTで正常に閉じず、launchが終了コード-2をERRORとして記録する。ready 2回で再現し、起動直後にはPython依存モジュールのimport中にKeyboardInterruptも発生した。

実行ソース：`859f53587c458ea07957caf1acd49f7faea9ddd4`、clean。Jazzy / CycloneDDS / domain100 / VNC :1。原証拠は `../DESCRIPTION-STANDALONE-001/baseline/`。親bringupを含まないprefixでの再現をstandalone-environment.jsonに保存した。

証明した原因：インストール済みjoint_state_publisher_guiのmainは、表示後にSIGINTをSIG_DFLへ設定する。SIGINTがQtのclose処理へ渡らず、プロセスがシグナル終了する。main前のimport中にはまだ終了要求を保持するハンドラーがなく、同じSIGINTがKeyboardInterruptとなる。これは保存したSDKソースと実際の-2終了・importスタックで確認した内容。

変更可能：launch/display.launch.pyのジョイントGUIの起動先、CMakeLists.txtの当該スクリプトinstall、package.xmlの当該実行依存、scripts/joint_state_gui.py。

禁止：SDK本体、RViz起動方式、rover_twist_relay、モデルXML、mesh、摩擦、オプション初期状態、親bringupの検証済み入口。

修正方法：親bringupで確認済みのQt close→worker join→ROS node破棄という処理順を、この独立パッケージの入口で再利用する。親bringupは単独prefixから解決できないため、この入口内へ同じ実装を配置する。追加の差分は、重いSDK import前に終了要求を保持し、起動途中のSIGINTをKeyboardInterruptにしないことに限定する。

検証条件：既存のready / early-sigint再現を使用し、ジョイントGUIが終了コード0で閉じ、同GUIのTraceback・ERROR・強制終了・残留がないこと。モデル・TF・joint_state配信が維持されること。3機種のGUI表示は全体の検証時に同じ条件で確認する。

RVizの独立した失敗は、この候補の合格扱いへ変更しない。単独display全体はRVizの問題が解消するまでFAILのまま保持する。mainや上流へ昇格しない。
