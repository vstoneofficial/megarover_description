# DESCRIPTION-RVIZ-CONTEXT-001

対象：Jazzy / CycloneDDS / domain100 / VNC :1、親bringupを含まない単独display。

再現ソース：`5ce172699ed80e88e1ea326d0d903a576685db6f`、clean。原証拠は `../DESCRIPTION-JOINT-GUI-001/controlled-candidate/joint-candidate-mega3-early-sigint/`。ジョイントGUIは正常終了するが、RVizは初期化中のSIGINT後に無効なROS contextでguard conditionを作ろうとしてRCLErrorを出し、SIGKILLまで進む。

証明する対象原因は、単独launchがGUIの初期化・閉鎖を仲介せず、SDKのRVizへ直接SIGINTを届ける起動経路である。ソース上はrviz2 Nodeを直接起動し、再現ログではSIGINT処理がOpenGL初期化完了とguard condition作成より先行する。同一ソース・SDK・モデル・RMWのready runではこの初期化時RCLErrorは発生しない。アロケータや描画ドライバーの欠陥を原因とする主張はしない。

変更可能：launch/display.launch.pyのRViz起動経路、CMakeLists.txtとpackage.xmlのその実行・ビルド依存、scripts/gui_session.py、src/rviz_no_prompt.cpp。

禁止：SDK本体、ジョイントGUIの確認済み処理、モデルXML・mesh・摩擦・TG30初期コメント、親bringupの確認済み入口。

使用する終了経路は、既に親bringupで確認したGUI仲介・RViz adapterを独立パッケージへ配置する。SDKのGUI初期化が戻ってからQt closeを実行し、GUI終了までROS contextと選択RMWを保持する。描画完了とFile→Save機能を保持する既存adapterを同じ実装のまま再利用し、新しいSDK改造や停止条件は追加しない。親bringupが単独環境から解決できないことは記録済み。

合格条件は元のDESCRIPTION-STANDALONE-001と同じready / early-sigintで、30秒以内にTraceback・RCLError・ERROR・FATAL・強制終了・所有プロセス残留なく終了すること。まずexact reproductionを行い、同一artifactで3機種×GUI有無と再起動を確認する。モデル・TF・joint_statesを維持し、実行前後でartifactが一致すること。診断の成功で初期化途中の終了確認を代替しない。

main・上流へ昇格しない。候補の対象確認を記録してから次の独立した問題へ進む。
