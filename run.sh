conda activate
conda deactivate
conda  activate  chanlun
brew services restart  redis
uvicorn zen:app --reload --port 3001 
