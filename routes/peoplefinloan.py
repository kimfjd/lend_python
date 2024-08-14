from flask import request, jsonify
from elasticsearch import Elasticsearch
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Elasticsearch 설정
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

# 인덱스명
index_name = 'peoplefinloan'

# 데이터 로드 및 전처리 함수
def load_data_from_elasticsearch():
    query = {
        "size": 10000,
        "_source": ["순번", "금융 상품명", "전처리 대출 한도", "전처리 이자율", "전처리 최대 상환 기간"]
    }
    res = es.search(index=index_name, body=query)
    data = [doc['_source'] for doc in res['hits']['hits']]
    df = pd.DataFrame(data)

    # 데이터 타입 변환 및 결측값 처리
    df['순번'] = pd.to_numeric(df['순번'], errors='coerce')
    df['전처리 대출 한도'] = pd.to_numeric(df['전처리 대출 한도'], errors='coerce')
    df['전처리 이자율'] = pd.to_numeric(df['전처리 이자율'], errors='coerce')
    df['전처리 최대 상환 기간'] = pd.to_numeric(df['전처리 최대 상환 기간'], errors='coerce')
    df = df.dropna().reset_index(drop=True)

    return df

# 대출 상품과 비슷한 추천 상품을 찾는 함수 정의
def get_loan_similarity(data, loan_index, num_recommendations=5):
    selected_loan = data.iloc[loan_index][['전처리 대출 한도', '전처리 이자율', '전처리 최대 상환 기간']].values.reshape(1, -1)
    all_loans = data[['전처리 대출 한도', '전처리 이자율', '전처리 최대 상환 기간']].values
    similarity_scores = cosine_similarity(selected_loan, all_loans).flatten()
    similar_loan_indices = similarity_scores.argsort()[::-1][1:num_recommendations + 1]
    return data.iloc[similar_loan_indices]

def recommend_loans():
    try:
        loan_number = int(request.json['loan_number'])
    except (ValueError, KeyError):
        return jsonify({"error": "유효하지 않은 입력입니다. 숫자를 입력해 주세요."}), 400

    data = load_data_from_elasticsearch()

    if loan_number in data['순번'].values:
        selected_row = data[data['순번'] == loan_number]
        loan_index = selected_row.index[0]
        recommended_loans = get_loan_similarity(data, loan_index)

        return jsonify(recommended_loans[['순번', '금융 상품명', '전처리 대출 한도', '전처리 이자율', '전처리 최대 상환 기간']].to_dict(orient='records'))
    else:
        return jsonify({"error": f"해당 순번의 상품이 존재하지 않습니다: {loan_number}"}), 404
