from elasticsearch import Elasticsearch
from apscheduler.schedulers.blocking import BlockingScheduler
import pandas as pd
import json


def get_loan_data():
    # CSV 파일 읽기
    df = pd.read_csv('credit_loan.csv')

    # DataFrame을 JSON으로 변환
    loan_data = df.to_json(orient='records')

    return loan_data


def send_to_elasticsearch():
    # Elasticsearch 클라이언트 생성
    es = Elasticsearch("http://localhost:9200")

    # 인덱스 이름
    index_name = "credit_loan"

    # get_loan_data() 함수에서 반환된 JSON 데이터를 파싱
    loan_data = json.loads(get_loan_data())

    # 각 대출 상품 항목을 별도의 문서로 인덱싱
    for loan in loan_data:
        # es.index() 메서드를 사용하여 데이터를 엘라스틱서치에 저장
        response = es.index(index=index_name, body=loan)
        print(response)

    print("Data sent to Elasticsearch")


# 스케줄러 생성
scheduler = BlockingScheduler()

# 매 분마다 실행
scheduler.add_job(func=send_to_elasticsearch, trigger="cron", minute='*/1', id="send_loan_data")

# 스케줄러 시작
scheduler.start()
