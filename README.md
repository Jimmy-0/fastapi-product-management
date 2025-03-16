# fastapi-product-management
## Conclusion
| Feature | Requirement (Original Quote) | Status | Evidence |
|---------|------------------------------|--------|-------------------|
| **Product CRUD** | 提供 CRUD 操作（創建、查詢、更新、刪除）。 | ✅ Accomplished | API endpoints for GET, POST, PUT, DELETE on `/api/v1/products/` |
| **Validation** | 名稱（必填，3~100 字符）價格（必須為正數，最多兩位小數）庫存數量（非負整數）折扣（0% - 100%） | ✅ Accomplished | Products API with validation (confirmed in tests) |
| **Pagination** | 分頁（支持分頁查詢）。 | ❌ Not accomplish |  |
| **Sorting** | 排序（可根據價格、庫存、時間排序）。 | ✅ Accomplished | Implemented in GET `/api/v1/products/` |
| **Filtering** | 條件篩選（如依產品分類、價格區間、庫存範圍查詢）。 | ✅ Accomplished | Implemented in GET `/api/v1/products/` |
| **Fuzzy Search** | 模糊查詢（如根據產品名稱或描述進行關鍵字匹配）。 | ❌ Not accomplish |  |
| **Batch Create** | 批量新增：允許一次創建多個產品。 | ✅ Accomplished | POST `/api/v1/products/batch` endpoint |
| **Batch Update** | 批量更新：一次更新多個產品的屬性（如批量調整價格、修改庫存）。 | ✅ Accomplished | PUT `/api/v1/products/batch` endpoint |
| **Batch Delete** | 批量刪除：允許一次性刪除多個產品。 | ✅ Accomplished | DELETE `/api/v1/products/batch` endpoint |
| **Price History** | 當產品的價格...變更時，應自動存入歷史記錄。 | ✅ Accomplished | GET `/api/v1/history/price/{product_id}` endpoint |
| **Stock History** | 當產品的...庫存變更時，應自動存入歷史記錄。 | ✅ Accomplished | GET `/api/v1/history/stock/{product_id}` endpoint |
| **History Time Range API** | 提供 API 查詢特定時間範圍內的價格與庫存變動。 | ✅ Accomplished | GET `/api/v1/history/combined/{product_id}` endpoint |
| **Supplier Management** | 供應商資訊包括：<br>供應商名稱<br>聯絡資訊<br>信用評級（0~5 顆星） | ✅ Accomplished | Complete CRUD for suppliers via `/api/v1/suppliers/` endpoints |
| **Multiple Suppliers** | 一個產品可有 多個供應商（多對多關係）。 | ✅ Accomplished | Supplier management implementation |
| **Top-Rated Suppliers** | (Additional feature) | ✅ Accomplished | GET `/api/v1/suppliers/top-rated` endpoint |
| **Database Technology** | 使用 PostgreSQL 或 MySQL，搭配 SQLAlchemy ORM。 | ✅ Accomplished | PostgreSQL configured in docker-compose.yml and SQLAlchemy in database.py |
| **Database Indexing** | 設計適當的索引來提高查詢效能。 | ❌ Not accomplish |  |
| **Connection Pooling** | 資料庫連接池管理，確保高併發請求時效能穩定。 | ✅ Accomplished | Implemented in database.py |
| **JWT Authentication** | OAuth2 + JWT 進行身份驗證。 | ✅ Accomplished | Authentication endpoints and lock icons on protected routes |
| **RBAC** | RBAC（角色權限管理）：確保不同角色（管理員、供應商、一般使用者）能夠存取不同資源。 | ✅ Accomplished | Admin-specific endpoints under `/api/v1/admin/` |
| **API Documentation** | 使用OpenAPI+Swagger 撰寫API文件 | ✅ Accomplished | Screenshots show Swagger UI documentation |
| **Test Coverage** | 基本功能測試（CRUD）<br>錯誤處理測試（錯誤輸入、產品不存在等） | ✅ Accomplished | Comprehensive test suite |
| **Concurrency Testing** | 併發測試（模擬高流量請求） | ❌ Not accomplish |  |
| **Docker Support** | 使用 Docker 建立應用容器，包含 FastAPI 服務、資料庫... | ✅ Accomplished | Dockerfile |
| **Docker Compose** | 提供 Docker Compose 檔案 ( docker-compose.yml )，確保所有服務能夠一鍵啟動。 | ✅ Accomplished | docker-compose.yml |
| **Optimized Dockerfile** | Dockerfile 需支援最佳化，例如使用 多階段構建 減少映像大小。 | ⚠️ Partially accomplished | Basic optimizations but no multi-stage build |
| **Environment Variables** | 提供 環境變數設定（如 .env 文件），確保能靈活配置。 | ✅ Accomplished | Environment variables in docker-compose.yml |


## Tech Stack Overview
- Backend: Python with FastAPI
- Architecture: Microservice approach
- Database: PostgreSQL
- Containerization: Docker

## Architecture Layer
- Repository 模式：分離數據訪問邏輯和業務邏輯
- Service 層：實現各種業務邏輯和事務處理
- FastAPI 端點：處理 HTTP 請求並實現 RESTful API

## 資料流程
- 客戶端發送 HTTP 請求到 API 端點
- API 端點驗證請求並將其傳遞給 Service 層
- Service 層實現業務邏輯並呼叫適當的 Repository 方法
- Repository 層執行數據庫操作
- 結果沿著相同的路徑返回給客戶端

## 本地安裝

- 複製專案：

```bash
git clone https://github.com/your-username/fastapi-product-management.git

cd fastapi-product-management
```

- 安裝：

```bash
pip install -r requirements.txt
```

- 設定環境變數（或建立 .env 檔案）：

```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=product_service
POSTGRES_PORT=5432
```
- 啟動應用：

```bash
uvicorn app.main:app --reload
```
- Docker 安裝: 使用 Docker Compose ：
```bash
docker-compose up -d
```

- API 使用說明
啟動應用後，可以通過以下方式瀏覽 API 文檔：

Swagger UI: http://localhost:8000/docs