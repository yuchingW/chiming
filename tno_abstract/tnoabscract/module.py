import re
import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv('Chiming_abstract_KEY')


# 提取 tno 函數
def extract_tno(url):
    pattern = r'/topic/newstopic/(\d+)\.aspx'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None

# 根據 tno 獲取所有文章 id
def getTopic(tno):
    data = json.dumps({"tno": str(tno), "action": "0"})
    headers = {"Content-Type": "application/json", 'User-Agent': 'CNA-crawler-wrfAYr4ZaAXyaRu'}
    res = requests.post('https://www.cna.com.tw/cna2018api/api/ProjTopic', headers=headers, data=data).json()
    return res

# 設定錯誤判斷: 當tno不存在
class DataStructureError(Exception):
    pass

def get_title_data(title_data):
    if 'ResultData' in title_data and 'Items' in title_data['ResultData']:
        return pd.DataFrame([
            {'pid': i['Id'], 'published_dt': i['CreateTime'], 'h1': i['HeadLine']}
            for i in title_data['ResultData']['Items']
        ])
    else:
        print("Error: Unexpected data structure from getTopic")
        raise DataStructureError("Error: Unexpected data structure from getTopic")

# 根據 pid 獲取文章數據
def getArticle(pid):
    data = json.dumps({"id": str(pid)})
    headers = {"Content-Type": "application/json", 'User-Agent': 'CNA-crawler-wrfAYr4ZaAXyaRu'}
    res = requests.post('https://www.cna.com.tw/cna2018api/api/ProjNews', headers=headers, data=data).json()
    return res

# 計算 extender
def extender_counter(res):
    if 'ResultData' in res and 'News' in res['ResultData']:
        return len([url for photo in res['ResultData']['News']['Photos']
                    if photo.get('iType') == 'extender'
                    for url in photo.get('Photo', '').split('|$@$|')])
    return 0

# 計算文章日期
def story_dt_cnt(res):
    article_dt = datetime.strptime(res['ResultData']['MetaData']['DateCreated'], '%Y/%m/%d %H:%M')
    story_day = re.search(r'\d{1,2}日', res['ResultData']['News']['Content'][:40])
    story_day = int(story_day[0][:-1]) if story_day else article_dt.day
    return article_dt + timedelta(days=story_day - article_dt.day)

# 轉換日期名詞
def date_noun_converter(story_dt, text):
    date_nouns = {
        '前天': lambda dt: f"前天（{dt+timedelta(days=-2):%Y年%m月%d日}）",
        '昨天': lambda dt: f"昨天（{dt+timedelta(days=-1):%Y年%m月%d日}）",
        '今天': lambda dt: f"今天（{dt:%Y年%m月%d日}）",
        '明天': lambda dt: f"明天（{dt+timedelta(days=1):%Y年%m月%d日}）",
        '明後天': lambda dt: f"明後天（{dt+timedelta(days=1):%Y年%m月%d日}、{dt+timedelta(days=2):%Y年%m月%d日}）",
        '本月': lambda dt: f"本月{dt:%m月}",
        '上個月': lambda dt: f"上個月（{dt + relativedelta(months=-1):%m月}）",
        '下個月': lambda dt: f"下個月（{dt + relativedelta(months=+1):%m月}）",
        '今年': lambda dt: f"今年（{dt:%Y年}）",
        '去年': lambda dt: f"去年（{dt + relativedelta(years=-1):%Y年}）",
        '明年': lambda dt: f"明年（{dt + relativedelta(years=1):%Y年}）",
    }
    for key, func in date_nouns.items():
        text = text.replace(key, func(story_dt))
    return text

# 清理文章內容
def clean_text(res):
    strip_info = r'(（中央社[\w／、]{4,35}(專*電|報導|稿)）|[（(][\w／\/:： ]*[）)]\d{0,8}$)'
    story_dt = story_dt_cnt(res)
    news_content = res['ResultData']['News']['Content']
    paragraphs = re.sub(strip_info, '', BeautifulSoup(news_content.replace('(*#*)', ''), 'html.parser').text)
    return date_noun_converter(story_dt, paragraphs)

