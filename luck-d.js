// import dotenv from 'dotenv';
// dotenv.config();
import axios from 'axios';
import { load } from 'cheerio';
import fs from 'fs/promises';
import dateformat from 'dateformat';
import cron from 'node-cron';

const URL = 'https://www.luck-d.com';
const SLACK_TOKEN = 'T021VL39UH4/B04KS8KG3LG/7b4ulVhX2OpUrYYBhplOqSKf';
const KEY_JSON = 'keys.json';
let KEYS = [];

// console.log(process.env.SLACK_TOKEN);

const _parseHTML = async (url) => {
	try {
		return load((await axios.get(url)).data);
	} catch (err) {
		console.log(err);
	}
}

// const _getProductName = async (url) => {
// 	const $ = await _parseHTML(url);
// 	return $('.page_title').text();	
// }

const _getEndDate = (list) => {
	list.pop();	// '마감' 텍스트 제거
	if (list.length == 2) list.push('2359'); // 00시00분에 끝나는 시간은 23시59분으로 고정

	const date = new Date();
	const dateString = list.join('').replace(/[^0-9]/g, '')
	return `${date.getFullYear()}-${dateString.substring(0, 2)}-${dateString.substring(2, 4)} ${dateString.substring(4,6)}:${dateString.substring(6)}`;
}

const _getPre30mEndDate = (endDate) => {
	const date = new Date(endDate);
	date.setMinutes(date.getMinutes() - 30); // 마감 30분전
	return dateformat(date, 'yyyy-mm-dd HH:MM');
}

const _getNowDate = () => {
	return dateformat(new Date(), 'yyyy-mm-dd HH:MM');
}

const crawling = async () => {
	const $ = await _parseHTML(URL);
	const releaseCards = $('.release_agentsite_layer .raffle_layer').find('.release_card');

	const result = [];
	console.log(`크롤링: ${releaseCards.length}`);

	const promises = releaseCards.map(async (index, node) => {
		const seller = $(node).find('.agentsite_name').text();
		const productName = $(node).find('.product_name .text').text();
		const href = $(node).find('.release_card_inner').attr('onclick').split('=')[1].replaceAll('\'', '');
		const productId = href.split('/')[3];
		const endDate = _getEndDate($(node).find('.release_time .text').text().split('\n')[2].trim().split(' '));
		const pre30m = _getPre30mEndDate(endDate);
		const nowDate = _getNowDate();
		const key = `${seller}_${productId}_${endDate}`;

		if (!existKeys(key) && nowDate >= pre30m) {
			// const productName = await _getProductName(URL + href);
			result.push({
				key: key,
				seller: seller,
				link: URL + href,
				productId: productId,
				productName: productName,
				endDate: endDate,
			});
		}
	});
	await Promise.all(promises);

	return result;
}

const _orderBySellerDesc = async (arr) => {
	// 국내 판매처가 텍스트로 노출되기 위해 seller 내림차순 정렬
	arr.sort((a, b) => {
		const upperCaseA = a.seller.toUpperCase();
		const upperCaseB = b.seller.toUpperCase();

		if (upperCaseA < upperCaseB) return 1;
		if (upperCaseA > upperCaseB) return -1;
		if (upperCaseA === upperCaseB) return 0;
	});
}

const sendSlack = async (dataList) => {
	await _orderBySellerDesc(dataList);
	let text = `[${_getNowDate()}] ${dataList[0].seller} ${dataList.length > 1 ? `외 ${dataList.length-1}건` : ``} 마감 30분전\n`;
	dataList.forEach(element => {
		text += `- ${element.seller}: ${element.productName}\n`;
	});
	text += `${dataList[0].link}\n`;

	const result = await axios.post(`https://hooks.slack.com/services/${SLACK_TOKEN}`, {
        text: text
	}, {
		headers: {
			'Content-type': 'application/json'
		}
	});

	if (result.status == 200) return true;
	console.error(`슬랙 발송 실패!`);
	return false;
}

const readKeys = async () => {
	try {
		const data = await fs.readFile(KEY_JSON, { encoding: 'utf8' });
		KEYS = JSON.parse(data);
	} catch (err) {
		console.log(err);
	}
}

const writeKeys = async (dataList = []) => {
	try {
		KEYS.push(...dataList);
		await fs.writeFile(KEY_JSON, JSON.stringify(KEYS), 'utf8');
	} catch (err) {
		console.log(err);
	}
}

const updateKeys = async () => {
	const nowDate = _getNowDate();
	KEYS = KEYS.filter(element => element.endDate >= nowDate);
	writeKeys();
}

const existKeys = (key) => {
	return KEYS.findIndex(data => data.key === key) > -1;
}

const process = async () => {
	await readKeys();
	const resultList = await crawling();
	console.log(`마감 30분전: ${resultList.length}`);
	if (resultList.length > 0) {
		const result = await sendSlack(resultList);
		if (result) await writeKeys(resultList);
	}
	await updateKeys();
}
// await process();
const task = cron.schedule('* * * * *', async () => {
	console.log(`[${_getNowDate()}] cronjob 실행`);
	await process();
	console.log(`[${_getNowDate()}] cronjob 종료`);
}, {
	scheduled: false
});
task.start();