# contract_analyzer


#run UI
streamlit run app.py

#build container:
docker build -t contract_analyzer:01 ./Dockerfile

#run container:
docker run -p 5000:5000 -v $(pwd):/project contract_analyzer:01