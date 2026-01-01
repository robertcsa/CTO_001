# Trading Bot System

Egy teljes körű, kódalapú Trading Bot rendszer FastAPI backend-del és React frontend-del.

## 🚀 Funkciók

### Backend (FastAPI + Python 3.11+)
- **Bot Management**: Trading botok létrehozása, konfigurálása és vezérlése
- **Market Data**: Valós idejű piaci adatok lekérése és tárolása
- **Technical Indicators**: Support/Resistance, Linear Regression, Volatility számítások
- **Trading Strategies**: Blue Sky breakout stratégia (MVP)
- **Paper Trading**: Valós pénz nélküli kereskedés szimuláció
- **Scheduling**: APScheduler alapú bot futtatás
- **Authentication**: JWT token alapú hitelesítés
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Caching**: Redis gyorsítótár
- **Logging**: Strukturált naplózás bot_id, run_id, stage-ekkel

### Frontend (React/Next.js)
- **Bot Dashboard**: Botok listája és kezelése
- **Real-time Updates**: Polling-alapú frissítés (3-5 másodperc)
- **Interactive Charts**: Recharts alapú candle chart support/resistance szintekkel
- **Signal Tracking**: Kereskedési jelek megjelenítése
- **Order Management**: Nyitott/zárt pozíciók kezelése
- **Portfolio Summary**: P&L statisztikák és teljesítménymutatók

## 📋 Követelmények

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Node.js 18+ (frontend-hez)

## 🛠️ Telepítés és Futtatás

### Backend Setup

1. **Környezeti változók beállítása:**
```bash
cp .env.template .env
# Szerkeszd a .env fájlt a saját beállításokkal
```

2. **Python függőségek telepítése:**
```bash
pip install -r requirements.txt
```

3. **Adatbázis inicializálása:**
```bash
python init_db.py init
```

4. **Backend indítása:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Frontend könyvtár:**
```bash
cd frontend
```

2. **NPM függőségek telepítése:**
```bash
npm install
```

3. **Környezeti változók:**
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

4. **Frontend indítása:**
```bash
npm run dev
```

## 📁 Projekt Struktúra

```
/home/engine/project
├── main.py                 # FastAPI app
├── init_db.py             # DB inicializálás
├── requirements.txt       # Python függőségek
├── .env.template         # Környezeti változók template
├── core/                 # Alapvető konfigurációk
│   ├── config.py         # Settings
│   ├── db.py            # SQLAlchemy setup
│   ├── logging.py       # Strukturált logging
│   ├── security.py      # JWT auth
│   └── errors.py        # Custom exceptions
├── models/              # ORM modellek
│   ├── user.py         # User model
│   ├── bot.py          # Bot model
│   ├── candle.py       # MarketCandle model
│   ├── indicator.py    # Indicator model
│   ├── signal.py       # Signal model
│   └── order.py        # Order model
├── schemas/             # Pydantic modellek
│   ├── auth.py         # Auth schemas
│   ├── bot.py          # Bot schemas
│   ├── market.py       # Market data schemas
│   ├── signal.py       # Signal schemas
│   └── order.py        # Order schemas
├── services/            # Üzleti logika
│   ├── market_data.py  # Piaci adatok
│   ├── indicators.py   # Technical indicators
│   ├── execution.py    # Paper trading
│   ├── scheduler.py    # APScheduler
│   ├── audit.py        # Audit logging
│   └── strategies/     # Trading strategies
│       ├── base.py     # Strategy base
│       └── blue_sky.py # Blue Sky strategy
├── api/                # API réteg
│   ├── deps.py         # Dependencies
│   └── routes/         # API routes
│       ├── auth.py     # Auth endpoints
│       ├── bots.py     # Bot endpoints
│       ├── market.py   # Market endpoints
│       └── trading.py  # Trading endpoints
└── frontend/           # React frontend
    ├── components/     # React komponensek
    ├── hooks/         # Custom hooks
    ├── pages/         # Page komponensek
    ├── types/         # TypeScript típusok
    ├── utils/         # Utility függvények
    └── styles/        # CSS stílusok
```

## 🔧 Konfiguráció

### Backend (.env)
```env
# Database
POSTGRES_USER=tradingbot
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_DB=tradingbot_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=your_very_long_secret_key

# Market Data
MARKET_DATA_BASE_URL=https://api.binance.com
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Paper Trading
PAPER_TRADING_BALANCE=10000.0
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 API Végpontok

### Authentication
- `POST /auth/login-json` - Bejelentkezés
- `POST /auth/register` - Regisztráció
- `GET /auth/me` - Aktuális felhasználó

### Bots
- `GET /bots` - Botok listája
- `POST /bots` - Új bot létrehozása
- `GET /bots/{id}` - Bot részletek
- `PUT /bots/{id}` - Bot frissítése
- `DELETE /bots/{id}` - Bot törlése
- `POST /bots/{id}/start` - Bot indítása
- `POST /bots/{id}/stop` - Bot leállítása

### Market Data
- `GET /market/candles` - Piaci adatok lekérése
- `POST /market/refresh` - Adatok frissítése
- `GET /market/indicators` - Technical indicators

### Trading
- `GET /trading/signals` - Kereskedési jelek
- `GET /trading/orders` - Kereskedési megbízások
- `GET /trading/portfolio/{bot_id}` - Portfolio összefoglaló

## 🎯 Trading Stratégiák

### Blue Sky Strategy (MVP)
- **Rule**: `close_now > max(high[-N:]) → BUY else HOLD`
- **Parameters**:
  - `lookback`: 20 (alapértelmezett)
  - `min_confidence`: 0.6 (alapértelmezett)
- **Best for**: Trending markets with clear breakouts

## 📈 Technikai Indikátorok

1. **Support/Resistance**: Árszintek és azok erőssége
2. **Linear Regression**: Trend irány és R² érték
3. **Volatility**: Szórás és ATR (Average True Range)

## 🧪 Tesztelés

```bash
# Backend tesztek
pytest tests/

# Frontend tesztek
cd frontend && npm test
```

## 🚀 Produkció

### Docker (opcionális)
```bash
# Backend
docker build -t trading-bot-backend .
docker run -p 8000:8000 trading-bot-backend

# Frontend
cd frontend && docker build -t trading-bot-frontend .
docker run -p 3000:3000 trading-bot-frontend
```

### Production Settings
- `DEBUG=false`
- Proper database credentials
- SSL/TLS konfiguráció
- Rate limiting beállítása
- Log monitoring setup

## 📝 Licensz

MIT License - lásd LICENSE fájl részletekért.

## 🤝 Hozzájárulás

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Támogatás

- GitHub Issues: [Issues page](https://github.com/your-repo/issues)
- Documentation: [Wiki](https://github.com/your-repo/wiki)
- Discord: [Community server](https://discord.gg/your-server)

---

**⚠️ Figyelmeztetés**: Ez egy oktatási/példa projekt. Kereskedés előtt mindig konzultáljon pénzügyi tanácsadással. A valós kereskedés kockázatos lehet.