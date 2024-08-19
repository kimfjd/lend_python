import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
from flask import request, jsonify
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

es = Elasticsearch([{'scheme': 'http', 'host': '192.168.10.6', 'port': 9200}])


def get_data_from_elasticsearch(index_name):
    response = es.search(index=index_name, body={"query": {"match_all": {}}})
    hits = response['hits']['hits']
    if not hits:
        print("No data found in Elasticsearch index:", index_name)  # 추가된 로그
        return pd.DataFrame()
    df = pd.json_normalize([hit['_source'] for hit in hits])
    return df


def convert_to_numeric(value):
    try:
        value = str(value).replace(',', '')
        return float(value)
    except ValueError:
        return np.nan


def preprocess_data(data):

    data['순번'] = pd.to_numeric(data['순번'], errors='coerce')
    data.set_index('순번', inplace=True)

    # 평균 금리 계산 및 NaN 처리
    data['평균 금리'] = data.apply(
        lambda row: (row['최고 금리'] + row['최저 금리']) / 2 if pd.isna(row['평균 금리']) else row['평균 금리'], axis=1
    )

    numeric_features = ['전처리 대출 만기 경과 건 연체이자율', '최저 금리', '최고 금리', '평균 금리', '전처리 대출 한도']

    # Convert features to numeric and handle NaN
    data[numeric_features] = data[numeric_features].applymap(convert_to_numeric)
    data[numeric_features] = data[numeric_features].fillna(0)  # NaN을 0으로 채우기

    print("Data after filling NaNs:", data)  # 추가된 로그

    # 필터링 조건을 너무 엄격하게 하지 않고, 이후 추천 단계에서 다시 필터링
    data = data.dropna(subset=numeric_features)

    print("Data after dropping NaNs:", data)  # 추가된 로그

    return data


def recommend_similar_loans(data, rent_value, loan_amount, num_recommendations=5):
    user_data = pd.DataFrame({
        '전세금': [rent_value],
        '대출금': [loan_amount],
        '대출 한도 비율': [loan_amount / rent_value]
    })

    # Feature selection for similarity
    features = ['전세금', '대출금', '평균 금리', '전처리 대출 한도']

    data_for_similarity = data.copy()
    data_for_similarity['전세금'] = rent_value
    data_for_similarity['대출금'] = loan_amount
    data_for_similarity['대출 한도 비율'] = loan_amount / rent_value

    all_data = pd.concat([user_data, data_for_similarity[features]], axis=0)

    # Handle NaN values before scaling
    all_data.fillna(0, inplace=True)

    # Standardize the features
    scaler = StandardScaler()
    all_data_scaled = scaler.fit_transform(all_data)

    # Calculate cosine similarity
    similarities = cosine_similarity(all_data_scaled)
    similarities = similarities[0, 1:]  # Remove the first element (self similarity)

    # Debugging logs to check similarity calculations
    print("Similarities calculated:", similarities)

    # Get the most similar loans
    data_for_similarity['similarity'] = similarities
    sorted_data = data_for_similarity.sort_values(by='similarity', ascending=False).head(num_recommendations)

    print("Sorted data for recommendations:", sorted_data)  # 추가된 로그

    return sorted_data


def jeonse_loan():
    try:
        content = request.json
        rent_value = float(content.get("rent_value"))
        loan_amount = float(content.get("loan_amount"))

        data = get_data_from_elasticsearch('jeonse_loan')
        if data.empty:
            return jsonify({"message": "No data available in Elasticsearch"}), 404

        data = preprocess_data(data)
        print("Preprocessed data:", data)  # 추가된 로그

        recommended_loans = recommend_similar_loans(data, rent_value, loan_amount)

        if recommended_loans.empty:
            return jsonify({"message": "No loans found matching your criteria"}), 404

        result = recommended_loans[['금융회사 명', '금융 상품명', '평균 금리', '대출한도', 'similarity','대출종류명']].to_dict(orient='records')
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400