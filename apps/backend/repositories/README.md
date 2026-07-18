# repositories/

Data-access layer. Encapsulates all database queries (SQLAlchemy) behind repository interfaces.

- One repository per aggregate/entity.
- Services depend on repositories, not on the ORM session directly.
- Keeps persistence concerns isolated and unit-testable via fakes.
