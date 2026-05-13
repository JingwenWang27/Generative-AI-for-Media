# HealthMate: A Multimodal Generative AI Prototype for Personalised Lifestyle Media

## Abstract
HealthMate is a research-informed full-stack web application that explores the integration of generative AI into personalised lifestyle media. The system functions as a smart wardrobe and wellbeing assistant, combining a Python FastAPI backend, a vanilla web frontend, local SQLite databases, and a hosted vision-language model (Volcano Engine Ark API). 

The project demonstrates a hybrid pipeline that separates AI-based garment interpretation from deterministic, weather-based recommendation logic. It implements a strict human-in-the-loop interaction model, ensuring that AI outputs are presented as editable suggestions rather than authoritative decisions, thereby preserving user agency and mitigating automation bias.

---

## System Architecture

The system is built upon a lightweight, modular architecture designed for local prototyping and research evaluation:

*   **Frontend**: Browser-based interface developed with vanilla HTML, CSS, and JavaScript.
*   **Backend**: Python FastAPI handling API routing, orchestration, and external service communication.
*   **Database**: Two local SQLite databases (`wardrobe.db` and `healthmate.db`) for data persistence and separation of concerns.
*   **AI Integration**: Vision-Language Model (Doubao-1.5-vision-pro-32k) utilized for structured metadata extraction from garment images.
*   **Context Services**: OpenWeatherMap API for real-time environmental data to inform deterministic recommendation logic.

---

## Key Contributions

1.  **Human-in-the-Loop Design**: AI-generated clothing attributes (category, material, warmth) are explicitly framed as suggestions. Users must review, correct, and confirm these details before database insertion.
2.  **Hybrid Recommendation Pipeline**: Generative AI is restricted to image interpretation and contextual language generation. Outfit recommendations are handled exclusively by deterministic filtering based on temperature thresholds (`temp_min <= current_temp <= temp_max`).
3.  **Context-Aware Wellbeing Prompts**: The system generates lightweight, stateless behavioral nudges based on recent user activity and local weather conditions, avoiding authoritative medical advice.

---

## Installation and Setup

### Prerequisites
*   Python 3.8 or higher
*   Git

### Local Deployment
1.  **Clone the repository**
    ```bash
   git clone https://github.com/JingwenWang27/Generative-AI-for-Media.git
    cd HealthMate
    ```

2.  **Install dependencies**
    ```bash
    pip install fastapi uvicorn openai httpx python-multipart
    ```

3.  **Configure Environment Variables and API Keys**
    For security and academic integrity, personal API keys have been removed from this repository. Prior to running the application, you must supply your own credentials in the source code:
    *   Obtain an API key from Volcano Engine and assign it to the `DOUBAO_API_KEY` variable.
    *   Obtain an API key from OpenWeatherMap and assign it to the `OWM_API_KEY` variable.

4.  **Initialize the Server**
    ```bash
    uvicorn main:app --reload
    ```
    The application will be accessible at `http://127.0.0.1:8000`.

---


