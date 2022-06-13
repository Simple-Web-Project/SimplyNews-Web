# SimplyNews

SimplyNews is a website to read articles from other sites. Without JavaScript, ads or any other interruptions. Just content.

## How to install

### Clone the repository
```bash
git clone https://codeberg.org/SimpleWeb/SimplyNews-Web
```

### Install the dependencies
```sh
cd SimplyNews-Web/
pip install -r requirements.txt
sudo chmod +x drivers/chromedriver
tar -xf drivers/ungoogled-chromium_*.tar.xz -C ./drivers/
sudo apt-get install x11-utils gnumeric
```

### Run the main.py
Directly
```sh
python3 main.py
```
Using uvicorn
```sh
uvicorn main:app --port 5000
```
