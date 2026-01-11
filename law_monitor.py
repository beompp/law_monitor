import requests
import smtplib
import sys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import logging

# 로그 설정
logging.basicConfig(filename='law_monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
sys.stdout.reconfigure(encoding='utf-8')


####################
#      상수        #
####################
date = datetime.today().strftime('%Y-%m-%d')  # yyyy-mm-dd
# date = '2025-12-22'
yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

# 국가법령정보센터 법령
LAWGO_BASE_URL = "https://www.law.go.kr"
LAWGO_LIST = f"{LAWGO_BASE_URL}/LSW/lsSc.do?menuId=1&subMenuId=23&tabMenuId=123&eventGubun=060103&query=*"
LAWGO_ADMRULE_LIST = f"{LAWGO_BASE_URL}/admRulSc.do?menuId=5&subMenuId=45&tabMenuId=203"

# 국토교통부 입법예고
MOLIT_BASE_URL = "https://www.molit.go.kr"
MOLIT_LIST = f"{MOLIT_BASE_URL}/USR/law/m_46/lst.jsp"
MOLIT_DETAIL = f"{MOLIT_BASE_URL}/USR/law/m_46/"

# 법제처 입법예고
MOLEG_BASE_URL = "https://www.moleg.go.kr"
MOLEG_LIST = f"{MOLEG_BASE_URL}/lawinfo/makingList.mo?mid=a10104010000&pageCnt=10&cptOfiOrgCd=%EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%B5%EB%B6%80&keyField=lmNm"

# 행안부 주민등록정보(행정구역변경)
MOIS_BASE_URL = "https://www.mois.go.kr"
MOIS_LIST = f"{MOIS_BASE_URL}/frt/bbs/type001/commonSelectBoardList.do?bbsId=BBSMSTR_000000000052"


####################
#     공통함수      #
####################
def replace_text(text, spaceYn):
    if spaceYn:
        context = text.get_text().replace("\xa0", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
    else:
        context = text.get_text(strip=True).replace("\xa0", "").replace("\n", "").replace("\r", "").replace("\t", "")
    return context

def extract_text(text):
    startIndex = text.find('■ 변경대상')
    endIndex = text.find('■ 변경내역')
    if startIndex != -1 and endIndex != -1:
        return text[startIndex + len('■ 변경대상 : '):endIndex].strip()
    return ""



# 국토교통부 입법예고 페이지 파싱
def MOLIT_PARSE_INTITLE():
    logging.info(f"국토교통부 입법예고 시작: {MOLIT_LIST}")

    findNew = False        # 새로운 글이 있는지 확인
    results = []            # 본문 내용 구성
    rownum = 1              # 행 번호
    today = date

    results.append(f"● 국토교통부 입법예고  /  {MOLIT_LIST}")
    results.append("")

    # 세움터에서 다루는 법령 목록 로드
    try:
        with open('eais_law.txt', 'r', encoding='utf-8') as f:
            lawList = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        # 파일이 없을 때 로그를 남기고 빈 결과 반환
        logging.error(f"❌ 필수 파일 없음: eais_law.txt")
        return [] 
    except Exception as e:
        # 기타 파일 읽기 에러 발생 시 처리
        logging.error(f"❌ 파일 로드 중 알 수 없는 에러 발생: {e}")
        return []

    # 파싱 시작
    try:
        response = requests.get(MOLIT_LIST)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.select('table > tbody > tr')

        for row in rows:
            tds = row.select('td')
            startDate = tds[3].text.strip().split(' ~')[0]
            departmentName = tds[2].text.strip()

            if startDate == today:         # 오늘 새 글이 있는 경우
                detailUrls = row.select('a')[0]['href']
                detailSoup = requests.get(MOLIT_DETAIL + detailUrls)
                detailSoup = BeautifulSoup(detailSoup.content, 'html.parser')
                title = detailSoup.find('h4').text.strip()

                # 오늘 날짜로 파일 내 리스트에 법령명이 존재하는지 확인
                if any(law in title for law in lawList):
                    findNew = True
                    results.append(f" {rownum}")
                    results.append(f" - 제 목: {title}")
                    results.append(f" - 부 서: {departmentName}")
                    results.append(f" - 예고기간: {tds[3].text.strip().replace(' ~', ' ~ ')}")
                    results.append(f" - 주 소: {MOLIT_DETAIL}{detailUrls}")
                    results.append("")
                    rownum += 1
                
            results.append("")

    except Exception as e:
        logging.error(f"❌ 국토교통부 입법예고 파싱 에러 발생: {e}")
        return []

    if not findNew:
        results.clear()
        logging.info("파싱 결과 없음")
            
    logging.info("국토교통부 입법예고 완료")
    return results


# 국가법령정보센터 최신법령 파싱
def LAWGO_PARSE(target):      # target: eais or privacy / 같은 함수 재사용을 위해 인자 추가
    logging.info(f"국가법령정보센터 최신법령 파싱 시작({target})")

    findNew = False
    results = []
    rownum = 1
    today = date

    # 실제 데이터 요청 주소
    url = "https://www.law.go.kr/lsScListR.do"
    
    # Query String Parameters
    params = {
        "menuId": "1",
        "subMenuId": "23",
        "tabMenuId": "121"
    }

    # Form Data
    payload = {
        "q": "*", 
        "outmax": "150",  # 한 번에 가져올 개수
        "p2": "1,2,3",
        "p4": "110401,110402,110403,110404,110405,110406,110407",
        "p19": "1,3",
        "pg": "1",
        "fsort": "21,11,31",
        "isType": "7",
        "section": "lawNm",
        "lsiSeq": "0",
        "p9": "1,2,4"
    }

    # Request Headers (서버 차단 방지용)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Referer": "https://www.law.go.kr/lsSc.do",
        "X-Requested-With": "XMLHttpRequest"
    }

    results.append(f"● 국가법령정보센터 - 최신법령 / https://www.law.go.kr/lsSc.do")
    results.append("")

    # 세움터에서 다루는 법령 목록 로드
    try:
        with open(f'{target}_law.txt', 'r', encoding='utf-8') as f:
            lawList = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        # 파일이 없을 때 로그를 남기고 빈 결과 반환
        logging.error(f"❌ 필수 파일 없음: {target}_law.txt")
        return [] 
    except Exception as e:
        # 기타 파일 읽기 에러 발생 시 처리
        logging.error(f"❌ 파일 로드 중 알 수 없는 에러 발생: {e}")
        return []

    try:
        # 파싱 시작
        response = requests.post(url, params=params, data=payload, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.select('table tr')
        for row in rows:
            cols = row.find_all('td')

            if len(cols) < 8:
                continue

            # 파일 내 리스트에 법령명이 존재하는지 확인
            title = cols[1].get_text(strip=True)
            if title in lawList:
                openDate = cols[2].get_text(strip=True).replace('. ', '-').replace('.', '')
                startDate = cols[5].get_text(strip=True).replace('. ', '-').replace('.', '')
                departmentName = cols[7].get_text(strip=True)

                if openDate == today or startDate == today:     # 공포일자 혹은 시행일자가 오늘인 경우
                    findNew = True
                    results.append(f" {rownum}")
                    results.append(f" - 제 목: {title}")
                    results.append(f" - 부 서: {departmentName}")
                    results.append(f" - 공포일자: {openDate}")
                    results.append(f" - 시행일자: {startDate}")
                    results.append("")
                    rownum += 1
        
        results.append("")

    except Exception as e:
        logging.error(f"❌ 국가법령정보센터 최신법령 파싱 에러 발생: {e}")

    if not findNew:
        results.clear()
        logging.info("파싱 결과 없음 (매칭되는 법령 없음)")

    logging.info("국가법령정보센터 최신법령 파싱 완료")
    return results


# 법제처 입법예고 페이지 파싱
def MOLEG_PARSE():
    logging.info(f"법제처 입법예고 시작: {MOLEG_LIST}")

    findNew = False        # 새로운 글이 있는지 확인
    results = []            # 본문 내용 구성
    rownum = 1              # 행 번호
    today = date

    results.append(f"● 법제처 입법예고(세움터 관련 법령)  /  {MOLEG_LIST}")
    results.append("")

    # 세움터에서 다루는 법령 목록 로드
    try:
        with open('eais_law.txt', 'r', encoding='utf-8') as f:
            lawList = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        # 파일이 없을 때 로그를 남기고 빈 결과 반환
        logging.error(f"❌ 필수 파일 없음: eais_law.txt")
        return [] 
    except Exception as e:
        # 기타 파일 읽기 에러 발생 시 처리
        logging.error(f"❌ 파일 로드 중 알 수 없는 에러 발생: {e}")
        return []

    # 파싱 시작
    try:
        response = requests.get(MOLEG_LIST)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.select('table > tbody > tr')

        for row in rows:
            tds = row.select('td')

            title = tds[1].text.strip()
            startDate = tds[3].text.strip()
            departmentName = tds[2].text.strip()
            endDate = tds[4].text.strip()
            detailUrl = row.select('a')[0]['href'].replace('tPage', 'currentPage').replace('¤', '&').replace('국토교통부', '%EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%B5%EB%B6%80')

            # 오늘 날짜로 파일 내 리스트에 법령명이 존재하는지 확인
            if any(law in title for law in lawList) and startDate == today:
                findNew = True
                results.append(f" {rownum}")
                results.append(f" - 제 목: {title}")
                results.append(f" - 부 서: {departmentName}")
                results.append(f" - 시작일자: {startDate}")
                results.append(f" - 종료일자: {endDate}")
                results.append(f" - 주 소: {MOLEG_BASE_URL}{detailUrl} ")
                results.append("")
                rownum += 1
        
        results.append("")

    except Exception as e:
        logging.error(f"❌ 법제처 입법예고 파싱 에러 발생: {e}")

    if not findNew:
        results.clear()
        logging.info("파싱 결과 없음")

    logging.info("법제처 입법예고 완료")
    return results


# 행안부 주민등록정보 페이지 파싱
def MOIS_PARSE():
    logging.info(f"행안부 행변 시작: {MOIS_LIST}")

    findNew = False        # 새로운 글이 있는지 확인
    results = []            # 본문 내용 구성
    rownum = 1              # 행 번호
    today = date.replace('-', '.') + '.'

    results.append(f"● 행정안전부 주민등록정보(행정구역변경)  /  {MOIS_LIST}")
    results.append("")

    # 파싱 시작
    try:
        response = requests.get(MOIS_LIST)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.select('table > tbody > tr')

        for row in rows:
            tds = row.select('td')
            if len(tds) >= 5:
                linkTag = tds[1].select_one('div > a')
                dateValue = tds[4].text.strip()

                # Check if '법정동' is in the text of the link tag
                if linkTag and '법정동' in linkTag.text and dateValue == today:  # 오늘 새 글이 있는 경우
                    hrefValue = linkTag['href']
                    detailSoup = requests.get(MOIS_BASE_URL + hrefValue)
                    detailSoup = BeautifulSoup(detailSoup.content, 'html.parser').find('div', id='desc_mo')

                    extracted_text = extract_text(replace_text(detailSoup, True))

                    if '(법정동(리)코드)변동사항없음' not in replace_text(detailSoup, False):
                        results.append(f" {rownum}")
                        results.append(f" - 제      목: {linkTag.text}")
                        results.append(f" - 변경대상: {extracted_text}")
                        results.append(f" - 주      소: {MOIS_BASE_URL}{hrefValue}")
                        results.append("")
                        rownum += 1
                        findNew = True
                
        results.append("")

    except Exception as e:
        logging.error(f"❌ 행안부 행변 파싱 에러 발생: {e}")

    if not findNew:
        results.clear()
        logging.info("파싱 결과 없음")

    logging.info("행안부 행변 완료")
    return results


# 국가법령정보센터 최신행정규칙 파싱
def LAWGO_ADMRULE_PARSE():
    logging.info(f"국가법령정보센터 최신행정규칙 파싱 시작: {LAWGO_ADMRULE_LIST}")

    findNew = False        # 새로운 글이 있는지 확인
    results = []            # 본문 내용 구성
    rownum = 1              # 행 번호
    today = date

    # 실제 데이터 요청 주소
    url = "https://www.law.go.kr/admRulScListR.do"
    
    # Query String Parameters
    params = {
        "menuId": "5",
        "subMenuId": "41",
        "tabMenuId": "183"
    }

    # Form Data (가장 중요한 부분)
    payload = {
        "q": "*", 
        "outmax": "150",
        "pg": "1",
        "p6": "2,3",
        "fsort": "61,21,11,31",
        "section": "admRulNm",
        "admRulSeq": "0",
        "dtlYn": "N",
        "admType": "N",
        "p15": "1,3"
    }

    # Request Headers (서버가 거절하지 않게 하는 필수 정보)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Referer": "https://www.law.go.kr/admRulSc.do",     # 이 주소를 통해 들어왔다고 알려줌
        "X-Requested-With": "XMLHttpRequest"    # AJAX 요청임을 명시
    }

    results.append(f"● 국가법령정보센터 - 최신행정규칙(기관: 개인정보보호위원회)  /  {url}")
    results.append("")

    # 개인정보보호위원회에서 다루는 행정규칙 목록 로드
    try:
        with open('privacy_admRule.txt', 'r', encoding='utf-8') as f:
            privacy_list = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        # 파일이 없을 때 로그를 남기고 빈 결과 반환
        logging.error(f"❌ 필수 파일 없음: eais_law.txt")
        return [] 
    except Exception as e:
        # 기타 파일 읽기 에러 발생 시 처리
        logging.error(f"❌ 파일 로드 중 알 수 없는 에러 발생: {e}")
        return []

    # 파싱 시작
    try:
        response = requests.post(url, params=params, data=payload, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.select('table tr')
        for row in rows:
            cols = row.find_all('td')

            if len(cols) < 8:
                continue

            title = cols[1].get_text().strip()
            if title in privacy_list:           # 개인정보보호위원회에서 다루는 행정규칙인 경우
                openDate = cols[4].get_text().strip().replace('. ', '-').replace('.', '')
                startDate = cols[5].get_text().strip().replace('. ', '-').replace('.', '')
                departmentName = cols[7].get_text().strip()

                if today == openDate or today == startDate:   # 공포일자 혹은 시행일자가 오늘인 경우
                    findNew = True
                    results.append(f"{rownum}")
                    results.append(f" - 제 목: {title}")
                    results.append(f" - 부 서: {departmentName}")
                    results.append(f" - 공포일자: {cols[4].get_text().strip()}")
                    results.append(f" - 시행일자: {cols[5].get_text().strip()}")
                    results.append("")
                    rownum += 1

        results.append("")

    except Exception as e:
        logging.error(f"❌ 국가법령정보센터 개보위 행정규칙 파싱 에러 발생: {e}")

    if not findNew:
        results.clear()
        logging.info("파싱 결과 없음")        

    logging.info("국가법령정보센터 개보위 행정규칙 파싱 완료")
    return results


# 파싱 결과 이메일 발송
def send_email(body, reciever):
    logging.info(f"send_email 시작 / {reciever}")

    if(not body):
        logging.info("메일 발송할 내용 없음")
        return

    today = date
    smtpServer = "smtp.gmail.com"
    smtpPort = 587

    try:
        with open(f'/home/ec2-user/law-monitor/mailReciever_{reciever}.txt', 'r', encoding='utf-8') as file:
        # with open(f'../mail_reciever/mailReciever_{reciever}.txt', 'r', encoding='utf-8') as file:     # 메일 발송 테스트
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

            smtpUser = lines[0].strip()
            smtpPassword = lines[1].strip()
            toEmails = [line.strip() for line in lines[2:]]    # 세번째 값 부터는 모두 수신자 계정

        msg = MIMEText(body)
        if "법정동" in body:
            msg['Subject'] = "행정구역 변경 + 입법예고 정보 (" + today + ")"
        else:
            msg['Subject'] = "입법예고 정보 (" + today + ")"
        msg['From'] = smtpUser
        msg['To'] = ", ".join(toEmails)
        print(msg['To'])


        with smtplib.SMTP(smtpServer, smtpPort) as server:
            server.starttls()
            server.login(smtpUser, smtpPassword)
            server.sendmail(smtpUser, toEmails, msg.as_string())  ## 메일 발송 ##
            print("Email sent successfully")
            logging.info("이메일 발송 성공")

    except FileNotFoundError:
        # 파일이 없을 때 로그를 남기고 빈 결과 반환
        logging.error(f"❌ 필수 파일 없음: mailReciever_{reciever}.txt")
        return [] 
    except Exception as e:
        logging.error(f"❌ 이메일 발송 중 에러 발생: {e}")
        return []


def main():
    logging.info("==============================")
    logging.info("main 함수 시작")
    logging.info("==============================")

    # 국토부 EAIS 파싱
    molit = MOLIT_PARSE_INTITLE()       # 국토교통부 입법예고
    lawgo = LAWGO_PARSE("eais")         # 국가법령정보센터 최신법령
    moleg = MOLEG_PARSE()               # 법제처 입법예고
    mois = MOIS_PARSE()                 # 행안부 행정구역변경
    eaisBody = "\n".join(molit + lawgo + moleg + mois)

    # 개인정보보호위원회 파싱
    lawgoPrivacy = LAWGO_PARSE("privacy")     # 국가법령정보센터 최신법령
    lawgoPrivacyRule = LAWGO_ADMRULE_PARSE()   # 국가법령정보센터 최신행정규칙
    privacyBody = "\n".join(lawgoPrivacy + lawgoPrivacyRule)

    # 이메일 발송
    send_email(eaisBody, "eais")
    send_email(privacyBody, "privacy")

main()