import os
import json
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BLOG_ID = os.environ.get("BLOG_ID")
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")  # JSON 문자열


def post_to_blogger(title: str, html_content: str, image_url: str, labels: list) -> str:
    """Blogger에 포스팅. 성공 시 포스트 URL 반환."""
    creds = _get_credentials()
    service = build("blogger", "v3", credentials=creds)

    body_html = _build_html(image_url, html_content)

    post = {
        "title": title,
        "content": body_html,
        "labels": labels,
    }

    result = service.posts().insert(blogId=BLOG_ID, body=post, isDraft=False).execute()
    return result.get("url", "")


def _build_html(image_url: str, content: str) -> str:
    """이미지를 맨 위에 배치한 최종 HTML"""
    img_tag = f'<img src="{image_url}" alt="thumbnail" style="width:100%;border-radius:8px;margin-bottom:20px;" />' if image_url else ""
    return f"{img_tag}\n{content}"


def _get_credentials() -> Credentials:
    cred_data = json.loads(GOOGLE_CREDENTIALS)
    return Credentials(
        token=cred_data["token"],
        refresh_token=cred_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cred_data["client_id"],
        client_secret=cred_data["client_secret"],
    )
