import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch
from flask import request, jsonify

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])


def get_data_from_elasticsearch(index_name):
    response = es.search(index=index_name, body={"query": {"match_all": {}}})
    hits = response['hits']['hits']
    if not hits:
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

    data['평균 금리'] = data.apply(
        lambda row: (row['최고 금리'] + row['최저 금리']) / 2 if pd.isna(row['평균 금리']) else row['평균 금리'], axis=1
    )

    numeric_features = ['전처리 대출 만기 경과 건 연체이자율', '최저 금리', '최고 금리', '평균 금리', '전처리 대출 한도']
    data[numeric_features] = data[numeric_features].applymap(convert_to_numeric)

    data['전처리 대출 만기 경과 건 연체이자율'] = data['전처리 대출 만기 경과 건 연체이자율'].fillna(np.nan)
    data = data.dropna(subset=numeric_features)
    return data


def recommend_rent_deposit_loans(data, rent_value, loan_amount, num_recommendations=5):
    loan_to_value_ratio = loan_amount / rent_value
    filtered_data = data[
        ((data['전처리 대출 한도'] >= loan_to_value_ratio) | (data['전처리 대출 한도'] == 1))
    ]
    if filtered_data.empty:
        return pd.DataFrame()
    sorted_data = filtered_data.sort_values(by='평균 금리').head(num_recommendations)
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
        recommended_loans = recommend_rent_deposit_loans(data, rent_value, loan_amount)

        if recommended_loans.empty:
            return jsonify({"message": "No loans found matching your criteria"}), 404

        result = recommended_loans[['금융회사 명', '금융 상품명', '평균 금리', '대출한도']].to_dict(orient='records')
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400
