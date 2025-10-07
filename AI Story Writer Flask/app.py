from flask import Flask, render_template, request, jsonify
from config import Config
import json
import urllib.request

# Try to import the openai package; if it's not available, we'll call the HTTP API directly
try:
    import openai
    openai_available = True
except Exception:
    openai = None
    openai_available = False

app = Flask(__name__)
app.config.from_object(Config)

# If openai package is available, configure its api key
if openai_available:
    openai.api_key = app.config.get('OPENAI_TOKEN')


def call_openai_chat(messages, model="gpt-3.5-turbo", temperature=0.9, max_tokens=1000):
    """Call OpenAI ChatCompletion either via the openai package (if installed)
    or via a direct HTTP request to the OpenAI API using urllib (no extra deps).
    Returns the text content of the first choice, or raises on failure.
    """
    api_key = app.config.get('OPENAI_TOKEN')

    if openai_available:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        # openai package returns nested dict-like structure
        return resp['choices'][0]['message']['content'].strip()

    # Fallback: call the HTTP API with urllib
    url = 'https://api.openai.com/v1/chat/completions'
    body = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens
    }
    data = json.dumps(body).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp_data = r.read().decode('utf-8')
            resp = json.loads(resp_data)
            return resp['choices'][0]['message']['content'].strip()
    except urllib.error.HTTPError as e:
        # Try to surface a meaningful error message
        try:
            err = e.read().decode('utf-8')
            err_json = json.loads(err)
            print('OpenAI HTTP error:', err_json)
        except Exception:
            print('OpenAI HTTP error status:', e.code)
        raise

KNOWN_AUTHORS = ["Shakespeare", "Stephen King", "J.K. Rowling", "George Bernard Shaw"]

@app.route('/check_author', methods=['POST'])
def check_author():
    author = request.json.get('author', '').strip()
    result = is_established_author(author)
    return jsonify({'established': result})

def is_established_author(author):
    # First, check against the local list
    established_authors = [a.lower() for a in KNOWN_AUTHORS]
    if author.lower() in established_authors:
        return True

    # Use OpenAI to check if the author is established
    prompt = f"Is '{author}' a published or well-known author? Reply with 'yes' or 'no'."
    try:
        messages = [
            {"role": "system", "content": "You are an expert literary assistant."},
            {"role": "user", "content": prompt}
        ]
        answer = call_openai_chat(messages, model="gpt-3.5-turbo", temperature=0.0, max_tokens=10)
        return answer.strip().lower().startswith('yes')
    except Exception as e:
        print(f"OpenAI error: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    story = None
    selected_author = None
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        author = request.form.get('author', '').strip()
        established_author_flag = request.form.get('establishedAuthor', 'false').lower() == 'true'
        if not established_author_flag :
            selected_author = request.form.get('selected_author')
            if selected_author:
                story = generate_story(subject, selected_author)
                storyTitle = f"Story about {subject} in the style of {selected_author} \n\n {story}"
            else:
                story = generate_story(subject, author)
                storyTitle = f"Story about {subject} in the style of {author} \n\n {story}"
    # storyTitle may be defined only when POST; pass story (or None) into template
    return render_template('index.html', story=story, authors=KNOWN_AUTHORS, selected_author=selected_author)

def generate_story(subject, author):
    prompt = (
            f"Write a short story about {subject} in the style of {author}. "
            "Then act as an editor: make the story more engaging, fix grammar, enhance the plot, "
            "and preserve the original style. Return only the final story text."
            )

    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a creative and imaginative story writer who also acts as a skilled editor. "
                    "Your job is to craft engaging stories and refine them for clarity, emotion, and style. "
                    "Always preserve the tone and author's voice while improving the narrative."
                )
            },
            {
                "role": "assistant",
                "content": (
                    "Before finalizing the story, ensure it reads smoothly, with vivid imagery, "
                    "natural dialogue, and emotional depth. Make minor grammar or pacing improvements as needed."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        story = call_openai_chat(messages, model="gpt-3.5-turbo", temperature=0.9, max_tokens=1000)
        return story
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Contact Administrator.\n\nSorry, could not generate story."

if __name__ == '__main__':
    app.run(debug=True)
