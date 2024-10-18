import streamlit as st
from openai import OpenAI
import base64
from PIL import Image
import io
from typing import Optional, Dict
import json
import re

# Constants
TITLE = "🍸 Neighborhood Mixologist"
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 1500

# Updated system prompt
SYSTEM_PROMPT = """You are an expert bartender and cocktail recipe generator with exceptional skills in identifying alcohol bottles and other ingredients from images. Your task is to meticulously analyze the provided image and identify as many alcohol bottles and other relevant ingredients as possible, being as accurate and comprehensive as you can.

When analyzing the image:
1. Look for any and all alcohol bottles, including those that might be partially obscured or in the background.
2. Identify other relevant ingredients or mixers that might be visible (e.g., fruit, herbs, bitters, syrups).
3. If you see any bar tools or equipment, mention those as well, as they might influence the cocktail suggestions.
4. Be specific about brands when possible, but also note the type of alcohol if the brand isn't clear.
5. If you're unsure about a specific item, include it and note your uncertainty.

After identification, suggest cocktail recipes that can be made using some or all of the identified ingredients.

Format your response as a JSON string with the following structure:
{
    "identified_items": [
        {"name": "Item 1", "type": "Alcohol/Mixer/Tool", "notes": "Any additional observations"},
        {"name": "Item 2", "type": "Alcohol/Mixer/Tool", "notes": "Any additional observations"},
        ...
    ],
    "cocktails": [
        {
            "name": "Cocktail Name",
            "category": "Classic/Fruity/Other",
            "short_description": "A brief one-line description",
            "ingredients": [
                {"name": "Ingredient 1", "amount": "2 oz", "available": true/false},
                {"name": "Ingredient 2", "amount": "1 oz", "available": true/false},
                ...
            ],
            "instructions": ["Step 1", "Step 2", ...],
            "missing_ingredients": ["Ingredient 1", "Ingredient 2", ...]
        },
        ...
    ]
}

Strive for maximum accuracy and detail in your identification. Your thorough analysis will greatly enhance the cocktail suggestions and overall user experience."""

def get_cocktail_suggestions(client: OpenAI, image: bytes) -> Optional[Dict]:
    """
    Analyze image and get cocktail suggestions using OpenAI's API.
    
    Args:
        client (OpenAI): The OpenAI client
        image (bytes): The image data in bytes
    
    Returns:
        Optional[Dict]: Parsed JSON response or None if an error occurs
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
                        {"type": "text", "text": "Please identify the items in this image and suggest cocktail recipes."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=MAX_TOKENS
        )
        
        content = response.choices[0].message.content
        
        # Remove Markdown code block syntax if present
        content = re.sub(r'^```json\s*|\s*```$', '', content.strip())
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as json_error:
            st.error(f"Error parsing JSON: {str(json_error)}")
            st.write("Processed content:", content)
            return None
            
    except Exception as e:
        st.error(f"Error communicating with OpenAI API: {str(e)}")
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
    """Display detailed information for a selected cocktail."""
    st.subheader(cocktail['name'])
    st.write(f"Category: {cocktail['category']}")
    st.write(cocktail['short_description'])

    st.write("Ingredients:")
    for ingredient in cocktail['ingredients']:
        status = "✅" if ingredient['available'] else "❌"
        st.write(f"{status} {ingredient['amount']} {ingredient['name']}")

    st.write("Instructions:")
    for i, step in enumerate(cocktail['instructions'], 1):
        st.write(f"{i}. {step}")

    if cocktail['missing_ingredients']:
        st.write("Missing Ingredients:")
        for ingredient in cocktail['missing_ingredients']:
            st.write(f"- {ingredient}")
        st.write("Tips for obtaining missing ingredients:")
        st.write("1. Check local liquor stores or supermarkets")
        st.write("2. Look for online retailers that deliver to your area")
        st.write("3. Consider substitutes or alternatives for hard-to-find items")

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
    use_camera = st.sidebar.toggle("Use Camera", value=False)
    
    # Main content
    if use_camera:
        st.write("Take a photo of your liquor bottles and ingredients, and I'll suggest cocktail recipes!")
        image_input = st.camera_input("Take a photo")
    else:
        st.write("Upload a photo of your liquor bottles and ingredients, and I'll suggest cocktail recipes!")
        image_input = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
    
    if image_input:
        st.image(image_input, caption="Captured/Uploaded Image", use_column_width=True)
        
        if st.button("Analyze Photo"):
            with st.spinner("Analyzing your ingredients and crafting suggestions..."):
                img_bytes = process_image(image_input)
                if img_bytes:
                    suggestions = get_cocktail_suggestions(client, img_bytes)
                    if suggestions:
                        st.session_state.suggestions = suggestions
                        st.session_state.selected_cocktail = None

    # Display identified items and cocktail buttons only if suggestions exist
    if st.session_state.suggestions is not None and 'identified_items' in st.session_state.suggestions:
        st.markdown("## 📋 Identified Items")
        for i, item in enumerate(st.session_state.suggestions['identified_items'], 1):
            st.write(f"{i}. {item['name']} ({item['type']})")
            if item['notes']:
                st.write(f"   Note: {item['notes']}")
        
        if 'cocktails' in st.session_state.suggestions:
            st.markdown("## 🍹 Suggested Cocktails")
            for cocktail in st.session_state.suggestions['cocktails']:
                if st.button(f"{cocktail['name']} - {cocktail['short_description']}", key=cocktail['name']):
                    st.session_state.selected_cocktail = cocktail

    # Debug statements
    # st.write("Debug: Session state contents:", st.session_state)
    # st.write("Debug: Selected cocktail:", st.session_state.selected_cocktail)

    # Display selected cocktail details
    if st.session_state.selected_cocktail is not None:
        st.markdown("## 🍸 Selected Cocktail Details")
        display_cocktail_details(st.session_state.selected_cocktail)

if __name__ == "__main__":
    main()
