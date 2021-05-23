from selenium import webdriver
from datetime import datetime, timedelta
import requests
import json
import re
import pickle

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--remote-debugging-port=9222")

homePath = '<YOUR_PATH>'
driverPath = '<YOUR_PATH>/chromedriver'
driver = webdriver.Chrome(driverPath, options=options)
driver.implicitly_wait(1)

sendKey = []

def luckeydraw():
    url = 'https://www.luck-d.com'
    driver.get(url)

    # 응모마감예정
    div = driver.find_elements_by_css_selector('section > div.gallery')
    gallery = div[len(div)-1]

    # 내용가져오기
    a = gallery.find_elements_by_css_selector('div.agent_site_info > h5 > a')
    p = gallery.find_elements_by_css_selector('div.agent_site_info > p')

    print(len(p))

    for idx in range(len(p)):
        store = a[idx].get_attribute('text')
        endDate = getEndDate(p[idx].text)
        pre30mEndDate = getPre30EndDate(endDate)
        href = a[idx].get_attribute('href')
        key = store + ' ' + href.split('/')[5] + ' ' + endDate
        now = datetime.now().strftime('%m%d%H%M')

        if pre30mEndDate <= now:
            if key not in sendKey:
                response = sendSlack([
                    key,
                    href,
                ])
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

def appendSendKey(key):
    sendKey.append(key)

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
    with open(homePath + "/sendKey.txt", 'rb') as lf:
        sendKey = pickle.load(lf)
    print('read sendKey data = ')
    print(sendKey)

def writeSendKey(list):
    with open(homePath + "/sendKey.txt", 'wb') as lf:
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
    luckeydraw()
    removeSendKey()
    printTimeF('done crawling!!')
    print('')
    
## Main
if __name__ == "__main__":
    execute()
