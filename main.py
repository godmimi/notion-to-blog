import os
import re
import anthropic
import requests
from bs4 import BeautifulSoup

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


# ──────────────────────────────────────────
# 1. X 링크 → 본문 텍스트 추출
# ──────────────────────────────────────────
def fetch_x_content(url: str) -> str:
    """X(트위터) 링크에서 텍스트 추출. 실패 시 빈 문자열 반환."""
    # nitter 미러로 우선 시도
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

    # 직접 페이지 텍스트 시도 (fallback)
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        # og:description 메타태그
        meta = soup.find("meta", property="og:description")
        if meta:
            return meta.get("content", "")
    except Exception:
        pass

    return ""


def extract_tweet_id(url: str) -> str:
    """URL에서 트윗 ID 추출"""
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else ""


# ──────────────────────────────────────────
# 2. 텍스트 → 블로그 포스트 생성
# ──────────────────────────────────────────
def generate_post(x_content: str, x_url: str, post_type: str = "auto") -> dict:
    """Claude로 블로그 포스트 생성. 반환: {title, html_content, labels}"""

    if post_type == "auto":
        post_type = classify_type(x_content)

    if post_type == "A":
        prompt = build_prompt_a(x_content, x_url)
    elif post_type == "B":
        prompt = build_prompt_b(x_content, x_url)
    else:
        prompt = build_prompt_c(x_content, x_url)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text
    return parse_response(raw)


def classify_type(content: str) -> str:
    """Haiku로 A/B/C 타입 분류"""
    haiku = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    resp = haiku.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"""다음 내용을 분류해. 반드시 A, B, C 중 하나만 답해.
A: 튜토리얼/하우투 (단계별 방법, 설정법)
B: 뉴스/이슈 분석 (새로운 소식, 논란, 발표)
C: 개념 설명 (10분 이내로 이해 가능한 주제)

내용: {content[:300]}"""
        }]
    )
    t = resp.content[0].text.strip().upper()
    return t if t in ["A", "B", "C"] else "B"


# ──────────────────────────────────────────
# 3. 타입별 프롬프트
# ──────────────────────────────────────────
COMMON_RULES = """
작성 규칙:
- 독자: 한국 직장인, AI 입문자
- 말투: 친근하고 쉽게, 어미 다양하게 (해요/이에요/거든요/네요 섞기)
- AI 클리셰 금지: "혁신적", "놀라운", "게임체인저", "주목할 만한" 사용 금지
- 제목에 이모지, 연도 없음
- 출력 형식: XML 태그로 감싸서

<TITLE>제목</TITLE>
<LABELS>라벨1,라벨2,라벨3</LABELS>
<CONTENT>HTML 본문 전체</CONTENT>
"""

def build_prompt_a(content: str, url: str) -> str:
    return f"""다음 X 게시물을 바탕으로 A타입 블로그 포스트를 작성해.
A타입 형식: [주제] N단계 - 지금 당장 써먹기

X 내용: {content}
원문 링크: {url}

HTML 구조:
1. 준비 체크리스트 (ul)
2. 번호 실행 단계 (ol, 각 단계 설명 2~3줄)
3. 프롬프트 템플릿 (다크박스 스타일 pre 태그, 최소 1개)
4. 마무리 한 줄

{COMMON_RULES}"""


def build_prompt_b(content: str, url: str) -> str:
    return f"""다음 X 게시물을 바탕으로 B타입 블로그 포스트를 작성해.
B타입 형식: [이슈] N가지 - 팩트만 체크하기

X 내용: {content}
원문 링크: {url}

HTML 구조:
1. 팩트체크 섹션 (✅사실 / ❌오해 / ❓미확인 배지)
2. 분석 카드 4개: 무슨 일이 있었나 / 왜 중요한가 / 나에게 미치는 영향 / 지금 당장 할 것

{COMMON_RULES}"""


def build_prompt_c(content: str, url: str) -> str:
    return f"""다음 X 게시물을 바탕으로 C타입 블로그 포스트를 작성해.
C타입 형식: [주제] - 10분이면 충분해

X 내용: {content}
원문 링크: {url}

HTML 구조:
1. 핵심 개념 한 줄 요약
2. 쉬운 비유로 설명 (일상 예시)
3. 실제로 써먹는 법 3가지
4. 자주 묻는 질문 2~3개 (Q&A 형식)

{COMMON_RULES}"""


# ──────────────────────────────────────────
# 4. 응답 파싱
# ──────────────────────────────────────────
def parse_response(raw: str) -> dict:
    def extract(tag):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
        return m.group(1).strip() if m else ""

    title = extract("TITLE")
    labels = [l.strip() for l in extract("LABELS").split(",") if l.strip()]
    content = extract("CONTENT")

    return {"title": title, "html_content": content, "labels": labels}
