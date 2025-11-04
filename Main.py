from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key="")

@app.route("/")
def home():
    # Render the HTML page
    return render_template("index.html")

@app.route("/process-image", methods=["POST"])
def process_image():
    image = request.files["image"]
    image_path = f"./{image.filename}"
    image.save(image_path)

    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    file = genai.upload_file(image_path, mime_type="image/jpeg")
    print(file)

    # First message to get the solution
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    file,
                    "This is a math problem. Please solve it and provide step-by-step solution."
                ],
            }
        ]
    )
    solution_response = chat_session.send_message("Please solve the math problem and provide a step-by-step solution.")
    solution_text = solution_response.text.strip()

    # Second message to get the YouTube reference link
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    file,
                    "Please provide a YouTube reference link for this solution."
                ],
            }
        ]
    )
    youtube_response = chat_session.send_message("Provide a YouTube link related to the solution.")
    youtube_linkresponse = youtube_response.text.strip()
    youtube_link=extract_youtube_link(youtube_linkresponse)

    # Return the solution and YouTube link as separate responses
    return jsonify({
        "solution": solution_text,
        "youtube_reference": youtube_link
    })


@app.route("/process-manual-question", methods=["POST"])
def process_manual_question():
    """Process a manually typed question from the UI and return solution + youtube link."""
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided."}), 400

    # Use the same model to answer the manually typed question
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    # Ask for a step-by-step solution
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    question,
                    "This is a math problem. Please solve it and provide step-by-step solution."
                ],
            }
        ]
    )
    solution_response = chat_session.send_message("Please solve the math problem and provide a step-by-step solution.")
    solution_text = solution_response.text.strip()

    # Ask for a YouTube reference related to the solution
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    question,
                    "Please provide a YouTube reference link for this solution."
                ],
            }
        ]
    )
    youtube_response = chat_session.send_message("Provide a YouTube link related to the solution.")
    youtube_linkresponse = youtube_response.text.strip()
    youtube_link = extract_youtube_link(youtube_linkresponse)

    return jsonify({
        "solution": solution_text,
        "youtube_reference": youtube_link
    })
def extract_youtube_link(text):
    import re
    # Use a regex pattern to find YouTube URLs in the text
    match = re.search(r'(https?://www\.youtube\.com/watch\?v=[\w-]+)', text)
    if match:
        return match.group(0)
    return None


@app.route("/process-upload-question", methods=["POST"])
def process_upload_question():
    """Accept a text file upload containing a question and return the solution + youtube link."""
    if "question_file" not in request.files:
        return jsonify({"error": "No file part 'question_file' found."}), 400

    qfile = request.files["question_file"]
    if qfile.filename == "":
        return jsonify({"error": "No file selected."}), 400

    try:
        # Read bytes and decode to string
        content_bytes = qfile.read()
        try:
            question_text = content_bytes.decode("utf-8").strip()
        except Exception:
            # fallback to latin-1 if utf-8 fails
            question_text = content_bytes.decode("latin-1").strip()

        if not question_text:
            return jsonify({"error": "Uploaded file is empty."}), 400

        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        question_text,
                        "This is a math problem. Please solve it and provide step-by-step solution."
                    ],
                }
            ]
        )
        solution_response = chat_session.send_message("Please solve the math problem and provide a step-by-step solution.")
        solution_text = solution_response.text.strip()

        # Ask for YouTube reference
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        question_text,
                        "Please provide a YouTube reference link for this solution."
                    ],
                }
            ]
        )
        youtube_response = chat_session.send_message("Provide a YouTube link related to the solution.")
        youtube_linkresponse = youtube_response.text.strip()
        youtube_link = extract_youtube_link(youtube_linkresponse)

        return jsonify({
            "solution": solution_text,
            "youtube_reference": youtube_link
        })

    except Exception as e:
        print("Error processing uploaded question:", e)
        return jsonify({"error": "Failed to process uploaded question."}), 500

if __name__ == "__main__":
    app.run(debug=True)
