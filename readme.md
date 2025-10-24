<div align="center">

![UMKM-GO-AI](assets/images/icon.png)

</div>
# UMKM-Go AI 🚀

**Proactive AI Business Partner for Indonesian SMEs**

_Submission for the AI Accelerate: Unlocking New Frontiers Hackathon_

---

## 🎯 The Problem

Millions of Usaha Mikro, Kecil, dan Menengah (UMKM) or Small and Medium Enterprises (SMEs) form the backbone of the Indonesian economy. However, many owners operate as "one-person armies," juggling production, sales, marketing, and administration. They often lack the time, resources, and specialized knowledge to navigate complex regulations, devise effective marketing strategies, establish a strong brand identity, or discover new business opportunities, hindering their growth potential.

---

## ✨ Our Solution: UMKM-Go AI

UMKM-Go AI is a **multi-agent AI co-pilot** designed specifically for Indonesian SMEs. It acts as a virtual team of consultants accessible through a simple conversational mobile & web application. Powered by cutting-edge AI from **Google Cloud** and the advanced search capabilities of **Elastic**, UMKM-Go AI provides actionable advice, automates opportunity discovery, and even helps build a brand identity from scratch.

---

##  Features

Our application features several specialized AI agents working together under an intelligent orchestrator:

1.  **🏛️ Legal Agent:**
    * Answers questions about Indonesian business laws, regulations, permits (NIB, PIRT), taxes, and more.
    * Uses **Retrieval-Augmented Generation (RAG)**, leveraging **Elasticsearch Hybrid Search** (keyword + vector search) on a knowledge base of indexed Indonesian laws and regulations.

2.  **📣 Marketing Agent:**
    * Provides creative and actionable marketing ideas, social media content suggestions, branding tips, and simple market trend insights.
    * Uses **RAG** powered by **Elasticsearch KNN Search** on a knowledge base of curated marketing articles specific to SMEs.

3.  **🎨 Instant Brand Agent:**
    * Generates a complete brand identity kit (suggested names, taglines, logo concepts, Instagram bio) from a single photo of the user's product.
    * Utilizes a sophisticated **multimodal pipeline**:
        * **Gemini 2.5 Pro (Multimodal)** analyzes the product image for labels and colors.
        * **Vertex AI Multimodal Embeddings** generates image embeddings.
        * **Elasticsearch KNN Search** finds visually and semantically similar inspirations (logos, packaging, palettes) from a dedicated visual knowledge base.
        * **Gemini 2.5 Pro (Text)** generates the creative text content, considering the image analysis and visual inspirations.
        * **Imagen on Vertex AI** generates visual logo concepts based on Gemini's descriptions.
        * **Google Cloud Storage (GCS)** hosts the generated logo images.

4.  **🧠 Intelligent Orchestrator:**
    * Acts as the central "brain." Users ask questions naturally without needing to specify an agent.
    * Uses **Gemini 2.5 Pro** with a meta-prompt to classify the user's **intent** (Legal, Marketing, Brand, etc.) and routes the query to the appropriate specialist agent.

5.  **💡 Proactive Agent :**
    * Works autonomously in the background to find relevant business opportunities.
    * Triggered daily by **Cloud Scheduler**.
    * Scans external data sources (currently configured for **RSS Feeds** like Antara News Bisnis) for keywords like "UMKM," "peluang," "bantuan," etc.
    * Sends findings directly to the user's device via **Firebase Cloud Messaging (FCM)** push notifications.

6.  **📊 Operational Agent:**
    * Analyzes simple sales data uploaded by the user (CSV format).
    * Uses **Pandas** for statistical analysis (total revenue, best-sellers).
    * Uses **Gemini 2.5 Pro** to interpret the statistics and generate human-readable business insights and recommendations.

---

## 🛠️ Tech Stack

This project heavily utilizes technologies from both **Google Cloud** and **Elastic**:

### **Google Cloud Platform:**

