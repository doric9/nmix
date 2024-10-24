import streamlit as st
from openai import OpenAI
import base64
from PIL import Image
import io
from typing import Optional, Dict
import json
import re

# Constants
TITLE = "🍸 우리동네 믹솔로지스트"
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 1500

# System prompt remains in English
SYSTEM_PROMPT = """You are an expert bartender and cocktail recipe generator with exceptional skills in identifying alcohol bottles and other ingredients from images. Provide your response in Korean. Your task is to meticulously analyze the provided image and identify as many alcohol bottles and other relevant ingredients as possible, being as accurate and comprehensive as you can.

Format your response as a JSON string with the following structure:
{
    "identified_items": [
        {
            "name": "항목명",
            "type": "주류/믹서/도구",
            "notes": "추가 관찰사항"
        },
        ...
    ],
    "cocktails": [
        {
            "name": "칵테일 이름",
            "category": "클래식/프루티/기타",
            "short_description": "간단한 한 줄 설명",
            "ingredients": [
                {
                    "name": "재료명",
                    "amount": "30ml",
                    "available": true/false
                },
                ...
            ],
            "instructions": ["단계 1", "단계 2", ...],
            "missing_ingredients": ["없는 재료 1", "없는 재료 2", ...]
        },
        ...
    ]
}"""

def get_cocktail_suggestions(client: OpenAI, image: bytes) -> Optional[Dict]:
    """
    Analyze image and get cocktail suggestions using OpenAI's API.
    """
    try:
        base64_image = base64.b64encode(image).decode('utf-8')
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "이 이미지에서 식별된 항목들을 분석하고 칵테일 레시피를 추천해주세요."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=MAX_TOKENS
        )
        
        content = response.choices[0].message.content
        
        # Clean up the response content
        content = re.sub(r'^```json\s*|\s*```$', '', content.strip())
        content = content.replace('\n', '').replace('\r', '').strip()
        
        try:
            parsed_json = json.loads(content)
            return parsed_json
        
        except json.JSONDecodeError as json_error:
            st.error(f"JSON 파싱 오류: {str(json_error)}")
            st.write("파싱 실패한 내용:", content)
            return None
            
    except Exception as e:
        st.error(f"OpenAI API 통신 오류: {str(e)}")
        return None

def process_image(image_data) -> Optional[bytes]:
    """Process the image data and return it in bytes format."""
    try:
        image = Image.open(image_data)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format)
        return img_byte_arr.getvalue()
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def display_cocktail_details(cocktail: Dict):
    """칵테일 상세 정보를 표시합니다."""
    # Create a clean header with emoji
    st.markdown(f"### 🍸 {cocktail['name']}")
    
    # Display category and description in a clean, simple format
    st.markdown(f"{cocktail['category']} | *{cocktail['short_description']}*")
    
    # Display ingredients in a clean list
    st.markdown("#### 📝 재료")
    
    for ingredient in cocktail['ingredients']:
        status = "✅" if ingredient['available'] else "❌"
        st.markdown(f"<div style='display: flex; align-items: center; margin-bottom: 5px;'>"
                    f"<span style='width: 30px; text-align: center;'>{status}</span>"
                    f"<span style='width: 80px;'>{ingredient['amount']}</span>"
                    f"<span>{ingredient['name']}</span>"
                    f"</div>", unsafe_allow_html=True)

    # Display instructions in a numbered list
    st.markdown("#### 🥃 제조 방법")
    for i, step in enumerate(cocktail['instructions'], 1):
        st.markdown(f"{i}. {step}")

def main():
    st.set_page_config(page_title=TITLE, page_icon="🍸")
    st.title(TITLE)
    
    # Initialize session state variables if they don't exist
    if 'suggestions' not in st.session_state:
        st.session_state.suggestions = None
    if 'selected_cocktail' not in st.session_state:
        st.session_state.selected_cocktail = None
    
    # Initialize OpenAI client inside main function
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    # Sidebar
    use_camera = st.sidebar.toggle("카메라 사용", value=False)
    
    # Main content
    if use_camera:
        st.write("술병과 재료들의 사진을 찍으시면 칵테일 레시피를 추천해 드립니다!")
        image_input = st.camera_input("사진 찍기")
    else:
        st.write("술병과 재료들의 사진을 업로드하시면 칵테일 레시피를 추천해 드립니다!")
        image_input = st.file_uploader("이미지 파일 선택", type=["jpg", "jpeg", "png"])
    
    if image_input:
        st.image(image_input, caption="촬영/업로드된 이미지", use_column_width=True)
        
        if st.button("사진 분석"):
            with st.spinner("재료를 분석하고 제안을 준비하는 중..."):
                img_bytes = process_image(image_input)
                if img_bytes:
                    suggestions = get_cocktail_suggestions(client, img_bytes)
                    if suggestions:
                        st.session_state.suggestions = suggestions
                        st.session_state.selected_cocktail = None

    # Display identified items and cocktail suggestions
    if st.session_state.suggestions is not None:
        if 'identified_items' in st.session_state.suggestions:
            st.markdown("## 📋 식별된 항목")
            for i, item in enumerate(st.session_state.suggestions['identified_items'], 1):
                description = f"{item['name']}"
                if item['notes']:
                    description += f" : {item['notes']}"
                st.write(f"{i}. {description}")
        
        # Add this section to display cocktail suggestions
        if 'cocktails' in st.session_state.suggestions:
            st.markdown("## 🍸 추천 칵테일")
            for i, cocktail in enumerate(st.session_state.suggestions['cocktails'], 1):
                if st.button(f"{cocktail['name']} - {cocktail['short_description']}", key=cocktail['name']):
                    st.session_state.selected_cocktail = cocktail

    # Display selected cocktail details
    if st.session_state.selected_cocktail is not None:
        # The header for cocktail details is now part of the display_cocktail_details function
        display_cocktail_details(st.session_state.selected_cocktail)

if __name__ == "__main__":
    main()
