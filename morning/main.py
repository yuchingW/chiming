import pandas as pd
import re
from module import *

# summarize prompt
def summarise(meta_df):
    prompt01 = """
    你是大語言模型，熟悉中央社新聞報導的語法和用字遣詞
    任務 綜合數篇文章寫100個字以內的新聞電子報摘要

    依照以下步驟執行：
    1. 讀取meta_df裡，每一個pid文章的 whatHappen、keyFacts和stance
    2. 判斷新聞的核心內容 包含但不限於：事件最新進展、爆發原因、關鍵事件日期、相關人物說法等
    3. 改寫成50-100個字新聞摘要。以新聞電子報格式書寫，先寫事件最新進展，再補充爆發原因、影響、關鍵人物說法等。

    電子報摘要格式：
    1. 寫作必須符合中央社新聞報導的語法和用字遣詞。寫完要潤稿
    2. 人名第一次提到 如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用
    3. 提及人物 有職稱 格式: 人名(職稱) 用全形括弧
    4. 時間日期很重要 格式 年月日 時：分

    注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    注意! 這對我的工作很重要 鎖定在我提供資料 要遵守
    
    最終印出電子報摘要結果
    """

    prompt02 = """
    你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
    任務 寫新聞摘要

    # 這是偽代碼
    text = meta_df['whatHappen'].itterows()
    利用text的資料改寫成一則新聞摘要：先寫事件最新進展，再補充事件爆發原因、影響、關鍵人物說法等。
    寫完必須潤稿，書寫符合中央社新聞報導語法和用字
    摘要格式：
    1. 字數50-100個字以內 
    2. 人名第一次提到 如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用
    3. 提及人物要寫：職稱人名
    4. 時間日期很重要 格式 年月日 時：分

    注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    注意! 這對我的工作很重要 鎖定在我提供資料 要遵守
    """

    
    summary1 = generate_morning(prompt01, meta_df)
    summary2 = generate_morning(prompt02, meta_df)

    # 返回兩個摘要版本的列表
    return summary1, summary2


def main():
    # 手動輸入的 URLs
    urls = [
        'https://www.cna.com.tw/news/aopl/202410035007.aspx',
        'https://www.cna.com.tw/news/aopl/202410035004.aspx',
        'https://www.cna.com.tw/news/aopl/202410030259.aspx'
    ]

    # 從 URLs 中提取 PID，並轉換為整數
    pids = [int(re.search(r'\d+', url).group()) for url in urls if re.search(r'\d+', url)]
    print(f'Extracted PIDs: {pids}')
    articles= process_articles(pids)

    # 加載 all_metadata_df
    # all_metadata_df = pd.read_csv('tno_metadata_4603.csv')
    # meta_df = all_metadata_df[all_metadata_df['pid'].isin(pids)][['pid', 'whatHappen', 'keyFacts', 'stance']]
    meta_df = metaData(articles)
    meta_df.to_csv('1004morning_metadata_usa.csv', index=False, encoding='utf-8-sig')

    if not meta_df.empty:
        summary1, summary2 = summarise(meta_df)

        # 分別印出兩個版本的摘要
        print(f"var1:{summary1}")
        print(f"\nvar2:{summary2}")
    else:
        print("無法生成摘要，meta_df 為空。")

# 執行主程式
if __name__ == "__main__":
    main()
