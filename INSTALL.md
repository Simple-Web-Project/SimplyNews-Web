# How to install/use

## Clone simplynews_sites repository and install it
```sh
git clone https://codeberg.org/SimpleWeb/SimplyNews-Sites
cd SimplyNews-Sites
sudo python3 setup.py install
cd ..
```

## Clone the repository
``` sh
git clone https://codeberg.org/SimpleWeb/SimplyNews-Web
cd SimplyNews-Web
```

## Run main.py
- Option 1: Run it directly
  ```sh
  python3 main.py
  ```


- Run it through i.e. uvicorn
  ```sh
  uvicorn main:app --port 5000
  ```

