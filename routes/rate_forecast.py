import pandas as pd
from flask import request, jsonify
from elasticsearch import Elasticsearch
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import traceback

# Elasticsearch 설정
es = Elasticsearch("http:/192.168.10.6:9200")

def rate_forecast_endpoint():
    try:
        # Elasticsearch에서 데이터 가져오기
        query = {
            "query": {
                "match_all": {}
            },
            "size": 10000  # 필요한 경우 조정
        }
        res = es.search(index="finrate", body=query)
        data = [hit['_source'] for hit in res['hits']['hits']]

        # DataFrame 생성
        df = pd.DataFrame(data)

        # '연도'와 '분기'를 결합하여 '연도 분기' 열 생성
        def to_quarter_date(row):
            year = int(row['연도'])
            quarter = int(row['분기'])
            return pd.Timestamp(year=year, month=(quarter - 1) * 3 + 1, day=1)

        df['연도 분기'] = df.apply(to_quarter_date, axis=1)
        df.set_index('연도 분기', inplace=True)
        df = df.sort_index()

        # 결측치(NaN) 처리: 직전 값으로 채우기 (ffill)
        df.fillna(method='ffill', inplace=True)

        # 예측 모델 훈련
        features = ['생산자물가지수', '국내총생산(명목GDP)', '경제성장률(실질GDP성장률)', '실업률', '소비자물가지수']
        target = '기준금리'

        # 존재하지 않는 열을 사용하면 오류가 발생할 수 있으므로 확인
        missing_features = [feature for feature in features if feature not in df.columns]
        if missing_features:
            raise KeyError(f"다음 열이 데이터에 존재하지 않습니다: {', '.join(missing_features)}")

        X = df[features]
        y = df[target]

        # 데이터 스케일링
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 모델 훈련
        model = LinearRegression()
        model.fit(X_scaled, y)

        # 최근 데이터로 예측
        latest_data = df.iloc[-1][features].values.reshape(1, -1)
        latest_data_scaled = scaler.transform(latest_data)
        predicted_rate = model.predict(latest_data_scaled)[0]

        # 전체 데이터와 예측 결과를 반환
        result = {
            "historical_data": df.reset_index().to_dict(orient='records'),
            "predicted_rate": predicted_rate
        }

        return jsonify(result), 200

    except Exception as e:
        # 오류 발생 시 자세한 로그를 출력
        traceback.print_exc()
        return jsonify({"error": "예측 과정에서 오류가 발생했습니다.", "details": str(e)}), 500
