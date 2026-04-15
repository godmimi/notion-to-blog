# X 기반 자동포스팅

X(트위터) 링크를 텔레그램으로 보내면 자동으로 블로그 포스팅까지 완료되는 시스템.

## 흐름

```
텔레그램에 X 링크 전송 (이미지 첨부 선택)
→ X 내용 분석
→ Claude가 A/B/C 타입으로 블로그 글 작성
→ 이미지 없으면 Gemini가 자동 생성
→ Blogger 자동 포스팅
→ 완료 알림
```

## GitHub Secrets 설정

| 키 | 설명 |
|----|------|
| `TELEGRAM_TOKEN` | 텔레그램 봇 토큰 |
| `ALLOWED_USER_ID` | 허용할 텔레그램 유저 ID |
| `CLAUDE_API_KEY` | Anthropic API 키 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `IMGBB_API_KEY` | imgbb API 키 |
| `BLOG_ID` | Blogger 블로그 ID |
| `GOOGLE_CREDENTIALS` | Google OAuth JSON |

## 사용법

1. GitHub Actions에서 `X Auto Poster Bot` 워크플로우 수동 실행
2. 텔레그램에서 X 링크 전송
3. 완료 알림 대기
