# How to Run Stagify + Job Matcher LLM Integration

## 1. Prerequisites
- Node.js (v18 or newer)
- Python 3.9+
- `pip` (Python package manager)
- `npm` (Node.js package manager)

---

## 2. Start the Python LLM App

1. Open a terminal and navigate to the `job_matcher_llm` folder:
   ```sh
   cd job_matcher_llm
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```sh
   streamlit run app.py
   ```
4. The app will open at [http://localhost:8501](http://localhost:8501)

---

## 3. Start the React App

1. Open a new terminal and navigate to the `stagify_leoni-rh` folder:
   ```sh
   cd stagify_leoni-rh
   ```
2. Install dependencies (if not already done):
   ```sh
   npm install
   ```
3. Start the development server:
   ```sh
   npm run dev
   ```
4. The app will open at [http://localhost:5173](http://localhost:5173)

---

## 4. Workflow: Using the Integration

1. In the React app, go to the "Stagiaires" page.
2. For a stagiaire, click the "Coller IA" button (Paste IA).
3. In the Python app, upload a CV and enter a job description, then click "Analyze Job Fit".
4. Copy the JSON result shown in the Python app.
5. Paste the JSON into the modal in the React app and validate.
6. The IA analysis will appear in the stagiaire's card.

---

## 5. Demo Mode
- You can use the provided mock data and paste any valid JSON to test the workflow without running the Python app.

---

## 6. Troubleshooting
- If you encounter errors, ensure all dependencies are installed and both apps are running on their respective ports.
- For further help, provide error messages or screenshots.
