# 법개정 모니터링 프로그램

내용: 법제처 입법예고 게시판에 국토교통부 소관의 입법예고 글이 나에게 메일을 보내도록 작업
  - https://www.moleg.go.kr/lawinfo/makingList.mo?currentPage=1&lsClsCd=&cptOfiOrgCd=%EA%B5%AD%ED%86%A0%EA%B5%90%ED%86%B5%EB%B6%80&keyField=lmNm&keyWord=&stYdFmt=&edYdFmt=&mid=a10104010000&pageCnt=10

조건:
  1. (완료) 하루 한번 수행(오전 9시)
  2. (완료) 구글 메일서버 사용해서 회사 메일로 내용 전송
  3. (완료) 시작일자값이 당일인 자료에 대해 메일을 보내도록
     - (완료) 일자 빼고 부서 나오게 수정
  4. (완료) 검색조건에 소관부처로 국토교통부 지정
  5. (완료) 법제처 주소 하이퍼링크 되도록
  6. (완료) aws 무료 티어 서버 구축해서 올려두고 관리
  7. 게시글 제목 누르면 바로 링크 연결되도록
  8. (완료) 국토부 입법예고 게시글 상세페이지에서 제목 불러오도록
    - 제목을 잘라서 올리고 있음
  9. 법령정보센터 글 150개 조회해서 목록 찾아올 수 있도록
    - form 데이터에 outmax: 150 추가해서 던지고 결과 받을 수 있도록
  10. 행안부 행정구역변경 게시판 파싱 추가
  
  
  
"q: *
    outmax: 150
    p2: 3
    p18: 0
    p19: 1,3
    pg: 1
    fsort: 50,41
    csq: 1613000
    lsType: 8
    section: lawNm
    lsiSeq: 0
"
---------------
2025.02.13.
국토부 입법예고 추가
  - https://www.molit.go.kr/USR/law/m_46/lst.jsp

---------------
2025.02.18.
국가법령정보센터 - 최신법령 - 시행법령 추가
  - 국토부가 소관부처인 내용만 조회
  - https://www.law.go.kr/lsSc.do?menuId=1&subMenuId=23&tabMenuId=123&query=

---------------
2025.02.19.
실행 로그 기록하도록 수정 (law_monitor.log)

---------------
2025.02.23.
국토부 입법예고 상세페이지 가서 제목 불러오도록 수정

---------------
2025.02.25.
AWS에서 mailSender.txt 파일 절대경로로 읽어오도록 수정

---------------
2025.05.17.
행안부 행정구역변경 게시판 파싱 추가


