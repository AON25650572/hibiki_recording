import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import pydub

def wait_clickable(wait_seconds,Xpath_selector,driver):
    WebDriverWait(driver,wait_seconds).until(EC.element_to_be_clickable((By.XPATH,Xpath_selector)))

def wait_located(wait_seconds,Xpath_selector,driver):
    WebDriverWait(driver,wait_seconds).until(EC.presence_of_all_elements_located)

# 最新放送を全部取得
def new_radio_programs(urls,driver):
    # 放送回取得のためのXPath
    kaisuu = '/html/body/div[2]/div/div/div[1]/div/div[1]/div/div[2]/div[2]'
    
    programs = {}
    
    for radio_name,url in urls.items():
        # 録音ページにジャンプ
        driver.get(url)
        
        # 放送回数の存在を確認し回数を取得
        wait_clickable(wait_seconds=60,Xpath_selector=kaisuu,driver=driver)
        kaisu = driver.find_element_by_xpath(kaisuu).text[:-3]
        
        # 保存形式はmp3
        output_fname = radio_name + kaisu + '.mp3'
        programs[radio_name] = output_fname
        
    return programs

# audio_maker.py

import pyaudio  #録音機能を使うためのライブラリ
import wave     #wavファイルを扱うためのライブラリ
 
# RECORD_SECONDS = 10 #録音する時間の長さ（秒）
# WAVE_OUTPUT_FILENAME = "sample.wav" #音声を保存するファイル名
# iDeviceIndex = 0 #録音デバイスのインデックス番号
 
#基本情報の設定
# FORMAT = pyaudio.paInt16 #音声のフォーマット
# CHANNELS = 2             #ステレオ
# RATE = 44100             #サンプルレート
# CHUNK = 2**11            #データ点数
 
def wav_maker(RECORD_SECONDS = 10,WAVE_OUTPUT_FILENAME = "sample.wav",
              iDeviceIndex = 0,FORMAT = pyaudio.paInt16,CHANNELS = 2,RATE = 44100,CHUNK = 2**11): 
    audio = pyaudio.PyAudio() #pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
            rate=RATE, input=True,
            input_device_index = iDeviceIndex, #録音デバイスのインデックス番号
            frames_per_buffer=CHUNK)

    #--------------録音開始---------------
    
    print ("recording...")
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    
    print ("finished recording")
    
    #--------------録音終了---------------
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

# 0. ユーザー情報をリード
with open('user_datas.json','r',encoding='utf8') as f:
    user_datas = json.load(f)

# 1. 会員情報入力、ログイン
# 自前の環境ではドライバーのパス通しがうまくいかなかったので直下フォルダにドライバーを配置している
driver = webdriver.Chrome()

# 一度設定すると find_element 等の処理時に、要素が見つかるまで指定時間繰り返し探索するようになる
driver.implicitly_wait(30) # 秒

driver.get('https://hibiki-radio.jp/login')


# emailの入力
email_input = '/html/body/div[2]/div/div/div/div/div/form/div[1]/input'
wait_clickable(wait_seconds=60,Xpath_selector=email_input,driver=driver)
driver.find_element_by_xpath(email_input).send_keys(user_datas['mail'])

# パスワードの入力
pass_input = '/html/body/div[2]/div/div/div/div/div/form/div[2]/input'
wait_clickable(wait_seconds=60,Xpath_selector=pass_input,driver=driver)
driver.find_element_by_xpath(pass_input).send_keys(user_datas['pass'])

# ログインボタンのクリック
login_button = '/html/body/div[2]/div/div/div/div/div/form/div[3]/button'
wait_clickable(wait_seconds=60,Xpath_selector=login_button,driver=driver)
driver.find_element_by_xpath(login_button).click()

# メインバーナーが出るまで待機
main_banner = '//*[@id="banner-carousel"]'
driver.find_element_by_xpath(main_banner)

new_programs = new_radio_programs(user_datas['urls'],driver)

print('＝＝＝　最新回一覧　＝＝＝')
print()
for k,v in new_programs.items():
    print(f'{k}\t{v}')
print()

