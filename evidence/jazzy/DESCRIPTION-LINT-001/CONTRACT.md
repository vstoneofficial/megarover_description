# DESCRIPTION-LINT-001

同じ1455fe0の標準テストでflake8・cpplint・uncrustifyが不合格。変更したPythonのimport順・空白・長い行、既存relayのimport順、CPPのinclude順とlambda空白、GLX drawableの冗長なlong castが診断された。原ログとxunitを../DESCRIPTION-JSP-IMPORT-001/controlled-candidate/に保持した。

修正範囲はその6 PythonとCPPファイルの書式のみ。未使用のfixture importを除き、subscription保持は実際の破棄手順へ対応付ける。DDS/Qt/ROSの処理順、期限、配信周期、relay数式、モデル、controller設定は変更しない。

GLX headerのNone/Status macroをQt/ROSへ漏らさない順序を保持する。GLXDrawableの元の型を使用し、出力値を変更しない。旧SDK・mapper・親bringupを変更しない。

同じ標準lintを通し、Python関数ASTとrelay制御部分の同一性を確認する。新しいartifactで単独表示の3機種×GUI有無・early-sigint・再起動を再確認する。合格条件は既存contractから変更しない。
