from django.shortcuts import render
from .vector_db import get_vector_db, get_template
from django.views.decorators.http import require_http_methods
import json
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from django.http import JsonResponse



# Create your views here.
vector_retriever = None

def initialize_vector_db():
    """벡터 DB 초기화 함수"""
    global vector_retriever
    if vector_retriever is None:
        try:
            print("벡터 DB 초기화 시작...")
            vector_retriever = get_vector_db()
            print("벡터 DB 초기화 완료")
        except Exception as e:
            print(f"벡터 DB 초기화 실패: {str(e)}")
            raise

@require_http_methods(["GET", "POST"])
def chat_view(request):
    if request.method == "GET":
        return render(request, 'chatbot/chat.html')
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # 벡터 DB 검색
            retriever = get_vector_db()
            template = get_template()
            prompt = ChatPromptTemplate.from_template(template)
            
            # ChatOpenAI 모델 설정 - fine-tuned 모델 사용
            model = ChatOpenAI(
                model_name="ft:gpt-4o-mini-2024-07-18:personal::AXmDF5MY",  # fine-tuned 모델 ID
                temperature=0.7,
                max_tokens=1000,
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )

            # 문서 포맷팅
            def format_docs(docs):
                return '\n\n'.join([d.page_content for d in docs])

            # 체인 구성
            chain = {
                'context': retriever | format_docs,
                'question': RunnablePassthrough()
            } | prompt | model | StrOutputParser()

            # 응답 생성
            response = chain.invoke(user_message)

            return JsonResponse({
                'status': 'success',
                'response': response
            })

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
