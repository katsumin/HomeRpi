# HomeRpi
Home Metrics By Raspberry Pi

# Settings
1. config.ini
    - NanoPiではシリアルポートを2ch使用できるので、kyocera_dump_ser.pyによる通信が可能となる。その場合、[kyocera]セクションの設定が有効となる。

      |項番|セクション|キー|値|備考|
      |:-:|:-:|:-:|:-:|:-:|
      |1|smartmeter|bid|Bルートサービス開通の際に受け取った認証ID||
      |2||pwd|Bルートサービス開通の際に受け取ったパスワード||
      |3||serial_port|スマートメータ通信用シリアルポート・デバイス名||
      |4||serial_bps|スマートメータ通信用シリアルポート・ビットレート||
      |5|server|url|収集データ送信先(influxDBサーバ)のURL||
      |6|i2c|port|i2cポート番号|RaspberryPiでは、通常1|
      |7|kyocera|serial_port|京セラモニタ通信用シリアルポート・デバイス名|kyocera_dump_ser.py使用の場合|
      |8||serial_bps|京セラモニタ通信用シリアルポート・ビットレート|kyocera_dump_ser.py使用の場合|

1. Raspberry Pi 起動後
    1. スマートメータへの接続、送受信開始
        - bp35c0_sndrcv.pyを（常駐）起動
        - ここで、スマートメータのアドレスが自動的に抽出され、config.iniに記録される。
    1. エコキュート／エアコン受信開始
        - daikin_rcv.pyを（常駐）起動
    1. 室内温度／湿度／気圧測定開始
        - home_temp.pyを（常駐）起動

      ```
      #cd HomeRpi
      #nohup bp35c0_sndrcv.py &
      #nohup daikin_rcv.py &
      #nohup home_temp.py &
      ```

1. crontab
    - エコキュートの残湯量・瞬時電力値取得
      - 10分間隔で、ec_snd.pyを起動
    - エアコンの瞬時電力値・外気温・室温取得
      - 10分間隔で、ac_snd.pyを起動
    - 京セラモニタの情報取得
      - 毎時10分と40分に、kyocera_dump.pyを起動

    ```
    */10 * * * * /usr/bin/python /home/pi/ec_snd.py >> /home/pi/HomeRpi/cron.log 2>&1
    */10 * * * * /usr/bin/python /home/pi/ac_snd.py >> /home/pi/HomeRpi/cron.log 2>&1
    10,40 * * * * /usr/bin/python /home/pi/kyocera_dump.py >> /home/pi/HomeRpi/cron.log 2>&1
    ```
