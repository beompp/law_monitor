import requests
import smtplib
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import schedule
import time
import os
import logging

# 로그 설정
logging.basicConfig(filename='law_monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 상수
today = datetime.today().strftime('%Y-%m-%d')
yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

# 국가법령정보센터
LAWGO = "국가법령정보센터 - 최신법령 - 시행법령(소관: 국토교통부)"
LAWGO_URL = "https://www.law.go.kr"
LAWGO_LIST = "/LSW/lsSc.do?menuId=1&subMenuId=23&tabMenuId=123&eventGubun=060103&query="

# 국토교통부 입법예고
MOLIT = "국토교통부 입법예고"
MOLIT_URL = "https://www.molit.go.kr"
MOLIT_LIST = "/USR/law/m_46/lst.jsp"
MOLIT_DETAIL = "/USR/law/m_46/"

# 법제처 입법예고
MOLEG = "법제처 입법예고(소관: 국토교통부)"
MOLEG_URL = "https://www.moleg.go.kr"
MOLEG_LIST = "/lawinfo/makingList.mo?mid=a10104010000&pageCnt=10&cptOfiOrgCd=%EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%B5%EB%B6%80&keyField=lmNm"
MOLEG_DETAIL = "/lawinfo/makingInfo.mo"


# 국토교통부 입법예고 페이지 파싱
def MOLIT_PARSE_INTITLE():
    logging.info("MOLIT_PARSE_INTITLE 시작")

    find_new = False        # 새로운 글이 있는지 확인
    results = []            # 본문 내용 구성
    rownum = 1              # 행 번호

    results.append(f"● {MOLIT}  /  {MOLIT_URL}{MOLIT_LIST}")
    results.append("")

    response = requests.get(MOLIT_URL + MOLIT_LIST)
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.select('table > tbody > tr')

    for row in rows:
        tds = row.select('td')
        start_date = tds[3].text.strip().split(' ~')[0]
        department_name = tds[2].text.strip()

        if start_date == today:         # 오늘 새 글이 있는 경우
            find_new = True

            detail_urls = row.select('a')[0]['href']
            detail_response = requests.get(MOLIT_URL + MOLIT_DETAIL + detail_urls)
            detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
            title = detail_soup.find('h4').text.strip()
        
            results.append(f" {rownum}")
            results.append(f" - 제 목: {title}")
            results.append(f" - 부 서: {department_name}")
            results.append(f" - 예고기간: {tds[3].text.strip().replace(' ~', ' ~ ')}")
            results.append(f" - 주 소: {MOLIT_URL}{MOLIT_DETAIL}{detail_urls}")
            results.append("")
            rownum += 1
            
    if find_new == False:
        results.append("  (없음)")
        results.append("")
            
    results.append("")
    logging.info("MOLIT_PARSE 완료")
    return results


# 국가법령정보센터 페이지 파싱
def LAWGO_PARSE():
    logging.info("LAWGO_PARSE 시작")

    element = None          # 페이지 파싱 결과
    attempts = 0            # 페이지 파싱 시도 횟수
    find_new = False        # 새로운 글이 있는지 확인
    results = []            # 본문 내용 구성
    rownum = 1              # 행 번호
    
    results.append(f"● {LAWGO}  /  {LAWGO_URL}{LAWGO_LIST}")
    results.append("")

    # Chrome 드라이버 설정
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')              # 브라우저 창을 표시하지 않음
    driver = webdriver.Chrome(service=service, options=options)

    # 페이지 로드
    driver.get(LAWGO_URL + LAWGO_LIST)
    driver.implicitly_wait(10)                      # 페이지 로딩 대기 시간 10초

    # 결과가 나올 때까지 페이지 파싱
    while (element is None or not element.find_elements(By.CSS_SELECTOR, 'tr')) and attempts < 50:  # 50번까지 시도
        try:
            element = driver.find_element(By.CSS_SELECTOR, 'table')
            if not element.find_elements(By.CSS_SELECTOR, 'tr'):
                element = None
            print(element)
            logging.info(f"페이지 로드 중: {element}")
        except Exception as e:
            time.sleep(1)
            logging.error(f"LAWGO_PARSE 실패: {e}")
            attempts += 1

    if element is None:
        driver.quit()
        results.append("파싱에러")
        logging.error("LAWGO_PARSE 실패: 파싱에러")
        return results

    logging.info(f"페이지 로드 완료: {driver.title}")

    rows = element.find_elements(By.CSS_SELECTOR, 'tr')
    for row in rows:
        tds = row.find_elements(By.CSS_SELECTOR, 'td')
        if tds:
            # print([td.text for td in tds])
            logging.info(f"행 데이터: {[td.text for td in tds]}")
            title = tds[1].text.strip()
            department_name = tds[7].text.strip()
            open_date = tds[2].text.strip().replace('. ', '-').replace('.', '')

            if open_date == today.replace('-0', '-'):                   # 공포일자가 오늘인 경우
                if department_name == '국토교통부':                      # 국토교통부만 추출
                    find_new = True
                    results.append(f" {rownum}")
                    results.append(f" - 제 목: {title}")
                    results.append(f" - 부 서: {department_name}")
                    results.append(f" - 공포일자: {tds[5].text.strip()}")
                    results.append(f" - 시행일자: {tds[2].text.strip()}")
                    results.append("")
                    rownum += 1
            
    if find_new == False:
        results.append("  (없음)")
        results.append("")

    driver.quit()

    results.append("")
    logging.info("LAWGO_PARSE 완료")
    return results


# 법제처 입법예고 페이지 파싱
def MOLEG_PARSE():
    logging.info("MOLEG_PARSE 시작")

    find_new = False        # 새로운 글이 있는지 확인
    results = []            # 본문 내용 구성
    rownum = 1              # 행 번호

    results.append(f"● {MOLEG}  /  {MOLEG_URL}{MOLEG_LIST}")
    results.append("")

    response = requests.get(MOLEG_URL + MOLEG_LIST)
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.select('table > tbody > tr')

    for row in rows:
        tds = row.select('td')
        title = tds[1].text.strip()
        department_name = tds[2].text.strip()
        start_date = tds[3].text.strip()
        end_date = tds[4].text.strip()

        detail_url = row.select('a')[0]['href'].replace('tPage', 'currentPage').replace('¤', '&').replace('국토교통부', '%EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%B5%EB%B6%80')

        if start_date == today:          # 오늘 새 글이 있는 경우
            find_new = True
            results.append(f" {rownum}")
            results.append(f" - 제 목: {title}")
            results.append(f" - 부 서: {department_name}")
            results.append(f" - 시작일자: {start_date}")
            results.append(f" - 종료일자: {end_date}")
            results.append(f" - 주 소: {MOLEG_URL}{detail_url} ")
            results.append("")
            rownum += 1
            
    if find_new == False:
        results.append("  (없음)")
        results.append("")

    results.append("")
    logging.info("MOLEG_PARSE 완료")
    return results


# 파싱 결과 이메일 발송
def send_email(body):
    logging.info("이메일 발송 시작")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    with open('/home/ec2-user/law-monitor/mailSender.txt', 'r', encoding='utf-8') as file:
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
        logging.info("이메일 발송 성공")

def shutdown_pc():
    logging.info("PC 종료")
    os.system("shutdown /s /t 1")

def main():
    logging.info("main 함수 시작")
    molit_results = MOLIT_PARSE_INTITLE()
    lawgo_results = LAWGO_PARSE()
    moleg_results = MOLEG_PARSE()
    body = "\n".join(molit_results + lawgo_results + moleg_results)
    
    send_email(body)


main()