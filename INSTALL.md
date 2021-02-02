## How to install/use

1. Clone the repository
``` 
git clone https://git.sr.ht/~metalune/simplynews_web
cd simplynews_web
```

2. Download the simplynews_sites repository inside the simplynews_web folder and rename it to sites
```
git clone https://git.sr.ht/~metalune/simplynews_sites
mv simplynews_sites sites
```

3. Run main.py
Option 1: Run it directly
`python3 main.py`
Option 2: Run it through i.e. uvicorn
`uvicorn main:app --port 5000`
