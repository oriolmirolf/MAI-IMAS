python -m venv venv
source venv/bin/activate
curl -fsSL https://ollama.com/install.sh | sh
pip install -r requirements.txt
ollama pull llama3.1
crewai install