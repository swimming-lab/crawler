# 크롤링 봇 만들기

### 1. luck-d.py
- python + selenium + requests
- 크롤링 대상 사이트 : https://www.luck-d.com
- 설명 : 나이키 신발 응모 > 응모 마감 30분 남은 신발 리스트를 선택하여 슬랙으로 알람을 보냄
- ```bash
	python luck-d.py
	```

### 2. luck-d.js
- nodejs + node-cron + axios + cheerio 
- 설명 : python으로 작성한 코드를 개선, 비즈니스 고도화한 nodejs 버전
- ```bash
	npm install
	npm start
	```
