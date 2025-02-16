import requests
import smtplib
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import schedule
import time

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
    'cptOfiOrgCd': "국토교통부",  # 국토교통부 %EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%A5%EB%B6%80
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
    results.append(f"○ **{MOLEG}**")
    results.append(f"  {MOLEG_URL}{MOLEG_LIST}?{param_str})")
    results.append("")

    for row in rows:
        tds = row.select('td')
        title = tds[1].text.strip()
        start_date = tds[3].text.strip()
        detail_url = row.select('a')[0]['href'].replace('tPage', 'currentPage').replace('¤', '&')

        if start_date == today:          # 오늘 새 글이 있는 경우
            results.append(f" {rows.index(row) + 1}")
            results.append(f" - 제 목: {title}")
            results.append(f" - 시작일: {start_date}")
            results.append(f" - 주 소: {MOLEG_URL}{detail_url}")
            results.append("")

    results.append("")
    return results


# 국토교통부 입법예고 페이지 파싱
def MOLIT_PARSE():
    response = requests.get(MOLIT_URL + MOLIT_LIST)
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.select('table > tbody > tr')

    results = []
    results.append(f"○ **{MOLIT}**")
    results.append(f"  {MOLIT_URL}{MOLIT_LIST}")
    results.append("")

    for row in rows:
        tds = row.select('td')
        title = tds[1].text.strip()
        start_date = tds[3].text.strip().split(' ~')[0]
        detail_urls = row.select('a')[0]['href']
        
        if start_date == today:         # 오늘 새 글이 있는 경우
            results.append(f" {rows.index(row) + 1}")
            results.append(f" - 제 목: {title}")
            results.append(f" - 시작일: {start_date}")
            results.append(f" - 주 소: {MOLIT_URL}{MOLIT_DETAIL}{detail_urls}")
            results.append("")
            
    results.append("")
    return results


# 파싱 결과 이메일 발송
def send_email(body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    with open('mailSender.txt', 'r', encoding='utf-8') as file:
        lines = []
        for line in file:
            s_line = line.strip()
            if s_line.startswith('#'):
                continue
            if ' ' in s_line:
                s_line = s_line.split(' ')[0]               # 공백 나오면 앞부분만 사용
            if '#' in s_line:
                s_line = s_line.split('#')[0].strip()       # 주석된 줄은 제외
            if s_line:
                lines.append(s_line)

        smtp_user = lines[0].strip()
        smtp_password = lines[1].strip()
        to_emails = [line.strip() for line in lines[2:]]    # 세번째 값 부터는 모두 수신자 계정

    msg = MIMEText(body)
    msg['Subject'] = "입법예고 정보 (" + today + ")"
    msg['From'] = smtp_user
    msg['To'] = ", ".join(to_emails)
    print(msg['To'])

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_emails, msg.as_string())  ## 메일 발송 ##
        print("Email sent successfully")

def main():
    moleg_results = MOLEG_PARSE()
    molit_results = MOLIT_PARSE()
    body = "\n".join(moleg_results + molit_results)
    send_email(body)


# 매일 오전 9시 00분에 main 함수 실행 예약
schedule.every().day.at("09:00").do(main)

while True:
    schedule.run_pending()  # 예약된 작업이 있는지 확인하고 실행
    time.sleep(1)           # 1초 대기