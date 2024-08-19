from flask import request, jsonify
from elasticsearch import Elasticsearch
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Elasticsearch 클라이언트 설정
es = Elasticsearch(['http://192.168.10.6:9200'])

# 데이터 로드 함수
def load_data_from_es(index_name):
    query = {
        "query": {
            "match_all": {}
        }
    }
    response = es.search(index=index_name, body=query, size=10000)  # 최대 10,000 문서 조회
    hits = response['hits']['hits']
    data = [hit['_source'] for hit in hits]
    return data

# 데이터 전처리 함수
def preprocess_data(data):
    df = pd.DataFrame(data)

    # '순번'을 정수형으로 변환
    df['순번'] = pd.to_numeric(df['순번'], errors='coerce')
    df.set_index('순번', inplace=True)

    # '평균 금리' 열의 N/A 값을 (최고 금리 + 최저 금리) / 2로 대체
    df['평균 금리'] = df.apply(
        lambda row: (row['최고 금리'] + row['최저 금리']) / 2 if pd.isna(row['평균 금리']) else row['평균 금리'], axis=1
    )

    # 숫자형으로 변환할 수 없는 값이 있는지 확인하고 처리하는 함수
    def convert_to_numeric(value):
        try:
            value = str(value).replace(',', '')
            return float(value)
        except ValueError:
            return np.nan

    # 필요한 컬럼의 숫자형 변환
    numeric_features = ['전처리 연체이자율', '최저 금리', '최고 금리', '평균 금리']
    df[numeric_features] = df[numeric_features].applymap(convert_to_numeric)

    # NaN 값이 있는 행 제거
    df = df.dropna(subset=numeric_features)
    return df, numeric_features

# 대출 상품과 비슷한 추천 상품을 찾는 함수 정의
def find_loan_similarity(data, loan_index, numeric_features, num_recommendations=5):
    if loan_index not in data.index:
        raise IndexError("선택한 인덱스가 데이터의 범위를 초과합니다.")

    selected_loan = data.loc[loan_index, numeric_features].values.reshape(1, -1)
    all_loans = data[numeric_features].values

    similarity_scores = cosine_similarity(selected_loan, all_loans).flatten()
    similar_loan_indices = similarity_scores.argsort()[::-1][1:num_recommendations + 1]
    return data.iloc[similar_loan_indices]

# 추천 API 엔드포인트
def get_loan_similarity():
    request_data = request.get_json()
    loan_number = request_data.get('loan_number')

    if not loan_number:
        return jsonify({'error': 'loan_number is required'}), 400

    try:
        data = load_data_from_es('mortgage_loan')
        df, numeric_features = preprocess_data(data)

        recommended_loans = find_loan_similarity(df, loan_number, numeric_features)
        result = recommended_loans[['금융회사 명', '금융 상품명', '평균 금리']].to_dict(orient='records')

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
