from flask import Flask, render_template, request, jsonify
from config import Config
import openai

app = Flask(__name__)
app.config.from_object(Config)

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
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert literary assistant."},
                {"role": "user", "content": prompt}
            ],
            api_key=app.config['OPENAI_TOKEN']
        )
        answer = response['choices'][0]['message']['content'].strip().lower()
        return answer.startswith('yes')
    except Exception as e:
        print(f"OpenAI error: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    story = None
    show_dropdown = False
    selected_author = None
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        author = request.form.get('author', '').strip()
        if not is_established_author(author):
            show_dropdown = True
            selected_author = request.form.get('selected_author')
            if selected_author:
                story = generate_story(subject, selected_author)
        else:
            story = generate_story(subject, author)
    return render_template('index.html', story=story, show_dropdown=show_dropdown, authors=KNOWN_AUTHORS, selected_author=selected_author)

def generate_story(subject, author):
    prompt = (
        f"Write a short story about {subject} in the style of {author}. "
        "As an editor, make it more engaging, fix grammar, enhance the plot, and preserve the original style. "
        "Return only the story text."
    )
    try:
        client = openai.OpenAI(api_key=app.config['OPENAI_TOKEN'])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative story writer and editor."},
                {"role": "user", "content": prompt}
            ]
        )
        story = response.choices[0].message.content.strip()
        return f"Title: {subject}\nAuthor: {author}\n\n{story}"
    except Exception as e:
        print(f"OpenAI error: {e}")
        return f"Title: {subject}\nAuthor: {author}\n\nSorry, could not generate story.\n\n {e}"

if __name__ == '__main__':
    app.run(debug=True)
