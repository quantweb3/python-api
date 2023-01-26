conda activate
conda deactivate
conda  activate  chanlun
brew services restart  redis
uvicorn main:app --reload --port 3001 
