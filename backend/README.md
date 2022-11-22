# KidoFood — Backend

The backend code for KidoFood, made with FastAPI ⚡.

Run `pnpm dev` to start the dev server. Or activate the virtualenv and run `uvicorn app:app --port 5450 --reload`

## Structures
This is the folder structure and what it contains:
- `graphql` contains all the GraphQL API models and handler code.
  - `models` contains the GraphQL models.
- `internals` contains all the internal code that the API code use
  - `db` contains the database handling code and also ODM model
  - `models` contains the API response model.
  - `session` contains the session handling system (based on [fastapi-sessions](https://jordanisaacs.github.io/fastapi-sessions/))
- `routes` contains all the sub-routes
