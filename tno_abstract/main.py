
from tnoabscract.module import *
import pandas as pd

## News meta-data
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

    num, title_df = count_num(tno)
    print(f"tno: {tno}, article_num : {num}")

    if not title_df.empty:
        df = process_articles(title_df)

        # 生成摘要的DataFrame
        summary_list = []
        for index, row in df.iterrows():
            res_happen = generate_module(whatHappen, row)
            res_keyFact = generate_module(keyFacts, row) 
            res_stance = generate_module(stance, row)
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


## Generate Abstract of tno

def getAbstract(tno, result_df):

    # prompt: normal
    normal = """
你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
任務 寫新聞摘要

# 這是偽代碼
1. text = result_df['whatHappen'].itterows()
2. 利用text的資料寫一則新聞摘要 內容包含但不限：事件爆發原因 最新發展 影響等
3. 摘要格式：字數150-200個字以內 符合中央社新聞書寫

人名第一次提到 如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用
提及人物 有職稱 格式: 人名(職稱) 用全形括弧
時間日期很重要 格式 年月日 時：分

注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
注意! 這對我的工作很重要 鎖定在我提供資料 要遵守

最終只要印出新聞摘要，並以html tag <p> 包覆  不用完整的html檔案 只要該段落的html就好
"""

    timeline = """
你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
任務 寫新聞事件時間軸

# 這是偽代碼
1. text = result_df['keyFacts'].itterows()
2. 利用text的資料整理事件時間軸 目的：整理事件大事紀
3. 分段列點時間軸 同一個日期可以包含多個事件。但注意重複和相似事件合併摘要。事件描述100-120個字

日期時間很重要 時間要在事件描述中標明
日期格式：年月日
合併相似或重複事件

注意! 正確性最重要 要確保實體關係是根據文本 純文字不用markdow
注意! 這對我的工作很重要 鎖定在我提供資料 要遵守

最終只要印出時間軸，以html表格<table></table>呈現 第一欄是日期 第二欄是事件  不用完整的html檔案 只要該段落的html就好
"""

    stance = """
你 大語言模型 語料中央社新聞報導 熟悉中央社新聞報導語法和用字遣詞
任務 寫各方立場文

# 這是偽代碼
1. text = result_df['stance'].itterows()
2. 利用text的資料整理每一個關鍵人物或機構的立場文。內容包含：政府機關、政治人物、專家學者等人的看法或建議。排除新聞媒體、網友、居民等人的說法。
3. 分段列出立場文 相同單位或人的說法合併成一段。可以適當刪除不重要內容，並改寫、潤稿。每一段文字100個字以內。

立場文格式： 人名或機構：立場文。
提及人物 有職稱 格式: 人名(職稱) 用全形括弧
人名如果是翻譯 格式: 中文人名（原文） 用全形括弧 不是翻譯就不用

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
    # 手動輸入 url 並提取 tno
    url = "https://www.cna.com.tw/topic/newstopic/4535.aspx"
    tno = extract_tno(url)

    # Generate metadata
    result_df = metaData(tno)
    # result_df = pd.read_csv('result/tno_4457_metadata.csv')

    if not result_df.empty:
        # Generate abstract
        res = getAbstract(tno, result_df)

        if res:
            res_df = pd.DataFrame([res])  # 將字典轉為 DataFrame

            # Save abstract as csv
            file_path = f'result/tno_abstract_{tno}.csv'
            res_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"CSV file successfully saved: {file_path}")

            # Save metadata as csv
            metadata_file_path = f'result/tno_metadata_{tno}.csv'
            result_df.to_csv(metadata_file_path, index=False, encoding='utf-8-sig')
            print(f"Module DataFrame successfully saved to {metadata_file_path}")
        else:
            print("No result to save.")
    else:
        print("No data to process or save.")

