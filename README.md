# auto-blog-poster

Claude AI + fal.ai 기반 Blogger 자동 포스팅 시스템

## GitHub Secrets 설정

| Secret | 설명 |
|--------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 |
| `GOOGLE_REFRESH_TOKEN` | Google Refresh Token |
| `BLOG_ID` | Blogger 블로그 ID |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 텔레그램 채팅 ID |
| `FAL_KEY` | fal.ai API 키 (fal.ai에서 발급) |
| `CHARACTER_IMAGE_URL` | 캐릭터 레퍼런스 이미지 URL (공개 접근 가능한 URL) |

## FAL_KEY 발급
1. [fal.ai](https://fal.ai) 접속 후 회원가입
2. Dashboard → API Keys → 새 키 생성

## CHARACTER_IMAGE_URL 설정
- 캐릭터 이미지를 GitHub에 업로드 후 raw URL 사용
- 또는 공개 접근 가능한 이미지 URL 사용
