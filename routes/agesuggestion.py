import pandas as pd
from sqlalchemy import create_engine
from flask import request, jsonify

# MySQL 데이터베이스 연결 설정
db_user = 'root'
db_password = '5648'
db_host = '192.168.10.6'
db_port = 3306  # MySQL의 기본 포트 번호는 3306
db_name = 'lend'

# SQLAlchemy 엔진 생성
engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

# 데이터베이스에서 loanhistory 테이블 데이터 로드
def load_data():
    query = "SELECT loan_id, userage, loan_name, loan_category, rate FROM loanhistory"
    df = pd.read_sql(query, engine)
    return df

# 나이대별로 가장 많이 사용된 대출 상품 추천 함수
def recommend_loan_by_age(age, df):
    if df.empty:
        return []

    # 나이대에 해당하는 대출 데이터를 필터링
    filtered_df = df[(df['userage'] >= age - 5) & (df['userage'] <= age + 5)]

    if filtered_df.empty:
        return []

    # 대출 항목별로 그룹화하여 count가 높은 상위 5개 항목 선택
    top_loans = (
        filtered_df.groupby(['loan_id', 'loan_name', 'loan_category', 'rate'])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
        .head(5)
    )

    # 필요한 필드만 포함하여 리스트로 반환
    result = top_loans[['loan_id', 'loan_name', 'loan_category', 'rate']].to_dict(orient='records')
    return result

# 엔드포인트 함수 정의
def agesuggestion_endpoint():
    try:
        data = request.get_json()
        print("Received data:", data)  # 디버깅을 위해 받은 데이터 출력

        if not data or 'age' not in data:
            return jsonify({'error': 'Age is required and must be provided in the request body'}), 400

        age = data['age']

        if not isinstance(age, int) or age <= 0:
            return jsonify({'error': 'Age must be a positive integer'}), 400

        df = load_data()
        recommended_loans = recommend_loan_by_age(age, df)

        return jsonify({'recommended_loans': recommended_loans})

    except Exception as e:
        print("Error during age suggestion:", str(e))
        return jsonify({'error': 'An error occurred while processing your request'}), 500
