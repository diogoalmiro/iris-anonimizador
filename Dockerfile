FROM node:lts as builder

RUN git clone https://github.com/diogoalmiro/JurisPrudencia.git

WORKDIR /JurisPrudencia
RUN npm install
RUN npm run build

FROM python:3

WORKDIR /urs/src/app

RUN apt-get update && apt-get install -y pandoc git-lfs

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN git clone https://gitlab.com/diogoalmiro/iris-lfs-storage.git
RUN cd iris-lfs-storage && git lfs pull --include="model-best/"
RUN mv iris-lfs-storage/model-best/ .

COPY . . 

COPY --from=builder /JurisPrudencia/build/ ./build/

EXPOSE 7999

CMD ["python", "index.py"]
