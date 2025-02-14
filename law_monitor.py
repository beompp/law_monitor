import requests
import smtplib
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
from email.mime.text import MIMEText

# 상수
today = datetime.today().strftime('%Y-%m-%d')
yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

# 법제처 입법예고
MOLEG = "법제처 입법예고"
MOLEG_URL = "https://www.moleg.go.kr"
MOLEG_LIST = "/lawinfo/makingList.mo"
MOLEG_DETAIL = "/lawinfo/makingInfo.mo"
molegParams = {
    'mid': 'a10104010000',
    'pageCnt': 20,
    'lsClsCd': '',
    'cptOfiOrgCd': "%EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%B5%EB%B6%80", # 국토교통부
    'keyField': 'lmNm',
    'keyWord': '',
    'stYdFmt': '',
    'edYdFmt': ''
}
param_str = '&'.join([f"{key}={value}" for key, value in molegParams.items()])

# 국토교통부 입법예고
MOLIT = "국토교통부 입법예고"
MOLIT_URL = "https://www.molit.go.kr"
MOLIT_LIST = "/USR/law/m_46/lst.jsp"
MOLIT_DETAIL = "/USR/law/m_46/"

# 국가법령정보센터
LAWGO = "국가법령정보센터"
LAWGO_URL = "https://www.law.go.kr"
LAWGO_LIST = "/LSW/lsAstSc.do?cptOfiCd=1613000"


# 법제처 입법예고 페이지 파싱
def MOLEG_PARSE():
    response = requests.get(MOLEG_URL + MOLEG_LIST, params=molegParams)
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.select('table > tbody > tr')

    results = []
    results.append(f"○ {MOLEG} ({MOLEG_URL}{MOLEG_LIST}?{param_str})")

    for row in rows:
        tds = row.select('td')
        title = tds[1].text.strip()
        start_date = tds[3].text.strip()
        detail_url = row.select('a')[0]['href'].replace('tPage', 'currentPage').replace('¤', '&')

        # 새로운 글에 대한 제목과 주소 추출
        if start_date == yesterday:
            results.append(f"   {rows.index(row) + 1}")
            results.append(f"   - 제 목: {title}")
            results.append(f"   - 시작일: {start_date}")
            results.append(f"   - 주 소: {MOLEG_URL}{detail_url}")
            results.append("")

    results.append("")  # 빈 줄 추가하여 결과 구분
    return results

# 국토교통부 입법예고 페이지 파싱
def MOLIT_PARSE():
    response = requests.get(MOLIT_URL + MOLIT_LIST)
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.select('table > tbody > tr')

    results = []
    results.append(f"○ {MOLIT} ({MOLIT_URL}{MOLIT_LIST})")

    for row in rows:
        tds = row.select('td')
        title = tds[1].text.strip()
        start_date = tds[3].text.strip().split(' ~')[0]
        detail_urls = row.select('a')[0]['href']

        # 새로운 글에 대한 제목과 주소 추출
        if start_date == yesterday:
            results.append(f"   {rows.index(row) + 1}")
            results.append(f"   - 제 목: {title}")
            results.append(f"   - 시작일: {start_date}")
            results.append(f"   - 주 소: {MOLIT_URL}{MOLIT_DETAIL}{detail_urls}")
            results.append("")

    return results

def send_email(body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = ""
    smtp_password = ""
    to_email = "beomp@solideos.com"

    msg = MIMEText(body)
    msg['Subject'] = "입법예고 정보 (" + today + ")"
    msg['From'] = smtp_user
    msg['To'] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())

def main():
    moleg_results = MOLEG_PARSE()
    molit_results = MOLIT_PARSE()
    body = "\n".join(moleg_results + molit_results)
    send_email(body)

if __name__ == "__main__":
    main()