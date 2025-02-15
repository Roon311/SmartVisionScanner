import streamlit as st
import requests
import base64
from PIL import Image
from pyzbar.pyzbar import decode
import openai

# Additional imports for image display
from io import BytesIO



def formatInput(detected_texts):
  textconc=''
  for text in detected_texts:
    textconc += text['description'] + '\n'  # Adding a newline after each description
  return textconc
# Function to call Google Vision API
def detect_objects_and_barcodes(image_path, api_token=google_api):
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_token}"
    
    with open(image_path, "rb") as image_file:
        image_content = base64.b64encode(image_file.read()).decode("utf-8")
    
    payload = {
        "requests": [
            {
                "image": {"content": image_content},
                "features": [{"type": "OBJECT_LOCALIZATION"}, {"type": "TEXT_DETECTION"}],
            }
        ]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    
    return response.json()
def detect_text_with_token(image_path, api_token=google_api):
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_token}"

    with open(image_path, "rb") as image_file:# Read and encode the image in Base64
        image_content = base64.b64encode(image_file.read()).decode("utf-8")

    # Prepare request payload
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_content  # Base64-encoded image
                },
                "features": [
                    {"type": "TEXT_DETECTION"}
                ],
            }
        ]
    }

    # Make the API call
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    # Parse response
    result = response.json()
    return result["responses"][0].get("textAnnotations", [])

def extractSingle(api_token,image_path):
  try:
    detected_texts = detect_text_with_token(image_path, api_token)
    return detected_texts
  except Exception as e:
    print(e)
def extract_product_names(openai_token,text):
    try:
        # Call to OpenAI GPT-4o mini model
        openai.api_key=openai_token
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # This is the correct model name according to your description
            messages=[
                {"role": "system", "content": "You are a helpful assistant working in a warehouse with knowlege about products."},
                {"role": "user", "content": f"Identify the product names mentioned in the following text, answer only with the product, the name is usually 1 or 2 words only: {text}"}
            ],
            max_tokens=5  # limit to 5, could be changed later
        )
        product_names = response['choices'][0]['message']['content']
        return product_names
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
def decode_barcodes(image_path):
    image = Image.open(image_path)
    decoded_objects = decode(image)
    barcodes = []
    for obj in decoded_objects:
        barcodes.append({"type": obj.type, "data": obj.data.decode("utf-8")})
    return barcodes

# Streamlit application
st.title("Image Processing with Google Vision and GPT-4 Mini")

# Adding custom CSS to enhance look
st.markdown(
    """
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .image-container {
        position: relative;
        width: 100%;
        padding-top: 100%; /* 1:1 Aspect Ratio */
    }
    .image-container img {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        width: 100%;
        height: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)


#api_token = st.text_input("Enter Google Vision API Key:", type="password")
api_token = google_api
#gpt_api_key = st.text_input("Enter OpenAI Key:", type="password")

uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
if uploaded_file and api_token:
    # Display the uploaded image with interactive resizing
    st.subheader("Uploaded Image")
    resize_option = st.checkbox("Click to resize image", value=False)
    image_container = st.empty()  # Placeholder for dynamic image display
    if resize_option:
        image_container.image(uploaded_file, use_container_width=True)  # Dynamic resizing
    else:
        image_container.image(uploaded_file, width=300)  # Default size

    try:
        # Save uploaded image to a temporary file
        with open("uploaded_image.jpg", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Call Google Vision API
        st.subheader("Google Vision API Results")
        response = detect_objects_and_barcodes("uploaded_image.jpg", api_token)
        localized_objects = response["responses"][0].get("localizedObjectAnnotations", [])
        text_annotations = response["responses"][0].get("textAnnotations", [])
        
        st.write("Localized Objects:")
        for obj in localized_objects:
            st.write(f"- {obj['name']} (Confidence: {obj['score']:.2f})")
        
        # Toggle-able detected text section
        with st.expander("Toggle Detected Text"):
            if text_annotations:
                st.write(text_annotations[0].get("description", ""))
            else:
                st.write("No text detected.")
        
        # Decode barcodes
        st.subheader("Decoded Barcodes")
        barcodes = decode_barcodes("uploaded_image.jpg")
        if barcodes:
            for barcode in barcodes:
                st.write(f"- Type: {barcode['type']}, Data: {barcode['data']}")
        else:
            st.write("No barcodes detected.")
        
        # Pass results to GPT-4 Mini API (Placeholder)
        st.subheader("GPT-4 Mini Response")
        detected_texts = extractSingle(api_token=api_token, image_path="uploaded_image.jpg")
        textconc = formatInput(detected_texts)
        product_names = extract_product_names(gpt_api_key, textconc)
        st.markdown(f"<p class='big-font'>Product Name: {product_names}</p>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
