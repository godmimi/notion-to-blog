import os
import re
import anthropic
import requests
from bs4 import BeautifulSoup

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ──────────────────────────────────────────
# 1. URL → 본문 텍스트 추출
# ──────────────────────────────────────────
def fetch_content(url: str) -> str:
    """URL에서 텍스트 추출. X(트위터) 링크 포함."""
    tweet_id = extract_tweet_id(url)
    if tweet_id:
        for mirror in ["https://nitter.privacydev.net", "https://nitter.poast.org"]:
            try:
                r = requests.get(f"{mirror}/i/status/{tweet_id}", timeout=8,
                                 headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    tweet_div = soup.find("div", class_="tweet-content")
                    if tweet_div:
                        return tweet_div.get_text(strip=True)
            except Exception:
                continue

    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        meta = soup.find("meta", property="og:description")
        if meta:
            return meta.get("content", "")
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception:
        pass

    return ""


def extract_tweet_id(url: str) -> str:
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else ""


# ──────────────────────────────────────────
# 2. 타입 분류
# ──────────────────────────────────────────
def classify_type(content: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": f"""다음 내용을 분류해. 반드시 A, B, C 중 하나만 답해.
A: 튜토리얼/하우투 (단계별 방법, 설정법)
B: 뉴스/이슈 분석 (새로운 소식, 논란, 발표)
C: 개념 설명 (10분 이내로 이해 가능한 주제)

내용: {content[:300]}"""}]
    )
    t = resp.content[0].text.strip().upper()
    return t if t in ["A", "B", "C"] else "B"


# ──────────────────────────────────────────
# 3. 제목 생성
# ──────────────────────────────────────────
def generate_title(content: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": f"""다음 블로그 글에 가장 어울리는 제목 1개를 만들어.

규칙:
- 독자 입장에서 "나한테 뭐가 달라지냐"가 바로 보일 것
- 단순 팩트 나열이나 "더 좋아졌다" 식은 피할 것
- 이모지, 연도 없음
- 제목만 출력

글 내용: {content[:500]}"""}]
    )
    return resp.content[0].text.strip()


# ──────────────────────────────────────────
# 4. HTML 버전 생성 (구글 블로그용)
# ──────────────────────────────────────────
COMMON_RULES = """
작성 규칙:
- 독자: 한국 직장인, AI 입문자
- 말투: 친근하고 쉽게, 어미 다양하게 (해요/이에요/거든요/네요 섞기)
- 같은 어미 2문장 연속 금지
- AI 클리셰 금지: "혁신적", "놀라운", "게임체인저", "주목할 만한"
- 마크다운 금지, HTML만 출력
- 출력 형식:

<LABELS>라벨1,라벨2,라벨3</LABELS>
<CONTENT>HTML 본문 전체</CONTENT>
"""


def build_prompt_a(content: str, url: str) -> str:
    return f"""다음 내용을 바탕으로 A타입 블로그 포스트를 HTML로 작성해.
(A타입: 튜토리얼/사용법 — 준비물, 단계별 실행, 프롬프트 템플릿 포함)

내용: {content}
원문 링크: {url}

HTML 구조:
1. 준비 체크리스트 (ul)
2. 번호 실행 단계 (ol, 각 단계 2~3줄)
3. 프롬프트 템플릿 (다크박스 스타일 pre 태그, 최소 1개)
4. 마무리 한 줄

{COMMON_RULES}"""


def build_prompt_b(content: str, url: str) -> str:
    return f"""다음 내용을 바탕으로 B타입 블로그 포스트를 HTML로 작성해.
(B타입: 뉴스/이슈 분석)

내용: {content}
원문 링크: {url}

HTML 구조:
[헤드라인] 언제/누가/무엇 팩트 한 줄, 핵심 변화 나열, 독자에게 의미 한 줄

[팩트체크]
- ✅ 사실: 독자가 "진짜야?" 싶을 것만
- ❌ 오해: 실제로 잘못 알고 있을 것만
- 억지로 개수 채우지 말 것

[이슈 분석] 무슨 일이 있었나 / 왜 중요한가 / 우리에게 미치는 영향
- 각 섹션 2~3문장, 헤드라인 반복 금지

{COMMON_RULES}"""


def build_prompt_c(content: str, url: str) -> str:
    return f"""다음 내용을 바탕으로 C타입 블로그 포스트를 HTML로 작성해.
(C타입: 빠른 개념 설명 — 짧고 임팩트 있게)

내용: {content}
원문 링크: {url}

HTML 구조:
1. 핵심 개념 한 줄 요약
2. 쉬운 비유로 설명 (일상 예시)
3. 실제로 써먹는 법 3가지
4. 자주 묻는 질문 2~3개 (Q&A)

{COMMON_RULES}"""


def generate_html_post(content: str, url: str, post_type: str) -> dict:
    """HTML 버전 생성 (구글 블로그용)"""
    if post_type == "A":
        prompt = build_prompt_a(content, url)
    elif post_type == "B":
        prompt = build_prompt_b(content, url)
    else:
        prompt = build_prompt_c(content, url)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text

    def extract(tag):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
        return m.group(1).strip() if m else ""

    html_content = extract("CONTENT")
    labels = [l.strip() for l in extract("LABELS").split(",") if l.strip()]
    title = generate_title(html_content)

    return {"title": title, "html_content": html_content, "labels": labels}


# ──────────────────────────────────────────
# 5. 텍스트 버전 생성 (네이버 블로그용)
# ──────────────────────────────────────────
def generate_text_post(content: str, url: str, post_type: str) -> str:
    """네이버 블로그용 plain text 버전 생성"""
    type_desc = {
        "A": "튜토리얼/사용법 (준비물, 단계별 실행, 프롬프트 예시 포함)",
        "B": "뉴스/이슈 분석 (팩트 정리, 이슈 분석, 독자 영향)",
        "C": "빠른 개념 설명 (핵심 요약, 비유, 써먹는 법, Q&A)"
    }.get(post_type, "")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": f"""다음 내용을 바탕으로 네이버 블로그에 바로 붙여넣을 수 있는 글을 작성해.

내용: {content}
원문 링크: {url}
글 유형: {type_desc}

작성 규칙:
- HTML 태그 없이 순수 텍스트로
- 제목은 맨 위에 한 줄
- 소제목은 【 】로 감싸기 (예: 【준비물】)
- 독자: 한국 직장인, AI 입문자
- 말투: 친근하고 쉽게, 어미 다양하게
- AI 클리셰 금지: "혁신적", "놀라운", "게임체인저"
"""}]
    )
    return response.content[0].text.strip()
