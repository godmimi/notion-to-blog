import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from main import fetch_x_content, generate_post
from image import generate_image, upload_user_image
from blogger import post_to_blogger

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))  # 민욱 본인만 허용

logging.basicConfig(level=logging.INFO)


# ──────────────────────────────────────────
# 메시지 핸들러
# ──────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        return

    message = update.message
    text = message.text or message.caption or ""
    photo = message.photo

    # X 링크 추출
    x_url = extract_x_url(text)
    if not x_url:
        await message.reply_text("❌ X 링크를 찾을 수 없어요. x.com 또는 twitter.com 링크를 보내주세요.")
        return

    await message.reply_text("🔍 X 내용 분석 중...")

    # 1. X 내용 가져오기
    x_content = fetch_x_content(x_url)
    if not x_content:
        x_content = text.replace(x_url, "").strip()  # 링크 제외한 텍스트 fallback

    if not x_content:
        await message.reply_text("⚠️ X 내용을 가져오지 못했어요. 링크 + 내용을 함께 보내주세요.")
        return

    await message.reply_text("✍️ 블로그 글 작성 중...")

    # 2. 블로그 글 생성
    try:
        post = generate_post(x_content, x_url)
    except Exception as e:
        await message.reply_text(f"❌ 글 생성 실패: {e}")
        return

    # 3. 이미지 처리
    await message.reply_text("🖼️ 이미지 준비 중...")
    image_url = ""

    if photo:
        # 사용자가 이미지 직접 첨부한 경우
        file = await photo[-1].get_file()
        image_bytes = await file.download_as_bytearray()
        image_url = upload_user_image(bytes(image_bytes))
    else:
        # Gemini로 이미지 생성
        image_url = generate_image(post["title"])

    # 4. Blogger 포스팅
    await message.reply_text("📤 블로그 포스팅 중...")
    try:
        post_url = post_to_blogger(
            title=post["title"],
            html_content=post["html_content"],
            image_url=image_url,
            labels=post["labels"]
        )
        await message.reply_text(
            f"✅ 포스팅 완료!\n\n"
            f"📝 제목: {post['title']}\n"
            f"🔗 링크: {post_url}"
        )
    except Exception as e:
        await message.reply_text(f"❌ 포스팅 실패: {e}")


def extract_x_url(text: str) -> str:
    """텍스트에서 X URL 추출"""
    import re
    match = re.search(r"https?://(x\.com|twitter\.com)/\S+", text)
    return match.group(0) if match else ""


# ──────────────────────────────────────────
# 봇 실행
# ──────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    print("✅ 봇 시작됨")
    app.run_polling()


if __name__ == "__main__":
    main()
