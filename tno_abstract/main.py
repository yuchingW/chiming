# import json
import pandas as pd
# import time
# from datetime import datetime
from tnoabscract.module import *

## 生成摘要
def metaData(tno):
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

    # # prompt: why important?
    # whyImportant = """
    # 你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
    # 任務 摘要事件重要性

    # 1. 實體辨識 取文本內實體Entity 以人物(不包含中央社記者)、組織、事件、地名、日期、關係分組 分別條列實體
    # 2. 列出事件重要性 目的：告訴讀者事件對台灣、國際或城市的影響
    # 3. 寫重要性摘要 100-150個字，符合新聞書寫格式

    # 注意 最終只要印出重要性摘要
    # 注意！正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    # 請注意！這對我的工作很重要 鎖定在我提供資料 要遵守
    # """

    # # prompt : what data?
    # data = """
    #  你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
    # 任務 統整文章中證據資料

    # 1. 實體辨識 取文本內實體Entity 以人物(不包含中央社記者)、組織、事件、地名、日期、關係分組 分別條列實體
    # 2. 找出證據資料 包括但不限：數據、相關報告、證據等資料
    # 3. 分條列出證據資料，標明證據的資料來源，可能是機構或人

    # 注意 最終只要印出證據資料
    # 注意！正確性最重要 要確保實體關係是根據文本 純文字不用markdow
    # 請注意！這對我的工作很重要 鎖定在我提供資料 要遵守
    # """

    num, title_df = count_num(tno)
    print(f"tno: {tno}, article_num : {num}")

    if not title_df.empty:
        df = process_articles(title_df)

        # 生成摘要的DataFrame
        summary_list = []
        for index, row in df.iterrows():
            res_happen = generate_metadata(whatHappen, row)
            res_keyFact = generate_metadata(keyFacts, row) 
            res_stance = generate_metadata(stance, row)
            print(f"pid: {row['pid']}")

            # 將摘要和關鍵事件添加到summary_list
            summary_list.append({
                "tno": tno,
                "pid": row['pid'],
                "whatHappen": res_happen,
                "keyFacts": res_keyFact,
                "stance": res_stance
            })
        
        # 將摘要數據轉換為 DataFrame
        summaries_df = pd.DataFrame(summary_list)

        # 返回包含摘要的DataFrame
        return summaries_df
    else:
        print(f"No data to process for tno: {tno}")
        return pd.DataFrame()


def count_num(tno):
    title_data = getTopic(tno)
    num = len(title_data['ResultData']['Items'])
    title_df = get_title_data(title_data)
    return num, title_df


def getAbstract(tno, result_df):
    # prompt: normal
    normal = """
你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
任務 寫新聞摘要

# 這是偽代碼
text = result_df['whatHappen'].itterows()
利用text的資料改寫成一則新聞摘要：先寫事件最新進展，再補充事件爆發原因、影響、關鍵人物說法等。
寫完必須潤稿，書寫符合中央社新聞報導語法和用字
摘要格式：
1. 字數150-200個字以內 
2. 人名第一次提到 如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用
3. 提及人物 有職稱 格式: 人名(職稱) 用全形括弧
4. 時間日期很重要 格式 年月日 時：分

注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
注意! 這對我的工作很重要 鎖定在我提供資料 要遵守

最終只要印出新聞摘要，並以html tag <p> 包覆  不用完整的html檔案 只要該段落的html就好
"""

    timeline = """
你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
任務 寫新聞事件時間軸

# 這是偽代碼
text = result_df['keyFacts'].itterows()
利用text的資料整理時間軸：依照日期先後排序，並用50-100個字摘要發生事件，可適當合併相似或重複事件。
時間軸整理完必須潤稿，書寫符合中央社新聞報導語法和用字

時間軸格式：
1. 時間軸一定要以事件發生日期舊到新排序，再列點事件摘要。
2. 時間很重要，必須在事件描述中標明
3. 日期格式：年月日


注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
注意! 這對我的工作很重要 鎖定在我提供資料 要遵守

最終只要印出時間軸，以html表格<table></table>呈現 第一欄是日期 第二欄是事件  不用完整的html檔案 只要該段落的html就好
"""

    stance = """
你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
任務 寫各方立場文

# 這是偽代碼
text = result_df['stance'].itterows()
利用text的資料整理每一個關鍵人物或機構的立場文：包含 政府機關、政治人物、專家學者等人的看法或建議，但排除新聞媒體、網友、居民等的說法。
相同單位或人的說法合併成一段，可適當刪除不重要內容並改寫
立場文整理完必須潤稿，書寫符合中央社新聞報導語法和用字

立場文格式：人名或機構：立場文
1. 每一段文字100個字以內
2. 提及人物 有職稱 格式: 人名(職稱) 用全形括弧
3. 人名如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用

注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
注意! 這對我的工作很重要 鎖定在我提供資料 要遵守

最終只要印出各方立場文，列點請使用html tag <ul> 和 <li> ，文字請用<p> 包覆 不用完整的html檔案 只要該段落的html就好
"""


    num, _= count_num(tno)
    print(f"tno: {tno}, article_num : {num}")

    # generate abstract and save as json
    if not result_df.empty:

        res_normal = generate_content(normal, result_df, 'whatHappen')
        print(res_normal)
        res_timeline = generate_content(timeline, result_df, 'keyFacts')
        res_stance = generate_content(stance, result_df, 'stance')

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_dict = {
            "tno": tno,
            "normal": res_normal,
            "timeline": res_timeline,
            "stance": res_stance,
            "article_num": int(num),
            "updateDt": date
        }
        return result_dict
        
    else:
        print(f"No data to process for tno: {tno}")
        return False



### MAIN
if __name__ == "__main__":

    #手動輸入 url 並提取 tno
    url = "https://www.cna.com.tw/topic/newstopic/4587.aspx"
    tno = extract_tno(url)

    # Generate metadata
    result_df = metaData(tno)
    # result_df = pd.read_csv('result/tno_4590_metadata.csv')

    if not result_df.empty:
        # Generate abstract
        res = getAbstract(tno, result_df)

        if res:
            res_df = pd.DataFrame([res])  # 將字典轉為 DataFrame

            # Save abstract as csv
            file_path = f'results/tno_abstract_{tno}.csv'
            res_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"CSV file successfully saved: {file_path}")

            # Save metadata as csv
            metadata_file_path = f'results/tno_metadata_{tno}.csv'
            result_df.to_csv(metadata_file_path, index=False, encoding='utf-8-sig')
            print(f"Module DataFrame successfully saved to {metadata_file_path}")
        else:
            print("No result to save.")
    else:
        print("No data to process or save.")