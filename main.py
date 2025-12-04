from sqlalchemy.orm.session import Session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
from sqlalchemy import create_engine, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import (
    sessionmaker,
    Mapped,
    mapped_column,
    relationship,
    joinedload,
)

engine = create_engine("sqlite:///example.db", echo=True)
SessionLocal = sessionmaker[Session](
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)


def get_session():
    return SessionLocal()


# Base = declarative_base()
class Base(DeclarativeBase): ...


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    age: Mapped[int] = mapped_column(Integer)

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="user")

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email}, age={self.age}, tasks={self.tasks})"


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"Task(id={self.id}, title={self.title}, description={self.description}, completed={self.completed})"


Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


class UserRepository:
    def create_user(self, name: str, email: str, age: int) -> User:
        with get_session() as session:
            try:
                user = User(name=name, email=email, age=age)
                session.add(user)
                session.commit()
                return user
            except Exception as e:
                session.rollback()
                raise e

    def get_user(self, filter_by: dict = None) -> User | None:
        if filter_by is None:
            filter_by = {}
        with get_session() as session:
            return (
                session.query(User)
                .filter_by(**filter_by)
                .options(joinedload(User.tasks))
                .first()
            )

    def get_users(self, filter_by: dict = None) -> list[User]:
        if filter_by is None:
            filter_by = {}
        with get_session() as session:
            return (
                session.query(User)
                .filter_by(**filter_by)
                .options(joinedload(User.tasks))
                .all()
            )

    def update_user(self, filter_by: dict = None, **kwargs) -> User:
        if filter_by is None:
            filter_by = {}
        with get_session() as session:
            try:
                session.query(User).filter_by(**filter_by).update(kwargs)
                session.commit()
                return (
                    session.query(User)
                    .filter_by(**filter_by)
                    .options(joinedload(User.tasks))
                    .first()
                )
            except Exception as e:
                session.rollback()
                raise e

    def get_users_tasks_count(self) -> list[tuple[int, str, int]]:
        with get_session() as session:
            return (
                session.query(
                    User.id, User.name, func.count(Task.id).label("tasks_count")
                )
                .outerjoin(Task)
                .group_by(User.id)
                .all()
            )


class TaskRepository:
    def create_task(
        self, title: str, description: str, completed: bool, user_id: int = None
    ) -> Task:
        with get_session() as session:
            try:
                task = Task(
                    title=title,
                    description=description,
                    completed=completed,
                    user_id=user_id,
                )
                session.add(task)
                session.commit()
                return task
            except Exception as e:
                session.rollback()
                raise e

    def get_task(self, filter_by: dict = None) -> Task | None:
        if filter_by is None:
            filter_by = {}
        with get_session() as session:
            return session.query(Task).filter_by(**filter_by).first()


user_repository = UserRepository()
task_repository = TaskRepository()

user1 = user_repository.create_user("John Doe", "john.doe@example.com", 30)
user2 = user_repository.create_user("John Snow", "john2.doe@example.com", 33)
user3 = user_repository.create_user("John 3", "john3.doe@example.com", 11)

task = task_repository.create_task(
    "Buy groceries", "Buy groceries", False, user_id=user1.id
)
task1 = task_repository.get_task(filter_by={"id": 1})

user1 = user_repository.get_user()
print("User 1", user1)

users = user_repository.get_users()
print("All users", users)

updated_user = user_repository.update_user(filter_by={"id": user1.id}, age=111)
print("Updated user", updated_user)

users_tasks_count = user_repository.get_users_tasks_count()
print("Users tasks count", users_tasks_count)
