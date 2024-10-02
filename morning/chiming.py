import pandas as pd
import re
from module import process_articles, metaData, generate_abstract  # 修正導入的函數

# summarize prompt
def summarise(meta_df):
    summarize_prompt = """
    你是大語言模型，熟悉中央社新聞報導的語法和用字遣詞
    任務 綜合數篇文章寫100個字以內的新聞摘要

    依照以下步驟執行：
    1. 讀取meta_df裡，每一個pid文章的資料。以whatHappen為主、keyFacts和stance為輔。
    2. 判斷新聞的核心內容 包含但不限於：事件、爆發原因、時間、相關人物、最新進展等
    3. 改寫成50個字新聞摘要。寫作風格必須符合新聞電子報，記得潤稿。

    人名第一次提到 如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用
    提及人物 有職稱 格式: 人名(職稱) 用全形括弧
    時間日期很重要 格式 年月日 時：分

    注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    注意! 這對我的工作很重要 鎖定在我提供資料 要遵守
    
    最終印出摘要結果
    """

    # 準備存儲摘要結果的列表
    final_summary_list = []

    # 針對 meta_df 的每一行生成摘要
    for index, row in meta_df.iterrows():
        final_summary = generate_abstract(summarize_prompt, row)
        final_summary_list.append(final_summary)

    # 返回所有生成的摘要
    return final_summary_list

def main():

    # 手動輸入的 URLs
    urls = [
        'https://www.cna.com.tw/news/asoc/202410010181.aspx',
        'https://www.cna.com.tw/news/asoc/202410010350.aspx',
        'https://www.cna.com.tw/news/asoc/202410010309.aspx',
        'https://www.cna.com.tw/news/asoc/202410010027.aspx'
    ]

    # 從 URLs 中提取 PID
    pids = [re.search(r'\d+', url).group() for url in urls if re.search(r'\d+', url)]
    print(f'pids: {pids}')

    # 透過 PID 處理文章並生成資料
    articles = process_articles(pids)

    # 使用 metaData 函數將文章資料結構化
    meta_df = metaData(articles) 
    meta_df.to_csv('1002test_morning_metadata.csv', index=False, encoding='utf-8-sig') 

    # 如果 meta_df 非空，進行摘要生成
    if not meta_df.empty:
        final_summary = summarise(meta_df)
        print(final_summary)  # 印出所有摘要
    else:
        print("無法生成摘要，meta_df 為空。")

# 執行主程式
if __name__ == "__main__":
    main()

