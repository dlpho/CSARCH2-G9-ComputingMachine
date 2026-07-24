# How to Run

Please make sure you are using a compatible version (Python 3.14, specifically 3.14.6).

1. Create a virtual environment.  

    Check first your default version `python --version`. 
    If your default version is 3.14:
    ```pwsh
    python -m venv .venv
    ```

    If not (but you have downloaded it):
    ```pwsh
    python3.14 -m venv .venv
    ```

2. Activate & install requirements.
    ```pwsh
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```
3. Start the Streamlit app
    ```pwsh
    streamlit run app.py
    ```
