import streamlit as st
from openai import OpenAI
import base64
from PIL import Image
import io
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit page config
st.set_page_config(page_title="Neighborhood Mixologist", page_icon="🍸")

def get_cocktail_suggestions(image: bytes) -> Dict:
    # Convert image to base64
    base64_image = base64.b64encode(image).decode('utf-8')
    
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
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Updated model name
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
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}")
        return None

def main():
    st.title("🍸 Neighborhood Mixologist")
    st.write("Upload a photo of your liquor bottles, and I'll suggest cocktail recipes!")

    # File uploader
    uploaded_file = st.file_uploader("Take a photo or choose an image file", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        # Add a button to trigger analysis
        if st.button("Analyze Photo"):
            with st.spinner("Analyzing your bottles and crafting suggestions..."):
                # Convert image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_byte_arr = img_byte_arr.getvalue()
                
                # Get cocktail suggestions
                suggestions = get_cocktail_suggestions(img_byte_arr)
                
                if suggestions:
                    st.markdown("## 📋 Results")
                    st.markdown(suggestions)

if __name__ == "__main__":
    main()
