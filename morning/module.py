import json
import requests
import pandas as pd
import re
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import time
# import openai

# open ai setting
load_dotenv()
openai_api_key = os.getenv('Chiming_morning_KEY')

# get articles
def getArticle(pid):
    data = json.dumps({"id": str(pid)})
    headers = {"Content-Type": "application/json", 'User-Agent': 'CNA-crawler-wrfAYr4ZaAXyaRu'}
    res = requests.post('https://www.cna.com.tw/cna2018api/api/ProjNews', headers=headers, data=data).json()
    return res

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

# 保存文章資料
def get_article_data(pid):
    article_data = getArticle(pid)
    news = article_data['ResultData']['News']
    return {
        'pid': news['Id'],
        'published_dt': article_data['ResultData']['MetaData']['DateCreated'],
        'h1': news['Title'],
        'article': clean_text(article_data),
        'category': news['TypeName']
    }

def process_articles(pids):
    article_data_list = []
    for pid in pids:
        article_data_list.append(get_article_data(pid))
        time.sleep(2)
    return pd.DataFrame(article_data_list)

# OpenAI API 的設置
def get_completion(messages, model="gpt-4o", temperature=0):
    payload = { "model": model, "temperature": temperature, "messages": messages}
    headers = { "Authorization": f'Bearer {openai_api_key}', "Content-Type": "application/json" }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers = headers, data = json.dumps(payload) )
    obj = json.loads(response.text)
    if response.status_code == 200:
        return obj["choices"][0]["message"]["content"]
    else:
        return obj["error"]
    

## 生成metadata
# chat gpt setting
def generate_metadata(prompt, data):
    full_prompt = prompt
    full_prompt += f"```{data['article']}```\n"
    
    messages = [
        { "role": "user", "content": full_prompt }
    ]
    return get_completion(messages)

# generate metadata prompt
def metaData(articles):
    # prompt: what happen?
    whatHappen = """
    你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
    任務 閱讀文章寫100字摘要

    1. 實體辨識 取文本內實體Entity 以人物(不包含中央社記者)、組織、事件、地名、日期、關係分組 分別條列實體
    2. 判斷新聞核心事件或議題 包含但不限 事件名稱、相關人物、關鍵事件、日期時間
    3. 寫事件摘要：150個字以內、符合新聞書寫格式

    人名第一次提到 如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用
    提及人物 有職稱 格式: 人名(職稱) 用全形括弧

    注意 最終只要印出事件摘要結果
    注意！正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    請注意！這對我的工作很重要 鎖定在我提供資料 要遵守
    """

    # prompt: what are the key facts?
    keyFacts = """
    你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
    任務 閱讀文章分條列出關鍵事件

    1. 實體辨識 取文本內實體Entity 以人物(不包含中央社記者)、組織、事件、地名、日期、關係分組 分別條列實體
    2. 判斷關鍵事件 目的要凸顯事件發生經過，包含但不限：發生事件名稱 日期 地點 時間 
    3. 分條列出關鍵事件，不要超過5點。每一關鍵事件字數100個字以內

    時間日期很重要 格式 年月日 時：分

    注意 最終只要印出關鍵事件
    注意！正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    請注意！這對我的工作很重要 鎖定在我提供資料 要遵守
    """

    # prompt: what key person say?
    stance = """
    你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
    任務 閱讀文章寫各方立場文

    1. 實體辨識 取文本內實體Entity 以人物(不包含中央社記者)、組織、事件、地名、日期、關係分組 分別條列實體
    2. 判斷各方立場文 目的在說明相關人或機構的立場、說法，包含但不限：相關人或機構名稱 說法、看法、立場
    3. 分段列出各方立場文 格式 機構或人名：100個字以內立場文

    人名第一次提到 如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用
    提及人物 有職稱 格式: 人名(職稱) 用全形括弧

    注意 最終只要印出各方立場文
    注意！正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    請注意！這對我的工作很重要 鎖定在我提供資料 要遵守
    """

    if not articles.empty:
        summary_list = []
        for index, row in articles.iterrows():
            # 使用 generate_content 生成摘要
            res_happen = generate_content(whatHappen, row)
            res_keyFact = generate_content(keyFacts, row)
            res_stance = generate_content(stance, row)

            # 將摘要結果存入 summary_list
            summary_list.append({
                "pid": row['pid'],
                "whatHappen": res_happen,
                "keyFacts": res_keyFact,
                "stance": res_stance
            })

        # 將 summary_list 轉換為 DataFrame
        summaries_df = pd.DataFrame(summary_list)
        return summaries_df
    else:
        print(f"No data to process.")
        return pd.DataFrame()

    

# for generate metadata
def generate_content(summarise, article_row):
    full_prompt = summarise + f"```{article_row['article']}```\n"
    messages = [
        { "role": "user", "content": full_prompt }
    ]
    return get_completion(messages)


# for generate summarise
def generate_abstract(summarise, meta_row):
    # 生成摘要的 prompt，基於已經處理好的摘要欄位
    full_prompt = summarise + f"""
    事件摘要: {meta_row['whatHappen']}
    關鍵事件: {meta_row['keyFacts']}
    立場文: {meta_row['stance']}
    """
    
    messages = [
        { "role": "user", "content": full_prompt }
    ]
    
    # 呼叫 OpenAI API 並返回最終摘要
    return get_completion(messages)