* **Vertex AI:**
    * **Gemini 2.5 Pro:** Core LLM for RAG responses, intent classification (Orchestrator), creative text generation (Brand Agent), and multimodal image analysis (Brand Agent).
    * **Multimodal Embeddings API:** Generating vector representations for **images** in the visual knowledge base and user uploads (Brand Agent).
    * **Imagen API:** Generating visual logo concepts via text-to-image synthesis (Brand Agent).
* **Cloud Run:** Scalable, serverless hosting for our Python (FastAPI) backend API.
* **Cloud Scheduler:** Triggering the Proactive Agent's daily opportunity scans reliably.
* **Firebase Cloud Messaging (FCM):** Delivering real-time push notifications for the Proactive Agent.
* **Secret Manager:** Securely storing sensitive API keys (like the Elastic API Key).
* **Cloud Storage (GCS):** Storing and serving publicly accessible generated logo images.
* **Artifact Registry:** Storing our containerized backend application images.
* **Cloud Build:** Automating the CI/CD process for building and deploying the backend container to Cloud Run.
* **IAM:** Managing secure access between services and users.
* **Google Cloud APIs:** Underlying APIs enabling communication between services.

### **Elastic:**

* **Elasticsearch (on Elastic Cloud):**
    * **Vector Database:** Storing and searching both **text embeddings** (from legal docs/marketing articles via SentenceTransformer) and **multimodal embeddings** (from images via Vertex AI).
    * **Hybrid Search:** Combining traditional keyword search (BM25) with semantic vector search for high-relevance retrieval in the Legal Agent (using text embeddings).
    * **KNN Search:** Performing efficient vector similarity searches for the Marketing Agent (using text embeddings) and the visual inspiration component of the Brand Agent (using image embeddings).
* **Elastic Cloud:** Managed Elasticsearch service ensuring scalability and reliability.
* **Kibana:** Used during development for data verification, index management, and exploring the knowledge bases.

### **Other Technologies:**

* **Backend:** Python, FastAPI, Pandas
* **Frontend:** Flutter (Mobile & Web), BLoC (State Management)
* **Data Processing:** Python, Selenium, BeautifulSoup4, **PyMuPDF (PDF Text Extraction)**, Requests
* **AI Models (Self-Hosted/OSS):** **SentenceTransformers (for Text Embeddings)**
* **CI/CD:** Docker, Cloud Build

---

## 🚀 Demo & Access

* **Video:** [https://youtu.be/SbNlPSbSK0A]
* **Try the Web App:** [https://umkm-go-ai-460016.web.app/]
* **Source Code:** [(https://github.com/tegezc/umkm-go-ai)]
* **Hackathon:** https://devpost.com/software/umkm-go-ai
---

## ⚙️ Getting Started (Local Development)

*(Instruksi singkat untuk menjalankan di lokal - sesuaikan jika perlu)*

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/tegezc/umkm-go-ai.git
    cd umkm-go-ai
    ```
2.  **Backend Setup:**
    * Navigate to `backend/`.
    * Create and activate a Python virtual environment (`python -m venv env`, `source env/bin/activate` or `env\Scripts\activate`).
    * Install dependencies: `pip install -r requirements.txt`.
    * Create a `.env` file based on `.env.example` and fill in your Elastic credentials and GCP Project ID.
    * Ensure you have downloaded the embedding model to `backend/embedding_model_files` (e.g., using `download_model.py`).
    * Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to your Firebase Admin SDK key file.
    * Run `gcloud auth application-default login`.
    * Start the server: `uvicorn main:app --reload`.
3.  **Frontend Setup:**
    * Navigate to `mobile_app/`.
    * Ensure you have Flutter SDK installed.
    * Place the `google-services.json` file in `mobile_app/android/app/`.
    * Run `flutter pub get`.
    * Run the app on an emulator or web: `flutter run`.

    **Note on Proactive Agent:** The Proactive Agent's scheduled scans (`/api/v1/agent/proactive/scan_opportunities`) are triggered by **Cloud Scheduler** in the deployed Google Cloud environment. For local testing, you can trigger this endpoint manually (e.g., using the `/docs` page or `curl`).
---

## 📜 License

This project is licensed under the Apache License 2.0

---

## 👨‍💻 Author

* **Suparman**