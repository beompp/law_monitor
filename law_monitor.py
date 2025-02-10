import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 상수
today = datetime.today().strftime('%Y-%m-%d')
DEPARTMENT = "국토교통부"

# 법제처 입법예고
MOLEG_KO = "법제처 입법예고"
MOLEG_URL = "https://www.moleg.go.kr"
MOLEG_LIST = "/lawinfo/makingList.mo"
MOLEG_DETAIL = "/lawinfo/makingInfo.mo"
molegParams = {
    'mid': 'a10104010000',
    'pageCnt': 20,
    'lsClsCd': '',
    'cptOfiOrgCd': DEPARTMENT,
    'keyField': 'lmNm',
    'keyWord': '',
    'stYdFmt': '',
    'edYdFmt': ''
}

# 국토교통부 입법예고
MOLIT_KO = "국토교통부 입법예고"
MOLIT_URL = "https://www.molit.go.kr"
MOLIT_LIST = "/USR/law/m_46/lst.jsp"
MOLIT_DETAIL = "/USR/law/m_46/dtl.jsp"

# 국가법령정보센터
LAWGO_KO = "국가법령정보센터"
LAWGO_URL = "https://www.law.go.kr"
LAWGO_LIST = "/LSW/lsAstSc.do?cptOfiCd=1613000"






# 법제처 입법예고 페이지 파싱
# def MOLEG_PARSE():
#     response = requests.get(MOLEG_URL + MOLEG_LIST, params=molegParams)
#     soup = BeautifulSoup(response.content, 'html.parser')
#     rows = soup.select('table > tbody > tr')

#     for row in rows:
#         tds = row.select('td')
#         urls = row.select('a')

#         # 새로운 글에 대한 제목과 주소 추출
#         if tds[3].text.strip() == today:
#             detail_url = urls[0]['href'].replace('tPage', 'currentPage').replace('¤', '&')

#             print(f"○ {MOLEG_KO}에 새로운 글 게시")
#             print(f"   - 시작일: {tds[3].text.strip()}")
#             print(f"   - 제 목: {tds[1].text.strip()}")
#             print(f"   - 주 소: {MOLEG_URL}{detail_url}")
            

# 국토교통부 입법예고 페이지 파싱
# def MOLIT_PARSE():
response = requests.get(MOLIT_URL + MOLIT_LIST)
soup = BeautifulSoup(response.content, 'html.parser')
rows = soup.select('div.board_list > table > tbody > tr')
print(rows)

for row in rows:
    tds = row.select('td')
    urls = row.select('a')

    # 새로운 글에 대한 제목과 주소 추출
    if tds[4].text.strip() == today:
        detail_url = urls[0]['href']

        print(f"○ {MOLIT_KO}에 새로운 글 게시")
        print(f"   - 시작일: {tds[4].text.strip()}")
        print(f"   - 제 목: {tds[1].text.strip()}")
        print(f"   - 주 소: {MOLIT_URL}{detail_url}")




# 매일 오전 9시에 작업 예약
# schedule.every().day.at("09:00").do(job)
# schedule.every().minute.do(job)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
# MOLEG_PARSE()