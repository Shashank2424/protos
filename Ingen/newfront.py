import streamlit as st
import base64
from io import BytesIO
from PIL import Image
import pickle
import os
import sys

st.set_page_config(page_title="InGen", layout="wide")

st.title("InGen")

with st.form("blueprint_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        location = st.text_input("Location (City, Country)", "Seattle, USA")
        terrain_type = st.selectbox("Terrain Type", ["Flat", "Hilly", "Coastal", "Mountainous", "Urban"])
        climate = st.selectbox("Climate", ["Temperate", "Tropical", "Arid", "Continental", "Polar"])
        structure_type = st.selectbox("Structure Type", ["Residential", "Commercial", "Mixed-Use", "Industrial"])
    
    with col2:
        if structure_type == "Residential":
            bedrooms = st.number_input("Number of Bedrooms", min_value=1, max_value=10, value=3)
            bathrooms = st.number_input("Number of Bathrooms", min_value=1, max_value=6, value=2)
            kitchen_size = st.selectbox("Kitchen Size", ["Small", "Medium", "Large"])
        else:
            floors = st.number_input("Number of Floors", min_value=1, max_value=50, value=2)
            office_space = st.selectbox("Office Space Size", ["Small", "Medium", "Large"])
            parking = st.checkbox("Include Parking", value=True)
            
        house_size = st.slider("Building Size (sq ft)", min_value=500, max_value=10000, value=2000, step=100)
    
    safety_considerations = st.multiselect(
        "Safety Considerations",
        ["Earthquake Resistance", "Flood Protection", "Hurricane Resistance", "Fire Safety", "Energy Efficiency"],
        ["Energy Efficiency"]
    )
    
    additional_notes = st.text_area("Additional Requirements or Notes")
    
    submit_button = st.form_submit_button("Generate Blueprint")

if submit_button:
    with st.spinner("Generating blueprints... This may take a few minutes"):
        # Construct the prompt based on form inputs
        prompt = {
            "location": location,
            "terrain_type": terrain_type,
            "climate": climate,
            "structure_type": structure_type,
            "house_size": house_size,
            "safety_considerations": safety_considerations,
            "additional_notes": additional_notes,
        }
        
        # Add conditional fields based on structure type
        if structure_type == "Residential":
            prompt.update({
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "kitchen_size": kitchen_size
            })
        else:
            prompt.update({
                "floors": floors,
                "office_space": office_space,
                "parking": parking
            })
        
        with open('blueprint_request.pkl', 'wb') as f:
            pickle.dump(prompt, f)
        
        try:
           
            blueprint_generator_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blueprint_generator.py')
            
            os.system(f'{sys.executable} {blueprint_generator_path}')
            
            
            if os.path.exists('interior_blueprint.png') and os.path.exists('exterior_blueprint.png'):
                interior_img = Image.open('interior_blueprint.png')
                exterior_img = Image.open('exterior_blueprint.png')
                
                st.subheader("Generated Blueprints")
                
                cols = st.columns(2)
                with cols[0]:
                    st.image(interior_img, caption="2D Blueprint", use_column_width=True)
                with cols[1]:
                    st.image(exterior_img, caption="3D Blueprint", use_column_width=True)
                
                
                if os.path.exists('blueprint_result.pkl'):
                    with open('blueprint_result.pkl', 'rb') as f:
                        result = pickle.load(f)
                    
                    st.subheader("Blueprint Details")
                    st.write(result['blueprint_description'])
                    
                    
                    with st.expander("View prompts used"):
                        st.write("**Interior Prompt:**")
                        st.write(result['interior_prompt'])
                        st.write("**Exterior Prompt:**")
                        st.write(result['exterior_prompt'])
                    
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        with open('interior_blueprint.png', 'rb') as f:
                            interior_bytes = f.read()
                        st.download_button(
                            label="Download 2D Blueprint",
                            data=interior_bytes,
                            file_name="interior_blueprint.png",
                            mime="image/png"
                        )
                    
                    with col2:
                        with open('exterior_blueprint.png', 'rb') as f:
                            exterior_bytes = f.read()
                        st.download_button(
                            label="Download 3D Blueprint",
                            data=exterior_bytes,
                            file_name="exterior_blueprint.png",
                            mime="image/png"
                        )
                    
                    
                    with open('combined_blueprint.png', 'rb') as f:
                        combined_bytes = f.read()
                    st.download_button(
                        label="Download Combined Blueprint",
                        data=combined_bytes,
                        file_name="combined_blueprint.png",
                        mime="image/png"
                    )
                else:
                    st.error("Blueprint generation failed. Please check the logs.")
            else:
                st.error("Blueprint generation failed. No blueprint images were created.")
        except Exception as e:
            st.error(f"Failed to generate blueprint: {str(e)}")