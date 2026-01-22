from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import BoardList
import requests, traceback
from django.shortcuts import render, redirect
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from datetime import datetime
from markdown import markdown
import re
from django.utils.safestring import mark_safe

from django.core.paginator import Paginator
from .models import Issue

# Create your views here.
ERROR_MAP = {
	"4062431206512053339" : "개발자오류",
	"4062430467230728515" : "기초데이터오류",
	"4046759869914686137" : "기타",
	"4062430701032815370" : "데이터베이스설계오류",
	"4062431462386295964" : "데이터수정요청",
	"4062431104728936691" : "사용자실수",
	"4062430245571674949" : "소스코드문제",
	"4062430981821462507" : "연계오류",
	"4062431548321775843" : "프로그램업그레이드",
}
HANDLE_MAP = {
	"4053701202528745339" : "DB설계수정",
	"4062444602614098566" : "JAVA단수정",
	"4062490455185115159" : "RD수정",
	"4062491529107142759" : "기타",
	"4062490946487267455" : "데이터수정",
	"4062491098207363073" : "업무가이드",
	"4062490642973051206" : "외부업체전달",
	"4062490027540277272" : "쿼리수정",
	"4062444456885161442" : "화면수정"
}

def index(request):
    posts = BoardList.objects.all().order_by('-CREATE_DATE')  # 최신순 정렬

    search_text = request.GET.get('search-text', '')
    error_type = request.GET.get('error-type', '')
    handle_type = request.GET.get('handle-type', '')
    schedule = request.GET.get('schedule', '')

    if search_text:
        issues = issues.filter(content__icontains=search_text)
    if error_type and error_type != 'error-none':
        issues = issues.filter(error_type=error_type)
    if handle_type and handle_type != 'handle-none':
        issues = issues.filter(handle_type=handle_type)
    if schedule:
        issues = issues.filter(schedule=schedule)


    page = request.GET.get('page')
    paginator = Paginator(posts, 40)
    posts = paginator.get_page(page)

    current_page = posts.number
    total_pages = paginator.num_pages
    max_display = 8
    half = max_display // 2
    start_page = max(current_page - half, 1)
    end_page = min(start_page + max_display - 1, total_pages)
    if end_page - start_page < max_display - 1:
        start_page = max(end_page - max_display + 1, 1)
    page_range = range(start_page, end_page + 1)

    return render(request, 'list.html', {
        'boards': posts,
        'page_range': page_range,
        'search_text': search_text,
        'error_type': error_type,
        'handle_type': handle_type,
        'schedule': schedule,
    })\
    
    #return render(request, 'list.html', {'boards': posts})

def post(request):
    return render(request, 'post.html')

def detail(request, post_id):
    post = get_object_or_404(BoardList, id=post_id)
    post.content = mark_safe(convert_markdown_images(post.content))
    print("📌 선택된 게시글:", post)
    print("📌 제목:", post.title)

    return render(request, 'detail.html', {'post': post})

def convert_markdown_images(content):
    def replacer(match):
        alt_text = match.group(1)
        file_id = match.group(2)
        image_url = f"https://snetsystems.dooray.com/files/{file_id}"
        return f'<img src="{image_url}" alt="{alt_text}" style="max-width: 100%; margin-bottom: 1rem;">'

    # 마크다운: ![설명](/files/file_id)
    pattern = r'!\[(.*?)\]\(/files/(\d+)\)'
    return re.sub(pattern, replacer, content)

@csrf_exempt
def sync(request):
    if request.method == "POST":
        count = 0
        page = 0
        size = 100


        while True: 
            try:
                print("▶ 동기화 시작")

                url = "https://api.dooray.com/project/v1/projects/4046755324790625408/posts/"  # API 주소
                headers = {
                    "Authorization": "dooray-api smoqjaev945f:Z4J-cxpKQ36O0M-Vrd41kQ"
                }
                params = {
                    "page": page,
                    "size": size,
                    "statuses": "open,closed,trash"
                }
                response = requests.get(url, headers=headers,params=params)
                print("▶ 응답 코드:", response.status_code)
                response.raise_for_status()
                data_list = response.json().get("result",[])
                print("▶ 받은 항목 수:", len(data_list))

            except Exception as e:
                print("오류 발생:", e)
                traceback.print_exc()  # 상세 스택트레이스 출력
                messages.error(request, f"동기화 실패: {e}")

            if not data_list:
                break

            with connection.cursor() as cursor:
                for item in data_list:
                    post_id = item.get("id") # 글 id
                    detail_url = f"https://api.dooray.com/project/v1/projects/4046755324790625408/posts/{post_id}" # 상세 API 주소
                    detail_res = requests.get(detail_url, headers=headers,params=params)
                    detail = detail_res.json().get("result",{})

                    _id = detail.get("id")
                    _title = detail.get("subject")
                    _content = detail.get("body",{}).get("content","")

                    # 장애유형, 처리유형 tag 선언
                    tags = detail.get("tags",[])
                    _error_tp = ERROR_MAP.get(tags[1]["id"], "알 수 없음") if len(tags) > 1 else None
                    _handle_tp = HANDLE_MAP.get(tags[2]["id"], "알 수 없음") if len(tags) > 2 else None
                    _status = detail.get("workflow",{}).get("name","")

                    # 날짜 유형
                    _create_date_str = detail.get("createdAt")
                    if _create_date_str:
                        _create_date = datetime.strptime(_create_date_str, '%Y-%m-%dT%H:%M:%SZ')
                    else:
                        _create_date = None  # 또는 기본값
                    _ticket_num = item.get("number")

                    files = detail.get("files",[])
                    for file in files:
                        file_id = file.get("id") 
                    print("sync() : ", file_id)
                    cursor.execute("""
                        MERGE INTO BOARD b
                        USING (SELECT :id AS id FROM dual) src
                        ON (b.id = src.id)
                        WHEN MATCHED THEN
                          UPDATE SET
                            error_tp = :error_tp,
                            handle_tp = :handle_tp,
                            status = :status
                          WHERE b.create_date >= TO_DATE('2025-07-01', 'YYYY-MM-DD')
                        WHEN NOT MATCHED THEN
                        INSERT (id, title, content, error_tp, handle_tp, status, create_date, ticket_num)
                        VALUES (:id, :title, :content, :error_tp, :handle_tp, :status, :create_date, :ticket_num)
                    """, {
                        'id': int(_id),
                        'title': _title,
                        'content' : _content,
                        'error_tp' : _error_tp,
                        'handle_tp' : _handle_tp,
                        'status' : _status,
                        'create_date': _create_date,
                        'ticket_num' : _ticket_num
                    })
                    count+=1
                    print(f"영향갯수 : {cursor.rowcount}개, 총 진행갯수 : {count}개 ")
                messages.success(request, f"{len(data_list)}건 동기화 완료!")

                
            print(f"▶ 현재 {page} 페이지 처리 완료")
            page += 1
    return redirect('index')


