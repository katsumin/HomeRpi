# HomeRpi
Home Metrics By Raspberry Pi

# Settings
1. config.ini
    - addressについては、スマートメータ接続プログラム（bp35c0_join2.py）が、自動取得する。

      |項番|キー|値|備考|
      |:-:|:-:|:-:|:-:|
      |1|bid|ID|Bルートサービス開通の際に受け取った認証ID|
      |2|pwd|パスワード|Bルートサービス開通の際に受け取ったパスワード|
      |3|url|収集データ送信先|influxDBサーバのURL|

1. Raspberry Pi 起動後
    1. スマートメータへの接続
        - bp35c0_join2.pyを起動
        - ここで、スマートメータのアドレスがconfig.iniに設定される。
    1. スマートメータ受信開始
        - bp35c0_rcv2.pyを（常駐）起動
    1. エコキュート受信開始
        - ec_rcv.pyを（常駐）起動

      ```
      #bp35c0_join2.py
      #nohup bp35c0_rcv2.py &
      #nohup ec_rcv.py &
      ```

1. crontab
    - スマートメータの瞬時電力値取得
      - 1分間隔で、bp35c0_e7.pyを起動
    - エコキュートの残湯量・瞬時電力値取得
      - 10分間隔で、ec_snd.pyを起動
    - 京セラモニタの情報取得
      - 毎時10分と40分に、kyocera_dump.pyを起動

    ```
    */1 * * * * /usr/bin/python /home/pi/bp35c0_e7.py >> /home/pi/cron.log 2>&1
    */10 * * * * /usr/bin/python /home/pi/ec_snd.py >> /home/pi/cron.log 2>&1
    10,40 * * * * /usr/bin/python /home/pi/kyocera_dump.py >> /home/pi/cron.log 2>&1
    ```
