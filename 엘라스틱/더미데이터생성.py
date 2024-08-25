import pandas as pd
from faker import Faker
import requests
import json

# CSV 파일 경로
csv_file_path = 'mortgage_loan.csv'

# CSV 파일 읽기
df = pd.read_csv(csv_file_path)

# Faker 객체 생성
fake = Faker()


# 더미 데이터 생성 함수
def generate_dummy_data(df):
    # 랜덤하게 하나의 행 선택
    row = df.sample(1).iloc[0]

    # CSV 데이터 추출
    loan_id = int(row['순번'])  # int로 변환
    loan_name = str(row['금융 상품명'])
    loan_category = str(row['대출종류명'])
    rate = str(row['평균 금리'])
    lim = row.get('대출한도', None)  # '대출한도' 컬럼이 없으면 None 반환
    if pd.notnull(lim):  # lim이 null이 아닐 때만 변환
        lim = str(lim)

    # Faker로 랜덤 데이터 생성
    memberid = fake.uuid4()
    userage = fake.random_int(min=20, max=80)

    return {
        'memberid': memberid,
        'loan_name': loan_name,
        'loan_category': loan_category,
        'loan_id': loan_id,
        'userage': userage,
        'rate': rate,
        'lim': lim
    }


# 자바 백엔드 서버 URL 설정
url = "http://localhost:8118/loanhistory/save"

# 예시: 10개의 더미 데이터 생성 및 전송
for _ in range(300):
    dummy_data = generate_dummy_data(df)

    # JSON으로 변환
    json_data = json.dumps(dummy_data)

    # POST 요청 보내기
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json_data)

    # 서버 응답 확인
    if response.status_code == 200:
        print(f"Successfully sent data: {dummy_data}")
    else:
        print(f"Failed to send data: {dummy_data}, Status code: {response.status_code}")