# 保存文章數據
def get_article_data(pid):
    article_data = getArticle(pid)
    news = article_data['ResultData']['News']
    return {
        'pid': news['Id'],
        'published_dt': article_data['ResultData']['MetaData']['DateCreated'],
        'h1': news['Title'],
        'article': clean_text(article_data),
        'extender': extender_counter(article_data),
        'category': news['TypeName']
    }

def process_articles(title_df):
    article_data_list = []
    for pid in title_df['pid']:
        article_data_list.append(get_article_data(pid))
        time.sleep(2)
    return pd.DataFrame(article_data_list)

# 計算加權分數
def calculate_weighted_scores(df):
    df['ex_score'] = df['extender'] * 1.5
    date_counts = df['published_dt'].value_counts().sort_values(ascending=False)
    date_weights = {date: len(date_counts) - i for i, date in enumerate(date_counts.index)}
    df['weighted_score'] = df.apply(lambda row: row['ex_score'] + date_weights[row['published_dt']], axis=1)
    df = df.sort_values('weighted_score', ascending=False)
    df_filtered = df[df['weighted_score'] > df['weighted_score'].max() / 2]
    return df_filtered

# OpenAI API 的設置
def get_completion(messages, model="gpt-4o", temperature=0):
    payload = { "model": model, "temperature": temperature, "messages": messages}
    headers = { "Authorization": f'Bearer {openai_api_key}', "Content-Type": "application/json" }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers = headers, data = json.dumps(payload) )
    obj = json.loads(response.text)
    if response.status_code == 200:
        return obj["choices"][0]["message"]["content"]
    else:
        print(obj["error"])
        return obj["error"]

# 生成內容
def generate_content(prompt, data, colName):
    full_prompt = prompt
    for index, row in data.iterrows():
        full_prompt += f"```{row[colName]}```\n"
    messages = [
        { "role": "user", "content": full_prompt }
    ]
    return get_completion(messages)

# 生成module
def generate_metadata(prompt, data):
    full_prompt = prompt
    full_prompt += f"```{data['article']}```\n"
    
    messages = [
        { "role": "user", "content": full_prompt }
    ]
    return get_completion(messages)

    

# Google Spreadsheet 的設置
# def sheetAuth(authFilePath):
#     scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
#     credentials = Credentials.from_service_account_file(authFilePath, scopes=scopes)
#     gc = gspread.authorize(credentials)
#     return gc

# def update_or_insert(authFilePath, fileId, sheet, data):
#     gc = sheetAuth(authFilePath)
#     file = gc.open_by_key(fileId)
#     worksheet = file.worksheet(sheet)

#     # 獲取工作表的標題行
#     header = worksheet.row_values(1)

#     # 確保所有必要欄位都存在
#     required_columns = ["tno", "摘要", "時間軸", "立場摘要", "更新時間", "更新次數"]
#     for column in required_columns:
#         if column not in header:
#             raise ValueError(f"工作表中未找到 '{column}' 欄位。")

#     # 構建要更新的資料
#     tno = data.get('tno')
#     if not tno:
#         raise ValueError("Data must contain 'tno' field.")

#     # 查找 tno 是否存在
#     tno_index = header.index("tno") + 1  # Google Sheets API 是 1-based 索引
#     cell_values = worksheet.col_values(tno_index)  # 根據 "tno" 欄位找到對應列

#     if tno in cell_values:
#         row = cell_values.index(tno) + 1

#         # 更新現有行的資料
#         existing_data = worksheet.row_values(row)

#         # 計算更新次數
#         update_count_index = header.index("更新次數")
#         existing_count = int(existing_data[update_count_index]) if existing_data[update_count_index] else 0
#         new_count = existing_count + 1

#         # 構建更新的資料
#         update_data = [data.get(key, '') for key in header]
#         update_data[update_count_index] = new_count
#         update_data[header.index("更新時間")] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         # 構建更新範圍
#         cell_range = f"A{row}:{chr(65 + len(header) - 1)}{row}"
#         worksheet.update(cell_range, [update_data])
#     else:
#         # 在最後一行插入新資料
#         new_row = [data.get(key, '') for key in header]

#         # 設置「更新次數」為1
#         new_row[header.index("更新次數")] = 1
#         # 設置「更新時間」為當前時間
#         new_row[header.index("更新時間")] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         worksheet.append_row(new_row)


