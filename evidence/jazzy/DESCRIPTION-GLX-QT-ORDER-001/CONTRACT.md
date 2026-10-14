# DESCRIPTION-GLX-QT-ORDER-001

書式候補b102494の標準ビルドはexit2となり、GUI実行へ進んでいない。失敗ログを保持し、CPP include順の変更を棄却する。Python書式や他の無関係な変更を巻き戻さない。

証明した原因：GLXがXlibのBool / CursorShape等のmacroを定義してからQt headerを読むと、qmetatype.hの明示的#errorとqnamespace.hのenum構文エラーが発生する。NoneとStatusだけのundefでは不足する。

修正可能なのはsrc/rviz_no_prompt.cppのinclude順だけ。QtをGLXより先に読み、その後GLXを読む。Qt/C header群とC++標準header群を分けてlintに適合させる。SDK・処理内容・GL同期・ROS/Qt停止順・modelは変更しない。

元のJazzy標準build/colcon testを成功させ、同一artifactの単独表示matrixを実行する。純粋なcpplint成功だけでビルド成功と扱わない。main・上流へ昇格しない。
