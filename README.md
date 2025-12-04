# SQLAlchemy - Подробная Шпаргалка

## Содержание
1. [Введение](#введение)
2. [Создание Engine и Session](#создание-engine-и-session)
3. [Два стиля работы: ORM и Core](#два-стиля-работы-orm-и-core)
4. [Описание таблиц: Императивное vs Декларативное](#описание-таблиц-императивное-vs-декларативное)
5. [Примеры кода](#примеры-кода)
6. [Сравнительная таблица](#сравнительная-таблица)

---

## Введение

SQLAlchemy - это мощная библиотека Python для работы с базами данных, которая предоставляет два основных подхода:
- **Core** - низкоуровневый SQL-ориентированный подход
- **ORM** - высокоуровневый объектно-реляционный подход

---

## Создание Engine и Session

### Engine (Движок)

**Engine** - это центральный объект SQLAlchemy, который управляет соединениями с базой данных. Он создается один раз для приложения и используется для всех операций с БД.

#### Создание Engine

```python
from sqlalchemy import create_engine

# Базовый синтаксис
engine = create_engine('sqlite:///example.db')

# С параметрами
engine = create_engine(
    'postgresql://user:password@localhost/dbname',
    echo=True,  # Логирование SQL-запросов
    pool_size=5,  # Размер пула соединений
    max_overflow=10,  # Максимальное количество дополнительных соединений
    pool_pre_ping=True,  # Проверка соединений перед использованием
    pool_recycle=3600  # Переиспользование соединений через час
)
```

#### Строки подключения (Connection Strings)

**SQLite:**
```python
# Файловая БД
engine = create_engine('sqlite:///path/to/database.db')

# В памяти
engine = create_engine('sqlite:///:memory:')

# Абсолютный путь (Windows)
engine = create_engine(r'sqlite:///C:\path\to\database.db')
```

**PostgreSQL:**
```python
# Базовый формат
engine = create_engine('postgresql://user:password@localhost/dbname')

# С портом
engine = create_engine('postgresql://user:password@localhost:5432/dbname')

# Используя psycopg2
engine = create_engine('postgresql+psycopg2://user:password@localhost/dbname')

# Используя asyncpg (асинхронный)
engine = create_engine('postgresql+asyncpg://user:password@localhost/dbname')
```

**MySQL:**
```python
# Базовый формат
engine = create_engine('mysql://user:password@localhost/dbname')

# Используя pymysql
engine = create_engine('mysql+pymysql://user:password@localhost/dbname')

# Используя mysqlclient
engine = create_engine('mysql+mysqldb://user:password@localhost/dbname')
```

**SQL Server:**
```python
# Используя pyodbc
engine = create_engine('mssql+pyodbc://user:password@server/dbname?driver=ODBC+Driver+17+for+SQL+Server')
```

### Session (Сессия) - для ORM

**Session** - это объект, который управляет взаимодействием между Python-объектами и базой данных в ORM подходе. Сессия отслеживает изменения объектов и синхронизирует их с БД.

#### Создание Session

```python
from sqlalchemy.orm import sessionmaker, Session

# Создание фабрики сессий
SessionLocal = sessionmaker(bind=engine)

# Создание сессии
session = SessionLocal()

# Использование
try:
    # Работа с данными
    user = User(name='Иван')
    session.add(user)
    session.commit()
except Exception:
    session.rollback()
    raise
finally:
    session.close()
```

#### Контекстный менеджер (рекомендуемый способ)

```python
# Создание фабрики сессий
SessionLocal = sessionmaker(bind=engine)

# Использование с контекстным менеджером
with SessionLocal() as session:
    user = User(name='Иван')
    session.add(user)
    session.commit()
    # Сессия автоматически закроется
```

#### Настройка Session с параметрами

```python
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,  # Автоматический commit (не рекомендуется)
    autoflush=False,  # Автоматический flush перед запросами
    expire_on_commit=True,  # Истечение объектов после commit
    class_=Session  # Класс сессии
)

session = SessionLocal()
```

#### Dependency Injection (для веб-приложений)

```python
from sqlalchemy.orm import sessionmaker

# Создание фабрики
SessionLocal = sessionmaker(bind=engine)

# Функция для получения сессии (например, для FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Использование в FastAPI
from fastapi import Depends

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### Connection (Соединение) - для Core

В Core подходе используется прямое соединение через Engine:

```python
# Прямое соединение
with engine.connect() as connection:
    result = connection.execute(select(users_table))
    for row in result:
        print(row)
    # Соединение автоматически закроется

# С транзакцией
with engine.begin() as connection:
    connection.execute(insert(users_table).values(name='Иван'))
    # Автоматический commit при успехе или rollback при ошибке
```

### Управление транзакциями

#### В ORM (Session)

```python
session = SessionLocal()

try:
    # Начало транзакции (неявно)
    user1 = User(name='Иван')
    user2 = User(name='Петр')
    session.add(user1)
    session.add(user2)
    
    # Явный flush (отправка SQL, но без commit)
    session.flush()
    
    # Commit транзакции
    session.commit()
except Exception:
    # Rollback при ошибке
    session.rollback()
    raise
finally:
    session.close()
```

#### В Core (Connection)

```python
# Автоматическая транзакция
with engine.begin() as conn:
    conn.execute(insert(users_table).values(name='Иван'))
    conn.execute(insert(users_table).values(name='Петр'))
    # Автоматический commit

# Ручное управление
with engine.connect() as conn:
    trans = conn.begin()
    try:
        conn.execute(insert(users_table).values(name='Иван'))
        conn.execute(insert(users_table).values(name='Петр'))
        trans.commit()
    except Exception:
        trans.rollback()
        raise
```

### Пул соединений (Connection Pooling)

SQLAlchemy автоматически управляет пулом соединений:

```python
engine = create_engine(
    'postgresql://user:password@localhost/dbname',
    pool_size=5,  # Количество постоянных соединений
    max_overflow=10,  # Дополнительные соединения при нагрузке
    pool_timeout=30,  # Таймаут ожидания соединения
    pool_recycle=3600,  # Переиспользование соединений (секунды)
    pool_pre_ping=True  # Проверка соединения перед использованием
)
```

### Асинхронные сессии (SQLAlchemy 2.0+)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Асинхронный движок
async_engine = create_async_engine(
    'postgresql+asyncpg://user:password@localhost/dbname',
    echo=True
)

# Асинхронная фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Использование
async with AsyncSessionLocal() as session:
    user = User(name='Иван')
    session.add(user)
    await session.commit()
```

### Рекомендации

1. **Создавайте Engine один раз** при запуске приложения
2. **Используйте контекстные менеджеры** для автоматического закрытия сессий
3. **Всегда обрабатывайте исключения** и делайте rollback при ошибках
4. **Не храните сессии долго** - создавайте их для каждой операции или запроса
5. **Используйте пул соединений** для production приложений
6. **Настройте pool_pre_ping=True** для проверки соединений

---

## Два стиля работы: ORM и Core

### SQLAlchemy Core

**Core** - это низкоуровневый подход, который работает напрямую с SQL-конструкциями. Он предоставляет:
- Прямой контроль над SQL-запросами
- Высокую производительность
- Гибкость в написании сложных запросов
- Меньше абстракций

**Основные компоненты Core:**
- `Engine` - соединение с БД
- `MetaData` - контейнер для описания схемы БД
- `Table` - описание таблицы
- `Column` - описание колонки
- `select()`, `insert()`, `update()`, `delete()` - SQL-конструкции

**Когда использовать Core:**
- Когда нужен полный контроль над SQL
- Для сложных запросов с множеством JOIN
- Когда производительность критична
- Для миграций и административных задач
- Когда не нужна объектная модель

### SQLAlchemy ORM

**ORM** (Object-Relational Mapping) - это высокоуровневый подход, который маппит таблицы БД на Python-классы:
- Автоматическое маппирование объектов на таблицы
- Удобная работа с данными как с объектами
- Автоматическое управление сессиями
- Реляционные связи между объектами

**Основные компоненты ORM:**
- `Session` - сессия для работы с объектами
- `declarative_base()` - базовый класс для моделей
- `relationship()` - описание связей между моделями
- Query API - объектно-ориентированные запросы

**Когда использовать ORM:**
- Для быстрой разработки приложений
- Когда нужна удобная работа с данными
- Для типичных CRUD операций
- Когда важна читаемость кода
- Для работы со связями между таблицами

---

## Описание таблиц: Императивное vs Декларативное

### Императивное описание (Imperative / Table Configuration)

**Императивный стиль** - это явное описание структуры таблицы через объекты `Table` и `Column`. Таблицы описываются отдельно от классов Python.

**Характеристики:**
- Таблицы создаются через `Table()` конструктор
- Классы Python описываются отдельно
- Маппинг между классом и таблицей создается через `mapper()` или `registry.map_imperatively()`
- Больше контроля над процессом
- Более явный и понятный код

**Преимущества:**
- Полный контроль над структурой таблицы
- Можно переиспользовать описание таблицы
- Легче создавать таблицы программно
- Удобно для миграций

**Недостатки:**
- Больше кода
- Дублирование информации (таблица и класс)

### Декларативное описание (Declarative)

**Декларативный стиль** - это описание таблицы и класса в одном месте через наследование от базового класса.

**Характеристики:**
- Класс наследуется от `Base` (созданного через `declarative_base()`)
- Таблица описывается через атрибуты класса (`__tablename__`, `Column`)
- Автоматический маппинг класса на таблицу
- Меньше кода, более Pythonic стиль

**Преимущества:**
- Меньше кода
- Все в одном месте (класс и таблица)
- Более читаемый код
- Стандартный подход в современном SQLAlchemy

**Недостатки:**
- Меньше гибкости для сложных случаев
- Сложнее создавать таблицы динамически

---

## Примеры кода

### 1. Core - Императивное описание таблицы

```python
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.sql import select, insert, update, delete

# Создание движка
engine = create_engine('sqlite:///example.db', echo=True)

# Создание метаданных
metadata = MetaData()

# Императивное описание таблицы
users_table = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50), nullable=False),
    Column('email', String(100), unique=True),
    Column('age', Integer)
)

posts_table = Table(
    'posts',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(200), nullable=False),
    Column('content', String(1000)),
    Column('user_id', Integer, ForeignKey('users.id'))
)

# Создание таблиц
metadata.create_all(engine)

# Работа с данными через Core
with engine.connect() as conn:
    # INSERT
    conn.execute(insert(users_table).values(
        name='Иван',
        email='ivan@example.com',
        age=25
    ))
    conn.commit()
    
    # SELECT
    result = conn.execute(select(users_table))
    for row in result:
        print(row)
    
    # UPDATE
    conn.execute(
        update(users_table)
        .where(users_table.c.id == 1)
        .values(age=26)
    )
    conn.commit()
    
    # DELETE
    conn.execute(delete(users_table).where(users_table.c.id == 1))
    conn.commit()
```

### 2. ORM - Декларативное описание таблицы

```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Создание движка
engine = create_engine('sqlite:///example.db', echo=True)

# Создание базового класса
Base = declarative_base()

# Декларативное описание таблицы
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    age = Column(Integer)
    
    # Связь с постами (ORM feature)
    posts = relationship('Post', back_populates='user')

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(String(1000))
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Связь с пользователем
    user = relationship('User', back_populates='posts')

# Создание таблиц
Base.metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()

# Работа с данными через ORM
# INSERT
user = User(name='Иван', email='ivan@example.com', age=25)
session.add(user)
session.commit()

# SELECT
users = session.query(User).all()
user = session.query(User).filter(User.id == 1).first()

# UPDATE
user.age = 26
session.commit()

# DELETE
session.delete(user)
session.commit()

session.close()
```

### 3. ORM - Императивное описание таблицы

```python
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import registry, sessionmaker, relationship

# Создание движка
engine = create_engine('sqlite:///example.db', echo=True)

# Создание реестра (новый способ в SQLAlchemy 1.4+)
mapper_registry = registry()
metadata = MetaData()

# Императивное описание таблицы
users_table = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50), nullable=False),
    Column('email', String(100), unique=True),
    Column('age', Integer)
)

posts_table = Table(
    'posts',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(200), nullable=False),
    Column('content', String(1000)),
    Column('user_id', Integer, ForeignKey('users.id'))
)

# Python классы
class User:
    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age
    
    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}')>"

class Post:
    def __init__(self, title, content):
        self.title = title
        self.content = content
    
    def __repr__(self):
        return f"<Post(title='{self.title}')>"

# Маппинг класса на таблицу (императивный стиль)
mapper_registry.map_imperatively(User, users_table, properties={
    'posts': relationship(Post, back_populates='user')
})

mapper_registry.map_imperatively(Post, posts_table, properties={
    'user': relationship(User, back_populates='posts')
})

# Создание таблиц
metadata.create_all(engine)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()

# Работа с данными через ORM
user = User(name='Иван', email='ivan@example.com', age=25)
session.add(user)
session.commit()

users = session.query(User).all()
session.close()
```

### 4. Core - Декларативное описание (гибридный подход)

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import select

engine = create_engine('sqlite:///example.db', echo=True)
Base = declarative_base()

# Декларативное описание
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)

Base.metadata.create_all(engine)

# Но работа через Core API
with engine.connect() as conn:
    result = conn.execute(select(User.__table__))
    for row in result:
        print(row)
```

---

## Сравнительная таблица

| Критерий | Core | ORM |
|----------|------|-----|
| **Уровень абстракции** | Низкий (близко к SQL) | Высокий (объекты Python) |
| **Производительность** | Выше | Ниже (но обычно достаточно) |
| **Контроль над SQL** | Полный | Ограниченный |
| **Читаемость кода** | Средняя | Высокая |
| **Сложность запросов** | Легко писать сложные | Может быть сложнее |
| **Связи между таблицами** | Вручную через JOIN | Автоматически через relationship() |
| **Использование** | Сложные запросы, миграции | Типичные CRUD операции |

| Критерий | Императивное | Декларативное |
|----------|--------------|---------------|
| **Синтаксис** | `Table()` + `mapper()` | Наследование от `Base` |
| **Разделение** | Таблица и класс отдельно | Все в одном классе |
| **Гибкость** | Выше | Ниже |
| **Количество кода** | Больше | Меньше |
| **Читаемость** | Средняя | Выше |
| **Динамическое создание** | Легче | Сложнее |
| **Стандартность** | Менее распространен | Стандартный подход |

---

## Рекомендации по выбору

### Когда использовать Core:
- ✅ Сложные аналитические запросы
- ✅ Высоконагруженные системы
- ✅ Миграции и административные задачи
- ✅ Когда нужен полный контроль над SQL

### Когда использовать ORM:
- ✅ Типичные веб-приложения
- ✅ CRUD операции
- ✅ Работа со связями между таблицами
- ✅ Быстрая разработка

### Когда использовать императивный стиль:
- ✅ Динамическое создание таблиц
- ✅ Переиспользование описаний таблиц
- ✅ Сложные схемы БД
- ✅ Миграции

### Когда использовать декларативный стиль:
- ✅ Стандартные приложения
- ✅ Когда нужна читаемость
- ✅ Типичные модели данных
- ✅ **Рекомендуется по умолчанию**

---

## Дополнительные примеры

### Связи в ORM (relationship)

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    
    # One-to-Many
    posts = relationship('Post', back_populates='user')
    
    # Many-to-Many (через промежуточную таблицу)
    roles = relationship('Role', secondary='user_roles', back_populates='users')

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Many-to-One
    user = relationship('User', back_populates='posts')
```

### Сложные запросы в Core

```python
from sqlalchemy import select, func, and_, or_

# JOIN
query = select(users_table, posts_table).join(
    posts_table, users_table.c.id == posts_table.c.user_id
)

# Агрегация
query = select(
    users_table.c.name,
    func.count(posts_table.c.id).label('post_count')
).join(
    posts_table, users_table.c.id == posts_table.c.user_id
).group_by(users_table.c.id)

# Условия
query = select(users_table).where(
    and_(
        users_table.c.age > 18,
        or_(
            users_table.c.name.like('%Иван%'),
            users_table.c.email.contains('example')
        )
    )
)
```

### Сложные запросы в ORM

```python
from sqlalchemy.orm import joinedload, subqueryload

# Eager loading (загрузка связанных данных)
users = session.query(User).options(
    joinedload(User.posts)
).all()

# Подзапросы
from sqlalchemy import func
subquery = session.query(
    func.count(Post.id).label('post_count')
).filter(Post.user_id == User.id).scalar_subquery()

users = session.query(User, subquery.label('post_count')).all()

# Фильтрация и сортировка
users = session.query(User).filter(
    User.age > 18
).order_by(User.name).limit(10).all()
```

---

## Заключение

SQLAlchemy предоставляет гибкие инструменты для работы с БД:
- **Core** для максимального контроля и производительности
- **ORM** для удобной работы с объектами
- **Императивный стиль** для гибкости
- **Декларативный стиль** для простоты и читаемости

Выбор зависит от конкретных требований проекта, но в большинстве случаев рекомендуется использовать **ORM с декларативным стилем** как наиболее удобный и современный подход.

