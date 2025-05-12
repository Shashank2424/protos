
from huggingface_hub import InferenceClient
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import pickle
import textwrap
import os

def create_blueprint_with_annotations(interior_image, exterior_image, prompt_details):
    width, height = 768, 768
    if interior_image.size != (width, height):
        interior_image = interior_image.resize((width, height))
    if exterior_image.size != (width, height):
        exterior_image = exterior_image.resize((width, height))
    
    combined_width = width * 2 + 20
    combined_height = height + 200
    combined_image = Image.new('RGB', (combined_width, combined_height), (255, 255, 255))
    
    combined_image.paste(interior_image, (0, 0))
    combined_image.paste(exterior_image, (width + 20, 0))
    
    draw = ImageDraw.Draw(combined_image)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()
    
    y_position = height + 20
    structure_type = prompt_details["structure_type"]
    location = prompt_details["location"]
    size = f"{prompt_details['house_size']} sq ft"
    
    residential_info = ""
    if structure_type == "Residential":
        residential_info = f" | {prompt_details['bedrooms']} bedrooms | {prompt_details['bathrooms']} bathrooms | {prompt_details['kitchen_size']} kitchen"
    
    safety = ", ".join(prompt_details["safety_considerations"])
    
    draw.text((20, y_position), f"Structure: {structure_type} | Location: {location} | Size: {size}{residential_info}", fill=(0, 0, 0), font=font)
    draw.text((20, y_position + 30), f"Climate: {prompt_details['climate']} | Terrain: {prompt_details['terrain_type']}", fill=(0, 0, 0), font=font)
    draw.text((20, y_position + 60), f"Safety Features: {safety}", fill=(0, 0, 0), font=font)
    
    if prompt_details.get("additional_notes"):
        wrapped_notes = textwrap.wrap(prompt_details["additional_notes"], width=100)
        draw.text((20, y_position + 90), "Additional Notes:", fill=(0, 0, 0), font=font)
        for i, line in enumerate(wrapped_notes):
            draw.text((20, y_position + 110 + i*20), line, fill=(0, 0, 0), font=font)
    
    draw.text((width//2 - 80, 10), "Interior Blueprint", fill=(255, 255, 255), font=font)
    draw.text((width + width//2 - 80, 10), "Exterior Blueprint", fill=(255, 255, 255), font=font)
    
    return combined_image

def build_interior_prompt(data):
    base_prompt = (
        f"Flat 2D top-down blueprint view of a {data['structure_type']} located in {data['location']} "
        f"on {data['terrain_type']} terrain, designed for a {data['climate']} climate. "
    )
    if data["structure_type"] == "Residential":
        base_prompt += (
            f"Includes {data['bedrooms']} bedrooms, {data['bathrooms']} bathrooms, and a {data['kitchen_size']} kitchen. "
            f"Total area of {data['house_size']} sq ft. "
        )
    else:
        base_prompt += (
            f"{data['floors']} floors with {data['office_space']} office spaces. "
            f"Total area of {data['house_size']} sq ft. "
        )
    if data["safety_considerations"]:
        safety = ", ".join(data["safety_considerations"])
        base_prompt += f"Safety features included: {safety}. "
    
    base_prompt += (
        "Blueprint should have a clean flat style: white technical lines on blueprint blue background. "
        "Clearly label each room (bedroom, kitchen, bath, living room, etc.). "
        "Show basic furniture symbols like beds, toilets, sofas, and kitchen appliances. "
        "Highly organized, simple walls and clear door placements. No 3D effects, no shading, no shadows."
    )
    return base_prompt

def build_exterior_prompt(data):
    base_prompt = (
        f"Isometric 3D architectural model of a {data['structure_type']} located in {data['location']}, "
        f"designed for a {data['climate']} climate on {data['terrain_type']} terrain. "
    )
    if data["structure_type"] == "Residential":
        base_prompt += (
            f"Modern single-family home with {data['bedrooms']} bedrooms, {data['bathrooms']} bathrooms. "
        )
    else:
        base_prompt += (
            f"{data['floors']}-floor commercial building, contemporary design. "
        )
    
    base_prompt += (
        "Render style: clean, minimalist 3D architectural visualization. "
        "Solid walls, glass windows, visible material hints but no heavy photorealism. "
        "Neutral background, blueprint aesthetic. No heavy colors, no photorealistic textures."
    )
    return base_prompt

def generate_image(prompt):
    client = InferenceClient(
        "stabilityai/stable-diffusion-xl-base-1.0",
        token="hugging face api key"
    )
    
    image = client.text_to_image(prompt=prompt)
    return image

def main():
    if not os.path.exists('blueprint_request.pkl'):
        print("No blueprint request found.")
        return
    
    with open('blueprint_request.pkl', 'rb') as f:
        prompt_details = pickle.load(f)
    
    interior_prompt = build_interior_prompt(prompt_details)
    exterior_prompt = build_exterior_prompt(prompt_details)
    
    print("Generating interior blueprint...")
    interior_result = generate_image(interior_prompt)
    
    print("Generating exterior blueprint...")
    exterior_result = generate_image(exterior_prompt)
    
    print("Creating annotated blueprint...")
    combined_blueprint = create_blueprint_with_annotations(interior_result, exterior_result, prompt_details)
    
    interior_result.save("interior_blueprint.png")
    exterior_result.save("exterior_blueprint.png")
    combined_blueprint.save("combined_blueprint.png")
    
    buffered = BytesIO()
    combined_blueprint.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    description = f"""
    Blueprint details:
    - Type: {prompt_details['structure_type']}
    - Location: {prompt_details['location']}
    - Size: {prompt_details['house_size']} sq ft
    - Climate: {prompt_details['climate']}
    - Terrain: {prompt_details['terrain_type']}
    - Safety features: {', '.join(prompt_details['safety_considerations'])}
    """
    if prompt_details["structure_type"] == "Residential":
        description += f"""
    - Bedrooms: {prompt_details['bedrooms']}
    - Bathrooms: {prompt_details['bathrooms']}
    - Kitchen size: {prompt_details['kitchen_size']}
    """
    else:
        description += f"""
    - Floors: {prompt_details['floors']}
    - Office space: {prompt_details['office_space']}
    - Parking: {"Included" if prompt_details.get('parking') else "Not included"}
    """
    if prompt_details.get("additional_notes"):
        description += f"\nAdditional notes: {prompt_details['additional_notes']}"
    
    result = {
        'blueprint_image': img_str,
        'blueprint_description': description,
        'interior_prompt': interior_prompt,
        'exterior_prompt': exterior_prompt
    }
    
    with open('blueprint_result.pkl', 'wb') as f:
        pickle.dump(result, f)
    
    print(" Blueprint generation completed")

if __name__ == '__main__':
    main()