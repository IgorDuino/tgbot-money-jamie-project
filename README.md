# Carousell screenshot tgbot generator

This is a simple script to generate a screenshot of a Carousell and send it to a Telegram chat.

### To deploy

1) Clone repo

    ```
    git clone https://github.com/IgorDuino/tgbot-money-jamie-project.git
    # or
    git@github.com:IgorDuino/tgbot-money-jamie-project.git
    ```

2) Configure .env file

    ```
    cp .env.example .env
    # change values in .env file
    ```

3) run docker container

    ```
    docker-compose up -d --build
    # or
    docker compose up -d --build
    ```

Or you can run it without docker

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
