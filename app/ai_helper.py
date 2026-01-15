import google.generativeai as genai
import os

# Constants
MAX_CONTENT_LENGTH = 2000

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def continue_story(story_content, genre="general", words=150):
    """Continue a story from where the user left off."""
    if not model:
        return {"success": False, "error": "AI service not configured. Please set GEMINI_API_KEY environment variable."}
    
    prompt = f"""You are a creative story writer. Continue the following {genre} story naturally.
Write approximately {words} words. Match the tone and style of the existing text.
Do not repeat the original text, only provide the continuation.

Story so far:
{story_content}

Continue the story:"""
    
    try:
        response = model.generate_content(prompt)
        return {"success": True, "content": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_story_starter(genre, theme="", words=200):
    """Generate a story opening based on genre and theme."""
    if not model:
        return {"success": False, "error": "AI service not configured. Please set GEMINI_API_KEY environment variable."}
    
    prompt = f"""You are a creative story writer. Write an engaging opening for a {genre} story.
{f'Theme/Setting: {theme}' if theme else ''}
Write approximately {words} words. Make it captivating and hook the reader immediately.
Include vivid descriptions and introduce an interesting character or situation.

Write the story opening:"""
    
    try:
        response = model.generate_content(prompt)
        return {"success": True, "content": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def suggest_titles(story_content, count=5):
    """Generate title suggestions for a story."""
    if not model:
        return {"success": False, "error": "AI service not configured. Please set GEMINI_API_KEY environment variable."}
    
    prompt = f"""Based on the following story content, suggest {count} creative and catchy titles.
Make them intriguing and relevant to the story's theme.
Return only the titles, one per line, numbered.

Story:
{story_content[:MAX_CONTENT_LENGTH]}

Suggest {count} titles:"""
    
    try:
        response = model.generate_content(prompt)
        return {"success": True, "content": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def improve_writing(text):
    """Improve grammar, style, and vocabulary of the text."""
    if not model:
        return {"success": False, "error": "AI service not configured. Please set GEMINI_API_KEY environment variable."}
    
    prompt = f"""You are an expert editor. Improve the following text by:
1. Fixing any grammar or spelling errors
2. Enhancing vocabulary with better word choices
3. Improving sentence structure and flow
4. Making it more engaging and vivid

Keep the original meaning and story intact. Return only the improved text.

Original text:
{text}

Improved text:"""
    
    try:
        response = model.generate_content(prompt)
        return {"success": True, "content": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_writing_suggestions(story_content):
    """Get suggestions for plot, characters, or scenes."""
    if not model:
        return {"success": False, "error": "AI service not configured. Please set GEMINI_API_KEY environment variable."}
    
    prompt = f"""You are a creative writing coach. Based on this story, provide 3-4 brief suggestions for:
- Possible plot developments
- Character depth additions
- Scene or setting ideas

Keep suggestions concise and inspiring.

Story:
{story_content[:MAX_CONTENT_LENGTH]}

Suggestions:"""
    
    try:
        response = model.generate_content(prompt)
        return {"success": True, "content": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}
