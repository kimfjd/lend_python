from flask import request, jsonify
from elasticsearch import Elasticsearch
import pandas as pd
import numpy as np

# Elasticsearch 클라이언트 설정
es = Elasticsearch([{'scheme': 'http', 'host': '192.168.10.6', 'port': 9200}])

def get_applicable_rate(row, credit_score):
    if credit_score > 900:
        return row.get('900점 초과')
    elif credit_score >= 801:
        return row.get('801~900점')
    elif credit_score >= 701:
        return row.get('701~800점')
    elif credit_score >= 601:
        return row.get('601~700점')
    elif credit_score >= 501:
        return row.get('501~600점')
    elif credit_score >= 401:
        return row.get('401~500점')
    elif credit_score >= 301:
        return row.get('301~400점')
    else:
        return row.get('300점 이하')

def fetch_data_from_elasticsearch():
    query = {
        "query": {
            "match_all": {}
        }
    }
    try:
        response = es.search(index="credit_loan", body=query, size=10000)
        hits = response['hits']['hits']
        data = pd.json_normalize([hit['_source'] for hit in hits])
        return data
    except Exception as e:
        print(f"Error fetching data from Elasticsearch: {e}")
        return pd.DataFrame()

def recommend_loans_based_on_credit_score(credit_score, num_recommendations=5):
    data = fetch_data_from_elasticsearch()

    if data.empty:
        print("No data fetched from Elasticsearch.")
        return pd.DataFrame()

    data['적용 금리'] = data.apply(lambda row: get_applicable_rate(row, credit_score), axis=1)

    valid_loans = data[data['적용 금리'].notna() & (data['적용 금리'] != 'N/A')]

    sorted_loans = valid_loans.sort_values(by='적용 금리').head(num_recommendations)

    return sorted_loans

def recommend_loan_products():
    data = request.get_json()
    user_credit_score = data.get('credit_score')

    if user_credit_score is None:
        return jsonify({"error": "신용점수를 입력해 주세요."}), 400

    try:
        user_credit_score = float(user_credit_score)
    except ValueError:
        return jsonify({"error": "신용점수는 숫자여야 합니다."}), 400

    recommended_loans = recommend_loans_based_on_credit_score(user_credit_score)

    if not recommended_loans.empty:
        result = recommended_loans[['순번', '금융회사 명', '금융 상품명', '적용 금리', '대출종류명']].to_dict(orient='records')
        return jsonify(result)
    else:
        return jsonify({"message": "조건에 맞는 대출 상품이 없습니다."})
