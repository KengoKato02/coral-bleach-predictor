# 🪸 Coral Bleach Predictor

This application predicts coral bleaching risk using two models:

- **Coral Bleaching Predictor** – our custom-trained ML model.
- **LLaMA 3.1** – a large language model accessed via [Ollama](https://ollama.com/).


---

## 🔧 Setup Instructions

### 1. Start Ollama with LLaMA 3.1

Make sure [Ollama](https://ollama.com/) is installed and running.

Start the LLaMA 3.1 model using:

```bash
ollama run llama3.1
```

By default, Ollama runs on **http://localhost:11434**.

---

### 2. Generate the Custom ML Model Files

Due to their size, the trained model files are **not included in this repository**.  
You must generate them before running the app:

- `src/models/scaler.pkl`
- `src/models/coral_bleaching_predictor.pkl`

To generate these files, run the notebook:

```bash
notebooks/noaa_evaluation.ipynb
```

Once generated, place the files in the following directory:

```
app/backend/models/
├── coral_bleaching_predictor.pkl
└── scaler.pkl
```

---

### 3. Install Python Dependencies

Navigate to the backend directory and install required packages:

```bash
cd app/backend
pip install -r requirements.txt
```

---

### 4. Run the Backend API

Start the backend server:

```bash
cd api
python app.py
```

This will launch the backend on **http://localhost:8000**.

---

### 5. Test the Application in Your Browser

Open your browser and visit:

```
http://localhost:8000
```

You can now test coral bleaching predictions using:

- **Coral Bleaching Predictor** (our custom ML model)
- **LLaMA 3.1** (via Ollama)

and use interactive chat powered by **LLaMA 3.1**, capable of answering questions related to coral reefs, ocean data, and bleaching risk.

---

## 🛠 Notes

- The backend handles predictions from both models.
- Make sure Ollama is running before using the Coral Reef AI Assistant.
- If any issues occur:
  - Confirm ports `8000` and `11434` are open.
  - Ensure LLaMA 3.1 is fully loaded before sending requests.

- Notebook Notes Before Running:
  - Please make sure to create a virtual env and attach in the notebook kernel
  - Run ```pip install -e .``` from the root of the repo

---
