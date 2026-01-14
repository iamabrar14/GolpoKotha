# Testing Guide

## 1) Unit tests (pytest)

### Install dev dependencies
```bash
pip install -r requirements-dev.txt
pip install -r requirements.txt
```

### Run all tests
```bash
pytest -q
```

### Covered
- Registration, login, logout flow
- Create post (auth required)
- Owner-only edit/delete
- Comment requires login
- Pagination on home
- Case-insensitive usernames and login

---

## 2) Manual / Postman testing

### Common endpoints
- GET `/` – paginated feed
- GET `/posts` – paginated all posts
- GET `/register` – register form
- POST `/register` – create user (`username`, `password`) — case-insensitive uniqueness
- GET `/login` – login form
- POST `/login` – login (`username`, `password`) — case-insensitive
- GET `/logout` – logout
- GET `/dashboard` – your posts (auth)
- GET `/post/new` – new post form (auth)
- POST `/post/new` – create post (auth) – fields: `title`, `content`
- GET `/post/<id>` – detail and comments
- POST `/post/<id>` – add comment (auth) – field: `comment_content`
- GET `/post/<id>/edit` – edit form (auth, owner-only)
- POST `/post/<id>/edit` – submit edit (auth, owner-only)
- POST `/post/<id>/delete` – delete (auth, owner-only)

### Postman collection
Import `postman/TikBlog.postman_collection.json`. Ensure `baseUrl` matches your server (defaults to `http://127.0.0.1:5000`).

**Auth flow in Postman**: run **Login** first to set the session cookie. Then create/edit/delete/comment will work. Enable *Automatically follow redirects* in Postman settings.
