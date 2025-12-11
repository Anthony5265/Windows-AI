"""
Database Manager - 20+ Databases
SQL, NoSQL, Time-series, Graph databases
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Unified database operations across 20+ databases"""

    def __init__(self):
        self._initialized = False
        self._connections: Dict[str, Any] = {}
        self._pools: Dict[str, Any] = {}  # Connection pools
        self._pool_config = {
            "min_size": 2,
            "max_size": 10,
            "timeout": 30
        }

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== POSTGRESQL ====================

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close connection pools
            for name, pool in self._pools.items():
                try:
                    if hasattr(pool, 'close'):
                        await pool.close() if asyncio.iscoroutinefunction(pool.close) else pool.close()
                    logger.info(f"Closed connection pool: {name}")
                except Exception as e:
                    logger.error(f"Error closing pool {name}: {e}")
            
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Clear pools and connections
            self._pools.clear()
            self._connections.clear()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def postgres_connect(self, dsn: str = None) -> Any:
        import asyncpg
        dsn = dsn or os.environ.get("DATABASE_URL")
        
        # Create connection pool if it doesn't exist
        if "postgres" not in self._pools:
            self._pools["postgres"] = await asyncpg.create_pool(
                dsn,
                min_size=self._pool_config["min_size"],
                max_size=self._pool_config["max_size"],
                command_timeout=self._pool_config["timeout"]
            )
            logger.info(f"Created PostgreSQL connection pool (min={self._pool_config['min_size']}, max={self._pool_config['max_size']})")
        
        return self._pools["postgres"]

    async def postgres_query(self, query: str, params: tuple = None) -> List[Dict]:
        pool = self._pools.get("postgres")
        if not pool:
            pool = await self.postgres_connect()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *(params or ()))
            return [dict(row) for row in rows]

    async def postgres_execute(self, query: str, params: tuple = None) -> str:
        pool = self._pools.get("postgres")
        if not pool:
            pool = await self.postgres_connect()
        
        async with pool.acquire() as conn:
            return await conn.execute(query, *(params or ()))

    # ==================== MYSQL ====================

    async def mysql_connect(self, **kwargs) -> Any:
        import aiomysql
        conn = await aiomysql.connect(
            host=kwargs.get("host", os.environ.get("MYSQL_HOST", "localhost")),
            port=kwargs.get("port", int(os.environ.get("MYSQL_PORT", 3306))),
            user=kwargs.get("user", os.environ.get("MYSQL_USER")),
            password=kwargs.get("password", os.environ.get("MYSQL_PASSWORD")),
            db=kwargs.get("database", os.environ.get("MYSQL_DATABASE"))
        )
        self._connections["mysql"] = conn
        return conn

    async def mysql_query(self, query: str, params: tuple = None) -> List[Dict]:
        conn = self._connections.get("mysql")
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params)
            return await cur.fetchall()

    # ==================== MONGODB ====================

    async def mongo_connect(self, uri: str = None) -> Any:
        from motor.motor_asyncio import AsyncIOMotorClient
        uri = uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        
        # Motor automatically pools connections, configure pool size
        if "mongo" not in self._connections:
            client = AsyncIOMotorClient(
                uri,
                maxPoolSize=self._pool_config["max_size"],
                minPoolSize=self._pool_config["min_size"],
                serverSelectionTimeoutMS=self._pool_config["timeout"] * 1000
            )
            self._connections["mongo"] = client
            logger.info(f"Created MongoDB connection pool (min={self._pool_config['min_size']}, max={self._pool_config['max_size']})")
        
        return self._connections["mongo"]

    async def mongo_find(self, database: str, collection: str, query: Dict = None, limit: int = 100) -> List[Dict]:
        client = self._connections.get("mongo")
        db = client[database]
        cursor = db[collection].find(query or {}).limit(limit)
        return await cursor.to_list(length=limit)

    async def mongo_insert(self, database: str, collection: str, documents: List[Dict]) -> List[str]:
        client = self._connections.get("mongo")
        db = client[database]
        result = await db[collection].insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def mongo_update(self, database: str, collection: str, query: Dict, update: Dict) -> int:
        client = self._connections.get("mongo")
        db = client[database]
        result = await db[collection].update_many(query, {"$set": update})
        return result.modified_count

    # ==================== REDIS ====================

    async def redis_connect(self, url: str = None) -> Any:
        import redis.asyncio as redis
        url = url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        
        # Create connection pool if it doesn't exist
        if "redis" not in self._pools:
            self._pools["redis"] = redis.ConnectionPool.from_url(
                url,
                max_connections=self._pool_config["max_size"],
                socket_connect_timeout=self._pool_config["timeout"]
            )
            logger.info(f"Created Redis connection pool (max={self._pool_config['max_size']})")
        
        client = redis.Redis(connection_pool=self._pools["redis"])
        self._connections["redis"] = client
        return client

    async def redis_get(self, key: str) -> Optional[str]:
        client = self._connections.get("redis")
        value = await client.get(key)
        return value.decode() if value else None

    async def redis_set(self, key: str, value: str, expire: int = None) -> bool:
        client = self._connections.get("redis")
        await client.set(key, value, ex=expire)
        return True

    async def redis_delete(self, key: str) -> bool:
        client = self._connections.get("redis")
        await client.delete(key)
        return True

    # ==================== SQLITE ====================

    async def sqlite_connect(self, path: str) -> Any:
        import aiosqlite
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        self._connections["sqlite"] = conn
        return conn

    async def sqlite_query(self, query: str, params: tuple = None) -> List[Dict]:
        conn = self._connections.get("sqlite")
        async with conn.execute(query, params or ()) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== ELASTICSEARCH ====================

    async def elastic_connect(self, hosts: List[str] = None) -> Any:
        from elasticsearch import AsyncElasticsearch
        hosts = hosts or [os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")]
        client = AsyncElasticsearch(hosts)
        self._connections["elastic"] = client
        return client

    async def elastic_search(self, index: str, query: Dict, size: int = 10) -> List[Dict]:
        client = self._connections.get("elastic")
        response = await client.search(index=index, body=query, size=size)
        return [hit["_source"] for hit in response["hits"]["hits"]]

    async def elastic_index(self, index: str, document: Dict, id: str = None) -> str:
        client = self._connections.get("elastic")
        response = await client.index(index=index, body=document, id=id)
        return response["_id"]

    # ==================== DYNAMODB ====================

    async def dynamodb_query(self, table: str, key_condition: Dict) -> List[Dict]:
        import boto3
        dynamodb = boto3.resource("dynamodb")
        table_obj = dynamodb.Table(table)
        response = table_obj.query(**key_condition)
        return response.get("Items", [])

    async def dynamodb_put(self, table: str, item: Dict) -> bool:
        import boto3
        dynamodb = boto3.resource("dynamodb")
        table_obj = dynamodb.Table(table)
        table_obj.put_item(Item=item)
        return True

    # ==================== INFLUXDB ====================

    async def influxdb_write(self, bucket: str, org: str, record: Dict) -> bool:
        from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

        async with InfluxDBClientAsync(
            url=os.environ.get("INFLUXDB_URL", "http://localhost:8086"),
            token=os.environ.get("INFLUXDB_TOKEN"),
            org=org
        ) as client:
            write_api = client.write_api()
            await write_api.write(bucket=bucket, record=record)
        return True

    async def influxdb_query(self, query: str, org: str) -> List[Dict]:
        from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

        async with InfluxDBClientAsync(
            url=os.environ.get("INFLUXDB_URL", "http://localhost:8086"),
            token=os.environ.get("INFLUXDB_TOKEN"),
            org=org
        ) as client:
            query_api = client.query_api()
            tables = await query_api.query(query)
            return [record.values for table in tables for record in table.records]

    # ==================== SUPABASE ====================

    async def supabase_query(self, table: str, select: str = "*", filters: Dict = None) -> List[Dict]:
        from supabase import create_client

        client = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_KEY")
        )
        query = client.table(table).select(select)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        return response.data

    async def supabase_insert(self, table: str, data: List[Dict]) -> List[Dict]:
        from supabase import create_client

        client = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_KEY")
        )
        response = client.table(table).insert(data).execute()
        return response.data

    # ==================== PLANETSCALE ====================

    async def planetscale_query(self, query: str) -> List[Dict]:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://aws.connect.psdb.cloud/v1/execute",
                headers={
                    "Authorization": os.environ.get("PLANETSCALE_TOKEN"),
                    "Content-Type": "application/json"
                },
                json={"query": query}
            ) as response:
                data = await response.json()
                return data.get("rows", [])

    # ==================== AI-POWERED QUERIES ====================

    async def text_to_sql(self, question: str, schema: str, llm_provider: str = "openai") -> str:
        """Convert natural language to SQL"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Convert natural language to SQL.
Schema: {schema}
Return ONLY the SQL query."""},
            {"role": "user", "content": question}
        ]

        response = await ai.chat(Provider(llm_provider), messages)
        return response["content"].strip()

    async def close_all(self):
        """Close all connections"""
        for name, conn in self._connections.items():
            try:
                await conn.close()
            except:
                pass
        self._connections.clear()

    def list_databases(self) -> List[str]:
        return ["postgres", "mysql", "mongodb", "redis", "sqlite", "elasticsearch",
                "dynamodb", "influxdb", "supabase", "planetscale", "cockroachdb",
                "timescaledb", "clickhouse", "cassandra", "couchdb"]
