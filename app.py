from flask import Flask, render_template, request, redirect, url_for
import uuid
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, db
import openai
import os
import json
import random

app = Flask(__name__)

# 환경 변수에서 API 키를 읽어들임
api_keys = [
    os.environ.get('API_KEY1'),
    os.environ.get('API_KEY2')
]

# 유효한 API 키 필터링
api_keys = [key for key in api_keys if key is not None]

# 랜덤하게 API 키 선택
selected_api_key = random.choice(api_keys)
openai.api_key = selected_api_key

# Firebase 초기화
if not firebase_admin._apps:
    cred_path = os.environ.get('FIREBASE_CRED_PATH')
    if not cred_path:
        raise ValueError("FIREBASE_CRED_PATH 환경 변수가 설정되지 않았습니다.")
    with open(cred_path, "r", encoding="utf-8") as f:
        cred_data = json.load(f)
    cred = credentials.Certificate(cred_data)
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://metawebapp-10956-default-rtdb.firebaseio.com/'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    teacher_request = request.form['teacher_request']
    app_type = request.form['app_type']
    app_id = str(uuid.uuid4())
    app_dir = Path(f"apps/{app_id}")
    app_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = f"""
### 기능 설명
- assistant는 주어진 "요청"을 바탕으로 GPT가 효율적으로 작동하기 위한 "시스템 프롬프트"로 수정한다.
- "시스템 프롬프트"는 학생을 위한 GPT-API 기반 챗봇의 시스템 프롬프트이다.
- 수정될 프롬프트는 구조별로 식별부호 ##를 사용한다.
- text로 표현이 어려운 개념이나 역사적 사건의 연대는 명확하게 설명하도록 한다.
- 시스템 프롬프트의 구조에는 대화 설정, 규칙, 대화 과정, 필요한 예시를 포함한다.

### 시스템 프롬프트의 예

## 대화 설정:
- assistant는 친절하고 명확한 설명을 제공하며, 사회과학 지식이 풍부해야 함.
- 대화의 목적은 user가 사회과학 개념과 역사적 사건을 숙달하는 것임.
- 출력에는 제시한 질문의 답변을 명확하게 포함한다.

## 규칙:
- 다양한 주제의 사회과학 질문을 학생에게 제시하도록 함.
- 질문을 제시할 때 답변을 HTML 주석 태그 (<!-- -->)를 사용하여 숨김 처리하도록 함.
- 중요한 개념이나 연대를 정확히 설명하도록 지시함.
- 답변의 정확성을 유지하도록 함.

## 대화 과정:
- user가 정답을 맞출 경우 칭찬하고 다음 질문으로 넘어감.
- user가 오답을 제시하면 힌트를 제공하고, 필요시 추가 설명을 제시함.
- user가 특정 개념을 이해하기 어려워하면, 추가 예시나 설명을 제공하도록 함.
- user가 대화를 종료하려 할 때, 학습한 내용을 요약하고 채점 결과와 통계를 제공하도록 함.
- user가 잘못된 정보를 고집할 경우, 단호하게 바로잡고, 대화 목적과 관련 없는 대화는 거절하도록 지시함.

## user가 정답을 입력한 경우 대화 예시:
- 프랑스 혁명은 언제 일어났을까요? <!-- 1789년 -->
- 1789년입니다.
- 잘했어요. 이제 다음 질문을 풀어볼까요?

## user가 오답을 입력한 경우 대화 예시:
- 산업 혁명이 시작된 나라는 어디일까요? <!-- 영국 -->
- 모르겠어요.
- 산업 혁명은 18세기 후반에 시작되었고, 이 나라는 세계 최초로 대규모 기계화가 이루어졌어요.
- 영국입니다.
- 맞아요. 이제 다음 질문을 풀어볼까요?

### 요청
{teacher_request}
"""

    try:
        ref = db.reference(f"apps/{app_id}")
        ref.set({
            'request': teacher_request,
            'app_type': app_type
        })
        return redirect(url_for('app_created', app_id=app_id))
    except Exception as e:
        return f"앱 생성 중 오류가 발생했습니다: {e}"

@app.route('/app_created/<app_id>')
def app_created(app_id):
    return f"앱이 생성되었습니다! 앱 ID: {app_id}. 로컬 환경에서 앱이 실행 중입니다. 'python app.py' 명령을 실행하세요."

if __name__ == '__main__':
    app.run(debug=True)
    