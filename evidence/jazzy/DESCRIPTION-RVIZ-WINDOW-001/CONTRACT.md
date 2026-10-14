# DESCRIPTION-RVIZ-WINDOW-001

再現候補：`bf5d7135f657177b352b0b10b9cb1df9f78be9db`、clean。CPP sourceは親bringupの確認済み実装とbyte一致（b1039520...）。実行ELFは0e1fb9c3...。前件のRCLErrorは出なくなったが、同じearly-sigint条件でGUI supervisorがSIGKILLとなり、子RVizが残留した。単独display全体は未合格。

原証拠：`../DESCRIPTION-RVIZ-CONTEXT-001/controlled-candidate/rviz-candidate-1-mega3-true-early-sigint/`。

証明済みの原因：GUI supervisorが初期ウインドウへWM_DELETEを送った後、PIDをclosed集合へ追加する。その同じPIDで後から現れた別ウインドウは送信対象から除外される。失敗runの最初の対象は0x1e00006。対照runでは同じPIDの実際のRViz本体は0x1e00103であり、本体へ同じ終了要求を送ると2.128秒で終了した。cwdと子環境を元の再現へ揃えた対照runでも、最初0x1e00006→後続0x1e00106となり、終了要求の再送だけで1.217秒、エラー・強制終了・残留なしになった。

後続ウインドウのWM_NAMEは使用中のmega3.rvizを示し、WM_CLASSはrviz_no_prompt。最初のウインドウのSDK内部用途までは断定しない。

対照は診断であり、通常経路の合格と扱わない。最初の診断はモジュール読取りで生成したbytecode cacheがcleanチェックにかかり、候補を起動していない。ログを保持し、その診断で生成した1ファイルだけを削除した。再診断では親Pythonのbytecode書込みを無効化してcleanを維持した。

変更可能：scripts/gui_session.pyの重複送信の管理単位だけ。PID単位からウインドウID単位へ変更し、同じウインドウには重複送信せず、同じPIDの後続ウインドウには送信する。CPP、RMW、描画処理、モデル、期限、SIGINT条件は変更しない。

合格条件：元のearly-sigint再現を診断再送なしで2回、readyを1回成功させる。30秒以内に終了し、Traceback・ERROR・FATAL・異常終了・強制終了・残留なし。次に3機種×GUI有無と再起動を同じartifactで確認する。main・上流へ昇格しない。
