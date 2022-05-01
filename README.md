# SimplyNews

SimplyNews is a website to read articles from other sites. Without JavaScript, ads or any other interruptions. Just content.

## How to install

### Clone the repository
```bash
git clone https://codeberg.org/SimpleWeb/SimplyNews-Web
```

### Install the dependencies
```sh
sudo apt-get install xvfb xserver-xephyr tigervnc-standalone-server x11-utils gnumeric
cd SimplyNews-Web/
pip install -r requirements.txt
sudo chmod +x drivers/chromedriver
tar -xf drivers/ungoogled-chromium_*.tar.xz
```

### Run the main.py
```sh
# Directly
python3 main.py
# Using uvicorn
uvicorn main:app --port 5000
```
