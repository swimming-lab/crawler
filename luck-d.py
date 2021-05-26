from selenium import webdriver
from datetime import datetime, timedelta
import requests
import json
import re
import pickle


HOME_PATH = '<YOUR_PATH>'
DRIVER_PATH = '<YOUR_PATH>/chromedriver'
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--remote-debugging-port=9222")
driver = webdriver.Chrome(DRIVER_PATH, options = options)
driver.implicitly_wait(1)

sendKey = []

def process():
    URL = 'https://www.luck-d.com'
    driver.get(URL)

    # '응모 마감 예정' div 조회
    divs = driver.find_elements_by_css_selector('section > div.gallery')
    div = divs[len(divs)-1]

    # p,a 태그 조회
    a = div.find_elements_by_css_selector('div.agent_site_info > h5 > a')
    p = div.find_elements_by_css_selector('div.agent_site_info > p')
    # print(len(p))

    for idx in range(len(p)):
        # 크롤링 정보
        store = a[idx].get_attribute('text')                    # 판매처
        endDate = getEndDate(p[idx].text)                       # 응모 마감 시간
        pre30mEndDate = getPre30EndDate(endDate)                # 응모 마감 30분전 시간
        href = a[idx].get_attribute('href')                     # 링크주소
        key = store + ' ' + href.split('/')[5] + ' ' + endDate  # 중복 발송 키 생성(판매처 + 상품명 + 마감시간)
        now = datetime.now().strftime('%m%d%H%M')               # 현재 시간

        # 응모 마감 30분전 확인
        if pre30mEndDate <= now:
            # 중복 발송 제거
            if key not in sendKey:
                # 슬랙 발송
                response = sendSlack([
                    key,
                    href,
                ])

                # 중복 방지 key 추가
                if response.status_code == 200:
                    appendSendKey(key)

    driver.quit()

def getEndDate(str):
    str_list = str.split('\n')[1].split(' ')
    str_list.pop()
    if len(str_list) == 2:
        str_list.append('2359')
    strEndDate = ''.join(re.findall("\d+", ''.join(str_list)))
    return strEndDate

def getPre30EndDate(strEndDate):
    pre30mEndDate = (datetime.strptime(strEndDate, '%m%d%H%M') - timedelta(minutes=30)).strftime('%m%d%H%M')
    return pre30mEndDate

def sendSlack(data):
    printTimeF("sned Slack!!")

    text = datetime.now().strftime('[%y/%m/%d %H:%M:%S] ' + data[0] + ' 마감 30분전' + '\n' + data[1] + '\n----------')
    print('send data = ' + text)

    SLACK_BOT_TOKEN = '<YOUR_SLACK_BOT_TOKEN>'
    CHANNEL = '<YOUR_SLACK_CHANNEL>'
    payload = {
        'channel': CHANNEL,
        'text': text
    }
    response = requests.post(
        'https://slack.com/api/chat.postMessage',
        headers = {
            'Content-Type': 'application/json', 
            'Authorization': 'Bearer ' + SLACK_BOT_TOKEN
        },
        data = json.dumps(payload)
    )
    print(response)
    return response

def readSendKey():
    global sendKey
    with open(HOME_PATH + "/sendKey.txt", 'rb') as lf:
        sendKey = pickle.load(lf)
    print('read sendKey data = ')
    print(sendKey)

def appendSendKey(key):
    sendKey.append(key)

def writeSendKey(list):
    with open(HOME_PATH + "/sendKey.txt", 'wb') as lf:
        pickle.dump(list, lf)

def removeSendKey():
    global sendKey
    removeIdx = []
    for idx in range(len(sendKey)):
        array = sendKey[idx].split(' ')
        endDate = array[len(array) - 1]
        now = datetime.now().strftime('%m%d%H%M')

        if endDate < now:
            removeIdx.append(idx)
    
    sendKey = [i for j, i in enumerate(sendKey) if j not in removeIdx]
    writeSendKey(sendKey)

def printTimeF(text):
    print(datetime.now().strftime('[%y%m/%d %H:%M:%S] ') + text)

def execute():
    printTimeF('start crawling!!')
    readSendKey()
    process()
    removeSendKey()
    printTimeF('done crawling!!')
    print('')
    
# Main
if __name__ == "__main__":
    execute()
