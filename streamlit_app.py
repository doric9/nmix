import streamlit as st
from openai import OpenAI
import base64
from PIL import Image
import io
from typing import List, Dict, Optional

# Constants
TITLE = "🍸 Neighborhood Mixologist"
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 1000

# System prompt as a constant
SYSTEM_PROMPT = """You are an expert bartender and cocktail recipe generator. 
Given an image of alcohol bottles, identify the bottles present and suggest 
cocktail recipes that can be made using some or all of the identified ingredients.

Format your response as follows:
1. First, list all identified bottles
2. Then, for each cocktail recipe, provide:
   - Name
   - Category (Classic, Fruity, or Other)
   - Ingredients with measurements
   - Brief instructions

Only suggest cocktails that can be made primarily with the ingredients visible 
in the image. You may assume basic mixers (juice, soda) are available."""

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_cocktail_suggestions(image: bytes) -> Optional[str]:
    """
    Analyze image and get cocktail suggestions using OpenAI's API.
    
    Args:
        image (bytes): The image data in bytes
    
    Returns:
        Optional[str]: Cocktail suggestions or None if an error occurs
    """
    try:
        client = get_openai_client()
        base64_image = base64.b64encode(image).decode('utf-8')
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please identify the bottles and suggest cocktail recipes."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}")
        return None

def process_image(image_data) -> Optional[bytes]:
    """
    Process the image data and return it in bytes format.
    
    Args:
        image_data: Either a FileUploader object or camera input
    
    Returns:
        Optional[bytes]: Processed image in bytes or None if processing fails
    """
    try:
        image = Image.open(image_data)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format)
        return img_byte_arr.getvalue()
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def main():
    st.set_page_config(page_title=TITLE, page_icon="🍸")
    st.title(TITLE)
    
    # Sidebar
    use_camera = st.sidebar.toggle("Use Camera", value=False)
    
    # Main content
    if use_camera:
        st.write("Take a photo of your liquor bottles, and I'll suggest cocktail recipes!")
        image_input = st.camera_input("Take a photo")
    else:
        st.write("Upload a photo of your liquor bottles, and I'll suggest cocktail recipes!")
        image_input = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
    
    if image_input:
        # Display the image
        st.image(image_input, caption="Captured/Uploaded Image", use_column_width=True)
        
        # Add analyze button
        if st.button("Analyze Photo"):
            with st.spinner("Analyzing your bottles and crafting suggestions..."):
                # Process image
                img_bytes = process_image(image_input)
                if img_bytes:
                    # Get and display suggestions
                    suggestions = get_cocktail_suggestions(img_bytes)
                    if suggestions:
                        st.markdown("## 📋 Results")
                        st.markdown(suggestions)

if __name__ == "__main__":
    main()
