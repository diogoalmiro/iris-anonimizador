Models at: https://gitlab.com/diogoalmiro/iris-lfs-storage/

Running with python venv:

 - (install once:)
   - `python -m venv env`
   - `source env/bin/activate`
   - `pip install -U pip`
   - `pip install -r requirements.txt`
 - (running:)
   - `python index.py`

Running with docker:

 - (build once:)  `docker build . -t anonimizador`
 - (running:) `docker run -it -p 7999:7999 anonimizador`