# 保存先のフォルダの中身をlist化
saved_files = []
for path in user_datas['save_folders']:
    saved_files += os.listdir(path)

# 本放送と楽屋裏のXPath
nomal_button = '/html/body/div[2]/div/div/div[1]/div/div[1]'
gakuyaura_button = '/html/body/div[2]/div/div/div[1]/div/div[2]'
# 経過時間のXpath
total = '/html/body/program-player-ctrl/div[2]/div/div/div[4]/div[3]/span'

# 保存先に最新放送回がなければレコーディング
save_path = user_datas['save_folders'][0]
print('＝＝＝　レコーディング　＝＝＝')
for radio_name in new_programs.keys():
    if new_programs[radio_name] not in saved_files:
        print(f'レコーディング中：{radio_name}')
        # 録音ページにジャンプ
        driver.get(user_datas['urls'][radio_name])

        # 本放送の再生時間を取得
        wait_clickable(wait_seconds=60,Xpath_selector=nomal_button,driver=driver)
        sleep(3)# どうしてもうまくいきそうにないからsleep入れる
        driver.find_element_by_xpath(nomal_button).click()
        wait_clickable(wait_seconds=60,Xpath_selector=total,driver=driver)
        sleep(3)# どうしてもうまくいきそうにないからsleep入れる
        nomal = driver.find_element_by_xpath(total).text.split(':')
        print(f'本放送：{nomal[0]}:{nomal[1]}')
        nomal_second = int(nomal[0])*60+int(nomal[1])+3 # 3秒ほど余剰を入れる

        # 本放送の再生時間を取得
        if radio_name != 'Yuyake_Studio': # 夕焼けスタジオは楽屋裏がない
            wait_clickable(wait_seconds=60,Xpath_selector=gakuyaura_button,driver=driver)
            sleep(3)# どうしてもうまくいきそうにないからsleep入れる
            driver.find_element_by_xpath(gakuyaura_button).click()
            wait_clickable(wait_seconds=60,Xpath_selector=total,driver=driver)
            sleep(3)# どうしてもうまくいきそうにないからsleep入れる
            gakuya = driver.find_element_by_xpath(total).text.split(':')
            print(f'楽屋裏：{gakuya[0]}:{gakuya[1]}')
            gakuya_second = int(gakuya[0])*60+int(gakuya[1])+3 # 3秒ほど余剰を入れる

        # 一回リロード(確認再生分をチャラにするため)
        driver.get(user_datas['urls'][radio_name])

        # ラジオ再生先への遷移を確認 => 再生ボタンの有無 => クリック
        sleep(3)# どうしてもうまくいきそうにないからsleep入れる
        omote_button = driver.find_element_by_xpath(nomal_button).click()
        # 録音モジュールを起動
        print(radio_name + '本放送レコーディング中・・・')
        wav_maker(WAVE_OUTPUT_FILENAME=save_path+'nomal.wav',RECORD_SECONDS=nomal_second)

        # ラジオ裏再生(夕焼けスタジオは楽屋裏なし)
        if radio_name != 'Yuyake_Studio':
            driver.find_element_by_xpath(gakuyaura_button).click()
            # 録音モジュールを起動
            print(radio_name + '本放送レコーディング中・・・')
            wav_maker(WAVE_OUTPUT_FILENAME=save_path+'gakuya.wav',RECORD_SECONDS=gakuya_second)

        # 録音した音声を結合
        sound_1 = pydub.AudioSegment.from_wav(save_path+'nomal.wav')
        if radio_name != 'Yuyake_Studio':
                sound_2 = pydub.AudioSegment.from_wav(save_path+'gakuya.wav')

        if radio_name != 'Yuyake_Studio':
            export_sound = sound_1 + sound_2
        else:
            export_sound = sound_1

        (export_sound + 6).export(save_path+new_programs[radio_name], format="mp3")

        print()
        print('Complete!：'+new_programs[radio_name])
        print()
        print('-----------------------------\n')

# 一時ファイル削除
if 'nomal.wav' in os.listdir():
    os.remove('nomal.wav')
if 'gakuya.wav' in os.listdir():
    os.remove('gakuya.wav')

input('エンターキーで終了')
driver.quit()